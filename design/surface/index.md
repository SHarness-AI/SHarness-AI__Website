# What a process can do: the whole surface

> **Status: design, with the measured rows dated.** The question behind this page is Dinis Cruz's: *if we limit everything else, what else can a process do?* The answer is a list, and it is short enough to write down. For each kind of thing a process can do, this page says what SHarness bounds it with, whether that bound was measured (as of 24 Oct 2026, in one Claude agent workspace), and what the bound does not cover.

## 1. A process touches the world through the kernel, and only through the kernel

Everything a user-space process does outside its own memory is a system call. Linux has about 460 of them on x86-64; `sgit --version` uses 38 distinct ones (measured, [Evidence §5](../../evidence/index.md#5-footprint)), a bare Python start 31. They group into a dozen kinds of interface. A process that is bounded on every kind is a process whose operating system is its policy: what the policy lists exists, and nothing else does. That is the idea the design calls a Process Behaviour Policy, read from the other side.

![The whole surface of a process: twelve kinds of interface arranged around one process, each with what bounds it in SHarness.](../../assets/images/design/surface.svg)

*The whole surface. Green: bounded in the kernel. Purple: bounded by a separate component, because the kernel cannot see the thing being bounded (which host a TLS connection names, what a model is asked, what a secret is).*

## 2. The surface, one row per interface

| Interface | What a process can do through it | Bounded by (kernel) | The allowed part goes through | Measured | Not covered by the bound |
|---|---|---|---|---|---|
| **files**: read, write, execute, create, delete, rename | read any file its uid can; write; exec a binary; make device nodes, sockets, symlinks | Landlock path rules per process (ABI 1+); exec allowlist; the workspace with no execute right; a mount namespace with read-only binds | `sharness.fs`, the only writer of protected folders, with content rules (no clear keys) | read and write denial ✔ (E03, E04); exec allowlist and read-only binds: not yet | the content of what it may read: prompt injection travels inside allowed files |
| **network**: connect, listen, send, receive, resolve names | reach any host; listen on any port; UDP, raw sockets | an empty network namespace (nothing at all), or Landlock TCP port rules (ABI 4+); `iptables` per uid | `sharness.net`, the only client, and the TLS client, so it sees and verifies the host name; endpoint and vault-id allowlists | namespace ✔, port rules ✔, per-uid rule ✔ | UDP and ICMP under Landlock alone (the namespace covers them); what is sent on an allowed connection |
| **processes**: fork, exec, clone | start anything on the system; start itself again | `RLIMIT_NPROC=0` or a `pids` cgroup; seccomp denying `execve` after start; Landlock execute rights | `sharness.bash`: a server outside the domain runs each command in a fresh sandbox | no-fork ✔; the server design not yet run (E06) | a binary the policy lets it run (which is why `node` for the orchestrator is pinned by hash) |
| **signals and IPC**: kill, ptrace, pipes, Unix sockets, shared memory, abstract sockets | signal or trace another process; reach a socket by name | Landlock scoping of signals and abstract sockets (ABI 6+); a pid namespace (cannot even see the others); ptrace denied by seccomp | the mutual TLS edges: the only IPC that exists is the edge list, with roles in certificates and both sides checking | edges ✔ (exactly per the matrix); scoping and seccomp not yet | a message on an allowed edge: its schema bounds its shape, not its intent |
| **memory** | use as much as it likes; keep secrets in ordinary pages root can read | a `memory` cgroup; `PR_SET_DUMPABLE=0`, `mlockall`, `RLIMIT_CORE=0` | secrets in `memfd_secret` pages, scrubbed after copying | `memfd_secret` unreadable even by root ✔; dumpable stops non-root only ✔ | root reading ordinary memory (out of scope); OpenSSL's own copies during an operation |
| **time and limits** | run for ever; spin the CPU | `max_runtime_s`; a `cpu` cgroup; the freezer | the launcher freezes `sharness.kms` between calls | freeze 0.28 ms / thaw 0.13 ms ✔ | timing as a covert channel |
| **devices and mounts** | open device nodes; mount; ioctl | no device nodes in the namespace; a mount namespace; Landlock `IOCTL_DEV` (ABI 5+); `mount` denied by seccomp | nothing: components need no devices | namespaces ✔ (3.7 ms); read-only binds not yet | |
| **identity and privilege** | change uid; use capabilities; gain privilege through setuid binaries | one ephemeral uid per component, made for the session; bounding set empty; `no_new_privs` | the launcher makes the uids and deletes them | ✔ (49 ms per user, with a firewall rule and teardown) | root undoing it, when the agent is root and runs the launcher itself |
| **kernel services** | `keyctl`, `bpf`, `unshare`, `mount`, `ptrace`, `io_uring`, `userfaultfd` and the rest of the long tail | a seccomp-BPF allowlist of the 30 to 40 syscalls a component uses | nothing | available; no filter tested yet | a bug in an allowed syscall (the kernel is trusted) |
| **environment and arguments** | read secrets from `argv` and `environ`; the transcript sees both | the launcher sets them; nothing secret is ever in either | `SHARNESS_AI_POLICY_HASH` and the policy id, so a process can say what it runs under | E03 sets them ✔ | |
| **the model** (an agent's interface) | ask the model anything, with any tools, with any secret in the context | nothing in the kernel: the model API is an HTTPS host like any other | `sharness.llm`: model allowlist, pinned tool list, token budget, a secret filter on every tool result and user message, the real key added last | designed (E07) | the model being talked into a bad tool call: enforced where the tool executes, not here |
| **secrets** | hold a key, print it, write it, pass it on | nothing in the kernel; `memfd_secret` only hides the page | `sharness.kms`: opens sealed things and returns derived keys sealed to a one-time key; never a clear key | the holding ✔ (§ memory); the protocol designed (E08) | expiry is KMS policy, not cryptography; a session identity dies with its session |

Rows marked ✔ were measured on 24 Oct 2026, in one Claude agent workspace, with method on [Evidence](../../evidence/index.md); the rest is designed or planned. The policy fields behind each row are in the schema on [Policies §4](../policies/index.md#4-schema) and the enforcement map on [Policies §5](../policies/index.md#5-enforcement-map).

## 3. What is left: a virtual operating system for one process

Read the table from the right. Take away every interface that is bounded to nothing, and what remains for a component is:

- its own memory, under a limit;
- the files its policy lists, with the rights it lists, and nothing else on the filesystem;
- the one or two TCP ports its policy lists, on loopback or on a Unix socket, each answered by a process that checks its certificate;
- the syscalls on its allowlist;
- its standard streams to the launcher;
- and, for an agent, one door to the model and one door to the secrets, each a component with its own policy.

That is a complete description of the process's world. It is small enough to hash, to read in one sitting, to learn from a trace, and to ship with the code it binds. Nothing in it is new: it is what a kernel already offers, used all at once for one process, with the parts the kernel cannot see (host names, model requests, secrets) each given to one small process that can. The design calls the whole thing a harness; it could as well be called a virtual operating system whose system call table is the policy.

## 4. What this does not bound

- **Intent on an allowed channel.** A schema bounds the shape of a request, not what it means. A web page that tells the agent to push to an allowed host, with an allowed key, within the allowed count, is not stopped by any bound above; it is stopped by narrowing the mandate (one host, one vault id, `op=read`) and by the dual-LLM split on [Agents §5](../agents/index.md#5-untrusted-text-two-models-two-components).
- **Covert channels.** Timing, CPU load, cache effects, the size of allowed messages. Out of scope for a design that trusts the kernel.
- **Root and the kernel.** Anything with root can read ordinary memory and undo locks it applied itself; a kernel bug in an allowed syscall is not caught by any of this. The threat model says so ([Why](../why/index.md#threat-model)).
- **The platform.** Where the launcher runs, and whether the platform's own proxy and VM behave as documented, is outside the policy.

## 5. Where each bound is, today

| In the CLI today (v0 policy) | Designed, not built |
|---|---|
| files (Landlock read, write, exec); network (`none`, or TCP ports); `no_new_privs`; the environment carrying the hash | per-component uids, seccomp allowlists, cgroups, scoping, read-only binds, the launcher, `sharness.fs`, `.net`, `.bash`, `.llm`, `.kms` |

The v0 policy covers the two interfaces that leak most (files and network) for one process; each further row is one experiment on the [ladder](../../code/experiments/index.md).

Sources: [Policies](../policies/index.md) §4 and §5; [Components](../components/index.md); [Evidence](../../evidence/index.md) §3 to §6 and §9; the Landlock documentation at [docs.kernel.org](https://docs.kernel.org/userspace-api/landlock.html); `sgit --version` under `strace -c` on 24 Oct 2026 (36 distinct syscalls by that method, 38 by the design's).
