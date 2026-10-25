# Components

> **Status: design.** Every component below is proposed; none is built. Measured figures are as of 24 Oct 2026, in one Claude agent workspace.

| Component | Its one job | Was (early docs) |
|---|---|---|
| the harnessed app | orchestrates: parses the command, calls the components, renders output; holds no keys | sgit-cli |
| `sharness.launcher` | verifies the policy hash; makes uids, the session CA and certificates; starts, freezes and stops components | launcher |
| `sharness.kms` | holds private keys and secrets; opens sealed things; re-seals to one-time keys | sgit-kms |
| `sharness.net` | the only network client: host, endpoint and id allowlists; the TLS client | sgit-net |
| `sharness.fs` | the only writer of protected folders: path and content rules | sgit-fs |
| `sharness.bash` | runs shell commands, each in a fresh sandbox, under a profile | new |
| `sharness.llm` | the only client of the model API: request and response schemas, a secret filter on tool results, the API key held via `.kms` | new |
| `sharness.policy` | not a process: the manifest, its layers, its hash | Process Behaviour Policy |

Where the components sit and which may talk to which is on [Architecture](../architecture/index.md).

## The harnessed app (for sgit: its CLI)

| | |
|---|---|
| Job | parse the user's command, call `sharness.fs` and `sharness.net`, render output |
| Holds | no key of any kind; sees file **contents** (it must, to show diffs) |
| Talks to | `.fs` and `.net` only |
| Files | read-only on the clone folder; writes nothing (every write goes through `.fs`) |
| Network | none: a network namespace with only loopback, or Landlock network rules allowing only the `.fs` and `.net` ports |
| Lockdown | its own uid, all capabilities dropped, `no_new_privs`, `RLIMIT_NPROC=0`, Landlock, a seccomp allowlist |
| Refuses | `show-key` on a sealed clone without `--reveal`; any plain vault key on argv (all 14 sgit commands that take one) |

An agent loop such as Claude Code is the same role for agents: it routes, and runs nothing itself (see [Agents and LLMs](../agents/index.md#6-the-full-set)).

## sharness.launcher

Runs outside every domain. In order:

1. Read the policy manifest, compute its hash, and **refuse to continue unless it matches the hash the person supplied** or the manifest carries a valid signature from the root key.
2. Create one ephemeral uid per component (measured: user + firewall rule + locked launch + teardown ≈ 49 ms).
3. Create the session CA and the role certificates; destroy the CA key; record the CA certificate hash.
4. Start `sharness.kms`; it makes the session identity and prints **only** the public bundle (`k1`); freeze it.
5. Per command, start the other components under their policies (new namespaces ≈ 4 ms, measured), let them run, tear them down.
6. At session end, thaw and kill `sharness.kms`; delete users, firewall rules and sockets.

**Who runs the launcher decides what the locks are.** If the agent runs it inside its own session, the locks are a Boundary for everything the agent starts but only a Setting for the agent itself (in the measured environment the agent is root and could undo them). A script that starts the agent makes them a Boundary for the agent; the platform running the launcher makes them a Boundary all the way down.

## sharness.kms

| | |
|---|---|
| Job | open a sealed message addressed to its identity, check it, derive keys, re-seal them to the caller's one-time key |
| Holds | the session identity's private key (made inside, never exported); the nonce record |
| Answers | `sharness.net` and `sharness.llm` only |
| Files / network | none (Landlock with no filesystem rights after start; empty network namespace) |
| Lifetime | frozen between requests: thaw → answer → freeze (0.13 ms / 0.28 ms, measured) |

It **never returns a clear key**. Protocol and key lifetime: [Keys and the KMS](../keys/index.md).

## sharness.net

| | |
|---|---|
| Job | every byte to and from the outside; the KMS client; (in the full split) all vault encryption, decryption and signing |
| Holds | derived read/write keys for **one command**, in a `memfd_secret` page; never the vault key |
| Business rules | host allowlist; endpoint allowlist; vault-id allowlist; read-only vs read-write per policy; no redirects to other hosts; IP literals refused |
| Why it is the TLS client | the kernel only sees `127.0.0.1:<proxy port>`. `sharness.net` sends `CONNECT host:443`, sets SNI and Host, and verifies the certificate for that name. A pure relay would let the inner process choose SNI and Host (domain fronting) |

## sharness.fs

| | |
|---|---|
| Job | apply writes to protected folders (for sgit: the working tree and `.sg_vault/`) under rules |
| Holds | no keys; talks to nobody, only answers the app |
| Business rules | writes only under the root it owns; no symlink or `..` escapes; in `.sg_vault/local/` accepts only sealed formats and **refuses anything that parses as a clear vault key, a PEM private key or a bearer token**; strips exec bits unless policy allows; size and count limits |
| Implementation | first, a process owning the folder (other uids have no write permission); later, possibly a FUSE mount enforcing the same rules for any tool. Which one is an [open decision](../roadmap/index.md) |

## sharness.bash

Bash is the escape hatch from every other component: while the model can run any command as root with network, the policies on `.fs`, `.net` and `.kms` mean little. A command is free text, so **no schema can bound its intent**; enforcement is on what the process can do.

| Lock | Setting (proposed) |
|---|---|
| uid | one ephemeral uid per session, never root |
| pid namespace | cannot see or signal the harness or any component |
| process count | `pids` cgroup limit (e.g. 64), not `RLIMIT_NPROC=0`: a shell must fork |
| files | Landlock: workspace per profile; `/usr` read-only; no other component's folders or sockets; the workspace has **no execute right** |
| network | none by default; when allowed, only via `sharness.net` |
| seccomp | deny `ptrace`, `mount`, `keyctl`, `bpf`, `unshare`, `execveat`, … (seccomp not yet measured) |
| output | stdout and stderr pass the same secret filter before becoming a tool result |

Profiles are chosen by policy and requested by the model: `analyse` (workspace read-only, no network), `build` (read-write, package registries and GitHub via `.net`), `admin` (fresh approval from the person each time). Making Bash impossible to skip is [Enforcing the process tree](../process-tree/index.md).

## sharness.llm

A Messages API endpoint with a Process Behaviour Policy, sitting where `ANTHROPIC_BASE_URL` points. It checks the request (model allowlist, pinned tools list, token budget), filters every tool result and user message for secrets, adds the real API key (obtained sealed from `.kms`), forwards, and streams the response back unchanged. Details on [Agents and LLMs](../agents/index.md#3-sharness-llm).

## sharness.policy

Not a process: the manifest, one entry per component, composed by intersection and hashed. The hash the person supplies covers everything, including the session CA certificate and the code hash of every component. See [Process Behaviour Policies](../policies/index.md).

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

## Two ways for an app to be compatible

Running an unmodified app in the harness breaks it: it tries to write where it may not, connect where it may not, read keys that are not there.

**Transparent (no app changes).** The harness presents ordinary interfaces backed by its components:

| App expects | Harness presents |
|---|---|
| a writable folder | a bind mount or FUSE mount served by `sharness.fs` |
| the internet | `HTTPS_PROXY` pointing at `sharness.net` (CONNECT with host allowlist) |
| a model API | `ANTHROPIC_BASE_URL` pointing at `sharness.llm` |
| a shell | `sharness.bash` as an MCP server, or a one-line hook rewriting to its client |
| a secret in an env var or file | **nothing**: this is the case transparency cannot cover safely |

**Harness-aware (small app changes)** for what transparency can't do, mostly secrets. For sgit: one key-source interface backed by `sharness.kms`; `clone --sealed`, `vault_key.sealed`, `vault seal --to`, plain keys refused on argv; later, vault crypto and server I/O move into `sharness.net`.

**The rule:** an app needs harness awareness only where it handles secrets or where a policy must understand its protocol. Everything else is transparent.

## As little code as possible

Most of the harness is configuration of things Linux and Python already have:

| Need | Use | Not |
|---|---|---|
| process isolation | uids, `setpriv`, namespaces, Landlock, seccomp, cgroups | a custom sandbox |
| transport and identity | stdlib `ssl`, `cryptography` for the session CA | a custom protocol or a mesh |
| schemas | JSON Schema (and MCP `inputSchema` for tools) | hand-written validators |
| policy | canonical JSON + SHA-256 + an existing signature (sgit PKI) | a policy language |
| tracing a policy | `strace` | a tracer |
| secret storage | `memfd_secret`, cgroup freezer, kernel keyring | an HSM emulator |

Size targets (proposed): launcher ≤ 400 lines; each component ≤ 300; a shared library (Landlock, mutual TLS, framing, schema check) ≤ 400. Components must be small enough to read in one sitting; that is part of their security.

Sources: [05-sharness](../../project/sources/sharness-brief-pack/docs/05-sharness.md) §1, §3–5; [01-architecture](../../project/sources/sharness-brief-pack/docs/01-architecture.md) §2, §6; [06-llm-and-the-agent-loop](../../project/sources/sharness-brief-pack/docs/06-llm-and-the-agent-loop.md) §3–4.
