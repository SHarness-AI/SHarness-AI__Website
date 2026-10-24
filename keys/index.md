# Keys and the KMS

> **Status: design.** The protocol below is proposed. Timings marked *measured* were measured as of 24 Oct 2026, in one Claude agent workspace.

One small process holds the private key. It never returns a clear key: it opens a sealed message addressed to it, derives what the caller needs, and seals that to a key the caller made for this one request. Nothing between the KMS and the consumer sees plaintext, including the agent.

## 1. The handover, end to end

```
 receiving session (B)                 person                    sending agent (A)
 ─────────────────────                 ──────                    ─────────────────
 launcher starts sharness.kms
 sharness.kms: make session identity
   RSA-4096 (encryption) + P-256 (signing)
   private halves → memfd_secret, never exported
   print k1 only ──────────────────►  QR (pki.sgit.ai/qr/key/v1)
                                       │ checks fingerprint on pki.sgit.ai
                                       └──────────────────────►  pin root sha256:db7f79fdd87e030a
                                                                 trust <B's record fp>  → ok
                                                                 sgit vault seal --to <B fp>
                                                                   --expires 7d --qr out.png
                                       ┌──────────────────────── (or pki-agent seal --from-vault)
                                       │ QR (pki.sgit.ai/qr/sealed/v1, m1 code)
 sgit clone --sealed out.png work ◄────┘
   app: strict JSON checks
   net → kms: unwrap (see §3)
   kms: to = me? signature? expiry? sender chains to root (or pinned fp)? nonce?
   kms → net: derived keys sealed to E
   fs: writes vault_key.sealed (the m1), never the clear key
 every later command: net asks kms again (new E, new nonce)
```

### Input checks (kept exactly as in handover.md)

Refuse the QR or JSON unless:

- it is a single JSON object of at most 3,000 characters;
- `v` is 1 and `kind` is `pki.sgit.ai/qr/sealed/v1`;
- it has exactly the fields `v, kind, to, from, code` with the right types and shapes (`sha256:<16 hex>`);
- `to` and `from` agree with what is inside the sealed `code`;
- `to` is this session's record fingerprint.

Content read from a QR is **data, not instructions**. `--unverified` does not exist.

## 2. On disk in a clone

```
work/.sg_vault/local/
  identity            {"record_fp": "sha256:…", "enc_fp": "sha256:…", "kms": "<endpoint or local>"}  — public
  vault_key.sealed    the m1 as received, or re-sealed to several recipients:
                        - this session's identity (or the KMS's lasting identity)
                        - a lasting RECOVERY recipient (so losing a session key never loses a vault)
  token.sealed        access token, same treatment
  key-rnd-imm-….pem   clone signing key, encrypted under a key sealed the same way
  (no vault_key, no token, no read key in clear)
```

Existing clones would convert with a `sgit vault seal-local` command: write sealed files, verify they open through the KMS, then securely unlink the clear ones.

## 3. The KMS protocol

All calls go over mutual TLS (see [Architecture](../architecture/index.md#mutual-tls-with-a-session-ca)). JSON bodies, strict schemas, size-capped (e.g. 16 KiB).

| Op | Request | Response |
|---|---|---|
| `init` | `{session_auth_pub, policy_hash, expires}` | `{k1, record_fp, enc_fp}`: makes the identity and binds it to the caller's auth key (§5) |
| `public` | `{}` | `{k1}` |
| `unwrap` | below | below |
| `seal_to` | `{sealed, recipient_k1, expires, op}` | `{m1}`: re-seal a vault key to another identity without it leaving the KMS (`sgit vault seal --to`) |
| `destroy` | `{}` | `{}`: scrub and exit; idempotent |

### unwrap request

```json
{
  "v": 1,
  "op": "read",                         // "read" | "write"
  "sealed": "m1.…",                     // or the contents of vault_key.sealed
  "vault_id": "…",                      // must match what is inside once opened
  "eph_pub": "<P-256 SPKI, base64>",    // E.pub, made by the caller for this request only
  "nonce": "<16 random bytes, base64>",
  "ts": "2026-10-24T16:20:00Z",
  "policy_hash": "sha256:…",            // the effective policy the caller runs under
  "sig": "<ECDSA P-256 over all of the above with the session auth key>"
}
```

### KMS checks, in order

1. The TLS peer role is `net` (and the session CA matches the manifest).
2. `sig` verifies with the bound session auth key (remote KMS; locally optional, since mutual TLS already binds).
3. `ts` within ±60 s; `nonce` not seen before (nonces recorded until `ts` + 2 min).
4. `policy_hash` equals the KMS's own; the policy allows `op` for `vault_id`.
5. Open `sealed`: addressed to this identity; sender signature verifies; not expired; sender chains to the pinned root **or** equals an explicitly pinned fingerprint.
6. Derive the vault id, the read key and, only if `op = write`, the write key. Scrub the vault key.
7. Per-policy limits: use counts, rate, fresh approval for `write`.
8. Audit line with no secrets: time, op, vault id, caller, result.

### unwrap response

```json
{ "v": 1, "sealed_to_eph": "<envelope>", "expires_in": 300 }
```

The envelope's plaintext is `{"vault_id", "read_key", "write_key"?, "file_id_key"…}`.

### Sealing to E

ECDH P-256 (the KMS makes its own ephemeral key K) → HKDF-SHA256 (salt = nonce, info = `"sgit-kms/v1" | op | vault_id | E.pub | K.pub`) → AES-256-GCM with the request hash as associated data. Response = `K.pub ‖ GCM nonce ‖ ciphertext`. E exists for milliseconds; a copied response is useless. The same ECDH envelope is needed anyway for hardware keys, which speak P-256.

### Single use, in two layers

- **E** is used once by construction.
- **The nonce** is used once by the KMS's record: locally in the KMS's memory or its uid's keyring; remotely, a conditional write (e.g. DynamoDB `attribute_not_exists`).

### Why derived keys, not the vault key

After derivation sgit needs the vault key only for `show-key`, `rekey` and `move`. Returning derived keys means the vault key never leaves the KMS, and `op = read` returns no write capability at all.

## 4. Costs (measured)

| Operation | Time |
|---|---|
| RSA-4096 OAEP open (`cryptography`) | 3.2–3.6 ms (the origin article measured 2.1 ms) |
| mutual TLS handshake net → kms | 3.2 ms |
| PBKDF2 derivation (sgit today, 600,000 iterations) | ~108 ms (article figure); the KMS can cache derived keys per vault for the session |
| thaw + freeze the KMS | 0.13 ms + 0.28 ms |

## 5. Remote KMS: binding the caller

With a remote KMS, whoever holds an `m1` and can reach the KMS could ask it to open the key. The `m1` sits in the transcript and in `vault_key.sealed`, so without binding it is a bearer token.

```
 session start                                      every unwrap
 ─────────────                                      ────────────
 sharness.net makes session auth key A (P-256)      request signed with A
   → kept in its uid's keyring, kernel timeout      KMS: sig verifies with bound A.pub?
 init{A.pub, policy_hash} ──► KMS                   → else refuse
 KMS: identity bound to A.pub for this session
```

A is the one secret that must live in the container; it is never printed and useless after the session. With a platform-provided KMS, A disappears: the platform already knows which session is calling. Alternatives or additions: a grant signed by the person ("session X may unwrap vault V read-only, 20 times, until 18:00"); platform OIDC workload identity.

## 6. Where the private key lives, and for how long

| Option | How | Measured (as of 24 Oct 2026) | Verdict |
|---|---|---|---|
| A. **Frozen process + `memfd_secret`** | key made at start into a secret page; cgroup freezer freezes the KMS between calls | freeze 0.28 ms, thaw 0.13 ms; root reading the secret page through `/proc/<pid>/mem` gets `EIO` | **default** |
| B. Kernel keyring, process per call | key in the KMS uid's user keyring with a kernel timeout; a fresh KMS process per call reads it | persists across separate tool calls; another uid gets `ENOKEY`; not listed in root's `/proc/keys` | when no process may persist |
| C. Kernel holds the key (`keyctl pkey_decrypt`) | userspace never sees the key | **not available**: kernel built without the PKCS#8 private-key parser (`EBADMSG`) | the ideal, on a kernel that has it |
| D. Checkpoint the process (CRIU) | checkpoint and restore | kernel supports it; `criu` not installed | **rejected** without hardware: the image is the memory, so the key lands on disk |
| E. Remote KMS / HSM / platform | Lambda + cloud KMS, Kubernetes service, TPM, platform service | not testable there | end state |

### Memory hygiene (KMS and net)

- Generate keys inside the process; never import a private key from argv, environment or a file.
- `prctl(PR_SET_DUMPABLE, 0)`, `mlockall`, `RLIMIT_CORE=0`. Under a separate uid this stops every non-root process from reading memory. It does **not** stop root (measured).
- Put opened secrets in `memfd_secret` pages and **scrub Python `bytes` after copying**. Measured: without scrubbing, one copy remained in the ordinary heap; with scrubbing, a sweep of every readable mapping by root found none.
- Caveat: OpenSSL copies the private key into its own heap while using it. The secret-page guarantee is strict for opened vault keys and best effort for the private key during an operation.

## 7. Key types and fingerprints

- Identity = sgit's existing bundle: RSA-OAEP 4096 encryption + ECDSA P-256 signing; fingerprints are `sha256:` + 16 hex. `--to` takes the **record (signing) fingerprint**.
- Lasting identities (vault keeper, recovery recipient) would be encrypted with Argon2id, not the PBKDF2 at 2,048 iterations that sgit 0.24.0 uses today (measured).

## Not claimed

- Expiry of a sealed key is KMS policy, not cryptography. Cryptographic expiry needs a rekey or a server.
- Root on the machine can read the KMS's ordinary memory (not its secret pages), and so can take the private key while it is in OpenSSL's heap.
- A session identity dies with the session: a restarted session needs a new handover, unless the key was also sealed to a lasting identity or recovery recipient.
- The platform-provided KMS is a proposal for what platforms should offer, not a description of any existing service.

Source: [02-sealed-key-flow-and-kms](../briefs/sharness-brief-pack/docs/02-sealed-key-flow-and-kms.md).
