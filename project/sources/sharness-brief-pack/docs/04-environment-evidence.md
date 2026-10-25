# 04 — Environment evidence

Everything below was observed on **24 October 2026** in a Claude agent workspace (claude.ai, cloud session). Re-run the probes before relying on them elsewhere: other platforms, and later versions of this one, may differ.

## 1. The environment

| Fact | Observed |
|---|---|
| Isolation | Firecracker microVM; PID 1 is `/process_api --firecracker-init …` (not systemd) |
| OS / kernel | Ubuntu 24.04.5, Linux 6.18.44, x86_64 |
| Agent's identity | **uid 0 (root)**, full capability set (`CapEff 000001fffeffffff`) |
| Hardening present | no seccomp, `NoNewPrivs 0`, no Yama (`/proc/sys/kernel/yama` absent) |
| Core dumps | `ulimit -c 0`; `core_pattern = core` |
| Python / crypto | Python 3.13.17; `cryptography` 50.0.1 |
| sgit | `pip install sgit-ai` → **0.24.0** (the version the article analysed) |
| Hardware keys | no `/dev/tpm*` |
| Egress | every outbound HTTPS goes through a platform proxy at `127.0.0.1:43305`; `send.sgraph.ai`, `pki.sgit.ai`, `cli.sgit.ai` reachable (HTTP 200) |
| Scratch space | the agent's scratchpad is root-only (other uids get `EACCES`) |
| Process lifetime | per the platform: a process detached with `nohup`/`&` is stopped within minutes of the agent's reply; a tool-managed background process can run up to 2 h. **Not measured.** |
| Firewall tools | `iptables`, `nft` present; OUTPUT policy ACCEPT, empty |
| cgroups | v1 hierarchy: blkio, cpu, cpuacct, cpuset, devices, freezer, memory, pids, systemd, unified |
| FUSE | `/dev/fuse` (root-only), `fusermount3` present |

### Kernel configuration (`/proc/config.gz`)

| Option | Value | Relevance |
|---|---|---|
| `CONFIG_SECURITY_LANDLOCK` | y (ABI 7) | file + TCP port sandboxing |
| `CONFIG_SECCOMP` | y | syscall allowlists |
| `CONFIG_SECRETMEM` | y | `memfd_secret` |
| `CONFIG_CGROUP_FREEZER` | y | freeze the KMS between calls |
| `CONFIG_CHECKPOINT_RESTORE` | y | CRIU possible (binary not installed) |
| `CONFIG_FUSE_FS` | y | sgit-fs as a mount |
| `CONFIG_ASYMMETRIC_KEY_TYPE` | y | kernel asymmetric keys … |
| `CONFIG_PKCS8_PRIVATE_KEY_PARSER` | **not set** | … but no private keys → kernel-held decryption unavailable |
| `CONFIG_TRUSTED_KEYS` | not set | (needs TPM anyway) |
| `CONFIG_ENCRYPTED_KEYS` | y | symmetric blobs only |

## 2. Article claims checked against sgit 0.24.0

| Claim | Result | Method |
|---|---|---|
| `pki keygen` makes RSA-OAEP 4096 + ECDSA P-256, `sha256:`+16 hex | ✔ | ran it with a throwaway HOME |
| Private keys encrypted with PBKDF2 at 2,048 iterations | ✔ `INTEGER :0800` on both `private_key.pem` and `signing_private.pem` | `openssl asn1parse` |
| `Secrets__Store` fixed salt | ✔ `salt = f'{SECRETS_SALT_PREFIX}:master'` | source |
| `BestAvailableEncryption` used for keys | ✔ `crypto/PKI__Crypto.py:37` | source |
| Key read in many places | 65 references in 23 files for `_read_vault_key\|load_vault_key\|vault_key_path` (broad grep incl. imports; article counts 27 read sites in 17 files) | grep |
| Public key files mode | `public_key.pem` 0644; private PEMs 0600 | `ls -l` |

## 3. Memory

| Probe | Result |
|---|---|
| `prctl(PR_SET_DUMPABLE, 0)` then root reads `/proc/<pid>/mem` | **secret found** — root's `CAP_SYS_PTRACE` overrides |
| `mlock` / `mlockall` | succeed |
| `memfd_secret` (syscall 447) | available |
| root reads a `memfd_secret` page through `/proc/<pid>/mem` | **`EIO`** |
| RSA-4096 OAEP open → copy into secret page → **no** scrub; root sweeps all readable mappings | one copy found in anonymous heap |
| same, **with** scrubbing the returned `bytes` (and the test's own original) | **no copy found** |
| RSA-4096 OAEP open time | 3.2–3.6 ms |
| kernel keyring `add_key` (process keyring) | works |
| user keyring entry persists across separate agent tool calls | ✔ |
| key in uid `sgit-dec` user keyring, searched by uid `sgit-run` | `ENOKEY` |
| that key in root's `/proc/keys` | not listed |
| `add_key("asymmetric", <PKCS#8 RSA-4096 DER>)` | **`EBADMSG`** (parser not built) |
| cgroup freezer: freeze / thaw a process (avg of 20) | **0.28 ms / 0.13 ms**; frozen state `D` |

## 4. Process isolation

| Probe | Result |
|---|---|
| create system users (`useradd -r -M -s nologin`) | ✔ |
| `setpriv --reuid --regid --clear-groups --no-new-privs --inh-caps=-all --bounding-set=-all` | CapEff 0, CapBnd 0, NoNewPrivs 1 |
| other uid reads a root file | denied |
| `unshare --net` then connect out | `ENETUNREACH` (101) |
| `unshare --user --map-root-user --pid --fork --mount-proc` | ✔ |
| Landlock ABI | 7 |
| `RLIMIT_NPROC=0` then `fork` | `EAGAIN` (blocked) |
| Landlock fs (ro `/usr /etc /lib /lib64 /proc`): read `/etc/hostname` | allowed |
| Landlock fs: read a file elsewhere | `EACCES` |
| Landlock fs: write `/tmp/x` | `EACCES` |
| Landlock net (connect only to 43305): proxy port | allowed |
| Landlock net: `127.0.0.1:22`, `1.1.1.1:443` | `EACCES` |
| `iptables -A OUTPUT -m owner --uid-owner <user> -j REJECT` | accepted |
| `SO_PEERCRED` on Unix socket | returns pid, uid, gid |
| abstract-namespace Unix socket | ✔ |
| ephemeral user + firewall rule + locked launch + teardown (avg of 10) | **49 ms** |
| new net + pid + mount namespaces (avg of 10) | **3.7 ms** |
| seccomp filter | available, **not tested** |

## 5. Footprint (strace -f, file/network/process/ipc)

| Command | Paths opened OK | Folders | Distinct syscalls | execve | socket/connect |
|---|---|---|---|---|---|
| `python3 -I -c print(1)` | 39 | 21 | 31 | 1 | 0 |
| `sgit --version` | 1,104 | 212 | 38 | 1 | 0 |
| `sgit pki list` | 1,109 | 215 | 39 | 1 | 0 |
| `import sgit_ai.cli.CLI__Main` | 529 modules, 146 ms | | | | |
| bare `python3 -I -c pass` start | 15 ms | | | | |

## 6. Transport (Python `ssl`, TLS 1.3, P-256; server is a thread in the benchmark process)

| | Connect + handshake | 600 B round trip | Bulk (64 MiB echo) |
|---|---|---|---|
| TCP plain | 0.10 ms | 15 µs | ~300 MB/s |
| TCP mutual TLS | **3.2 ms** | 67 µs | ~320 MB/s |
| Unix plain | 0.09 ms | 56 µs | ~320 MB/s |
| Unix mutual TLS | 3.4 ms | 74 µs | ~420 MB/s |
| pipe to a separate process | — | 34 µs | — |
| TCP mutual TLS **without** server `TCP_NODELAY` | 46 ms | | |

Session CA + four role certificates (P-256, 2 h): **24 ms**.

Edge enforcement with roles in `subjectAltName` URIs, policy `fs←{cli}, net←{cli}, kms←{net}`:

```
cli → fs   OK        fs  → kms  DENY
cli → net  OK        cli → kms  DENY
net → kms  OK        fs  → net  DENY
```

Figures are from the final of three runs. Across runs, round trips and bulk varied by up to ~25% (TCP mutual TLS bulk: 250, 275, 318 MB/s; Unix mutual TLS bulk: 349, 378, 418 MB/s); handshake times were stable. Microsecond figures are noisy because the server thread shares Python's interpreter lock with the client: treat them as upper bounds.

## 7. The agent loop in this environment (read-only observation)

| Item | Observed |
|---|---|
| PID 1 | `/process_api --firecracker-init --addr 0.0.0.0:2024 … --block-local-connections` |
| PID 89 | `environment-manager task-run --stdin --session cse_… --session-mode resume`, root; own HTTPS connections to `160.79.104.10:443` |
| PID 96 | `/opt/claude-code/bin/claude`, Claude Code **2.1.42**, root; ~18 established HTTPS connections to `160.79.104.10:443`; listens on `127.0.0.1:<port>` |
| the agent's Bash | direct child of PID 96 (`ppid = 96`) |
| other | `sbx-telemetry-collector` (uid 64321), `rclone-filestore multimount` |
| model endpoint | `ANTHROPIC_BASE_URL=https://api.anthropic.com`; `/etc/hosts` pins it to `160.79.104.10`; it is in `no_proxy`, so model calls bypass the egress proxy |
| credentials | carried in `ANTHROPIC_CUSTOM_HEADERS` — value **deliberately not read** |
| harness flags (names/booleans only) | `CLAUDE_CODE_REMOTE=true`, `CLAUDE_CODE_ENTRYPOINT=remote_cowork`, `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=1`, `CCR_AGENT_PROXY_ENABLED=1`, `CCR_UPSTREAM_PROXY_ENABLED=1`, `CLAUDE_CODE_PROXY_RESOLVES_HOSTS=true` |
| `/opt/claude-code` | read-only mount |
| `/root/.claude/settings.json` | writable by root (3 bytes); no `/etc/claude-code/` managed settings |
| `/etc/hosts` | writable by root; mtime changed mid-session (16:47) |
| kernel cmdline | `nomodule` |

Method: `ps --forest`, `/proc/net/tcp` mapped to `/proc/<pid>/fd` socket inodes, environment variable **names** from `/proc/96/environ`, `findmnt`. TLS traffic was not inspected and no configuration was changed.

## 8. Left in the environment
Users `sgit-dec`, `sgit-run`; `/opt/sgit-probe/` (probe scripts); a user-keyring entry `sgit:persist-probe` (root). All die with the VM.
