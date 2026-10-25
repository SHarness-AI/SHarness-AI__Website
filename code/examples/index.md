# Examples

> Every runnable example, with its output as of 25 Oct 2026 in one Claude agent workspace (Ubuntu 24.04, Linux 6.18, Landlock ABI 7, uid 0). Nothing here is a component; each is an experiment on the [ladder](../experiments/index.md).

## Install

```
pip install git+https://github.com/SHarness-AI/SHarness-AI__CLI@dev     # the experiments (unreleased to PyPI)
sharness-ai --version
```

## E01: the grant

```
$ sharness-ai probe
sharness-ai probe   the grant: what a process here can do before any policy
identity    uid 0 (root) · capabilities all (CapEff 000001fffeffffff, CapBnd 000001fffeffffff) · NoNewPrivs 0 · Seccomp 0
kernel      linux 6.18.44-fc-v153 · Landlock ABI 7 · memfd_secret yes · cgroups hybrid (v1 + unified)
namespaces  cgroup, ipc, mnt, net, pid, pid_for_children, time, time_for_children, user, uts
config      CGROUP_FREEZER=y  USER_NS=y  SECCOMP=y  SECRETMEM=y  FUSE_FS=y  SECURITY_LANDLOCK=y  PKCS8_PRIVATE_KEY_PARSER=not set
tools       unshare ✔  setpriv ✔  bwrap ✗  strace ✔  iptables ✔  nft ✔  useradd ✔  fusermount3 ✗  criu ✗
egress      proxy variables set: HTTPS_PROXY, https_proxy, NO_PROXY, no_proxy (names only; values are never printed)
reading     this process is root with every capability and no seccomp: the grant is everything. A policy applied from here binds its children, not itself.
```

`--json` gives the same as a machine-readable object.

## E02: a policy and its hash

The deny-all example, `experiments/policies/deny-all-example.json`:

```json
{"pbp": 1, "id": "deny-all-example", "layer": "invocation",
 "notes": "E02 example: read and exec the system, write nowhere, no network. ...",
 "files": {"read": ["/usr", "/lib", "/lib64", "/bin", "/etc"], "write": [], "exec": ["/usr", "/bin"]},
 "network": "none",
 "process": {"no_new_privs": true}}
```

```
$ sharness-ai policy hash experiments/policies/deny-all-example.json
sha256:ab1d3e4e779313274f7a1d3ef3e46f6eacef038d8cfaa6198151a45cd82dcc76
$ sharness-ai policy check experiments/policies/deny-all-example.json
experiments/policies/deny-all-example.json: well-formed v0 policy, id deny-all-example: read 5 path(s), write 0, exec 2; network none; sha256:ab1d…cc76
```

Paste the same file into [the browser mockup](../../explain/mockups/policy-hash.html): the hash is the same. The second example, `allow-https-example.json`, is the same policy with `"network": {"connect_tcp_ports": [443]}`.

## E03: one command under a policy

```
$ sharness-ai run --policy experiments/policies/deny-all-example.json -- /bin/sh -c 'echo "$SHARNESS_AI_POLICY_ID $SHARNESS_AI_POLICY_HASH"; touch /x; grep NoNewPrivs /proc/self/status'
deny-all-example sha256:ab1d3e4e779313274f7a1d3ef3e46f6eacef038d8cfaa6198151a45cd82dcc76
touch: cannot touch '/x': Permission denied
grep: /proc/self/status: Permission denied

$ sharness-ai run --policy experiments/policies/allow-https-example.json -- python3 -I -c "import socket; print(socket.create_connection(('1.1.1.1', 443)).getpeername())"
('1.1.1.1', 443)
$ sharness-ai run --policy experiments/policies/allow-https-example.json -- python3 -I -c "import socket; socket.create_connection(('1.1.1.1', 80))"
PermissionError: [Errno 13] Permission denied

$ sharness-ai run --policy experiments/policies/deny-all-example.json --expect-hash sha256:0000…0000 -- /bin/true
sharness-ai run: refused. The policy hashes to sha256:ab1d…cc76; the hash supplied was sha256:0000…0000. Nothing ran.
```

`/proc` is unreadable under the deny-all policy because it is not in the read list: the policy means what it says. Port 443 allowed and port 80 refused is Landlock ABI 4's TCP rule.

With caps (`"process": {"no_new_privs": true, "max_memory_mb": 64, "max_pids": 4}`), `--verbose` reports what was applied, and the fifth background process cannot be started:

```
sharness-ai run: applied {'netns': 'netns', 'landlock_abi': 7, 'paths': 7, 'missing': [], 'ports': [],
  'limits': ['cgroup1 memory.limit_in_bytes=64MiB', 'cgroup1 pids.max=4', 'RLIMIT_AS=64MiB', 'RLIMIT_NPROC=4']}
/bin/sh: 0: Cannot fork
```

## E04: the acceptance test

```
$ sharness-ai hello
sharness-ai hello   experiment E04: the memo's acceptance test, for one child process
policy      hello  sha256:ad37e58bea6f4da65656687045b33ae9977caf90feef0ff5716a44db041b35af
            read-only: /bin, /etc, /lib, /lib64, /opt, /sbin, <the workspace>, /usr, /usr/bin
            write: none · exec: system and Python · network: none · memory: 128 MiB
kernel      Landlock ABI 7 · empty network namespace: yes (uid 0)
  ✔ read       expected allowed  got allowed
  ✔ write-tmp  expected refused  got refused (PermissionError: [Errno 13] Permission denied: '/tmp/sharness-ai-hello.tmp')
  ✔ write-cwd  expected refused  got refused (PermissionError: [Errno 13] Permission denied: 'sharness-ai-hello.tmp')
  ✔ net        expected refused  got refused (PermissionError: [Errno 13] Permission denied)
  ✔ memory     expected refused  got refused (MemoryError)
  ✔ hash       expected refused  got refused
result      6/6 held
caveat      applied by this process to its own children: a Boundary for them, a Setting for whoever ran this, who could have skipped it. ...
```

Exit 0 when every expectation held; `--json` for the Evidence page. The hash differs per machine because the policy lists the workspace.

## sgit under a policy

sgit 0.24.0, unchanged, under a v0 policy that allows the system and the key store read-only, no writes, no network (24 Oct 2026):

```
$ sharness-ai run --policy p-sgit-ro.json -- sgit --version
sgit-ai v0.24.0
$ sharness-ai run --policy p-sgit-ro.json -- sgit pki list
No key pairs found.
```

The commands that need no key and no network run as they are: transparent mode, for those. The map of what changes for the others is on [the spectrum](../../design/spectrum/index.md#3-sgits-next-version-the-compatibility-map).

## In a Claude Code session

The skill `sharness-hello` in the CLI repository runs E01 and E04 inside a session under the design's safety rules (never touch the orchestrator, never firewall uid 0, everything as a child subtree, leave nothing behind) and reports in the site's status words. Ask the session to "run the sharness hello".

## Not examples

The mockups compute; they enforce nothing. The storyboards draw the design. Nothing on this page binds the agent that runs it: each example confines a child process of the shell it was typed into.
