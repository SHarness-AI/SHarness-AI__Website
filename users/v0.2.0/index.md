# sharness-ai v0.2.0, as three users found it

**Tested as of 29 Oct 2026 by [users@sharness](../../admin/members/users/index.md)**, against `sharness-ai` 0.2.0 installed from PyPI, answering the CLI's [release checklist](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/qa/RELEASE.md) (R1 to R14) and [this release's asks](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/qa/v0.2.0.md) (Q0.2.0-1 to Q0.2.0-11). The tester did not read the CLI's source before testing anything. It read the installed `REALITY.md` of `sharness.fs` only after the door's tests, to compare.

## The verdicts

| Id | Who | Verdict | In one line |
|---|---|---|---|
| R1 | newcomer | Confusing | installs with no dependencies; the summary says nothing of the MVPs |
| R2 | newcomer | Confirmed | `sharness-ai v0.2.0` |
| R3 | newcomer | Confirmed | the guide screen, no traceback; on a pipe, the argparse help instead |
| R4 | newcomer | Confirmed | every row is a fact or says why; the JSON parses |
| R5 | newcomer | Confusing | a verdict and a next step; the advice box cuts its own sentence in half |
| R6 | newcomer | **Not confirmed** | 6 of 6 from a venv; **0 of 6 after a per-user `pip install`**, with "RAN" against the hash probe |
| R7 | newcomer | Confusing | policy, hash, `ls` runs; a sixth row (`pids 16`) is written that no question asked about |
| R8 | builder | **Not confirmed** | the write is refused, but the message is the shell's `Permission denied`: no "the kernel", no row |
| R9 | builder | Confirmed | sentence, one hash, held, not held, not covered |
| R10 | builder | Confirmed | four command lines, each with what it cannot enforce |
| R11 | skeptic | Confusing | no claim against root or the kernel; `run` and `contain` never say Boundary or Setting |
| R12 | skeptic | **Not confirmed** | a binary the child wrote runs through the dynamic loader; a script it wrote runs through `sh` |
| R13 | newcomer | Could not run | PyPI served a bot challenge to the headless browser; the source shows relative paths (board T31) |
| R14 | all | Confusing | five first-ten-minutes trips, listed under R14 below |
| Q0.2.0-1 | newcomer | **Not confirmed** | the quick start word for word: `run … -- my-tool` fails, with a hint that blames the kernel |
| Q0.2.0-2 | newcomer | Could not run | no Mac here |
| Q0.2.0-3 | newcomer | Confirmed | `none in effect` as a user, `all in effect` as root, bounding set apart |
| Q0.2.0-4 | newcomer | Confirmed | every refused probe's `got` names `PermissionError` or `MemoryError` |
| Q0.2.0-5 | builder | Confirmed | writes land under the root only; nine climbs refused `within_root`; hello says Setting |
| Q0.2.0-6 | builder | Confirmed | 294 bytes in, the same 294 bytes and sha256 back; plain `fs get` mixes the status line into the content |
| Q0.2.0-7 | skeptic | Confirmed | the split header is refused; nine other forms and a PGP key get through, which `REALITY.md` only partly names |
| Q0.2.0-8 | builder | Confirmed | no "nothing else is reachable"; github.com held as port 443 |
| Q0.2.0-9 | builder | **Not confirmed** | `pip download` fails three ways inside the shell; refusals do not say who; the summary says nothing was undone |
| Q0.2.0-10 | skeptic | Confirmed | 127.0.0.2, other hosts, UDP out and DNS: all refused or no route |
| Q0.2.0-11 | skeptic | Confirmed | three kinds of background job gone on exit, the uid removed; the summary is silent about it |

**The three things a newcomer trips on first:**

1. **`pip install sharness-ai` without a venv** (a per-user install into `~/.local`) gives `hello` 0 of 6 and `run` "Permission denied, nothing ran", because the child cannot import the package from `~/.local`. The screen blames nothing and says the hash check "RAN". A venv in the home directory works.
2. **The quick start's last line** (`sharness-ai run --policy my-tool.json -- my-tool`) runs a command that does not exist, and the refusal's hint sends the reader to `probe` and `--best-effort` instead of saying "no such command".
3. **A refusal under `run` is the program's own `Permission denied`**, not the "refused by the kernel, change row X" the README promises. The newcomer cannot tell a policy refusal from an ordinary permission error.

## Where it ran

| | |
|---|---|
| Machine | a Claude Code cloud session: a Linux container (`systemd-detect-virt`: docker) in a Firecracker VM |
| OS | Ubuntu 24.04.5 LTS, x86_64 |
| Kernel | `6.18.44-fc-v185`, Landlock ABI 7 (from `sharness-ai probe`), cgroups hybrid (v1 + unified) |
| Python | 3.13.17 |
| Who | root (uid 0) and four fresh non-root users: `newcomer` (uid 30033), `builder`, `skeptic`, `fresh` |
| Install | `python3 -m venv /opt/qa-venv && /opt/qa-venv/bin/pip install sharness-ai==0.2.0`; for R6 and Q0.2.0-1 also a per-user install and a venv in the user's home |
| Egress | through the session's HTTPS proxy (`HTTPS_PROXY` set: names only, never values) |
| Date | 29 Oct 2026, 03:25 to 03:45 UTC |

Outputs are pasted as they came back, ANSI colour removed. Where a command ended in `| tail`, `| sed` or `| grep`, the cut is in the command line shown.

## The release checklist

### R1: the PyPI page, then pip install (newcomer): Confusing

The page's text came from the JSON API (`https://pypi.org/pypi/sharness-ai/0.2.0/json`), since the browser could not load the page (R13).

```
summary: SHarness: runs agents and their tools as small, single-purpose, kernel-locked processes talking over mutually authenticated connections. Experiments stage: probe, policy hash/check/translate, run, hello.
requires_dist: None   requires_python: >=3.11

$ /opt/qa-venv/bin/pip install sharness-ai==0.2.0
Downloading sharness_ai-0.2.0-py3-none-any.whl (164 kB)
Installing collected packages: sharness-ai
Successfully installed sharness-ai-0.2.0
$ /opt/qa-venv/bin/pip list
Package     Version
----------- -------
pip         26.2.2
sharness-ai 0.2.0
```

No dependencies were pulled in. The page's first screen (the title, one paragraph, "Try it in 60 seconds") says what the tool is in under a minute. **Confusing:** the one-line summary, the first thing PyPI's search shows, lists only the experiments. The page's status block says "three MVPs". `sharness-ai --help` says "no SHarness component is built yet". [What exists today](../../evidence/status/index.md) says three MVPs, and [AGENTS.md](../../admin/guidance/index.md) section 1 says two. A newcomer reading three places gets three answers. *Expected instead:* one count of the MVPs, the same in the summary, the page and `--help`. The summary is item 5 of board T31.

### R2: --version (newcomer): Confirmed

```
# sharness-ai --version
sharness-ai v0.2.0
[exit 0]
```

### R3: no arguments (newcomer): Confirmed

On a terminal (`script -qc 'sharness-ai --width 100'`, as `newcomer`, after the steps below):

```
  where you are   linux 6.18.44-fc-v185 · Landlock ABI 7 · uid 30033 · cgroups hybrid (v1 + unified)
                  a policy will hold here: files by Landlock ABI 7; TCP ports by Landlock too
                  network none tries a user namespace for an empty network namespace, else Landlock
                  TCP rules (UDP not covered)

  the ladder      ✔ 1  probe      the grant: what a process here can do before any policy
                  ✔ 2  hello      the acceptance test: 6/6 held on 2026-10-29 03:27
                  ✔ 3  policy     my-tool  sha256:7704…055a
                  ✔ 4  run        last: my-tool exit 2 on 2026-10-29 03:28
                  ○ 5  shell      a shell under the harness: sharness-ai shell --workspace
                  . --sites github.com
  ...
  what next?      1 probe   2 hello   3 new policy   4 run a command
                  5 translate   6 components   7 doctor   8 contain
                  (a sentence)   9 shell (under the harness)   q quit
  > [q]
```

Where you are, what to do next and the command to type, with no traceback. Two small things. The README says "the four steps" and the screen draws five. On a pipe, `sharness-ai` with no arguments prints argparse's usage, as the README says it will. That usage text opens with "Status: experiments; no SHarness component is built yet" (see R1).

### R4: probe, then probe --json (newcomer): Confirmed

```
$ sharness-ai probe
sharness-ai probe   the grant: what a process here can do before any policy
  identity        uid 30033 · capabilities none in effect (CapEff
                  0000000000000000); bounding set full (CapBnd 000001fffeffffff)
                  · NoNewPrivs 0 · Seccomp 0
  kernel          linux 6.18.44-fc-v185 · Landlock ABI 7 · memfd_secret yes ·
                  cgroups hybrid (v1 + unified)
  namespaces      cgroup, ipc, mnt, net, pid, pid_for_children, time,
                  time_for_children, user, uts
  config          CGROUP_FREEZER=y  USER_NS=y  SECCOMP=y  SECRETMEM=y  FUSE_FS=y
                  SECURITY_LANDLOCK=y  PKCS8_PRIVATE_KEY_PARSER=not set
  tools           unshare ✔  setpriv ✔  bwrap ✘  strace ✔  iptables ✔  nft ✔
                  useradd ✔  fusermount3 ✘  criu ✘
  egress          proxy variables set: none (names only; values are never
                  printed)
  workspace       /home/newcomer/work writable: yes · python 3.13.17
  reading         a policy will hold here: files by Landlock ABI 7; TCP ports by
                  Landlock too
                  network none tries a user namespace for an empty network
                  namespace, else Landlock TCP rules (UDP not covered)
  next            sharness-ai hello   the acceptance test: six probes under one
                  policy
[exit 0]

# sharness-ai probe --json | python3 -m json.tool > /dev/null && echo JSON parses
JSON parses
[exit 0]
```

As root, `egress` named the proxy variables by name only, as it says it will.

### R5: doctor (newcomer): Confusing

```
$ sharness-ai doctor
sharness-ai doctor   can a policy hold here? nine checks, each with what to do about it

  [1/9] ✔ kernel             linux 6.18.44-fc-v185
  [2/9] ✔ landlock_files     ABI 7: file rules (read, write, exec) will hold
  [3/9] ✔ landlock_tcp       ABI 7: TCP port rules will hold (UDP is never covered)
  [4/9] ✔ network_namespace  an empty network namespace can be made (userns+netns)  (4 ms)
  [5/9] ⚠ cgroups            cgroups 1, not writable: memory by RLIMIT_AS only
  ┌─ what to do ───────────────────────────────────────────────────────────────┐
  │  RLIMIT_AS caps address space, not re…nt memory; a writable /sys/fs/cgroup │
  │  gives a real cap                                                          │
  └────────────────────────────────────────────────────────────────────────────┘
  [6/9] ✔ max_pids           RLIMIT_NPROC binds uid 30033: max_pids will hold
  [7/9] ✔ write_probe        the kernel refused a write the policy did not allow (EACCES)  (145 ms)
  [8/9] ✔ openssl            OpenSSL 3.0.13 30 Jan 2024 (Library: OpenSSL 3.0.13 30 Jan 2024): sessions and doors can be made  (3 ms)
  [9/9] ✔ doors              sharness.fs (sharness.fs.disk.twin) and sharness.net (proxy port 36653) answer hello over mutual TLS; a Setting until the launcher  (1130 ms)

  overall         degraded: a policy will hold here with the gaps named above
  next            sharness-ai hello   the acceptance test, six probes under one
                  policy
[exit 0]
```

As root: `healthy: a policy will hold here as written`, nine passes. **Confusing:** the one box that tells a user what to do truncates its own sentence ("not re…nt memory"), at 80 columns and on a pipe. *Expected instead:* the advice wrapped, not cut. The README says "seven checks"; that is item 4 of board T31.

### R6: hello (newcomer): Not confirmed

From a venv, as root and as `newcomer`, 6 of 6 held:

```
$ sharness-ai hello
  ✔ read      /usr (listing)               allowed
  ✔ write-tmp /tmp/…tmp (create)           refused by the kernel (EACCES)
  ✔ write-cwd ./…tmp (create)              refused by the kernel (EACCES)
  ✔ net       1.1.1.1:443 (connect)        refused by the kernel (EACCES)
  ✔ memory    400 MiB under 128            refused by the kernel (MemoryError)
  ✔ hash      sha256:0000… (--expect-hash) refused by sharness-ai

  result          ████████████ 6/6 held · measured 29 Oct 2026, Landlock ABI 7
```

After the install a newcomer is most likely to make: `pip install sharness-ai` as a normal user with no venv. pip put it in `~/.local`, and on this image it did not refuse with "externally managed". As user `fresh`, after a new login:

```
$ pip install sharness-ai
Installing collected packages: sharness-ai
  WARNING: The script sharness-ai is installed in '/home/fresh/.local/bin' which is not on PATH.
Successfully installed sharness-ai-0.2.0
$ sharness-ai hello
  ✘ read      /usr (listing)               failed otherwise  expected allowed; otherwise (/usr/bin/python3: No module named sharness_ai
  ✘ write-tmp /tmp/…tmp (create)           failed otherwise  expected refused; otherwise (/usr/bin/python3: No module named sharness_ai
  ✘ write-cwd ./…tmp (create)              failed otherwise  expected refused; otherwise (/usr/bin/python3: No module named sharness_ai
  ✘ net       1.1.1.1:443 (connect)        failed otherwise  expected refused; otherwise (/usr/bin/python3: No module named sharness_ai
  ✘ memory    400 MiB under 128            failed otherwise  expected refused; otherwise (/usr/bin/python3: No module named sharness_ai
  ✘ hash      sha256:0000… (--expect-hash) RAN: sharness-ai did not refuse  expected refused; exit 1

  result          ░░░░░░░░░░░░ 0/6 held · measured 29 Oct 2026, Landlock ABI 7
  ...
  next            sharness-ai probe   says what this kernel has; please report
                  the result
[exit 1]
```

The same user, with a venv in the home directory (`python3 -m venv ~/venv && ~/venv/bin/pip install sharness-ai==0.2.0`), got 6 of 6. *Expected instead:* 6 of 6 from a per-user install too. Failing that, one line saying the child could not import `sharness_ai` from `~/.local`, and never "RAN: sharness-ai did not refuse" for a check that never got to run. A newcomer would send this as a report that the kernel does not hold.

### R7: policy new, then run (newcomer): Confusing

```
$ sharness-ai policy new my-tool.json        (Enter at each of the five questions)
  1/5  what may it read?                  [/usr /lib /lib64 /bin /sbin /etc /home/newcomer/work]
  2/5  where may it write?                [nowhere]  paths, space-separated; 'none' for nowhere
  3/5  what may it run?                   [/usr /lib /lib64 /bin /sbin /etc]
  4/5  which TCP ports may it connect to? [none]  e.g. 443, or 'none'
  5/5  memory cap, in MiB?                [256]  0 for no cap
  policy          my-tool   my-tool.json
  ┌─ files ─────────────────┐  ┌─ network ────────────┐  ┌─ process ────────┐
  │ read  /bin /etc +5      │  │ connect_tcp  none    │  │ memory  256 MiB  │
  │ write none              │  │ UDP and Unix sockets │  │ pids    16       │
  │ exec  /bin /etc /lib +3 │  │ are not covered      │  │ no_new_privs yes │
  └─────────────────────────┘  └──────────────────────┘  └──────────────────┘
  written         my-tool.json
                  sha256:7704d102aa75a5d05c7c2dac1aed38c4a02e4b4d93a6f2caa183d0d6d424055a
  next            sharness-ai run --policy my-tool.json --expect-hash sha256:7704d102aa75a5d05c7c2dac1aed38c4a02e4b4d93a6f2caa183d0d6d424055a -- CMD

$ sharness-ai run --policy my-tool.json -- ls
sharness-ai run  my-tool  sha256:7704d102aa75a5d05c7c2dac1aed38c4a02e4b4d93a6f2caa183d0d6d424055a
  enforced by     Landlock ABI 7: files · empty network namespace, else Landlock
                  TCP rules · rlimits, and a cgroup where one can be made
  not covered     UDP (DNS) unless the namespace applied · Unix sockets by path
                  · the inherited environment
── ls starts ───────────────────────────────────────────────────────────────────
sharness-ai run: not covered here:
  - Unix-domain sockets by path are not covered (Landlock has no rule for them)
  - memory: RLIMIT_AS only (no memory cgroup could be made); the cap is on address space, which a child can exhaust differently from resident memory
  - the child inherits this process's environment variables (v0 has no row for them)
my-tool.json
── ls exit 0 · 0.0 s ───────────────────────────────────────────────────────────
[exit 0]
```

A policy, its hash, and `ls` under it: as expected. **Confusing:**

- The file carries `"max_pids": 16`. No question asked about it, and it was not shown before it was accepted, though the wizard says "every default is shown before it is accepted".
- The default `exec` row includes `/etc`. The register's SD-09 says nothing needs that, and `policy check` advises against it.
- The questions ran together on one line when answered from a pipe.

*Expected instead:* a sixth question, or the pids cap shown with the other defaults.

### R8: a write to /etc under the policy (builder): Not confirmed

```
$ sharness-ai run --policy my-tool.json -- sh -c 'echo x > /etc/sharness-test'
── sh starts ───────────────────────────────────────────────────────────────────
sharness-ai run: not covered here:
  ...
sh: 1: cannot create /etc/sharness-test: Permission denied
── sh exit 2 · 0.0 s ───────────────────────────────────────────────────────────
  next            sharness-ai policy translate my-tool.json --to docker -- CMD
                  carries the same policy to another enforcer, with what it
                  cannot enforce
[exit 2]
```

The write was refused and nothing was written. But the only message is the shell's own. Nothing says the kernel refused it, or which row (`files.write`) to change, and the next step offered is `translate`. *Expected instead:* what the README promises ("every refusal names who refused … and the row of the policy to change"), at least as a closing line when the child exits non-zero. `hello` already does this for its own probes.

### R9: contain --dry-run (builder): Confirmed

```
$ sharness-ai contain --workspace . --sites pypi.org --dry-run -- my-agent
sharness-ai contain   one sentence, compiled to the kernel, named by one hash
  you said        contain my-agent to /home/newcomer/work, pypi.org, no secrets
  it became       profile coding-agent (4) → 13 path rows + network + caps (3) →
                  one door, the kernel (2) → 14 kernel rules (1)
  the name        sha256:40548b916c51346533f9076d7b6da5e4fddc19837619950fd946e723871a4193
                  every level below is recomputed from it
  held            ✔ 16 rows by the kernel: files, ports, caps
  not held        ⚠ pypi.org: held as port 443; the host name is not held until
                  sharness.net runs here
  not covered     UDP (DNS) unless an empty network namespace applied · Unix
                  sockets by path · the inherited environment
  deeper          sharness-ai explain FILE   the same sentence drawn level by
                  level (--save FILE keeps it)
[exit 0]
```

Everything the ask lists is there. Two small things: "13 path rows", "14 kernel rules" and "16 rows" in three lines do not obviously add up; and "until sharness.net runs here" does not say that `sharness-ai shell` is how to make it run.

### R10: policy translate, four targets (builder): Confirmed

```
$ sharness-ai policy translate my-tool.json --to docker
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges --user 65534:65534 --network none --memory 256m --pids-limit 16 -v /home/newcomer/work:/home/newcomer/work:ro python:3.12-alpine /bin/sh -c 'echo hello'

# docker: not enforced from policy my-tool (sha256:7704d102aa75…):
#   - image python:3.12-alpine is named by tag; pin it by digest (image@sha256:…) so the policy binds to one build
#   - files.read of system paths (/usr, /lib, /bin, /sbin, /etc): taken from the image, not bound from the host
#   - files.exec: not distinct from read; everything readable in the image is executable (Docker has no exec allowlist)
#   - the policy hash: Docker does not check one; the launcher's --expect-hash has no equivalent

$ sharness-ai policy translate my-tool.json --to bwrap
bwrap --unshare-all --die-with-parent --new-session --cap-drop ALL --ro-bind /bin /bin --ro-bind /etc /etc --ro-bind /home/newcomer/work /home/newcomer/work --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /sbin /sbin --ro-bind /usr /usr -- /bin/sh -c 'echo hello'

# bwrap: not enforced from policy my-tool (sha256:7704d102aa75…):
#   - no_new_privs: bwrap sets it (PR_SET_NO_NEW_PRIVS) for the sandboxed process
#   - files.exec: not distinct from files.read; a read-only bind is also executable in bwrap (use noexec mounts or Landlock inside)
#   - process.max_memory_mb 256: not enforced by bwrap; prefix with `prlimit --as=268435456` or run under a cgroup
#   - process.max_pids 16: not enforced by bwrap; `prlimit --nproc=16` or a pids cgroup
```

`--to claude-code` printed a `sandbox` settings fragment and six lines of what it does not enforce. `--to kubernetes` printed a Pod and a NetworkPolicy and seven lines. One small thing: bwrap's "not enforced" list opens with a line saying bwrap *does* set `no_new_privs`.

### R11: every screen, read for its claims (skeptic): Confusing

- **Root and the kernel:** no screen claims protection against either. `probe` as root says "A policy applied from here binds its children, not itself".
- **Boundary and Setting:**
  - `hello` says "a Boundary for the child, a Setting for the parent".
  - `fs hello` and `doctor` say the door is a Setting until the launcher.
  - `shell` says the host allowlist is "a Boundary for the shell: another uid, outside it".
  - **`run` and `contain` never say Boundary or Setting**, and they are the two commands that apply a policy to a child.
  - `fs serve` prints hello's parent-and-child caveat, though no child is involved there; `fs hello` gets the door right.
- **Not covered:** UDP, Unix sockets by path and the inherited environment are named on `hello`, `run`, `contain` and every policy box.

*Expected instead:* the caveat line from `hello` on `run` and `contain` too.

### R12: get around a refusal without root (skeptic): Not confirmed

Under a policy that writes only `~/work/out` (`sharness-ai policy new sk.json --write $HOME/work/out -y`), as `skeptic`:

```
$ sharness-ai run --policy sk.json -- sh -c 'cp /bin/echo out/myecho; ./out/myecho direct-exec; /lib64/ld-linux-x86-64.so.2 ./out/myecho via-the-loader; printf "echo dropped script ran\n" > out/s.sh; chmod +x out/s.sh; ./out/s.sh; sh out/s.sh'
── sh starts ───────────────────────────────────────────────────────────────────
sh: 1: ./out/myecho: Permission denied
via-the-loader
sh: 1: ./out/s.sh: Permission denied
dropped script ran
── sh exit 0 · 0.0 s ───────────────────────────────────────────────────────────
```

The kernel refused `execve` of the dropped files, as SR-01's fix intends. But a binary the child wrote ran anyway through the dynamic loader, which is on the exec list, and a script it wrote ran through `sh`. The README says "a writable path gets every right but execute, so a file the child drops cannot run"; the register marks SR-01 *fixed*. *Expected instead:* the claim narrowed to "cannot be `execve`d", and the loader and interpreter route named under not covered. That is the skeptic's reading; whether to close it (no loader on the exec list, or seccomp) is for cli@ and security@.

The other attempts held, or got through only where the tool already says it will:

```
$ sharness-ai run --policy sk.json -- sh t2.sh        (ln ~/.profile out/p; echo x > /dev/shm/x; echo x >> ~/.profile)
ln: failed to create hard link 'out/p' => '/home/skeptic/.profile': Invalid cross-device link
t2.sh: 2: cannot create /dev/shm/x: Permission denied
t2.sh: 3: cannot create /home/skeptic/.profile: Permission denied

$ sharness-ai run --policy sk.json -- /usr/bin/python3 -c 'import socket; s=socket.socket(socket.AF_UNIX); s.connect("/home/skeptic/work/helper.sock"); s.send(b"via a unix socket\n"); print("sent")'
sent
$ cat ~/written-by-helper.txt          (written by a helper outside the policy, listening on that socket)
via a unix socket

$ sharness-ai run --policy sk.json -- sh -c 'echo through the inherited stdout' > ./not-in-write-rows.txt; tail -1 not-in-write-rows.txt
through the inherited stdout
```

The hard link, `/dev/shm` and `~/.profile` were refused by the kernel. The Unix socket got through, and every screen names it as not covered. The inherited stdout is the caller's own redirection, not a bypass.

### R13: the PyPI page in a browser (newcomer): Could not run

Headless Chromium through the session's proxy got PyPI's "Client Challenge" page, not the project page, so nothing could be seen rendered. What would be needed: a browser a person drives. From the description PyPI serves (the JSON API), the page has three images by relative path (`docs/anim/one-idea.svg`, `docs/anim/hello-replay.svg`, `docs/anim/kernel-in-a-tab.svg`) and relative links to `experiments/policies/README.md`, `experiments/README.md`, `.claude/skills/sharness-hello/SKILL.md` and `SECURITY.md`. PyPI does not resolve those against the repository. Board T31 (website@) already carries the patch.

### R14: the first ten minutes (all): Confusing

- **`fs get FILE > copy` does not copy** (builder). The status line goes to stdout with the content:

  ```
  $ sharness-ai fs get notes.txt > copy.txt 2>/dev/null; cat copy.txt; cmp copy.txt work/notes.txt
    ✔ get       notes.txt                    allowed by sharness.fs
  first line
  second line
  copy.txt work/notes.txt differ: byte 1, line 1
  ```

  For a binary file, plain `fs get` prints `content  294 bytes, not UTF-8: base64 in --json`, which does tell the user what to do.
- **`--json` goes before the command.** `sharness-ai fs hello --json` is `error: unrecognized arguments: --json`, while `sharness-ai --json fs hello` works. Every ask in qa/ writes it after the command.
- **The shell needs a workspace its own uid can use.** As root, `sharness-ai shell` in `/root/...` and then in a fresh `/tmp/qa-ws` was refused twice before anything ran. Both messages are clear and say what to do (`chmod o+rx` / `o+w`, or `--no-user`), but the README's `shell --workspace ./work` example would hit the same as root.
- **Files the shell wrote stay owned by a uid that no longer exists** (`ls -ln`: `996 995`), and the next shell gets uid 996 again.
- **A tool in the same venv cannot run under its own policy.** `run -- python3 …` with the venv's `python3` first on `PATH` fails, because the default read rows do not include the venv:

  ```
  PermissionError: [Errno 13] Permission denied: '/opt/qa-venv/pyvenv.cfg'
  ```

## This release's asks

### Q0.2.0-1: the quick start, word for word (newcomer): Not confirmed

On a fresh user, the four lines after `pip install`, exactly as the page writes them:

```
$ sharness-ai --version
sharness-ai v0.2.0
$ sharness-ai hello                       (0/6 after the per-user install: see R6)
$ sharness-ai policy new my-tool.json -y | tail -2
                  sha256:e628967c1ef4e712fcfd77205dd1bbbc39988ff0a7a1ac7ac9cf4f6a8685aee7
  next            sharness-ai run --policy my-tool.json --expect-hash sha256:e628967c1ef4e712fcfd77205dd1bbbc39988ff0a7a1ac7ac9cf4f6a8685aee7 -- CMD
$ sharness-ai run --policy my-tool.json -- my-tool 2>&1 | tail -2
sharness-ai run: could not apply the policy or start the command: [Errno 13] Permission denied. Nothing ran.
  hint: the policy could not be applied here and nothing ran: sharness-ai probe says what this kernel has; --best-effort runs anyway and says what is NOT enforced
```

`run … -- ls` from the same per-user install failed the same way. From a venv it ran (R7). Two things fail here. First, the per-user install (R6). Second, the last line runs `my-tool`, which is the reader's placeholder but reads as a command, and the hint blames the kernel and offers `--best-effort`. *Expected instead:* the quick start says "with a venv" (or the per-user install works), its last line runs something that exists (`-- ls`), and a missing command or an unimportable package is named as such.

### Q0.2.0-2: macOS says what is missing (newcomer): Could not run

No Mac in this session. What it needs: a real Mac (any recent macOS) with Python 3.11 or later, to run `sharness-ai probe`, `sharness-ai run --policy p.json -- ls` and `sharness-ai hello` and paste the three outputs and exit codes.

### Q0.2.0-3: the capabilities label (newcomer): Confirmed

```
$ sharness-ai probe            (uid 30033)
  identity        uid 30033 · capabilities none in effect (CapEff
                  0000000000000000); bounding set full (CapBnd 000001fffeffffff)
# sharness-ai probe            (root)
  identity        uid 0 (root) · capabilities all in effect (CapEff
                  000001fffeffffff); bounding set full (CapBnd 000001fffeffffff)
```

### Q0.2.0-4: a refusal names its error (newcomer): Confirmed

```
$ sharness-ai hello --json | python3 -c '…print each probe and got…'
read | allowed
write-tmp | refused (PermissionError: [Errno 13] Permission denied: '/tmp/sharness-ai-hello.tmp')
write-cwd | refused (PermissionError: [Errno 13] Permission denied: 'sharness-ai-hello.tmp')
net | refused (PermissionError: [Errno 13] Permission denied)
memory | refused (MemoryError)
hash | refused
6 6
```

Each `got` names the error, never a fragment of screen text. (After the per-user install, `got` was `otherwise (/usr/bin/python3: No module named sharness_ai`, which is honest about the cause but not about the verdict: R6.)

### Q0.2.0-5: the first door, sharness.fs (builder): Confirmed

As `builder`: `sharness-ai session new`, then `sharness-ai fs serve --target disk --root ./work --audit` in the background.

```
$ sharness-ai fs hello
  ✔ get       /v0/hello                    allowed by sharness.fs
  targets         sharness.fs.disk (live)
  caveat          a Boundary for the caller only once the launcher gives this
                  door its own uid and closes every other path; until then a
                  Setting
$ echo 'first line' | sharness-ai fs put notes.txt
  ✔ put       notes.txt                    allowed by sharness.fs
$ echo 'second line' | sharness-ai fs append notes.txt
  ✔ post      notes.txt/append             allowed by sharness.fs
$ sharness-ai fs ls
  ✔ get       /v0/files                    allowed by sharness.fs
    notes.txt
$ ls -la work/ && cat work/notes.txt
-rw-r--r-- 1 builder builder   23 Oct 29 03:28 notes.txt
first line
second line

$ echo pwned | sharness-ai fs put ../escape.txt
  ✘ put       ../escape.txt                refused by sharness.fs (403)  '../escape.txt' is outside the root or not a path  row: within_root (every path)
$ echo pwned | sharness-ai fs put /tmp/escape.txt
  ✘ put       /tmp/escape.txt              refused by sharness.fs (403)  '/tmp/escape.txt' is outside the root or not a path  row: within_root (every path)
$ echo pwned | sharness-ai fs put a/../../escape2.txt
  ✘ put       a/../../escape2.txt          refused by sharness.fs (403)  'a/../../escape2.txt' is outside the root or not a path  row: within_root (every path)
$ sharness-ai fs get ../../.bashrc
  ✘ get       ../../.bashrc                refused by sharness.fs (403)  '../../.bashrc' is outside the root or not a path  row: within_root (every path)
$ ln -s /home/builder work/link && echo pwned | sharness-ai fs put link/escape3.txt; sharness-ai fs get link/.bashrc
  ✘ put       link/escape3.txt             refused by sharness.fs (403)  symlink escape: link in link is a symbolic link  row: within_root (every path)
  ✘ get       link/.bashrc                 refused by sharness.fs (404)  no such file
```

Straight to the port with the app's certificate (`curl -sk --cert app.crt --key app.key`): `%2e%2e%2fwork%2fnotes.txt`, `..%2f..%2f.bashrc`, `PUT %2e%2e/escape4.txt` and `notes.txt%00x` all came back `{"allowed": false, "status": 403, … "row": "within_root (every path)"}`. Without a client certificate, `curl` got no TLS session (exit 56). No `escape*` file appeared outside the root. The session's keys are `0600` in a `0700` folder; another user's `cat` of `app.key` got `Permission denied`. One small inconsistency: through a symlink, `put` says `403 within_root` but `get` says `404 no such file`.

### Q0.2.0-6: binary files read back (builder): Confirmed

```
$ python3 -c "…write 294 bytes: a PNG signature, bytes 0 to 255, then \x00\xff\xfe ×10…"; sha256sum img.png; wc -c img.png; sharness-ai fs put img.png img.png
41ad22340584541bc23cf98d9b8f34dc67e2867c4b12fc0d5e8fd0711b7d5810  img.png
294 img.png
  ✔ put       img.png                      allowed by sharness.fs
$ sharness-ai --json fs get img.png | python3 -c '…decode content_b64, print its length and sha256…'
['allowed', 'content_b64', 'path', 'size', 'status']
294 41ad22340584541bc23cf98d9b8f34dc67e2867c4b12fc0d5e8fd0711b7d5810
```

### Q0.2.0-7: a secret split across appends (skeptic): Confirmed

```
$ printf -- 'log start\n-----BEGIN PRIV' | sharness-ai fs put split.txt; printf -- 'ATE KEY-----\nMIIfake\n' | sharness-ai fs append split.txt; sharness-ai fs get split.txt
  ✔ put       split.txt                    allowed by sharness.fs
  ✘ post      split.txt/append             refused by sharness.fs (403)  refuses clear secrets: the bytes parse as a private key  row: refuse_secrets (every path)
  ✔ get       split.txt                    allowed by sharness.fs
log start
-----BEGIN PRIV
```

The header split four ways (`-----BEG`, `IN PRIV`, `ATE KE`, `Y-----…`) was refused at the fourth append. Headers for RSA, OPENSSH, EC, ENCRYPTED and DSA keys were refused, and so were a CRLF copy, an indented one, one inside a Python string and a real throwaway ed25519 key from `openssl genpkey`. Then the attempts to beat it. Each wrote a fake block (`MIIfake`) unless it says otherwise:

```
  ✔ put       e-b64.txt                    allowed by sharness.fs      (the whole PEM, base64)
  ✔ put       e-hex.txt                    allowed by sharness.fs      (hex)
  ✔ put       e-gz.bin                     allowed by sharness.fs      (gzip)
  ✔ put       e-utf16.txt                  allowed by sharness.fs      (UTF-16)
  ✔ put       e-lower.txt                  allowed by sharness.fs      (lower case)
  ✔ put       e-spaces.txt                 allowed by sharness.fs      (----- BEGIN PRIVATE KEY -----)
  ✔ put       e-endash.txt                 allowed by sharness.fs      (the first dash an en dash)
  ✔ put       t-PGP_PRIVATE_KEY_BLOCK.pem  allowed by sharness.fs      (-----BEGIN PGP PRIVATE KEY BLOCK-----)
  ✔ put       e-body-only.txt              allowed by sharness.fs      (a real ed25519 key, header and footer lines removed)
  ✔ put       e-der.bin                    allowed by sharness.fs      (a real ed25519 key, DER)
```

The door's `REALITY.md` names "another encoding (base64, UTF-16)" and a split more than 4 KiB apart. It does not name hex, gzip, case, spacing, look-alike dashes, PGP blocks, a key body without its armour, or DER. The ask itself held, so the verdict is Confirmed. The list of what gets through is for cli@ to add to `REALITY.md` or close. The two throwaway keys were deleted through the door straight after.

### Q0.2.0-8: contain's wording (builder): Confirmed

```
$ sharness-ai contain --workspace . --sites github.com --dry-run -- x
  held            ✔ 16 rows by the kernel: files, ports, caps
  not held        ⚠ github.com: held as port 443; the host name is not held
                  until sharness.net runs here
```

### Q0.2.0-9: the shell under the harness (builder): Not confirmed

As root, workspace `/tmp/qa-ws` (made writable by others after the refusals in R14):

```
# cd /tmp/qa-ws && sharness-ai shell --sites pypi.org --no-ui -- sh -c '…'
  who             uid 996 (sharness-da0bdd, made for this shell, removed on
                  exit)
  network         only 127.0.0.1:39983, sharness.net.proxy · hosts pypi.org ·
                  HTTPS_PROXY set
  held            ✔ files, the port and the caps by the kernel · ✔ the host
                  names by sharness.net (a Boundary for the shell: another uid,
                  outside it)
── sh starts ───────────────────────────────────────────────────────────────────
IN: uid=996(sharness-da0bdd) gid=995(sharness-da0bdd) groups=995(sharness-da0bdd)
sh: 1: /opt/qa-venv/bin/pip: Permission denied
curl: (56) CONNECT tunnel failed, response 403
000
sh: 1: cannot create /etc/sharness-shell-test: Permission denied
sh: 1: cannot create /root/outside.txt: Permission denied
sh: 1: cannot create /tmp/outside.txt: Permission denied
── sh exit 0 ───────────────────────────────────────────────────────────────────
  summary         1 requests through sharness.net: 0 allowed, 1 refused
```

`https://example.com` was refused by the proxy and the writes by the kernel, and none of the three files exists afterwards. `curl https://pypi.org/simple/sharness-ai/` inside the shell got `200` (`summary … 1 allowed … hosts reached: pypi.org`). But `pip download` from pypi.org did not work as the ask writes it, for three separate reasons:

```
PYTHONPATH is /opt/qa-venv/lib/python3.13/site-packages          (set by the shell; the shell's uid cannot read it)
PermissionError: [Errno 13] Permission denied: '/opt/qa-venv/lib/python3.13/site-packages'
sh: 1: cannot create /dev/null: Permission denied                   (also: curl -o /dev/null fails, and sh cannot start a background job)
pip._vendor.requests.exceptions.ProxyError: HTTPSConnectionPool(host='files.pythonhosted.org', port=443): … Tunnel connection failed: 403 Forbidden
```

With `unset PYTHONPATH` and `--sites pypi.org files.pythonhosted.org`, `python3 -m pip download --no-deps sharness-ai==0.1.0` saved the wheel (`2 requests through sharness.net: 2 allowed`). *Expected instead:*

- the shell does not set a `PYTHONPATH` its own policy cannot read;
- `/dev/null` is writable (website@ found the same: board T30, item 2);
- `--sites pypi.org` says that pip also needs `files.pythonhosted.org`.

The refusals inside also do not say who refused: curl shows `response 403` and sh shows `Permission denied`. The exit summary does not say what was undone. Q0.2.0-11 shows it was undone; the summary just does not say so.

### Q0.2.0-10: the shell reaches only its proxy (skeptic): Confirmed

Inside `sharness-ai shell --sites pypi.org`, a Python script (`unset PYTHONPATH` first):

```
tcp 127.0.0.1:45619  -> CONNECTED                  (the proxy)
tcp 127.0.0.2:45619  -> refused: ConnectionRefusedError [Errno 111] Connection refused
tcp 127.1.2.3:45619  -> refused: ConnectionRefusedError [Errno 111] Connection refused
tcp 10.0.0.1:45619  -> refused: OSError [Errno 101] Network is unreachable
tcp 1.1.1.1:45619  -> refused: OSError [Errno 101] Network is unreachable
tcp 127.0.0.1:22 -> refused: PermissionError [Errno 13] Permission denied
tcp [::1] proxy port -> refused: OSError [Errno 97] Address family not supported by protocol
udp 1.1.1.1:53 -> refused: OSError [Errno 101] Network is unreachable
udp 8.8.8.8:53 -> refused: OSError [Errno 101] Network is unreachable
udp 127.0.0.53:53 -> sent (no error)               (loopback inside the shell's own namespace)
udp 127.0.0.1:9999 -> sent (no error)
dns example.com -> failed: gaierror [Errno -3] Temporary failure in name resolution
```

Through the proxy: `https://pypi.org:22/`, `https://151.101.0.223/`, `https://PyPI.org./`, `https://pypi.org.evil.example/` and `https://evil.pypi.org/` were all refused. `http://pypi.org/` got 301 (`7 requests through sharness.net: 1 allowed, 6 refused`). Inside, the note says "the network namespace has loopback only, so UDP has no route out", and nothing says DNS still resolves. It is printed under the heading `sharness-ai run: not covered here`, though the command typed was `shell`.

### Q0.2.0-11: nothing of the shell outlives it (skeptic): Confirmed

Three background writers, started with `os.fork()`: one plain, one after `setsid()`, one double-forked after `setsid()`.

```
started plain
started setsid
started double
  4 bg-double.log
  4 bg-plain.log
  4 bg-setsid.log
── sh exit 0 ───────────────────────────────────────────────────────────────────
  summary         0 requests through sharness.net: 0 allowed, 0 refused

# wc -l bg-*.log; sleep 3; wc -l bg-*.log; ps -eo uid,pid,cmd | awk '$1>=990 && $1<1000'; grep -c sharness- /etc/passwd
  8 bg-double.log
  8 bg-plain.log
  8 bg-setsid.log
  8 bg-double.log
  8 bg-plain.log
  8 bg-setsid.log
0
```

All three stopped when the shell exited: the counts did not grow over three seconds and no process of the shell's uid is left. The user is gone from `/etc/passwd`. The summary does not say any of that (see Q0.2.0-9).

## What happens next

Every *Not confirmed* went to cli@ as a `To-cli:` note, with its ask id, in the commit that published this report. The R12 finding went to security@ as well, since SR-01 is on the register as fixed. When v0.2.1 or v0.3.0 reaches PyPI with `qa/v<X.Y.Z>.md`, the users run the checklist and that file again, and the next report goes beside this one.

---

*Generated from [content/users/v0.2.0.md](https://github.com/SHarness-AI/SHarness-AI__Website/blob/dev/content/users/v0.2.0.md) by `tools/gen_users.py`; edit the source, never this file. The asks are the CLI's [qa/](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/qa/README.md).*
