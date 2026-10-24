# 06 — The LLM and the agent loop inside the harness

The same model that keeps a vault key out of sgit's hands can keep secrets out of an agent's context and narrow what an agent's tools can do. This document shows how a message actually flows in the measured environment, where the harness plugs in, and the two new components: `sharness.llm` and `sharness.bash`.

## 1. How a message flows today (observed)

Observed on 24 Oct 2026 in a Claude agent workspace (claude.ai, cloud session). Roles of processes 89 and 96 are inferred from their names, arguments, environment variable names and connections; TLS traffic was not inspected.

```
 you (claude.ai app)
   │ HTTPS
   ▼
 Anthropic backend ──(session ingress)──► environment-manager           PID 89, root
                                            │ stdin                     own HTTPS → 160.79.104.10:443
                                            ▼
                                 Claude Code harness 2.1.42             PID 96, root
                                 /opt/claude-code/bin/claude            ~18 HTTPS conns → 160.79.104.10:443
                                   ANTHROPIC_BASE_URL=https://api.anthropic.com
                                   credentials in ANTHROPIC_CUSTOM_HEADERS (not read)
                                   /etc/hosts pins api.anthropic.com → 160.79.104.10
                                   api.anthropic.com in no_proxy → bypasses the egress proxy
                                            │ POST /v1/messages (stream)
                                            ▼
                                 model ──► text and/or tool_use blocks
                                            │
                                 harness, per tool_use:
                                   PreToolUse hooks → run tool LOCALLY → PostToolUse hooks
                                   Bash = child process of PID 96, root, full capabilities, network
                                   append tool_result → POST /v1/messages again → … end of turn
                                            │
                                 events ─► environment-manager ─► backend ─► app
```

Other processes: PID 1 `/process_api` (VM init, vsock control), `sbx-telemetry-collector` (uid 64321), `rclone-filestore` (file storage mounts).

### 1.1 The request
A standard Messages API call: `model`, `system`, `tools` (each with an `input_schema`), `messages` (the whole history, including every `tool_use` and every `tool_result`), `max_tokens`, `stream: true`.

### 1.2 Who sees what
| Party | Sees |
|---|---|
| harness | everything; it builds the request |
| hooks | events: the user prompt, each tool call's input, each tool's output — not the raw request |
| the model | the assembled context |
| transcript / logs | every `tool_result` — which is why a printed key leaks |

### 1.3 What protects the harness's own configuration (read-only check)
| Item | State |
|---|---|
| `/opt/claude-code` (binary) | read-only mount |
| running harness environment | fixed at start by environment-manager |
| `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=1` | set — suggests host-managed provider settings; untested |
| `/root/.claude/settings.json` | writable by root; no `/etc/claude-code/` managed settings |
| `/etc/hosts` | writable by root; modified mid-session (something maintains it) |
| kernel modules | disabled (`nomodule`) |

## 2. Where the harness plugs in

| # | Injection point | Exists today in Claude Code? | What moves out of the harness |
|---|---|---|---|
| 1 | `ANTHROPIC_BASE_URL` → `sharness.llm` | yes (env var / SDK `base_url`) | model credentials, request/response policy, secret filtering, audit |
| 2 | tools as **MCP servers**, built-in tools denied by permission settings | yes | tool execution, tool input schemas |
| 3 | one-line hook rewriting Bash to `sharness.bash` | believed yes (PreToolUse returning modified input) — **verify on the version used**; otherwise deny Bash and use the MCP route | shell execution |
| 4 | launcher applies Landlock/seccomp/uid to the harness before it starts | not a Claude Code feature; a launcher feature | the ability to bypass 1–3 (07) |
| 5 | the platform (environment-manager, process_api) | platform only | everything above, as a Boundary for the agent itself |

Hooks become routing: verify the policy hash, forward to a component. Data, not code.

## 3. `sharness.llm`

A Messages API endpoint with a Process Behaviour Policy. It sits where `ANTHROPIC_BASE_URL` points.

```
 harness (Claude Code / SDK / own loop)
   │ POST /v1/messages   (dummy API key)
   ▼
 sharness.llm  (uid harness-llm; only uid allowed to reach 160.79.104.10:443)
   1. TLS peer is the app; policy hash matches
   2. request schema: model ∈ allowlist; tools list hash = pinned; max_tokens ≤ budget;
      no tool definitions outside the pinned set
   3. SECRET FILTER on every tool_result and user content: refuse or redact anything parsing as
      a vault key, PEM private key, API key pattern, bearer token, m1 opened payload
   4. get real API key from harness.kms (sealed to llm's one-time key), add auth header
   5. forward to api.anthropic.com; stream response back unchanged
   6. on each completed tool_use block: validate input against that tool's input_schema
      and business rules → log; flag violations (enforcement happens at the tool component)
   7. audit: model, tokens, tools called, filter hits — never content of secrets
```

Design choices:
- **Don't rewrite responses.** The client records the assistant message as received; rewriting breaks the conversation and prompt caching. Enforce tool calls where they execute.
- **Do filter requests.** The request is the only path into the model's context and into the transcript; filtering there closes the transcript leak for every tool at once.
- **Pin by hash, normalise first.** Claude Code's system prompt contains dynamic parts (dates, environment). Pin the tools list exactly; pin the system prompt by a normalised prefix or not at all.
- **The API key is a sealed secret.** It arrives as a sealed handover to `harness.kms`, exactly like a vault key. The harness process holds a dummy.

### 3.1 Compatibility
`harness.llm` speaks the Messages API unchanged, so:
- Claude Code anywhere: `ANTHROPIC_BASE_URL=https://127.0.0.1:<port>`;
- Agent SDK and Anthropic SDKs: same env var or `base_url`;
- your own orchestrator: just another client;
- later: an OpenAI-compatible front for other clients.

Prior art: LLM gateways (LiteLLM, Portkey, Cloudflare AI Gateway) proxy this API for routing, keys and logging. New here: policy-hash enforcement, the secret filter on tool results, sealed API-key delivery, and the gateway as one locked component among several.

## 4. `sharness.bash`

Bash is the escape hatch from every other component: while the model can run any command as root with network, the policies on `.fs`, `.net` and `.kms` mean little. In the measured session every command ran as root.

A command is free text, so **no schema can bound its intent**. Enforcement is on what the process can do.

| Lock | Setting |
|---|---|
| uid | one ephemeral uid per session (~49 ms to create, measured), never root |
| pid namespace | cannot see or signal the harness or any component (~4 ms, measured) |
| process count | `pids` cgroup limit (e.g. 64). Not `RLIMIT_NPROC=0` — a shell must fork |
| files | Landlock: workspace per profile; `/usr` read-only; no other component's folders or sockets; workspace has **no execute right** |
| network | none by default (empty netns); when allowed, only via `harness.net` |
| seccomp | deny `ptrace`, `mount`, `keyctl`, `bpf`, `unshare`, `execveat`, … |
| capabilities | none; `no_new_privs` |
| output | stdout/stderr pass the same secret filter before becoming `tool_result` |

### 4.1 Profiles (chosen by policy, requested by the model)
| Profile | Files | Network | Approval |
|---|---|---|---|
| `analyse` | workspace read-only | none | none |
| `build` | workspace read-write | package registries + GitHub via `harness.net` | none |
| `admin` | as needed (e.g. `useradd`, `iptables`, cgroups) | as needed | fresh approval from the person each time |

### 4.2 How it plugs in
- an MCP server named `bash`, with the built-in Bash tool denied; or
- a PreToolUse hook that rewrites each Bash call to `sharness-bash-client --profile <p> -- <cmd>`.

Either way the hook holds no logic. Making it impossible to *skip* is document 07.

## 5. Untrusted text: two models, two components

Schemas bound shape, not intent, and free text (web pages, vault files) is where injection enters. The strongest known pattern splits the model's roles (Simon Willison's dual-LLM pattern; Google DeepMind's CaMeL formalises it):

```
 privileged model (plans, calls tools)          quarantined model (reads untrusted text)
   never sees untrusted text directly    ──►      sees untrusted text, has NO tools
   gets back only schema-typed values    ◄──      output constrained to a JSON schema
                                                   (e.g. {"title": str ≤ 80, "date": iso8601})
```

In the harness these are two `harness.llm` policies (two uids, two tool sets) with the quarantined one's output schema enforced on the edge back to the orchestrator.

## 6. The full set

```
 sharness.llm (model calls)    sharness.bash (shell)
            ▲                               ▲
            │                               │
 orchestrator ───── routes ─────────────────┴──► sgit-cli ──► sharness.fs
 (Claude Code / own loop)                                └──► sharness.net ──► sharness.kms
```

The orchestrator holds no keys and runs no tools itself; it routes messages between components that each have their own policy.
