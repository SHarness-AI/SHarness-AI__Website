# Enforceability: which rows of a policy can run where

> **Status: a map, as of 25 Oct 2026**, from each target's documentation as read for the [market analysis](../market/index.md) and from the CLI's own code; no translation has been run against its target in this project. Each cell answers the three questions of the [landscape](../index.md#3-the-three-questions-for-any-policy-and-any-environment): can the row be expressed, can the target enforce it, and as what kind of barrier. The command `sharness-ai policy translate FILE --to TARGET` writes the translation and prints the gap for the first four columns ([E10](../../code/experiments/index.md)).

## 1. The matrix

Barrier kinds are ABP's: **B** a Boundary (enforced above the subject, by the kernel or a separate process); **S** a Setting (the subject's own process reads and could change it); **E** an Expectation (prose, or a check the subject performs on itself); **–** nothing.

| Policy row (v0 and the designed schema) | SHarness (`run` today) | bubblewrap | Docker (`run`) | Claude Code sandbox | Kubernetes Pod + NetworkPolicy | microVM providers (E2B, Fly, Docker Sandboxes) | ToolHive (MCP servers) | OpenShell (NemoClaw) |
|---|---|---|---|---|---|---|---|---|
| `files.read` as an allowlist | **B** Landlock | **B** ro-binds (the rest absent) | **B** the image, read-only | **–** reads most of the machine; `denyRead` is a deny list | **B** the image; host paths as volumes | **B** the guest's own disk | **B** container with profile paths | **B** "filesystem controls" (not detailed) |
| `files.write` | **B** Landlock | **B** binds | **B** volumes | **B** `allowWrite` | **B** volumes | **B** | **B** | **B** |
| `files.exec` allowlist | **B** Landlock | **–** read implies exec | **–** | **–** | **–** | **–** | **–** | not stated |
| `network: none` | **B** empty namespace (+ Landlock) | **B** `--unshare-net` | **B** `--network none` | **B** proxy with an empty allowlist (UDP cannot leave) | **B** NetworkPolicy egress [] | **B** | **B** `--isolate-network` | **B** "blocks unapproved destinations" |
| `network.connect_tcp_ports` | **B** Landlock ports | **–** | **–** (needs iptables) | **–** domains, not ports | **B** NetworkPolicy ports | varies | partial (hosts and ports in the profile) | not stated |
| host names | designed: `sharness.net` as the TLS client | **–** | **–** | **S/B** hostname proxy (not TLS-terminating; managed settings make it B for the user) | **–** without a mesh | **B** at the provider's egress (Cloudflare, Docker Sandboxes) | **B** egress proxy | **B** operator-approved destinations |
| `process.max_memory_mb` | **B** rlimit + cgroup | **–** | **B** `--memory` | **–** | **B** `resources.limits` | **B** the VM size | **B** container limits | not stated |
| `process.max_pids` | **B** rlimit + cgroup | **–** | **B** `--pids-limit` | **–** | **–** per pod | **B** | **B** | not stated |
| `no_new_privs`, no capabilities | **B** | **B** | **B** `--cap-drop ALL`, `no-new-privileges` | **B** (bubblewrap underneath) | **B** securityContext | **B** | **B** | **B** |
| a separate uid per component | designed (launcher) | **B** user namespace | **B** `--user` | **–** one uid | **B** `runAsUser` | **B** | **B** per container | not stated |
| seccomp allowlist from the policy | designed | **B** (`--seccomp` takes a filter) | **B** `--security-opt seccomp=` | **–** (optional Unix-socket filter only) | **S** RuntimeDefault, or a Localhost profile (**B**) | provider's | **B** container runtime default | "process controls" |
| IPC edges (who may talk to whom) | designed: mutual TLS, both sides check | **–** | **–** (networks, not roles) | **–** | partial: NetworkPolicy between pods | **–** | **–** | **–** |
| the model (`sharness.llm`: pinned tools, secret filter) | designed | **–** | **–** | **S** `allowedMcpServers`, permissions (the agent's own settings) | **–** | **–** | **–** | **B** managed inference through `inference.local` |
| secrets never in the agent's process | designed (`sharness.kms`) | **–** | **–** | **S** credential masks at the proxy (the clear key is in the proxy) | **–** (a Secret is mounted into the pod) | **B** credentials injected outside the VM (Docker Sandboxes, Cloudflare) | **B** secrets into the container process only | **B** "credentials remain outside the sandbox" |
| the policy hash supplied from outside | **B** `--expect-hash` (for a child) | **–** | **–** | **–** (settings are the subject's own; managed settings are **B** for the user) | **–** (an admission controller could) | **–** | **–** | **–** |
| who enforces | the process itself today (**S** for itself); the launcher, designed | the caller | the daemon | the agent's process; managed settings | the kubelet and the CNI | the provider | the gateway | the OpenShell host |

Legend for "not stated": the product's documentation read for the market analysis does not say; "varies": differs by provider.

## 2. Reading the matrix

- **The rows every target can do** (writes, no network, no new privileges, memory) are the rows the market has settled; a policy with only those rows runs natively almost anywhere, and `policy translate` writes it for four of them.
- **The rows only SHarness does** are the ones the design was written for: an execute allowlist, TCP port rules without a proxy, IPC edges with roles, the secret in a process the agent cannot reach, and a hash checked above the subject. These are the gaps the components fill, and the reason the reference implementation exists.
- **The column no product fills** is "who enforces": in every shell sandbox the agent's own process reads the settings. The launcher above the agent is the one piece that turns a column of **S** into **B**, which is why it is first on the [order of work](../../evidence/research/index.md#4-what-is-still-open-in-the-order-to-take-it) after the process tree.

## 3. The command

```
$ sharness-ai policy translate experiments/policies/allow-https-example.json --to bwrap -- python3 -c "print(1)"
bwrap --unshare-all --die-with-parent --new-session --cap-drop ALL --share-net --ro-bind /bin /bin --ro-bind /etc /etc \
  --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /usr /usr -- python3 -c 'print(1)'

# bwrap: not enforced from policy allow-https-example (sha256:2944751573bb…):
#   - no_new_privs: bwrap sets it (PR_SET_NO_NEW_PRIVS) for the sandboxed process
#   - network.connect_tcp_ports [443]: not enforced; bwrap shares or unshares the whole network, it has no port allowlist
#   - files.exec: not distinct from files.read; a read-only bind is also executable in bwrap (use noexec mounts or Landlock inside)
```

The same for `--to docker`, `--to claude-code` (a `settings.json` fragment) and `--to kubernetes` (a Pod and a NetworkPolicy). Every output ends with the list of what the target does not enforce, which is the matrix row by row, made executable. `--to landlock` prints what `run` itself does, for completeness.

## 4. What the matrix does not say

- Nothing here was run against its target in this project; a cell is what the target's documentation says it does, as of the date the market analysis read it. A row that reads **B** can still be misconfigured.
- Barrier kinds are about *who* enforces, not about strength: a **B** at a hostname proxy that does not terminate TLS is a Boundary with a documented hole (domain fronting).
- The policy is v0 plus the designed rows. Layers composed by intersection, signing, business rules and the audit format are not yet in the matrix.

Sources: the [market analysis](../market/index.md) and each product's documentation it cites; [Policies §5, the enforcement map](../../design/policies/index.md#5-enforcement-map); `sharness_ai/translate.py` on the CLI's `dev` branch; [riskmandate.ai/abp](https://riskmandate.ai/abp.html) for the barrier kinds.
