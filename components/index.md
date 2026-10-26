# The components: the operating system a process sees

> **Status: design, with one door and two halves runnable.** Six components, one job each, proposed; one door, [sharness.fs](fs/index.md), runs as an MVP since 26 Oct 2026 (a Setting until the launcher exists), and the other five are not built; the kernel locks under them are runnable today (`sharness-ai run`) and the network allowlist outside a process is a working prototype in [the playground](../code/playground/index.html#network). This page is the components as a user would meet them: the only doors a process has, each a small REST service on loopback, each worth adopting on its own. Written as of 25 Oct 2026.

![The operating system a process sees: in the middle, the process (an agent's tool, or bash). Around it, its only doors: sharness.fs for writes, sharness.net for the network, sharness.llm for the model, sharness.bash for commands, sharness.kms for secrets, each a REST service on loopback with mutual TLS. Below, the launcher that bootstrapped them: one uid per component, a session CA, the policy hash. Requests animate: a write under the workspace allowed; a write of a clear key refused by fs; a connect to an allowed host served by net; one to another host refused; the KMS answering net with a re-sealed key, never a clear one.](../assets/anim/os-of-one-process.svg)

*What is left when everything else is bounded. Each door is a process with its own uid and policy; each edge is a loopback TCP connection under mutual TLS with the roles in the certificates. Designed, not built; the animation shows the designed verdicts.*

## 1. Why "an operating system"

Ask what a process can do at all and the list is short: files, the network, other processes, memory, its identity, the model it talks to, the secrets it needs ([the whole surface](../design/surface/index.md)). SHarness bounds each in the kernel where the kernel can (Landlock, namespaces, seccomp, cgroups, one uid per process) and puts a component where it cannot: the kernel can refuse a `connect()`, but it cannot say which hostname is allowed; it can refuse a `write()`, but not that the bytes are a clear key. So a process in the harness has no filesystem of its own to write, no network stack of its own, no key store, no shell, no model API. It has five doors, and each door is a small service with a policy, a port and a certificate. That is an operating system for one process: it contains exactly what the policy lists, and nothing else.

| What a process would use | What it has instead | The door |
|---|---|---|
| the filesystem, to write | a service that writes under rules, and refuses clear keys | [sharness.fs](fs/index.md) |
| a network stack | a service that is the TLS client, with host, endpoint and id allowlists | [sharness.net](net/index.md) |
| a key file, a token in an env var | a service that holds every secret and never returns one in clear | [sharness.kms](kms/index.md) |
| a shell | a service that runs each command in a fresh sandbox under a profile | [sharness.bash](bash/index.md) |
| the model API and its key | a service that is the only model client, with the key, a pinned tool list and a secret filter | [sharness.llm](llm/index.md) |
| `init`, users, trust | the bootstrap: one uid per component, a session CA, the manifest hash from the person | [sharness.launcher](launcher/index.md) |
| a configuration | the manifest: one policy per component, hashed | [sharness.policy](policy/index.md) |

## 2. Everything is a request

Every door speaks the same way: a small REST API over a loopback TCP port, under mutual TLS from a session CA, one certificate per role, and an edge list that says which role may call which ([Architecture](../design/architecture/index.md#edges-deny-by-default)). A request is a JSON body; a verdict is a status code and a reason. That has three consequences a user feels at once:

- **Any language can call a door.** A harness-aware app, an MCP server, a shell script with `curl` and a client certificate: the protocol is HTTP.
- **Every door can be watched.** A request that was refused says why, and a log of requests is a log of what the agent tried. The playground's [network panel](../code/playground/index.html#network) is this for one door, in a browser.
- **The cost is small, and measured.** A mutual TLS handshake between two local processes took about 3.2 ms, a 600-byte round trip under a millisecond, and the three handshakes of an sgit command about 10 ms, against 146 ms the command already spends importing Python ([Evidence §6](../evidence/index.md#6-transport), 24 Oct 2026). Loopback is not where the time goes.

Each component page shows its requests: what is asked, what is allowed, what is refused and by which layer. The clickable [edge matrix](../explain/mockups/edges.html) shows which layer refuses a call between any two roles.

## 3. Pick one

The components are designed to run together under one manifest hash, and that is the reference implementation. They are also designed so that **one of them, alone, is worth having**:

| Just this one | What you get on day one | Who wants it |
|---|---|---|
| [sharness.net](net/index.md) | an inline proxy that is the TLS client for everything the agent reaches, with a hostname allowlist, no redirects to other hosts, no IP literals, and a log of every request; the model API traffic included | anyone running an agent that must not talk to the wrong host |
| [sharness.bash](bash/index.md) | every shell command the agent runs in a fresh sandbox under a named profile, output filtered for secrets | anyone whose agent runs commands |
| [sharness.llm](llm/index.md) | the model API key out of the agent's process; a pinned tool list; a secret filter on every tool result before the model sees it | anyone whose agent holds an API key in an env var |
| [sharness.kms](kms/index.md) | secrets that are never in clear anywhere a transcript can see | anyone handing keys to an agent |
| [sharness.fs](fs/index.md) | writes under rules, and a refusal to store anything that parses as a key | anyone whose agent writes into a repository |

Adopting one door does not bind the agent itself: that is the launcher's job, and the caveat on every page here. It does bind everything that goes through the door, which is where most of the damage an injected agent can do goes through.

## 4. Where to start: bash

The first component to build is `sharness.bash`, because it is where the others are decided. A shell command is free text; no schema bounds its intent, so the only enforcement is on what the process can do, and that is exactly the set of locks every other component also needs: its own uid, no capabilities, `no_new_privs`, a pid namespace, a pids cgroup, Landlock on the workspace with no execute right, network none or through `.net` only, seccomp. `sharness-ai run` is the one-process form of that today, measured on three kernels; `sharness.bash` is the same locks behind a request, applied by a server outside the agent's domain so the agent cannot skip them ([the process tree](../design/process-tree/index.md)). Once a command can only run through that door, the other doors are the only ways out of it.

## 5. Status, component by component

| Component | Designed | Runnable today | Measured |
|---|---|---|---|
| launcher | yes | `sharness-ai run`: one process under one policy with the hash checked | uid creation ≈ 49 ms, namespaces ≈ 4 ms (24 Oct 2026) |
| kms | yes, with the protocol | no | thaw and freeze 0.13 and 0.28 ms; the sealed handover end to end, by hand |
| net | yes | the playground's interceptor: a hostname allowlist outside a process, in a browser | three verdicts in one session (25 Oct 2026) |
| fs | yes | no | |
| bash | yes | the sandbox half: `sharness-ai run` | `hello` 6 of 6 in five places |
| llm | yes | no | the Messages API flow observed in a live session (24 Oct 2026) |
| policy | yes, v0 shape | `policy hash`, `check`, `translate`; seven examples | one hash in three implementations |

Reading on: [the brief](../design/index.md) for how they work together, [Architecture](../design/architecture/index.md) for the edges and the transport, [Containment](../design/containment/index.md) for how far each holds.
