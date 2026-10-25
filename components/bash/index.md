# sharness.bash: the shell, as a service

> **Status: designed; the sandbox half is runnable.** `sharness-ai run` applies the locks below to one command today, measured on three kernels. The server that applies them from outside the agent's domain, so the agent cannot skip it, is designed and its proof of concept not yet run. Written as of 25 Oct 2026.

## Its one job

Run one shell command in a fresh sandbox under a named profile, and return its output with secrets filtered. Nothing else: no state between commands, no key, no network of its own.

## Why it is the centre

A shell command is free text. No schema can bound what `bash -c` means, so the only enforcement there is on what the process can do. That makes `sharness.bash` the place where every lock the harness has is applied at once, and the first component to build: once a command can only run through this door, `.fs`, `.net`, `.kms` and `.llm` are the only ways out of the sandbox, and their policies mean something. Without it, the model can run any command as root with the network, and the policies on the other doors mean little.

## The API (proposed)

A loopback TCP port, mutual TLS, the caller's certificate role must be `app` or `orchestrator`.

| Request | Body | Response |
|---|---|---|
| `POST /v0/run` | `{"profile": "analyse", "cmd": "grep -rn TODO src", "cwd": "/work", "timeout_s": 60}` | `{"exit": 0, "stdout": "…", "stderr": "…", "filtered": 0, "ms": 412}` |
| `GET /v0/profiles` | | the profiles this server offers, each with its policy hash |
| `GET /v0/policy` | | this component's own policy and its hash |

Transparent mode: the same server as an MCP tool (`run_command`), or a one-line hook that rewrites the agent's own shell tool to the client. The client is a messenger: a small static binary that cannot run anything itself.

## Requests, and their verdicts (designed)

| The agent asks | Profile | Verdict | By |
|---|---|---|---|
| `grep -rn TODO src` | analyse | runs; output returned | the sandbox |
| `cat ~/.aws/credentials` | analyse | `cat: No such file`: the home directory is not in the sandbox's Landlock domain | the kernel |
| `curl https://pypi.org/simple/` | analyse | `connect: Permission denied`: no network in this profile | the kernel (empty network namespace) |
| `curl https://pypi.org/simple/` | build | served, through `sharness.net`, if `pypi.org` is on its allowlist | `.net` |
| `echo $ANTHROPIC_API_KEY` | any | empty: the sandbox's environment holds no secret | the server |
| `./work/payload` | any | `Permission denied`: the workspace has no execute right | the kernel |
| `python3 -c "import os; os.setuid(0)"` | any | `EPERM`: no capabilities, `no_new_privs` | the kernel |
| a command whose output contains a vault key | any | the key replaced by `[filtered: vault key]`, `filtered: 1` in the response | the server |
| `sudo rm -rf /` | admin | held for a fresh approval from the person, then refused anyway: no capabilities | policy, then the kernel |

## What it enforces, with what

| Lock | Setting (proposed) | Today |
|---|---|---|
| uid | one ephemeral uid per session, never root | measured: a user, a firewall rule, a locked launch and teardown ≈ 49 ms (24 Oct 2026) |
| pid namespace | cannot see or signal the harness or any component | `unshare` ≈ 4 ms, measured |
| process count | a `pids` cgroup limit (64), since a shell must fork | `max_pids`, measured 25 Oct 2026 |
| files | Landlock: the workspace per profile, `/usr` read-only, no other component's folders or sockets; the workspace has no execute right | `sharness-ai run`, measured in five places |
| network | none by default; when a profile allows it, only via `sharness.net` | `network: "none"` as an empty namespace, measured |
| seccomp | deny `ptrace`, `mount`, `keyctl`, `bpf`, `unshare`, `execveat`, … | not yet measured |
| output | stdout and stderr pass the secret filter before becoming a tool result | designed |

The three profiles: `analyse` (workspace read-only, no network), `build` (read-write, package registries and GitHub via `.net`), `admin` (a fresh approval from the person each time). A profile is a Process Behaviour Policy; its hash is in the manifest.

## On its own

Adopt only this component and every command the agent runs is confined and logged, with secrets filtered from its output, without changing the agent: as an MCP tool, or a hook. What it does not do alone: bind the agent's own process, which can still `execve("/bin/sh")` unless the launcher above it removed that right ([Enforcing the process tree](../../design/process-tree/index.md)).

## What it does not do

It cannot judge a command's intent. It cannot stop an allowed interpreter from doing file or network work in-process; that is the sandbox's Landlock policy. It is a Boundary for the command and a Setting for whoever started the server, until a launcher above the agent starts it.

Sources: [Components](../../design/components/index.md#sharnessbash), [Agents and LLMs §4](../../design/agents/index.md#4-sharnessbash), [Enforcing the process tree](../../design/process-tree/index.md). Measurements: [Evidence](../../evidence/index.md).
