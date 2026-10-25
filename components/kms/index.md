# sharness.kms: the only place a secret lives

> **Status: designed, with the protocol written and the handover measured by hand.** Not built. Written as of 25 Oct 2026.

## Its one job

Open a sealed message addressed to its identity, check it, derive the keys the caller needs, and re-seal them to a key the caller made for this one request. It never returns a clear key. It holds the session identity's private key, made inside it and never exported, in a `memfd_secret` page, and it is frozen by the launcher between calls.

## The API (proposed; the protocol is on [Keys and the KMS §3](../../design/keys/index.md#3-the-kms-protocol))

Answers `sharness.net` and `sharness.llm` only: the edge list has no other caller, and the app can never reach it.

| Request | Body | Response |
|---|---|---|
| `POST /v0/unwrap` | `{"v": 1, "sealed": "m1.…", "eph_pub": "<P-256 SPKI>", "op": "read", "vault_id": "…", "nonce": "…", "expires_in": 300}` | `{"v": 1, "sealed_to_eph": "<envelope>", "expires_in": 300}`: the derived keys, sealed to the caller's one-time key; the vault key itself never leaves |
| `POST /v0/seal_to` | `{"sealed": "m1.…", "recipient_k1": "…", "expires": "…", "op": "read"}` | `{"m1": "…"}`: the key re-sealed to another identity without ever being in clear outside the KMS (`sgit vault seal --to`) |
| `GET /v0/identity` | | the public bundle `k1` (record and encryption fingerprints); the only thing it ever prints |
| `GET /v0/policy` | | its own policy and hash |

## Requests, and their verdicts (designed)

| Who asks what | Verdict | By |
|---|---|---|
| `.net` asks `unwrap` for a vault with `op=read`, a fresh nonce, a sealed key addressed to this identity | the read key, sealed to the caller's one-time key; the nonce recorded | `.kms` |
| the same nonce a second time | refused: replay | `.kms` |
| `unwrap` of a message sealed to a different identity | refused: not addressed to me | `.kms` |
| `unwrap` of a message whose sender does not chain to the pinned root | refused | `.kms` |
| `.net` asks `op=write` where the policy binds writes to a fresh approval | held until the person approves, then answered | policy, then `.kms` |
| the app, or bash, or any process but `.net` and `.llm`, opens a connection | the TLS handshake fails: the role is not in the edge list | the session CA and the edge list |
| anything reads `/proc/<kms pid>/mem` | `EPERM`: a different uid, and the page is `memfd_secret`, unreadable even by root | the kernel |
| anything asks for the private key | there is no such request | the design |

## What it enforces, with what

| | |
|---|---|
| Files and network | none: Landlock with no filesystem rights after start; an empty network namespace; it answers on loopback only |
| Memory | the private key in a `memfd_secret` page: measured unreadable even by root (24 Oct 2026) |
| Lifetime | frozen between requests by the launcher: thaw, answer, freeze; 0.13 ms and 0.28 ms measured |
| The envelope | ECDH P-256 to the caller's ephemeral key, HKDF-SHA256, AES-256-GCM with the request hash as associated data; a copied response is useless, the ephemeral key existed for milliseconds |
| Remote | the same protocol against a cloud KMS or an HSM, with the caller bound by its certificate ([§6](../../design/keys/index.md#6-remote-kms-binding-the-caller)) |

## On its own

Adopt only this component and a secret handed to an agent is never in clear on disk, on a command line, or in the transcript: it arrives sealed to the KMS's identity, and what comes out is sealed to a key that lives for one request. The agent sees a fingerprint and a status line. The [sealed handover](../../design/keys/index.md#1-the-handover-end-to-end) is the worked example, and the gap it closes is the one SHarness started from ([Why](../../design/why/index.md)).

## What it does not do

It does not decide what the derived keys are used for once sealed to the caller: that is the caller's policy, which is why `op=read` returns only the read key. It does not protect against root reading the page: it does, by `memfd_secret`, but against a compromised kernel nothing here holds, and the site says so.

Sources: [Keys and the KMS](../../design/keys/index.md), [Components](../../design/components/index.md#sharnesskms). Measurements: [Evidence §3](../../evidence/index.md#3-memory) and [§6](../../evidence/index.md#6-transport).
