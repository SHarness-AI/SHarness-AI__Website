# 01 — Architecture

Four components, each with one job, each under its own Process Behaviour Policy, talking only over mutual TLS along three allowed edges.

## 1. The picture

```
                       person (broker: carries QR images, supplies policy hash)
                                         │
                      k1 public key ◄────┤────► m1 sealed vault key
                                         │
 ┌───────────────────────────────── session (ephemeral VM / pod / host) ─────────────────────────────────┐
 │                                                                                                       │
 │   agent (LLM, root)  ── runs ──►  sgit CLI command                                                    │
 │        ▲  transcript sees only: commands, k1, m1, status output — never a clear key                   │
 │        │                                                                                              │
 │  ┌─────┴──────────────┐   mTLS   ┌────────────────────┐                                               │
 │  │  sgit-cli          │─────────►│  sgit-fs           │──► clone folder + .sg_vault/ (only writer)    │
 │  │  uid sgit-run      │  edge 1  │  uid sgit-fs       │    rules: paths, sealed formats only,         │
 │  │  orchestrates      │          │  no keys, no net   │    no symlinks out, no exec bits              │
 │  │  NO keys           │          └────────────────────┘                                               │
 │  │  NO network        │                                                                               │
 │  │  NO disk writes    │   mTLS   ┌────────────────────┐  TLS client,   ┌──────────────────┐           │
 │  │  no fork           │─────────►│  sgit-net          │─ allowlisted ─►│ platform egress  │──► send.sgraph.ai
 │  └────────────────────┘  edge 2  │  uid sgit-net      │  host names    │ proxy :43305     │   (vault server)
 │                                  │  holds DERIVED keys│                └──────────────────┘           │
 │                                  │  for one command   │                                               │
 │                                  │  does vault crypto │                                               │
 │                                  └─────────┬──────────┘                                               │
 │                                            │ mTLS edge 3                                              │
 │                                  ┌─────────▼──────────┐                                               │
 │                                  │  sgit-kms          │   private key in memfd_secret page            │
 │                                  │  uid sgit-kms      │   frozen between calls (cgroup freezer)       │
 │                                  │  no net, no disk   │   only op: open sealed → re-seal to E.pub     │
 │                                  └────────────────────┘   (or: remote — Lambda/KMS/HSM/platform)      │
 │                                                                                                       │
 │  launcher/runtime: makes uids, session CA, certs, applies PBPs, verifies policy hash, starts/freezes   │
 └───────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Components

### 2.1 sgit-cli — orchestration
| | |
|---|---|
| Job | parse the user's command, call sgit-fs and sgit-net, render output |
| Holds | no key of any kind; sees file **contents** (it must, to show diffs) |
| Talks to | sgit-fs (edge 1), sgit-net (edge 2). Nothing else |
| Files | read-only on the clone folder; write: none (all writes go through sgit-fs) |
| Network | none — network namespace with only loopback, or Landlock net with only the fs/net ports |
| Lockdown | uid `sgit-run`, all capabilities dropped, `no_new_privs`, `RLIMIT_NPROC=0`, Landlock, seccomp allowlist |
| Refuses | `show-key` on a sealed clone without `--reveal`; any plain vault key on argv (all 14 commands that take one) |

### 2.2 sgit-fs — the only writer
| | |
|---|---|
| Job | apply writes to the working tree and `.sg_vault/` under rules |
| Holds | no keys |
| Talks to | nobody; only answers sgit-cli |
| Business rules | writes only under the clone root; no symlink or `..` escapes; in `.sg_vault/local/` only accepts sealed formats and **refuses anything that parses as a clear vault key, a PEM private key or a bearer token**; strips exec bits from pulled files unless policy allows; size and count limits per command |
| Implementation | step 1: a process owning the folder (uid `sgit-fs`, others have no write permission). Later: a FUSE mount enforcing the same rules for any tool (FUSE measured available) |

### 2.3 sgit-net — network and vault crypto
| | |
|---|---|
| Job | every byte to and from the vault server; the KMS client; (full split) all vault encryption/decryption and signing |
| Holds | derived read/write keys for **one command**, in a `memfd_secret` page; never the vault key |
| Talks to | sgit-kms (edge 3); the vault server via the platform egress proxy |
| Business rules | host allowlist (e.g. `send.sgraph.ai`, KMS host); endpoint allowlist (sgit API paths); **vault-id allowlist**; read-only vs read-write per policy; no redirects to other hosts; IP literals refused |
| Why it is the TLS client | the kernel only sees `127.0.0.1:<proxy port>`. sgit-net sends `CONNECT host:443`, sets SNI and Host, and verifies the certificate for that name. A pure relay would let the inner process choose SNI/Host (domain fronting) |

### 2.4 sgit-kms — one operation
| | |
|---|---|
| Job | open an `m1` addressed to its identity, check it, derive keys, re-seal them to the caller's one-time key E |
| Holds | the session identity's private key (made inside, never exported); nonce record |
| Talks to | answers sgit-net only |
| Files / network | none locally (Landlock with no fs rights after start; empty network namespace) |
| Lifetime | frozen between requests; thaw → answer → freeze (see 02 §6) |

## 3. Edges and transport

### 3.1 Edge matrix (deny by default)

```
              callee →   fs      net     kms     vault server
 caller ↓
 cli                     ALLOW   ALLOW   deny    deny
 fs                      —       deny    deny    deny
 net                     deny    —       ALLOW   ALLOW (allowlisted names only)
 kms                     deny    deny    —       deny
```

Measured with a session CA and role certificates: cli→fs, cli→net, net→kms accepted; fs→kms, cli→kms, fs→net refused.

### 3.2 Mutual TLS with a session CA

```
 launcher                                    each component
 ────────                                    ──────────────
 1. make CA key (P-256), CA cert (2h, pathlen 0)
 2. for role in cli, fs, net, kms:
      make key, issue cert
        SAN URI spiffe://<session-id>/<role>
        SAN DNS localhost
        validity = session
 3. DESTROY CA private key  ───────────────► set of identities is now closed
 4. CA cert hash → into policy manifest      5. on connect, BOTH sides:
                                                 - verify chain to session CA
                                                 - read peer role from SAN URI
                                                 - check (caller, callee) ∈ edges
                                                 - reject otherwise
```

Rules:
- **TLS 1.3 only.** P-256 keys. 24 ms to make the CA plus four certs (measured).
- **Both sides check roles.** The callee checks the caller; the caller checks the callee, so a compromised component cannot pose as sgit-net to the CLI.
- **Use SPIFFE IDs** (`spiffe://<trust-domain>/<role>`). This is the SPIFFE/SPIRE and service-mesh pattern; on Kubernetes it lets SPIRE or a mesh issue the identities instead of the launcher.
- **Each component's TLS key is not its sealing identity.** sgit-kms's TLS key and its RSA identity are separate keys.
- **Set `TCP_NODELAY` on both ends.** Without it on the server, the TLS handshake measured 46 ms (delayed-ACK stall) instead of 3.2 ms.
- **Same protocol on any transport.** Unix sockets locally, TCP across machines. Measured costs are the same (§3.3). On Unix sockets add `SO_PEERCRED` uid checks as an independent third layer.
- **Wire format:** small HTTP/1.1 (or length-prefixed JSON) API over the TLS connection; one connection per command, reused for all requests in that command; TLS session resumption between commands.

### 3.3 What it costs (measured, Python `ssl`, TLS 1.3)

| Transport | Connect + handshake | 600 B round trip | Bulk |
|---|---|---|---|
| TCP plain | 0.10 ms | 15 µs | ~300 MB/s |
| **TCP mutual TLS** | **3.2 ms** | **67 µs** | **~320 MB/s** |
| Unix plain | 0.09 ms | 56 µs | ~320 MB/s |
| Unix mutual TLS | 3.4 ms | 74 µs | ~420 MB/s |

Per sgit command: three handshakes ≈ 10 ms, against 146 ms of sgit imports and 108 ms of PBKDF2 already paid today. Microsecond and bulk figures varied by up to ~25% between runs (server thread shared the interpreter lock with the client); handshake times were stable. Details in 04 §6.

## 4. Command flows

### 4.1 `sgit clone --sealed handover.png work`

```
 agent        cli            fs             net                 kms                vault server
   │ clone --sealed │          │              │                   │                      │
   │───────────────►│ parse QR JSON, strict schema (handover.md refusal rules)          │
   │                │ open(m1)────────────────►│                   │                      │
   │                │          │              │ make E (P-256)    │                      │
   │                │          │              │ unwrap{m1,E.pub,  │                      │
   │                │          │              │   nonce,ts,op=rw}─►│ thaw                 │
   │                │          │              │                   │ check: to=self, sig, │
   │                │          │              │                   │ expiry, sender trust,│
   │                │          │              │                   │ nonce unused         │
   │                │          │              │                   │ open → vault key     │
   │                │          │              │                   │ derive read/write,id │
   │                │          │              │                   │ scrub vault key      │
   │                │          │              │◄─sealed_to_E{keys}│ freeze               │
   │                │          │              │ open with E.priv; drop E                 │
   │                │          │              │ fetch packs ─────────────────────────────►│
   │                │          │              │◄──────────────────────────── encrypted ───│
   │                │          │              │ decrypt objects   │                      │
   │                │◄─────────── plain file contents ────────────│                      │
   │                │ write(tree)──►│ apply rules, write files    │                      │
   │                │ write(.sg_vault/local/vault_key.sealed = m1)►│ accepts: sealed format│
   │                │          │              │ scrub derived keys; exit                 │
   │◄── "cloned, sealed to sha256:… from sha256:… (chains to root), expires 30 Oct" ─────│
```

The transcript sees: the command, the m1 (it is ciphertext), fingerprints, progress. Never a key.

### 4.2 Read commands (`status`, `pull`, `ls`, `cat`)
Same as 4.1 from "make E", reading `vault_key.sealed` through sgit-fs and asking the KMS with `op=read`. The KMS returns **only the read key** (and ids). sgit-net cannot push in this command even if told to.

### 4.3 `push`
`op=write`: the KMS returns read + write keys. Policy may require a fresh approval (second factor) for `op=write`; the KMS is where that check lives.

### 4.4 `vault show-key`
Refused on a sealed clone. With `--reveal` it is a policy decision (default: denied in agent sessions). `sgit vault seal --to <record fp> --qr out.png` replaces every legitimate use: the KMS re-seals to another identity without the key appearing anywhere.

## 5. Deployment topologies

Same components, same protocol, same policies. Only the launcher changes.

```
 A. one VM, separate uids (what was measured)
 ┌──────────────────────── VM ────────────────────────┐
 │ sgit-run  sgit-fs  sgit-net  sgit-kms   (4 uids)   │
 │   └─ Unix sockets + mTLS + SO_PEERCRED + iptables  │
 └────────────────────────────────────────────────────┘

 B. Docker / compose: one container per component
 ┌─cli─┐  ┌─fs──┐  ┌─net─┐  ┌─kms─┐   network: internal only, except net
 │     │──│     │  │     │──│     │   volumes: clone folder mounted rw in fs, ro in cli
 └─────┘  └─────┘  └──┬──┘  └─────┘   kms: no network except the internal one, read-only rootfs
                      └──► egress

 C. Kubernetes: one pod, four containers (or kms as its own Deployment)
   identities from SPIRE / mesh (spiffe://<td>/<role>); NetworkPolicy mirrors the edge matrix;
   seccomp + readOnlyRootFilesystem + runAsNonRoot per container from the PBP

 D. remote KMS
   net ──mTLS/HTTPS──► Lambda / Cloud Function ──► cloud KMS asymmetric key (HSM)
   caller bound to the session's auth key (02 §5); nonce store e.g. DynamoDB conditional put

 E. platform-provided (end state)
   net ──► local platform endpoint (vsock / proxy) ──► platform KMS; session identity
   = the platform's own knowledge of the session; no auth key in the container
```

## 6. The launcher

Responsibilities, in order:

1. Read the policy manifest; compute its hash; **refuse to continue unless it matches the hash the person supplied** or the manifest carries a valid signature from the root key.
2. Create uids `sgit-run`, `sgit-fs`, `sgit-net`, `sgit-kms` (measured: create user + firewall rule + locked launch + teardown ≈ 49 ms each).
3. Create the session CA and four certificates; destroy the CA key; record the CA cert hash.
4. Start sgit-kms under its PBP; it makes the session identity and prints **only** the k1 public bundle; freeze it.
5. For each sgit command: start sgit-fs, sgit-net, sgit-cli under their PBPs (namespaces ≈ 4 ms), let them run, tear down.
6. At session end: thaw and kill sgit-kms, delete users, firewall rules and sockets.

**Who runs the launcher matters.** In the measured environment the agent is root, so every lock the agent sets up is a *Setting* from the agent's own point of view (it could undo it); it is a *Boundary* only for the components below it. Making the locks binding on the agent requires the platform to run the launcher. See 03 §2.

## 7. Refactor path in sgit

sgit 0.24.0 reads the vault key directly in many places (the article counts 27 read sites in 17 files; a broad grep for `_read_vault_key|load_vault_key|vault_key_path` finds 65 references in 23 files, including imports). After derivation almost nothing needs the clear key except `show-key`, `rekey` and `move`.

| Step | Change | Effect |
|---|---|---|
| 0 | Fix independently: private keys from `pki keygen` use PBKDF2 at **2,048** iterations (measured, `0x0800`) → Argon2id; `Secrets__Store` fixed salt → per-user random salt | removes two weaknesses whatever else happens |
| 1 | **The door**: one `Key_Source` interface — "vault id + derived keys for this folder". Reads `vault_key` today | no behaviour change; all call sites go through it; tests prove it |
| 2 | `Key_Source` backed by the KMS protocol. `clone --sealed`, `vault_key.sealed`, `vault seal-local`, `vault seal --to`. sgit-net filters traffic; cli receives derived keys sealed to **its own** E | key never on disk/argv/stdout; derived keys in cli memory for one command |
| 3 | **Full split**: vault crypto and server I/O move into sgit-net; cli asks for operations, not keys | cli holds no keys; cli has no network |
| 4 | sgit-fs as the only writer; then optional FUSE | business rules on disk enforced outside the cli |
| 5 | P-256 ECDH envelope for hardware keys (TPM / PIV / Secure Enclave); commit signing with the identity | hardware-backed KMS; commit author is a register record |

Lazy imports per subcommand belong with step 1: `sgit --version` loads 529 modules and opens 1,104 files (measured). Smaller footprint = smaller policy.
