# Containment: how far can hostile code inside be held?

> **Status: design, with the measured rows dated.** Dinis Cruz's question of 25 October 2026: can every one of these processes be constrained, memory included, and with malicious code running inside, how comfortable are we that the harsher settings contain it? The answers below are by threat class, each with what is measured (as of 25 Oct 2026, in one Claude agent workspace), what is designed, and where the answer is "not with this alone, use a microVM as well".

## 1. Can every process be constrained, memory included?

Yes. Every component is an ordinary Linux process, and Linux already has a bound for each kind of thing a process can do ([What a process can do](../surface/index.md)). The harsh setting for one component, all of it a Boundary because the launcher applies it from above:

| Bound | Mechanism | In the harsh profile |
|---|---|---|
| memory | a `memory` cgroup (`memory.max` on v2, `memory.limit_in_bytes` on v1); `RLIMIT_AS` as a second, cheaper cap | exceed it and the kernel kills the process; it is not throttled |
| CPU and time | a `cpu` cgroup; `max_runtime_s`; the freezer between calls | the KMS spends its life frozen |
| processes | `RLIMIT_NPROC=0` for anything that never forks; a `pids` cgroup (64) for the shell sandbox | a fork bomb hits a wall it cannot see |
| files | Landlock: only the listed paths, with the listed rights; no execute right anywhere it can write | a dropped binary cannot run |
| network | an empty network namespace, or Landlock TCP rules for one or two loopback ports | nothing to connect to |
| identity | a throwaway uid; an empty capability bounding set; `no_new_privs` | no setuid path back up |
| visibility | a pid namespace: it cannot see, signal or trace any other process | the harness is not there, from inside |
| IPC | Landlock scoping of signals and abstract sockets; mutual TLS on the one port it may reach | a wrong certificate is refused before any byte of payload |
| devices and mounts | no device nodes; a mount namespace; `mount` denied | |
| syscalls | a seccomp-BPF allowlist of the 30 to 40 it actually uses; `ptrace`, `mount`, `bpf`, `keyctl`, `unshare`, `io_uring`, `userfaultfd` denied | the kernel's attack surface, shrunk to what the job needs |

Measured so far: Landlock files and ports, the empty network namespace, uid and capability dropping, `no_new_privs`, the freezer, `memfd_secret` against root, and, since 25 Oct 2026, the memory and process-count caps applied by `sharness-ai run` (`RLIMIT_AS`, `RLIMIT_NPROC`, a memory and a pids cgroup; a 400 MiB allocation under a 128 MiB cap raises `MemoryError`, the fifth fork under `max_pids: 4` fails; [Evidence §9](../../evidence/index.md#9-the-first-experiments-run-by-the-cli)). Not yet: the `cpu` cgroup, seccomp, Landlock scoping, the execute allowlist.

## 2. With malicious code inside, by threat class

| The code inside tries to | Comfort | Why |
|---|---|---|
| read or write what it should not; reach the network; start a shell; signal the harness; raise privilege; exhaust memory, CPU or pids | **comfortable** | this is what Landlock, namespaces, cgroups, seccomp and uids exist for; each was measured on its own except seccomp and the exec allowlist; and the components make them independent layers, so one bug in one layer needs a second bug in another before anything leaks |
| steal the secret | **comfortable, for the design's goal** | the malicious process is never the one holding the key. The KMS is a different uid in an empty namespace that answers only `sharness.net`, and it returns derived keys sealed to a one-time key. A fully compromised `net` can misuse one command's derived read key, within its allowlisted host and vault id, for the life of that command |
| misuse what it is legitimately allowed to do | **not comfortable, and no sandbox is** | if the policy allows a push to host X, malicious code pushes to host X. The only defences are a narrower mandate (per-subcommand policies, `op=read`, fresh approval for writes) and the dual-LLM split on [Agents §5](../agents/index.md#5-untrusted-text-two-models-two-components). This is where most real damage happens |
| attack the kernel | **not comfortable alone; comfortable with a microVM around it** | a seccomp allowlist of about forty syscalls shrinks the surface a lot, but a bug in `read`, `mmap` or `futex` is still a bug, and the design trusts the kernel. For code expected to be hostile, run the whole harness inside a microVM (topologies B and C on [Architecture](../architecture/index.md#deployment-topologies): Firecracker, Docker Sandboxes, gVisor) so a kernel escape lands in a disposable guest |
| use a side channel: timing, CPU load, cache, the size of allowed messages | **out of scope** | said so on [Why](../why/index.md#threat-model), rather than claimed otherwise |

## 3. Defence in depth, drawn as layers

```
 the platform's VM, or a microVM (topology B, C)     the boundary for a kernel escape
  └ the launcher, above the agent                    makes every lock below a Boundary
     └ one uid, no capabilities, no_new_privs        no way back up
        └ namespaces: pid, net, mount                nothing to see or reach
           └ cgroups: memory, pids, cpu, freezer     nothing to exhaust
              └ Landlock: paths, ports, scoping      only the listed things exist
                 └ seccomp allowlist                 only the listed syscalls
                    └ mutual TLS edges + schemas     only the listed peers, only well-formed requests
                       └ the process, doing its one job

 and across all of them: the secret is in a different process (the KMS), so there is nothing here to steal
```

Each layer is enforced by something the layer inside it does not include. A failure of one layer leaves the next. The market analysis says why this is a complement to microVM products and not a competitor: they draw the outer ring; SHarness draws the inner ones ([Market §9](../../landscape/market/index.md#9-where-sharness-sits)).

## 4. Two caveats that matter more than the kernel

1. **Harsh settings are only harsh if a launcher above the process applied them.** A process that confines its own children can skip the step. Every `hello` run prints this. Until E06 and the launcher on a laptop, every measured row is a Boundary for a child and a Setting for the one that applied it ([Policies §2](../policies/index.md#2-who-enforces-decides-the-barrier-kind)).
2. **The two rows that make the containment claim strongest are the two not yet measured:** the seccomp allowlist and the process-tree execute allowlist. That is why E06 is first on the [order of work](../../evidence/research/index.md#4-what-is-still-open-in-the-order-to-take-it), and why this page says *designed* where it would like to say *measured*.

## 5. What this page does not claim

- No protection against root or a kernel bug from inside the same kernel; the microVM is the answer there, and it is someone else's product.
- No figure here is from a laptop; the measured rows are from one cloud workspace on 24 and 25 October 2026.
- "Comfortable" is a judgement about the design, offered by the agent that wrote this page, for Dinis Cruz to accept or challenge (R6 on the [comms board](../../project/comms.html)).

Sources: [What a process can do](../surface/index.md); [Policies §5](../policies/index.md#5-enforcement-map); [Evidence](../../evidence/index.md) §3, §4 and §9; [Architecture](../architecture/index.md#deployment-topologies); the kernel documentation for [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html), [Landlock](https://docs.kernel.org/userspace-api/landlock.html) and [seccomp](https://docs.kernel.org/userspace-api/seccomp_filter.html).
