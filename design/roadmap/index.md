# Roadmap and open decisions

> **Status: design.** Nothing is built. This page lists what is decided, what is open, and the first tasks for the agents that will build SHarness. Decisions below are dated as of 24 Oct 2026 unless marked otherwise.

## Decided

| Decided | Why |
|---|---|
| Single-purpose components, one job each (`sharness.<role>`) | the edges between them are the security model |
| Edges deny by default; the app never talks to the KMS | the app never sees keys; the KMS never sees the network or disk |
| **Mutual TLS 1.3 everywhere**, roles in certificate URI SANs, issued by a session CA whose key is destroyed after issuing | the same code local, Docker, Kubernetes, remote; ~3.2 ms per handshake, measured |
| The KMS **never returns a clear key**; it returns derived keys sealed to the caller's one-time key | nothing between the KMS and the consumer sees plaintext, including the agent |
| The KMS makes its own private key; it never leaves | one sealed place |
| Default key holding: **frozen process + `memfd_secret`** | 0.28 ms freeze / 0.13 ms thaw, measured; secret pages unreadable even through `/proc/<pid>/mem` |
| Policies are hashed (canonical JSON, SHA-256); the hash comes from the person or is signed by the root key | otherwise a prompt-injected agent could widen them |
| Host allowlisting is done by `sharness.net` as the TLS client, not by the kernel | the kernel only sees the platform proxy's port; `.net` sees and verifies the name |
| The command is `sharness-ai`, not plain `sharness` (decided 24 Oct 2026, after the design pack) | `sharness` is the Debian / pkgsrc / OpenBSD package of the unrelated shell test library; `sharness-ai` matches the PyPI distribution |
| **Build order: the ladder** (decided 24 Oct 2026, from the memo): browser mockups, then experiments any session can run, then Linux experiments, then components, then the launcher above the agent | start small, each piece in isolation; see [Mockups and experiments](../../code/experiments/index.md). E01 to E04 are runnable |
| A **v0 policy** of six keys that the CLI and the browser hash identically, enforced with Landlock, growing towards the full schema | two implementations, one hash, before layers and signing |

## Open decisions

| # | Decision | Notes |
|---|---|---|
| 1 | ~~Command name~~ | **settled**: `sharness-ai` (above). Proposed environment variable prefix `SHARNESS_AI_` |
| 2 | Full split vs. step 1 | full split: `.net` holds derived keys and does all vault crypto. Step 1: `.net` filters traffic; the app receives derived keys sealed to its own one-time key. Step 1 works with sgit 0.24's internals; the full split is the target |
| 3 | Remote KMS backend | AWS KMS asymmetric RSA-4096 with OAEP-SHA-256 should match sgit's envelope: **verify** before relying on it |
| 4 | `.fs` as a process owning the folder vs. a FUSE mount | FUSE was available in the measured environment; start with the owning process |
| 5 | Who runs the launcher | the agent today (so locks are only Settings against the agent itself), a local script, or the platform (end state) |
| 6 | Run the process-tree proof of concept and publish its results | see [Enforcing the process tree](../process-tree/index.md); follow its safety rules |
| 7 | One CLI project, or one per component | one for now (memo of 24 Oct); revisit when a component is useful on its own |
| 8 | What "a skill" means for SHarness | a skill can install and start the harness, but locks it applies to the agent that loaded it are only Settings; binding needs the launcher above the agent |
| 9 | **Claude Code's sandbox as a layer.** Should a PBP generate the sandbox's settings (`bubblewrap`, network namespace, hostname allowlist) as its transparent `sharness.bash` on a laptop, and what does the design still add there | prior art the pages had missed; comparison on [Mockups and experiments](../../code/experiments/index.md#what-claude-codes-own-sandbox-already-gives-and-what-sharness-adds) |
| 11 | **Languages.** Python for every component first; Rust for `sharness.kms` once the protocol is settled (memory hygiene) and for the bash client (a static binary, no interpreter on the allowlist). Extended 25 Oct 2026: reference implementations in several languages against one standard per component, with test vectors and a reviewed registry | recommended on [Languages](../../code/languages/index.md); the map and a proposed order (JavaScript, Go, Rust; Java, .NET, C later) on [One standard, many languages](../../articles/one-standard-many-languages.md); not yet decided |
| 10 | **Order of E05 to E08** | proposed on the [research note](../../evidence/research/index.md#4-what-is-still-open-in-the-order-to-take-it): E06 (the process tree), E05 (the edges as a script), E08 before E07 (the KMS before the LLM gateway), then the launcher as a script on a laptop |

## Guidance from Dinis Cruz's memo of 24 October {#memo-guidance}

From [voice memo 01](../../project/sources/memos/2026-10-24-memo-01-secure-harness.md), written up as [A secure harness for agents](../../articles/secure-harness-for-agents.md). All of it is direction, not design yet.

| Topic | Guidance | Status |
|---|---|---|
| How to build | very simple examples first; each component (network, KMS, file, LLM) built and tested in isolation; one CLI project for now, separate ones later if needed | proposed |
| Order of work | as simple, as fast and as slim as possible; then harden; then test, and see how the flow works | proposed |
| First users | (1) Dinis's own Claude sessions; (2) sgit, and the agents that use it all day, including the newsroom's agents, which run around the clock and read untrusted data | proposed |
| Acceptance test | a hello world with Claude, run inside SHarness, shows the agent cannot reach the internet, cannot write to the file system, and cannot make other requests, because SHarness is inline | **runnable for one child process** (E04, `sharness-ai hello`, measured 24 Oct 2026); for the agent itself it needs the launcher above the agent |
| Reach | as generic as possible; possibly packaged as a skill | partly answered: the `sharness-hello` skill runs E01 and E04 inside a session under the safety rules; a skill cannot apply locks that bind the session that loaded it (see [Policies §2](../policies/index.md#2-who-enforces-decides-the-barrier-kind)) |
| Policies | extend process behaviour policies with file behaviour policies and network behaviour policies | proposed ([Policies §10](../policies/index.md#10-next-file-and-network-behaviour-policies-proposed)) |
| As a service | run some components with a cloud provider (Cloudflare, AWS or another), to apply controls outside the agent's machine | proposal; no such service exists |
| Laptops | protect Claude running locally; disposable users per session | designed; ~49 ms per user measured in one cloud workspace, not on a laptop |

## Refactor path in sgit

sgit 0.24.0 reads the vault key directly in many places (the origin article counts 27 read sites in 17 files; a broad grep for `_read_vault_key|load_vault_key|vault_key_path` finds 65 references in 23 files, including imports). After derivation almost nothing needs the clear key except `show-key`, `rekey` and `move`.

| Step | Change | Effect |
|---|---|---|
| 0 | Fix independently: private keys from `pki keygen` use PBKDF2 at 2,048 iterations (measured, `0x0800`) → Argon2id; `Secrets__Store` fixed salt → per-user random salt | removes two weaknesses whatever else happens |
| 1 | **The door**: one `Key_Source` interface ("vault id + derived keys for this folder"), reading `vault_key` today; lazy imports per subcommand | no behaviour change; all call sites go through it; tests prove it |
| 2 | `Key_Source` backed by the KMS protocol; `clone --sealed`, `vault_key.sealed`, `vault seal-local`, `vault seal --to`; `.net` filters traffic; the app receives derived keys sealed to its own one-time key | key never on disk, argv or stdout |
| 3 | **Full split**: vault crypto and server I/O move into `.net`; the app asks for operations, not keys | the app holds no keys and has no network |
| 4 | `.fs` as the only writer; then optionally FUSE | business rules on disk enforced outside the app |
| 5 | P-256 ECDH envelope for hardware keys (TPM / PIV / Secure Enclave); commit signing with the identity | hardware-backed KMS |

## End state: the platform provides it

The local KMS process and a Lambda are stand-ins. The right owner of the KMS and of policy enforcement is the **agent execution environment**: it already knows which session is calling (which solves caller authentication for an ephemeral container), it already sits outside the container, and it can bind key lifetime to session lifetime and keep decrypted results out of transcripts and logs. The protocol is designed so that apps don't change when the KMS moves from a local uid to a Lambda to a platform service.

This is a **proposal for what platforms should offer**. No such service is known to exist today, and nothing on this site describes any platform's plans.

## For the agents that will build this

Read in order: [the design pack README](../../project/sources/sharness-brief-pack/docs/00-README.md), then documents 01 to 07 (all on [The source documents](../../project/sources/index.md)). Documents 01–04 use sgit-specific names: sgit-kms → `sharness.kms`, sgit-net → `sharness.net`, sgit-fs → `sharness.fs`, sgit-cli → the harnessed app.

Ground rules carried from the design:

- **Status words matter.** Say *measured* only with a method and a date; everything else is *designed* or *proposed*. Never claim anything is built or released before it is.
- **The threat model trusts the kernel.** Never claim protection against root or kernel compromise.
- **Components small enough to read in one sitting**: launcher ≤ 400 lines, each component ≤ 300, a shared library ≤ 400 (proposed targets).
- **Reuse before building**: Landlock, seccomp, namespaces, cgroups, stdlib `ssl`, JSON Schema, `strace`, `memfd_secret`.
- **Testing inside a live agent session follows the safety rules** on [Enforcing the process tree](../process-tree/index.md#4-safety-rules-for-testing-inside-a-live-agent-session): never touch the orchestrator, never firewall uid 0 or the model API, run experiments as child subtrees, clean up.
- **Publish results here**: every new measurement goes on [Evidence](../../evidence/index.md) with its method and date.

Source: [00-README](../../project/sources/sharness-brief-pack/docs/00-README.md) §5–6, [01-architecture](../../project/sources/sharness-brief-pack/docs/01-architecture.md) §7, and [the brief for this site](../../project/sources/sharness-brief-pack/BRIEF-for-website-agent.md) §7.
