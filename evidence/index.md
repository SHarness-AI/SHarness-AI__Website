# Evidence

> **Every figure on this page was observed as of 24 Oct 2026, in one Claude agent workspace (claude.ai, cloud session).** One environment, one day. Re-run the probes before relying on them elsewhere: other platforms, and later versions of this one, may differ.

Three labels are used across the site, and this page is where they are earned:

| Label | Means |
|---|---|
| **measured** | probed or timed in the environment below, with the method stated |
| **designed / proposed** | a description of how SHarness would work; nothing is built |
| **not yet measured** | named in the design, not tested: seccomp filters, read-only bind mounts, every side door on [Enforcing the process tree](../process-tree/index.md), and AWS KMS compatibility |

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

## Not yet measured

- seccomp filters (available in the kernel; no filter tested)
- read-only bind mounts (namespaces tested; read-only binds not separately)
- every side door on [Enforcing the process tree](../process-tree/index.md): the proof of concept has not been run
- AWS KMS asymmetric RSA-4096 with OAEP-SHA-256 matching sgit's envelope
- whether a Claude Code PreToolUse hook can rewrite a Bash call on the version used

Source: [04-environment-evidence](../briefs/sharness-brief-pack/docs/04-environment-evidence.md).
