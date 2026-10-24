# Architecture

> **Status: design.** Component behaviour, edges and topologies below are proposed. Figures marked *measured* were measured as of 24 Oct 2026 in one Claude agent workspace; see [Evidence](../evidence/index.md).

A launcher plus a small set of single-purpose components. Any process (sgit, a shell command, an agent loop) runs inside, each component under its own [Process Behaviour Policy](../policies/index.md), talking to the others only over allowed, mutually authenticated edges. Theme: **one role, one noun, one uid, one policy, one certificate.**

## The picture

```
                      person: supplies manifest hash sha256:M, carries sealed QR codes
                                                  │
 ┌──────────────────────────── sharness.launcher (outside every domain) ──────────────────────────────┐
 │                                                                                                      │
 │   harnessed app / orchestrator  (no keys, no tools of its own, Landlock exec allowlist)              │
 │        │               │                 │                 │                                         │
 │        ▼               ▼                 ▼                 ▼                                         │
 │   sharness.fs     sharness.net      sharness.bash     sharness.llm ──────► model API                 │
 │   (writes)        (network) ──┐     (sandboxes)            │                                         │
 │                               │                            │                                         │
 │                               └──────► sharness.kms ◄──────┘  (vault keys, API keys, sealed secrets) │
 │                                                                                                      │
 │   every edge: mutual TLS, roles in certificates, schemas on the payload, both sides check            │
 │   every component: own uid, own policy, kernel-enforced                                              │
 └──────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

The app-specific orchestrator (sgit's CLI, or an agent loop such as Claude Code) sits on top and routes. It holds nothing and runs nothing itself. What each component does is on [Components](../components/index.md).

## Edges (deny by default)

```
 caller ↓  callee →   fs     net    bash   llm    kms
 app/orchestrator     ✔      ✔      ✔      ✔      ✗
 net                  ✗      —      ✗      ✗      ✔
 llm                  ✗      ✗      ✗      —      ✔
 bash (sandbox)       ✗      ✔*     —      ✗      ✗      * only if the profile allows network
 fs, kms              ✗      ✗      ✗      ✗      —
```

The orchestrator never talks to the KMS. Only `sharness.net` and `sharness.llm` do, and the KMS never returns a clear key to either: it returns derived keys sealed to a one-time key (see [Keys and the KMS](../keys/index.md)).

## The original four, for sgit

The design began with four components for sgit. The early documents use sgit-specific names; the mapping is: sgit-kms → `sharness.kms`, sgit-net → `sharness.net`, sgit-fs → `sharness.fs`, sgit-cli → the harnessed app.

```
 ┌───────────────────────────────── session (ephemeral VM / pod / host) ──────────────────────────────┐
 │   agent (LLM)  ── runs ──►  sgit command (the harnessed app)                                        │
 │        ▲  transcript sees only: commands, k1, m1, status output — never a clear key                 │
 │  ┌─────┴──────────────┐   mTLS   ┌────────────────────┐                                             │
 │  │  sgit (app)        │─────────►│  sharness.fs       │──► clone folder + .sg_vault/ (only writer)  │
 │  │  orchestrates      │  edge 1  │  no keys, no net   │    paths, sealed formats only, no symlinks  │
 │  │  NO keys           │          └────────────────────┘    out, no exec bits                        │
 │  │  NO network        │   mTLS   ┌────────────────────┐  TLS client,   ┌──────────────────┐         │
 │  │  NO disk writes    │─────────►│  sharness.net      │─ allowlisted ─►│ platform egress  │──► vault │
 │  │  no fork           │  edge 2  │  DERIVED keys for  │  host names    │ proxy            │   server │
 │  └────────────────────┘          │  one command       │                └──────────────────┘         │
 │                                  └─────────┬──────────┘                                             │
 │                                            │ mTLS edge 3                                            │
 │                                  ┌─────────▼──────────┐   private key in a memfd_secret page        │
 │                                  │  sharness.kms      │   frozen between calls (cgroup freezer)     │
 │                                  │  no net, no disk   │   only op: open sealed → re-seal to E.pub   │
 │                                  └────────────────────┘   (or remote: Lambda / KMS / HSM / platform)│
 └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Measured** with a session CA and role certificates: app→fs, app→net and net→kms accepted; fs→kms, app→kms and fs→net refused, exactly per the matrix.

## Mutual TLS with a session CA

```
 launcher                                    each component
 ────────                                    ──────────────
 1. make CA key (P-256), CA cert (2h, pathlen 0)
 2. for each role:
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

Rules (proposed):

- **TLS 1.3 only**, P-256 keys. Making the CA plus four role certificates took 24 ms (measured).
- **Both sides check roles.** The callee checks the caller and the caller checks the callee, so a compromised component cannot pose as `sharness.net` to the app.
- **SPIFFE IDs** (`spiffe://<trust-domain>/<role>`): the SPIFFE/SPIRE and service-mesh pattern, so on Kubernetes SPIRE or a mesh can issue the identities instead of the launcher.
- **A component's TLS key is not its sealing identity.** `sharness.kms`'s TLS key and its RSA identity are separate keys.
- **Set `TCP_NODELAY` on both ends.** Without it on the server the handshake measured 46 ms (a delayed-ACK stall) instead of 3.2 ms.
- **Same protocol on any transport**: Unix sockets locally, TCP across machines. On Unix sockets, add `SO_PEERCRED` uid checks as an independent third layer.
- **Wire format:** a small HTTP/1.1 (or length-prefixed JSON) API over the TLS connection; one connection per command; TLS session resumption between commands.

## What it costs (measured)

Python `ssl`, TLS 1.3, P-256, server as a thread in the benchmark process, as of 24 Oct 2026.

| Transport | Connect + handshake | 600 B round trip | Bulk |
|---|---|---|---|
| TCP plain | 0.10 ms | 15 µs | ~300 MB/s |
| **TCP mutual TLS** | **3.2 ms** | **67 µs** | **~320 MB/s** |
| Unix plain | 0.09 ms | 56 µs | ~320 MB/s |
| Unix mutual TLS | 3.4 ms | 74 µs | ~420 MB/s |

Per sgit command: three handshakes ≈ 10 ms, against 146 ms of sgit imports and ~108 ms of key derivation already paid today. Round-trip and bulk figures varied by up to ~25% between runs; handshake times were stable. Method and caveats on [Evidence](../evidence/index.md#6-transport).

## Deployment topologies

Same components, same protocol, same policies. Only the launcher changes. Only A was measured.

```
 A. one VM, separate uids (what was measured)
 ┌──────────────────────── VM ────────────────────────┐
 │ app  fs  net  kms   (one uid each)                 │
 │   └─ Unix sockets + mTLS + SO_PEERCRED + iptables  │
 └────────────────────────────────────────────────────┘

 B. Docker / compose: one container per component
 ┌─app─┐  ┌─fs──┐  ┌─net─┐  ┌─kms─┐   network: internal only, except net
 │     │──│     │  │     │──│     │   volumes: clone folder rw in fs, ro in app
 └─────┘  └─────┘  └──┬──┘  └─────┘   kms: internal network only, read-only rootfs
                      └──► egress

 C. Kubernetes: one pod, one container per component (or kms as its own Deployment)
   identities from SPIRE / mesh (spiffe://<td>/<role>); NetworkPolicy mirrors the edge matrix;
   seccomp + readOnlyRootFilesystem + runAsNonRoot per container from the policy

 D. remote KMS
   net ──mTLS/HTTPS──► Lambda / Cloud Function ──► cloud KMS asymmetric key (HSM)
   caller bound to the session's auth key; nonce store e.g. DynamoDB conditional put

 E. platform-provided (proposed end state)
   net ──► local platform endpoint (vsock / proxy) ──► platform KMS; session identity
   = the platform's own knowledge of the session; no auth key in the container
```

Topology E is a proposal for what agent platforms should offer. No such service is known to exist today.

Sources: [05-sharness](../briefs/sharness-brief-pack/docs/05-sharness.md) §2, [01-architecture](../briefs/sharness-brief-pack/docs/01-architecture.md) §1, §3 and §5.
