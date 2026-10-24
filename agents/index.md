# Agents and LLMs

> **Status: design.** §1 is a read-only observation made as of 24 Oct 2026 in one Claude agent workspace (claude.ai, cloud session); it may differ elsewhere and later. Everything from §2 on is proposed.

The same model that keeps a vault key out of sgit's hands can keep secrets out of an agent's context and narrow what an agent's tools can do. This page shows how a message flowed in the observed environment, where SHarness plugs in, and the two components for agents: `sharness.llm` and `sharness.bash`.

## 1. How a message flows (observed)

Observed on 24 Oct 2026. The roles of processes 89 and 96 are inferred from their names, arguments, environment variable *names* and connections. TLS traffic was not inspected, no credentials or session identifiers were captured, and no configuration was changed.

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

The request is a standard Messages API call: `model`, `system`, `tools` (each with an `input_schema`), `messages` (the whole history, including every `tool_use` and every `tool_result`), `max_tokens`, `stream: true`.

| Party | Sees |
|---|---|
| the harness | everything; it builds the request |
| hooks | events: the user prompt, each tool call's input, each tool's output; not the raw request |
| the model | the assembled context |
| transcript and logs | every `tool_result`, which is why a printed key leaks |

## 2. Where SHarness plugs in

| # | Injection point | Exists in Claude Code? | What moves out of the harness |
|---|---|---|---|
| 1 | `ANTHROPIC_BASE_URL` → `sharness.llm` | yes (env var / SDK `base_url`) | model credentials, request and response policy, secret filtering, audit |
| 2 | tools as **MCP servers**, built-in tools denied by permission settings | yes | tool execution, tool input schemas |
| 3 | a one-line hook rewriting Bash to `sharness.bash` | believed yes (PreToolUse returning modified input): **verify on the version used**; otherwise deny Bash and use the MCP route | shell execution |
| 4 | the launcher applies Landlock, seccomp and a uid to the harness before it starts | not a Claude Code feature; a launcher feature | the ability to bypass 1–3 (see [Enforcing the process tree](../process-tree/index.md)) |
| 5 | the platform runs the launcher | platform only | everything above, as a Boundary for the agent itself |

Hooks become routing: verify the policy hash, forward to a component. Data, not code.

## 3. sharness.llm

A Messages API endpoint with a Process Behaviour Policy, sitting where `ANTHROPIC_BASE_URL` points.

```
 harness (Claude Code / SDK / own loop)
   │ POST /v1/messages   (dummy API key)
   ▼
 sharness.llm  (own uid; the only uid allowed to reach the model API)
   1. TLS peer is the app; policy hash matches
   2. request schema: model ∈ allowlist; tools list hash = pinned; max_tokens ≤ budget;
      no tool definitions outside the pinned set
   3. SECRET FILTER on every tool_result and user content: refuse or redact anything parsing as
      a vault key, PEM private key, API key pattern, bearer token, m1 opened payload
   4. get the real API key from sharness.kms (sealed to llm's one-time key), add the auth header
   5. forward to the model API; stream the response back unchanged
   6. on each completed tool_use block: validate input against that tool's input_schema
      and business rules → log; flag violations (enforcement happens at the tool component)
   7. audit: model, tokens, tools called, filter hits — never the content of secrets
```

Design choices:

- **Don't rewrite responses.** The client records the assistant message as received; rewriting breaks the conversation and prompt caching. Enforce tool calls where they execute.
- **Do filter requests.** The request is the only path into the model's context and into the transcript; filtering there closes the transcript leak for every tool at once.
- **Pin by hash, normalise first.** A harness's system prompt contains dynamic parts (dates, environment). Pin the tools list exactly; pin the system prompt by a normalised prefix or not at all.
- **The API key is a sealed secret.** It arrives as a sealed handover to `sharness.kms`, exactly like a vault key. The harness process holds a dummy.

### Claude API compatibility

`sharness.llm` speaks the Messages API unchanged, so:

- Claude Code anywhere: `ANTHROPIC_BASE_URL=https://127.0.0.1:<port>`;
- the Agent SDK and Anthropic SDKs: the same environment variable, or `base_url`;
- your own orchestrator: just another client;
- later: an OpenAI-compatible front for other clients.

Prior art: LLM gateways (LiteLLM, Portkey, Cloudflare AI Gateway) proxy this API for routing, keys and logging. New here: policy-hash enforcement, the secret filter on tool results, sealed API-key delivery, and the gateway as one locked component among several.

## 4. sharness.bash

Bash is the escape hatch from every other component: while the model can run any command as root with network, the policies on `.fs`, `.net` and `.kms` mean little. In the observed session every command ran as root. A command is free text, so no schema can bound its intent: enforcement is on what the process can do. The locks and profiles are on [Components](../components/index.md#sharness-bash).

It plugs in either as an MCP server named `bash` with the built-in Bash tool denied, or as a PreToolUse hook that rewrites each Bash call to `sharness-bash-client --profile <p> -- <cmd>`. Either way the hook holds no logic. Making it impossible to *skip* is [Enforcing the process tree](../process-tree/index.md).

## 5. Untrusted text: two models, two components

Schemas bound shape, not intent, and free text (web pages, vault files) is where injection enters. The strongest known pattern splits the model's roles (Simon Willison's dual-LLM pattern; Google DeepMind's CaMeL formalises it):

```
 privileged model (plans, calls tools)          quarantined model (reads untrusted text)
   never sees untrusted text directly    ──►      sees untrusted text, has NO tools
   gets back only schema-typed values    ◄──      output constrained to a JSON schema
                                                   (e.g. {"title": str ≤ 80, "date": iso8601})
```

In SHarness these are two `sharness.llm` policies (two uids, two tool sets), with the quarantined one's output schema enforced on the edge back to the orchestrator.

## 6. The full set

```
 sharness.llm (model calls)    sharness.bash (shell)
            ▲                               ▲
            │                               │
 orchestrator ───── routes ─────────────────┴──► sgit ──► sharness.fs
 (Claude Code / own loop)                            └──► sharness.net ──► sharness.kms
```

The orchestrator holds no keys and runs no tools itself; it routes messages between components that each have their own policy.

Source: [06-llm-and-the-agent-loop](../briefs/sharness-brief-pack/docs/06-llm-and-the-agent-loop.md).
