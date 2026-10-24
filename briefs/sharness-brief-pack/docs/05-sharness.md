# 05 — SHarness

Documents 01–04 designed four components to keep a vault key out of the transcript. Nothing in that design is specific to sgit. What it actually describes is a **harness**: a launcher plus a small set of single-purpose components that any process — sgit, a shell, an LLM agent loop — runs inside, each under its own Process Behaviour Policy, talking only over allowed edges.

sgit then has one job: **be compatible with running inside SHarness.**

Not to be confused with *Sharness*, the unrelated shell test library derived from Git's test suite (felipec/sharness). See §1.1.

## 1. Naming

| Name | Meaning |
|---|---|
| **SHarness** | the whole thing: launcher + components + policies. Official name (24 Oct 2026): domain sharness.ai, GitHub org SHarness-AI, PyPI `sharness-ai`. It grew out of sgit and uses sgit's PKI; sgit is its first harnessed app |
| `sharness.<role>` | one component. The role is the noun for its one job |
| **harnessed app** | a program running inside the harness (sgit, a shell command, an agent) |
| **harness-aware** | an app that speaks the harness protocol directly (asks `.kms` for keys, `.net` for operations) |
| **transparent** | an unmodified app that works because the harness presents ordinary interfaces (a proxy, a mount) |

### 1.1 Identity and naming rules

| Item | Value |
|---|---|
| Brand | **SHarness** (capital S, capital H) |
| Domain | sharness.ai |
| GitHub org | github.com/SHarness-AI |
| Repositories | `SHarness-AI__CLI` (the code), `SHarness-AI__Website` (the site) |
| PyPI distribution | `sharness-ai` |
| Python import | `sharness_ai` (proposed) |
| Component names | `sharness.<role>` |
| Command name | **open.** Avoid plain `sharness`: that is the Debian/pkgsrc/OpenBSD package and file name of the unrelated shell test library. Candidate: `sharness-ai` |
| Environment variable prefix | `SHARNESS_AI_` (proposed). Avoid `SHARNESS_`, which the shell test library uses |
| Disambiguation line | "SHarness is unrelated to Sharness, the shell testing library." |

Theme: one role, one noun, one uid, one policy, one certificate.

| Component | Role | Was (01–04) |
|---|---|---|
| `sharness.launcher` | verifies the policy hash, makes uids, session CA, certificates; starts, freezes and stops components | launcher |
| `sharness.kms` | holds private keys and secrets; opens sealed things; re-seals to one-time keys | sgit-kms |
| `sharness.net` | the only network client; host, endpoint and id allowlists; TLS client | sgit-net |
| `sharness.fs` | the only writer of protected folders; path and content rules | sgit-fs |
| `sharness.bash` | runs shell commands, each in a fresh sandbox, under a profile | new (06, 07) |
| `sharness.llm` | the only client of the model API; request/response schemas; secret filter on tool results; holds the API key via `.kms` | new (06) |
| `sharness.policy` | not a process: the manifest, its layers, its hash | PBP (03) |

The app-specific orchestrator (sgit-cli, or an agent loop such as Claude Code) sits on top and routes. It holds nothing and runs nothing itself.

## 2. The generic picture

```
                      person: supplies manifest hash sha256:M, carries sealed QR codes
                                                  │
 ┌─────────────────────────────── sharness.launcher (outside every domain) ──────────────────────────────┐
 │                                                                                                            │
 │   harnessed app / orchestrator  (no keys, no tools of its own, Landlock exec allowlist)                    │
 │        │            │              │               │                                                       │
 │        ▼            ▼              ▼               ▼                                                       │
 │   harness.fs   harness.net    harness.bash    harness.llm ─────────► model API (api.anthropic.com)          │
 │   (writes)     (network) ─┐   (sandboxes)          │                                                        │
 │                           │                        │                                                        │
 │                           └──────► harness.kms ◄───┘   (vault keys, API keys, any sealed secret)            │
 │                                                                                                            │
 │   every edge: mutual TLS, roles in certificates, schemas on the payload, both sides check                  │
 │   every component: own uid, own PBP, kernel-enforced                                                        │
 └────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Edges (deny by default):

```
 caller ↓  callee →   fs     net    bash   llm    kms
 app/orchestrator     ✔      ✔      ✔      ✔      ✗
 net                  ✗      —      ✗      ✗      ✔
 llm                  ✗      ✗      ✗      —      ✔
 bash (sandbox)       ✗      ✔*     —      ✗      ✗      * only if the profile allows network
 fs, kms              ✗      ✗      ✗      ✗      —
```

## 3. Two ways to be compatible

Running an unmodified app in the harness breaks it: it tries to write where it may not, connect where it may not, read keys that are not there. There are two ways to make it work.

### 3.1 Transparent (no app changes)
The harness presents ordinary interfaces backed by its components:

| App expects | Harness presents |
|---|---|
| a writable folder | a bind mount or FUSE mount served by `harness.fs` |
| the internet | `HTTPS_PROXY` pointing at `harness.net` (CONNECT with host allowlist) |
| a model API | `ANTHROPIC_BASE_URL` pointing at `harness.llm` |
| a shell | `harness.bash` as an MCP server, or a one-line hook rewriting to the client |
| a secret in an env var or file | **nothing** — this is the case transparency cannot cover safely |

Good for: build tools, test runners, most CLIs, Claude Code itself (06).

### 3.2 Harness-aware (small app changes)
The app speaks the harness protocol for the things transparency can't do — mostly **secrets**. For sgit:

| Change | Size |
|---|---|
| one `Key_Source` interface; backed by `harness.kms` when `SGIT_HARNESS` is set | the "door" refactor (01 §7 step 1–2) |
| `clone --sealed`, `vault_key.sealed`, `vault seal --to`, refuse plain keys on argv | small, local to the CLI |
| (later) vault crypto and server I/O move into a `harness.net` plug-in | the full split (01 §7 step 3) |

Everything else in sgit — file writes, server calls — can start transparent (mount + proxy) and move to harness-aware only where a business rule needs to see sgit's protocol (vault-id allowlists, sealed-only `.sg_vault/local`).

**The rule:** an app needs harness awareness only where it handles secrets or where a policy must understand its protocol. Everything else is transparent.

## 4. As little code as possible

Most of the harness is configuration of things Linux and Python already have:

| Need | Use | Not |
|---|---|---|
| process isolation | uids, `setpriv`, namespaces (`unshare`), Landlock, seccomp, cgroups | a custom sandbox |
| transport + identity | stdlib `ssl`, `cryptography` for the session CA | a custom protocol or a mesh |
| schemas | JSON Schema (and MCP `inputSchema` for tools) | hand-written validators |
| policy | canonical JSON + SHA-256 + an existing signature (sgit PKI) | a policy language |
| tracing a policy | `strace` | a tracer |
| secret storage | `memfd_secret`, cgroup freezer, kernel keyring | an HSM emulator |

Size targets (proposed): launcher ≤ 400 lines; each component ≤ 300; a shared `harness_lib` (Landlock, mTLS, framing, schema check) ≤ 400. Components must be small enough to read in one sitting — that is part of their security.

## 5. Policy in the harness

The manifest (03 §6) gains one entry per component, including `bash` profiles and `llm` schemas. Composition is still intersection; the hash the person supplies still covers everything, including the session CA certificate and the code hashes of every component.

```json
{
  "pbp_manifest": 1,
  "harness": "sharness/0.1",
  "session_ca_cert_sha256": "…",
  "components": {
    "kms":  {"policy": "sha256:…", "code": "sha256:…"},
    "net":  {"policy": "sha256:…", "code": "sha256:…"},
    "fs":   {"policy": "sha256:…", "code": "sha256:…"},
    "bash": {"policy": "sha256:…", "code": "sha256:…", "profiles": ["analyse", "build", "admin"]},
    "llm":  {"policy": "sha256:…", "code": "sha256:…", "tools_sha256": "…"}
  },
  "apps": {
    "sgit":        {"policy": "sha256:…", "mode": "harness-aware"},
    "claude-code": {"policy": "sha256:…", "mode": "transparent", "exec_allow": ["node", "rg", "sharness-bash-client"]}
  },
  "edges": [["app","fs"],["app","net"],["app","bash"],["app","llm"],["net","kms"],["llm","kms"],["bash","net"]]
}
```

## 6. Where enforcement lives (unchanged rule)

Locks applied by the agent to itself are *Settings*; locks applied by the launcher, above the agent, are *Boundaries* (03 §2). The harness is only as strong as whoever runs `sharness.launcher`:

| Who runs the launcher | Result |
|---|---|
| the agent, inside its own session | Boundary for everything the agent starts; Setting for the agent itself |
| a script that starts Claude Code on your machine | Boundary for Claude Code and everything below it |
| the agent platform (environment-manager / process_api here) | Boundary all the way down — the end state |
