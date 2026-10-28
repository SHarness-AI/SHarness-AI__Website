# sharness.launcher: the bootstrap

> **Update, 28 Oct 2026: a first slice runs.** `sharness-ai shell` (CLI `dev`, 63360be) is the launcher for one shell: where it is root it makes a unique system user and removes it on exit, starts the network door for that uid, compiles the shell's policy from a sentence with the proxy's port as its only network row, and starts the shell under `sharness-ai run`. Verified by website@sharness on 28 Oct 2026 (a Linux 6.18 container, root, Landlock ABI 7): the shell ran as a non-root uid, a write outside the workspace was refused, a write inside it landed, and the user was gone after exit; a background process did not outlive the shell. Not here: the fs door for the workspace under the shell, namespaces, the doors under their own policies, a manifest of components. The rest of this page is the design.
>
> **Status: designed; its one-process form is runnable.** `sharness-ai run --policy p.json --expect-hash sha256:… -- cmd` is the launcher for one process: it refuses unless the policy hashes to what the person supplied, applies the locks in the child, and starts the command; measured on three kernels. The session launcher that starts the components under one manifest is designed and not built. Written as of 25 Oct 2026.

## Its one job

Start the session the way `init` starts a machine: refuse unless the manifest hashes to the value the person supplied out of band; make one ephemeral uid per component; make a session CA and one certificate per role, then destroy the CA key; start `sharness.kms` and freeze it; start the other components under their policies; freeze, thaw, stop and clean up. It runs outside every domain and holds no secret.

## Not an API: a command

The launcher is what everything else trusts, so it has no port of its own. It is a command the person, a script, or the platform runs above the agent:

```
sharness-launch --manifest manifest.json --expect-hash sha256:M
```

| It does, in order | Measured |
|---|---|
| read the manifest, hash it, compare with `sha256:M` or verify the root key's signature; refuse otherwise | `--expect-hash` on `run`: a wrong hash runs nothing, exit 125 (five places, 25 Oct 2026) |
| one uid per component | user + firewall rule + locked launch + teardown ≈ 49 ms (24 Oct 2026) |
| a session CA, one certificate per role, the CA key destroyed, the CA certificate's hash recorded | a mutual TLS handshake ≈ 3.2 ms (24 Oct 2026) |
| start `.kms`, read only its public bundle, freeze it | thaw and freeze 0.13 and 0.28 ms |
| per command: start the others under their policies in new namespaces, run, tear down | namespaces ≈ 4 ms |
| at the end: thaw and kill `.kms`; delete users, rules, sockets | |

## Who runs it decides what the locks are

| The launcher is run by | The locks are, for the agent | |
|---|---|---|
| the agent, inside its own session (`sharness-ai run` today) | a Setting: a Boundary for every child, but the agent could have skipped it | what every experiment here has done |
| a script that starts the agent | a Boundary for the agent | the next rung |
| the platform | a Boundary all the way down | the end state |

This is the caveat printed with every result on this site, in one table.

## What it enforces, with what

The launcher applies nothing itself at run time; it tells the kernel, once, before each process starts: a uid, Landlock, seccomp, namespaces, a cgroup, `no_new_privs`, and the certificate that says which role the process has. After that the kernel and the certificates do the work and the launcher cannot be asked for more rights, because it is not listening.

## On its own

Adopt only this component and you have what `sharness-ai run` is today for one process, for a set of them: a policy per process, checked against a hash the person supplied, enforced by the kernel. No door, no filter, no KMS; and still every process it starts cannot do what its policy does not list.

Sources: [Components](../../design/components/index.md#sharnesslauncher), [Policies §2](../../design/policies/index.md#2-who-enforces-decides-the-barrier-kind), [Architecture: topologies](../../design/architecture/index.md#deployment-topologies). The one-process form: [The CLI](../../code/cli/index.md).
