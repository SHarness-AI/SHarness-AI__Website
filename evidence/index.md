# Evidence

> **Every figure on this page was observed as of 24 Oct 2026, in one Claude agent workspace (claude.ai, cloud session).** One environment, one day. Re-run the probes before relying on them elsewhere: other platforms, and later versions of this one, may differ.

Three labels are used across the site, and this page is where they are earned:

| Label | Means |
|---|---|
| **measured** | probed or timed in the environment below, with the method stated |
| **designed / proposed** | a description of how SHarness would work; nothing is built |
| **not yet measured** | named in the design, not tested: seccomp filters, read-only bind mounts, every side door on [Enforcing the process tree](../design/process-tree/index.md), and AWS KMS compatibility |

Every reported `hello` run, ours and yours, is on [hello on your machine](machines/index.md).

## 1. The environment

| Fact | Observed |
|---|---|
| Isolation | Firecracker microVM; PID 1 is `/process_api --firecracker-init …` (not systemd) |
| OS / kernel | Ubuntu 24.04.5, Linux 6.18.44, x86_64 |
| Agent's identity | **uid 0 (root)**, full capability set (`CapEff 000001fffeffffff`) |
| Hardening present | no seccomp, `NoNewPrivs 0`, no Yama (`/proc/sys/kernel/yama` absent) |
| Core dumps | `ulimit -c 0`; `core_pattern = core` |
| Python / crypto | Python 3.13.17; `cryptography` 50.0.1 |
| sgit | `pip install sgit-ai` → **0.24.0** (the version the origin article analysed, at commit `182cfc1`) |
| Hardware keys | no `/dev/tpm*` |
| Egress | every outbound HTTPS goes through a platform proxy at `127.0.0.1:43305`; `send.sgraph.ai`, `pki.sgit.ai`, `cli.sgit.ai` reachable (HTTP 200) |
| Scratch space | the agent's scratchpad is root-only (other uids get `EACCES`) |
| Process lifetime | per the platform: a process detached with `nohup`/`&` is stopped within minutes of the agent's reply; a tool-managed background process can run up to 2 h. **Not measured** |
| Firewall tools | `iptables`, `nft` present; OUTPUT policy ACCEPT, empty |
| cgroups | v1: blkio, cpu, cpuacct, cpuset, devices, freezer, memory, pids, systemd, unified |
| FUSE | `/dev/fuse` (root-only), `fusermount3` present |

### Kernel configuration (`/proc/config.gz`)

| Option | Value | Relevance |
|---|---|---|
| `CONFIG_SECURITY_LANDLOCK` | y (ABI 7) | file and TCP port sandboxing |
| `CONFIG_SECCOMP` | y | syscall allowlists |
| `CONFIG_SECRETMEM` | y | `memfd_secret` |
| `CONFIG_CGROUP_FREEZER` | y | freeze the KMS between calls |
| `CONFIG_CHECKPOINT_RESTORE` | y | CRIU possible (binary not installed) |
| `CONFIG_FUSE_FS` | y | `sharness.fs` as a mount |
| `CONFIG_ASYMMETRIC_KEY_TYPE` | y | kernel asymmetric keys … |
| `CONFIG_PKCS8_PRIVATE_KEY_PARSER` | **not set** | … but no private keys, so kernel-held decryption is unavailable |
| `CONFIG_TRUSTED_KEYS` | not set | (needs a TPM anyway) |
| `CONFIG_ENCRYPTED_KEYS` | y | symmetric blobs only |

## 2. sgit 0.24.0, checked

| Claim (from the origin article) | Result | Method |
|---|---|---|
| `pki keygen` makes RSA-OAEP 4096 + ECDSA P-256, `sha256:` + 16 hex | ✔ | ran it with a throwaway HOME |
| private keys encrypted with PBKDF2 at **2,048** iterations | ✔ `INTEGER :0800` on both `private_key.pem` and `signing_private.pem` | `openssl asn1parse` |
| `Secrets__Store` uses a fixed salt | ✔ `salt = f'{SECRETS_SALT_PREFIX}:master'` | source |
| `BestAvailableEncryption` used for keys | ✔ `crypto/PKI__Crypto.py:37` | source |
| the vault key is read in many places | 65 references in 23 files for `_read_vault_key\|load_vault_key\|vault_key_path` (broad grep including imports; the article counts 27 read sites in 17 files) | grep |
| key file modes | `public_key.pem` 0644; private PEMs 0600 | `ls -l` |

## 3. Memory

| Probe | Result |
|---|---|
| `prctl(PR_SET_DUMPABLE, 0)`, then root reads `/proc/<pid>/mem` | **secret found**: root's `CAP_SYS_PTRACE` overrides |
| `mlock` / `mlockall` | succeed |
| `memfd_secret` (syscall 447) | available |
| root reads a `memfd_secret` page through `/proc/<pid>/mem` | **`EIO`** |
| RSA-4096 OAEP open → copy into a secret page → **no** scrub; root sweeps all readable mappings | one copy found in the anonymous heap |
| the same, **with** scrubbing the returned `bytes` | **no copy found** |
| RSA-4096 OAEP open time | 3.2–3.6 ms |
| kernel keyring `add_key` (process keyring) | works |
| user keyring entry persists across separate agent tool calls | ✔ |
| key in uid `sgit-dec`'s user keyring, searched by uid `sgit-run` | `ENOKEY` |
| that key in root's `/proc/keys` | not listed |
| `add_key("asymmetric", <PKCS#8 RSA-4096 DER>)` | **`EBADMSG`** (parser not built) |
| cgroup freezer: freeze / thaw a process (average of 20) | **0.28 ms / 0.13 ms**; frozen state `D` |

## 4. Process isolation

| Probe | Result |
|---|---|
| create system users (`useradd -r -M -s nologin`) | ✔ |
| `setpriv --reuid --regid --clear-groups --no-new-privs --inh-caps=-all --bounding-set=-all` | CapEff 0, CapBnd 0, NoNewPrivs 1 |
| another uid reads a root file | denied |
| `unshare --net`, then connect out | `ENETUNREACH` (101) |
| `unshare --user --map-root-user --pid --fork --mount-proc` | ✔ |
| Landlock ABI | 7 |
| `RLIMIT_NPROC=0`, then `fork` | `EAGAIN` (blocked) |
| Landlock fs (read-only `/usr /etc /lib /lib64 /proc`): read `/etc/hostname` | allowed |
| Landlock fs: read a file elsewhere | `EACCES` |
| Landlock fs: write `/tmp/x` | `EACCES` |
| Landlock net (connect only to 43305): proxy port | allowed |
| Landlock net: `127.0.0.1:22`, `1.1.1.1:443` | `EACCES` |
| `iptables -A OUTPUT -m owner --uid-owner <user> -j REJECT` | accepted |
| `SO_PEERCRED` on a Unix socket | returns pid, uid, gid |
| abstract-namespace Unix socket | ✔ |
| ephemeral user + firewall rule + locked launch + teardown (average of 10) | **49 ms** |
| new net + pid + mount namespaces (average of 10) | **3.7 ms** |
| seccomp filter | available, **not tested** |

## 5. Footprint

`strace -f` (file, network, process, ipc), successful opens only.

| Command | Paths opened | Folders | Distinct syscalls | execve | socket / connect |
|---|---|---|---|---|---|
| `python3 -I -c print(1)` | 39 | 21 | 31 | 1 | 0 |
| `sgit --version` | 1,104 | 212 | 38 | 1 | 0 |
| `sgit pki list` | 1,109 | 215 | 39 | 1 | 0 |
| `import sgit_ai.cli.CLI__Main` | 529 modules, 146 ms | | | | |
| bare `python3 -I -c pass` start | 15 ms | | | | |

## 6. Transport

Python `ssl`, TLS 1.3, P-256; the server is a thread in the benchmark process.

| | Connect + handshake | 600 B round trip | Bulk (64 MiB echo) |
|---|---|---|---|
| TCP plain | 0.10 ms | 15 µs | ~300 MB/s |
| TCP mutual TLS | **3.2 ms** | 67 µs | ~320 MB/s |
| Unix plain | 0.09 ms | 56 µs | ~320 MB/s |
| Unix mutual TLS | 3.4 ms | 74 µs | ~420 MB/s |
| pipe to a separate process | — | 34 µs | — |
| TCP mutual TLS **without** server `TCP_NODELAY` | 46 ms | | |

Session CA + four role certificates (P-256, 2 h validity): **24 ms**.

Edge enforcement with roles in `subjectAltName` URIs, policy `fs←{cli}, net←{cli}, kms←{net}` (the probe named the app role `cli`, as sgit's CLI):

```
cli → fs   OK        fs  → kms  DENY
cli → net  OK        cli → kms  DENY
net → kms  OK        fs  → net  DENY
```

Figures are from the final of three runs. Across runs, round trips and bulk varied by up to ~25% (TCP mutual TLS bulk: 250, 275, 318 MB/s; Unix mutual TLS bulk: 349, 378, 418 MB/s); handshake times were stable. Microsecond figures are noisy because the server thread shares Python's interpreter lock with the client: treat them as upper bounds.

## 7. The agent loop in this environment (read-only observation)

Observed as of 24 Oct 2026; may differ elsewhere. Method: `ps --forest`, `/proc/net/tcp` mapped to socket inodes, environment variable **names** only, `findmnt`. TLS traffic was not inspected, no credentials or session identifiers were captured, and no configuration was changed.

| Item | Observed |
|---|---|
| PID 1 | `/process_api --firecracker-init … --block-local-connections` |
| PID 89 | `environment-manager task-run --stdin …`, root; its own HTTPS connections to the model API address |
| PID 96 | `/opt/claude-code/bin/claude`, Claude Code **2.1.42**, root; ~18 established HTTPS connections to the model API address; listens on a local port |
| the agent's Bash | direct child of PID 96 |
| other processes | `sbx-telemetry-collector` (own uid), `rclone-filestore multimount` |
| model endpoint | `ANTHROPIC_BASE_URL=https://api.anthropic.com`; `/etc/hosts` pins it; it is in `no_proxy`, so model calls bypass the egress proxy |
| credentials | carried in `ANTHROPIC_CUSTOM_HEADERS`; value **deliberately not read** |
| harness flags (names / booleans only) | `CLAUDE_CODE_REMOTE=true`, `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=1`, `CCR_AGENT_PROXY_ENABLED=1`, `CCR_UPSTREAM_PROXY_ENABLED=1`, `CLAUDE_CODE_PROXY_RESOLVES_HOSTS=true` |
| `/opt/claude-code` | read-only mount |
| `/root/.claude/settings.json` | writable by root; no managed settings under `/etc/claude-code/` |
| `/etc/hosts` | writable by root; its mtime changed mid-session |
| kernel cmdline | `nomodule` |

## 8. Left in the environment

The probes left users `sgit-dec` and `sgit-run`, a folder of probe scripts (`/opt/sgit-probe/`) and a user-keyring entry `sgit:persist-probe` (root). All died with the VM.

## 9. The first experiments, run by the CLI

Run on 24 October 2026 in a second Claude Code cloud session (as of 24 Oct 2026). The commands are experiments E01 to E04 in the CLI repository, [experiments/README.md](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/README.md); the map is [Mockups and experiments](../code/experiments/index.md). Method: `sharness-ai probe` for the environment (read-only; it prints the names of proxy variables, never values), `sharness-ai hello --json` for the result; each probe is `python3 -I -c …` run as a child under the policy by `sharness-ai run`.

| Fact | Observed (E01, probe) |
|---|---|
| Environment | Ubuntu 24.04.5, Linux 6.18.44, Python 3.13.17; uid 0, every capability, `NoNewPrivs 0`, `Seccomp 0` |
| Kernel | Landlock ABI 7; `memfd_secret` available; cgroups v1 with a unified mount; `CONFIG_PKCS8_PRIVATE_KEY_PARSER` not set |
| Tools | `unshare`, `setpriv`, `strace`, `iptables`, `nft`, `useradd` present; `bwrap`, `fusermount3`, `criu` absent |
| Egress | `HTTPS_PROXY` and `NO_PROXY` set (names only); the proxy port differed from the one seen in §7 |
| Harness | Claude Code **2.1.310** (§7 observed 2.1.42 on the same day in another session): versions move between sessions |

| Probe (E04, `hello`) | Policy says | Result |
|---|---|---|
| list `/usr` | allowed | allowed |
| create `/tmp/sharness-ai-hello.tmp` | refused | `EACCES` (Landlock) |
| create a file in the workspace | refused | `EACCES` (Landlock) |
| TCP connect to `1.1.1.1:443` | refused | `EACCES` (Landlock port rule; an empty network namespace was also applied) |
| run with a wrong `--expect-hash` | refused, nothing runs | exit 125, nothing ran |

Policy hash `sha256:ad37e58bea6f4da65656687045b33ae9977caf90feef0ff5716a44db041b35af` (the `hello` policy generated for that interpreter; the paths include the workspace, so the hash differs per machine). 5 of 5 held; the whole run took 0.6 s. Under E03 with the `allow-https-example` policy, a connect to `1.1.1.1:443` succeeded and one to port 80 was refused.

**Caps, measured 25 Oct 2026** (as of 25 Oct 2026, the same kind of session; cgroups v1 with a unified mount). `process.max_memory_mb` and `process.max_pids` in a v0 policy are applied by `sharness-ai run` as `RLIMIT_AS` and `RLIMIT_NPROC` on the child plus a memory and a pids cgroup under `/sys/fs/cgroup/memory/sharness-ai/<pid>` and `/sys/fs/cgroup/pids/sharness-ai/<pid>`, removed by the parent afterwards:

| Probe | Policy says | Result |
|---|---|---|
| `bytearray(400 << 20)` under `max_memory_mb: 128` (E04, `hello`, now 6 probes) | refused | `MemoryError` (the rlimit fires first; the cgroup would OOM-kill) |
| `bytearray(8 << 20)` under the same cap | allowed | allowed |
| the fifth background process under `max_pids: 4` | refused | `Cannot fork` from the shell |
| cgroup left behind after the run | none | none (the per-pid directories and the empty parent are removed) |

`hello` with the memory probe: 6 of 6 held. Not yet: the `cpu` cgroup, `max_runtime_s`, seccomp.

**E09, a second kernel, measured 25 Oct 2026** (as of 25 Oct 2026, the same session: Node 22.22; Chromium 153 headless through Playwright; v86 0.5.472; the guest Alpine 3.23 x86, `linux-virt` 6.18.58-0-virt, Python 3.12.15, built by `experiments/browser/build_guest.py`; each form run once, alone). Method: the guest's `/init` runs `dmesg | grep landlock`, `probe`, `hello`, `run` under the profiles P1, P2 and P0, and `policy check` and `hash` over the seven example files; the runners read the serial console and exit 0 only on `SHARNESS-HELLO-EXIT 0`. The chroot form mounts `/proc` in the built rootfs and runs `probe` and `hello` on the host kernel.

| Form | Guest | Result | To `hello`'s exit / to power-off |
|---|---|---|---|
| v86 in Node | `landlock: Up and running.`; Landlock ABI 7; `memfd_secret` yes; cgroups v2 | `hello` 6 of 6; P1: 443 `ENETUNREACH` (allowed; no network backend), 80 `EACCES`; P2: write refused, read allowed; P0: 200 MiB refused under 64 MiB; seven hashes equal to the host's | 58.0 s / 74.6 s |
| v86 in headless Chromium | the same | the same; `crossOriginIsolated false`, no `SharedArrayBuffer`, no page errors | 75.9 s / 95.9 s |
| chroot on the host kernel | host 6.18.44, Landlock ABI 7; binaries ELF `e_machine 0x0003` (i386) | `hello` 6 of 6 | under 2 s |

The timings are of a single emulated core and are not a measurement of the harness. Dinis Cruz's run of the published page in Chrome on Dinis's own machine, the same day (as of 25 Oct 2026, read off the page's clock in the screenshots; the browser version and machine not recorded): `hello` exit at 28.5 s, guest done at 32.2 s, every line as above. Write-up and what it does not show: [Linux in the browser](../code/browser/index.md); the story with the screenshots: [Linux in a tab](../articles/linux-in-a-tab.md).

**The playground, measured 25 Oct 2026** (as of 25 Oct 2026, headless Chromium 153 against [code/playground](../code/playground/index.html) served from this site's tree, `test_playground.mjs`): Pyodide 314.0.7 loaded in 3.2 s and `pip install sharness-ai` (the dev wheel, by micropip) finished by 3.8 s; `policy hash`, `translate`, `probe` gave the expected output and `hello` refused with exit 126; the Linux guest reached its shell in 38.8 s, `hello` held 6 of 6, P2 refused a write; P0 hashed identically by WebCrypto, Pyodide and Linux; 11 of 11 checks, no page errors.

**The guest on the page's network, measured 25 Oct 2026** (as of 25 Oct 2026, headless Chromium 153 against the playground served from this tree; the guest with a virtio-net card and v86's fetch backend; `test_playground.mjs`, 17 checks). With no policy, `wget http://sharness.ai/llms.txt` returned the file through the page's `fetch()`: the interceptor showed DNS, TCP :80 and `HTTP GET … allowed 200`. With `example.com` off the page's egress allowlist: `403 Forbidden` from the page, before any `fetch()`, logged as `blocked`. Under P1 (TCP 443 only): `Permission denied` on the connect from the kernel, no TCP or HTTP flow reached the page (4 → 4), and the DNS query did (4 → 6: Landlock does not see UDP). Under P5 (80 and 443): the file. In Node (`boot_node.mjs`, Node's `fetch()` through the environment's proxy) the scripted run gave the same three results.

**The example policies P0 to P4, run natively 25 Oct 2026** (as of 25 Oct 2026, uid 0, a stand-in workspace): P0 refused a 200 MiB allocation under its 64 MiB cap (`MemoryError`); P1 connected to `1.1.1.1:443`, was refused on port 80 (`EACCES`) and wrote the workspace; P2 was refused writes to the workspace and `/tmp` and the connect; P3 wrote `out/` and was refused `vault/`; P4 ran `sgit 0.24.0 --version` and `pki list`, wrote `vault/`, was refused `out/`, connected on 443 and read its own hash from `SHARNESS_AI_POLICY_HASH`. Files and the table: [Mockups and experiments](../code/experiments/index.md#the-example-policies).

**What this does not show.** The policy was applied by the session to its own children. It is a Boundary for them and a Setting for the session (the same root process that could have skipped it). It says nothing about seccomp, uids, cgroups, mutual TLS or the process tree, none of which the experiments touch yet.

## Documented, not yet exercised

- A Claude Code `PreToolUse` hook can replace a tool's input before it runs (`updatedInput`, documented 24 Oct 2026), which answers [Agents §2](../design/agents/index.md#2-where-sharness-plugs-in) row 3. Not yet exercised on a pinned version.

## Not yet measured

- seccomp filters (available in the kernel; no filter tested)
- read-only bind mounts (namespaces tested; read-only binds not separately)
- every side door on [Enforcing the process tree](../design/process-tree/index.md): the proof of concept has not been run
- AWS KMS asymmetric RSA-4096 with OAEP-SHA-256 matching sgit's envelope
- the experiments E01 to E04 on a laptop (no root; on Ubuntu 24.04 an unprivileged user namespace may be refused, so `network: "none"` falls back to Landlock's TCP rules, which do not cover UDP)

Source: [04-environment-evidence](../project/sources/sharness-brief-pack/docs/04-environment-evidence.md); §9 from the CLI's experiments, run 24 Oct 2026.
