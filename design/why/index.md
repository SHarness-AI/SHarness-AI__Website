# Why: the last metre

> **Status: design.** Nothing described here is built. This page describes the problem SHarness started from, in sgit 0.24.0 as observed as of 24 Oct 2026.

The [pki.sgit.ai handover](https://pki.sgit.ai/handover.md) protects a vault key **while it travels**: the sending agent seals it to the receiving agent's public key, and a person carries a QR image they cannot read. It stops protecting the key **the moment it arrives**.

```
   travel                          arrival (sgit 0.24.0 today)
 ┌────────────────────┐   ┌──────────────────────────────────────────────────────┐
 │ QR: sealed to the  │──►│ pki-agent open --save  → vault-key-<id>.txt   CLEAR │
 │ receiving agent    │   │ sgit clone <vault key> → argv, shell history, CLEAR │
 │ (person can't read)│   │                          the agent's transcript     │
 └────────────────────┘   │ .sg_vault/local/vault_key            (0600)  CLEAR │
                          │ .sg_vault/local/key-rnd-imm-*.pem    (PKCS#8) CLEAR │
                          │ .sg_vault/local/token                         CLEAR │
                          └──────────────────────────────────────────────────────┘
```

## The transcript is the biggest leak

For an AI agent the worst leak is not the disk. It is the **transcript**: every command line the agent writes and everything a command prints lands in the model's context and in conversation logs. A key passed as `sgit clone <key>`, or printed by `show-key`, is in the transcript for as long as the transcript exists.

## The person is the transport

In the handover the person carries things they cannot open: the receiving session's public key bundle one way, the sealed vault key the other.

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
                                       ┌────────────────────────
                                       │ QR (pki.sgit.ai/qr/sealed/v1, m1 code)
 sgit clone --sealed out.png work ◄────┘
   net → kms: unwrap
   kms: to = me? signature? expiry? sender chains to root? nonce?
   kms → net: derived keys sealed to a one-time key
   fs: writes vault_key.sealed (the m1), never the clear key
```

Under the design, the receiving agent never sees the key. The sealed `m1` itself becomes `vault_key.sealed`. The full flow and protocol are on [Keys and the KMS](../keys/index.md).

## The goals that follow

1. **The clear vault key is never written to disk, never on a command line, never printed.** It never enters the transcript.
2. **One place holds the private key**: a small KMS process, local and frozen between calls, or remote. Same protocol for both.
3. **Each component does one job and can do nothing else**, under its own Process Behaviour Policy, enforced by the kernel and by mutual TLS.
4. **Ephemeral.** Identities, certificates, users and policies are made for the session and die with it.
5. **Policies come from outside the agent.** The person supplies (or signs) the hash of the policy; the agent cannot widen it.
6. **No server changes.** What goes to the vault server is exactly what goes today.

## From one fix to a harness

Nothing in that fix is specific to sgit. It describes a launcher and a small set of single-purpose components that any process can run inside: sgit, a shell, an agent loop. That generalisation is SHarness, and sgit's job becomes being compatible with running inside it. See [Architecture](../architecture/index.md).

## Threat model

**Trusted:** the kernel, the hardware, and the platform that runs the VM. **Root and kernel compromise are out of scope**: anything with root on the machine can read any process's ordinary memory. The design shrinks where a key lives; it does not hide it from root.

| Threat | Example | Primary defence (designed) |
|---|---|---|
| Transcript leakage | the key printed by `show-key`, or passed as `sgit clone <key>` | the key never reaches stdout or argv; only sealed forms (`m1`) and public keys appear |
| At-rest leakage | a backup, a workspace zip, a container image with the folder in it | only sealed files on disk; clear keys live in one process's memory |
| Prompt injection driving the **agent** | a web page or vault file tells the agent to run `show-key` or push to another vault | policy hash fixed by the person; `sharness.net` refuses vault ids and hosts not in policy; `show-key` refused on sealed clones |
| Prompt injection driving **sgit** (confused deputy) | crafted QR JSON or vault content exploits sgit's parsing | strict input schemas; the exploited process holds no key, has no network, cannot start processes, cannot write outside its folder |
| A component exceeding its job | `sharness.fs` tries to reach the KMS | per-component uid, Landlock, seccomp, firewall, mutual TLS edge rules |
| A sealed key stolen from the transcript and replayed | the `m1` code copied out of a log | the KMS answers only its bound caller; nonces are single use; responses are sealed to one-time keys |

**Not claimed:** Python cannot guarantee erasure of secrets; expiry on a sealed key is policy enforced by the KMS, not cryptography; a session identity dies with its session, so a restarted session needs a new handover (by design).

Sources: [00-README](../../project/sources/sharness-brief-pack/docs/00-README.md) §1–3, [02-sealed-key-flow-and-kms](../../project/sources/sharness-brief-pack/docs/02-sealed-key-flow-and-kms.md) §1, and the origin article, [A vault key that never lands](https://cli.sgit.ai/articles/a-vault-key-that-never-lands.md).
