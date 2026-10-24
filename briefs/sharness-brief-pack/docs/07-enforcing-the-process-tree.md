# 07 — Enforcing the process tree: everything goes through `sharness.bash`

Routing Bash through a component is easy (06 §4.2). Making it **impossible to skip** is the real requirement: a prompt-injected agent will simply try `/bin/sh`, `python -c`, a binary written to the workspace, or a signal to the sandbox server.

## 1. Principle

**Enforce at the root of the process tree, before the harness starts, with restrictions that are inherited and cannot be removed.**

- Every process an agent runs is a descendant of the orchestrator (in the measured session: children of PID 96).
- Landlock domains, seccomp filters, `no_new_privs` and cgroup membership are inherited by every child and cannot be lifted by any descendant.
- Landlock binds root too: capabilities do not lift a Landlock domain.

## 2. Design

```
 sharness.launcher  (outside every domain; platform, or the script that starts the agent)
   │
   ├── sharness.bash-server   uid harness-bash, OUTSIDE the orchestrator's domain
   │      for each request: new pids cgroup → unshare (net, pid, mount) → drop to sandbox uid
   │      → Landlock profile → exec bash -c <cmd> → filter output → return
   │
   └── orchestrator (Claude Code / own loop)
         uid: not root; capabilities: none; no_new_privs
         Landlock domain (applied by the launcher before exec):
           EXECUTE only: node (itself), rg, sharness-bash-client, MCP server binaries
           READ:         /usr, /lib, /etc, the app's own files
           WRITE:        its own state folder only (NOT the workspace: that is the sandbox's)
           TCP connect:  harness.llm port, harness.bash-server port
           scope:        signal + abstract-unix (ABI 6+): cannot signal or reach anything outside
         │
         ├── execve("/bin/bash")            ✗ EACCES  (no execute right)
         ├── execve("/usr/bin/python3")     ✗ EACCES
         ├── execve("./work/payload")       ✗ EACCES  (workspace has no execute right)
         ├── kill(<bash-server pid>, …)     ✗ EPERM   (Landlock signal scoping)
         └── bash-client ──socket──► bash-server ──► sandbox (fresh uid, pidns, netns, Landlock, pids≤64)
```

### 2.1 Why a server, not a wrapper
Landlock layers only narrow. If the orchestrator's domain allowed executing `/bin/bash` so that a wrapper could exec it, the orchestrator could exec `/bin/bash` directly. The sandbox therefore has to be created by something **outside** the domain. The client is a messenger; it cannot run anything itself.

### 2.2 Side doors and how each is closed

| Side door | Closed by | Status |
|---|---|---|
| exec a shell or interpreter directly | Landlock EXECUTE allowlist | not yet measured |
| write a binary into the workspace and run it | workspace has no EXECUTE right | not yet measured |
| interpreter already allowed (node) does file/network work in-process | the orchestrator's own Landlock file and port policy | design |
| execute from memory (`memfd_create` + `fexecve`) | Landlock if the memfd is outside every rule; otherwise `vm.memfd_noexec=2` sysctl and seccomp deny `execveat` | not yet measured |
| signal or ptrace the bash server | Landlock signal scoping; ptrace across domains denied | not yet measured |
| hooks (they are shell commands) | hooks go through the bash client, or their binaries are on the allowlist | design |
| binaries the orchestrator legitimately needs (ripgrep, git, MCP servers) | learned by tracing the orchestrator (`pbp learn` on Claude Code) and pinned in the manifest | design |
| change the orchestrator's config (settings, `/etc/hosts`) | no write right to those paths in the domain; manifest hash | design |
| root undoes the locks | orchestrator is not root; locks applied by the launcher, above it | design |

## 3. Safety rules for testing inside a live agent session

Testing on the session's own harness is like disabling the network adapter over RDP: one mistake and the session cannot reach the model any more.

1. Never touch the orchestrator or session bridge (PIDs 96 and 89 in the measured session).
2. Never add firewall rules that match uid 0 or the model API address (`160.79.104.10`).
3. Never change global sysctls the harness depends on (e.g. `vm.memfd_noexec` — the harness may exec from memfd).
4. Run every experiment as a **child subtree** that ends when the test ends: a mini orchestrator under its own uid and Landlock domain.
5. Clean up cgroups, sockets and users the test created; leave a list of anything left behind.

## 4. Proof of concept

A mini orchestrator (Python, stands in for Claude Code) and a bash server (stands in for `sharness.bash-server`), both started by a small launcher in a child subtree.

- **launcher**: creates users `harness-orch` (orchestrator) and `harness-sbx` (sandboxes); starts the bash server as root outside any domain; starts the mini orchestrator as `harness-orch`, capabilities dropped, `no_new_privs`.
- **mini orchestrator**: applies its Landlock domain (EXECUTE: nothing new; READ: system + PoC files; WRITE: its workspace; signal scoping), then attempts each side door, then sends commands through the bash client (an in-process library call here; a small static binary in production, so that it needs no interpreter on the allowlist).
- **bash server**: per request, makes a `pids` cgroup (max 64), `unshare --net --pid --fork --mount-proc`, drops to `harness-sbx`, applies the sandbox Landlock profile, runs `bash -c`, filters output for secrets, returns JSON.



## 5. Results

Not run in this session. The proof of concept was started but not completed; the rows in §2.2 marked "not yet measured" remain to be tested by the building agent, following the safety rules in §3.
