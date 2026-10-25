# Languages

> **Status: a recommendation, as of 25 Oct 2026**, for [roadmap decision 11](../../design/roadmap/index.md#open-decisions). What each part of SHarness is written in, what it should be written in, and why. The rule behind every row: reuse what Linux and the standard library already have before writing anything, and keep each piece small enough to read in one sitting.

## What is written, and in what

| Part | Language today | Why |
|---|---|---|
| the CLI and experiments E01 to E04 | Python 3.11+, standard library only | fast to iterate; `ctypes` reaches Landlock, `unshare` and `memfd_secret` without a C extension; sgit, the first harnessed app, is Python, so the same team reads both; the design's measurements were taken in Python |
| the browser mockups | JavaScript in the page, no framework; WebCrypto for SHA-256 | the only language a browser runs; the point of the policy-hash mockup is a second implementation that must agree with the Python one |
| the storyboards | JSON data, drawn by the storyboards.sgit.ai kit (JavaScript, pinned release) | data, not code |
| this site's tools | Python standard library (generators) and Node (the gate, the kit's validator) | no build dependencies; the same pattern as the other sites in the network |

## What each component should be written in

| Component | Recommendation | Reason | When |
|---|---|---|---|
| `sharness.launcher` | **Python** first, a static binary later if a platform needs one | it is configuration of things the kernel already does (uids, namespaces, cgroups, certificates); the design's target is ≤ 400 lines; Python's `ssl` and the `cryptography` package make the session CA a few dozen lines | E06 onwards |
| `sharness.net`, `sharness.fs`, `sharness.llm` | **Python**, standard library plus `cryptography` where sealing is needed | each is a small server over mutual TLS with a JSON schema; Python's `ssl` module does TLS 1.3 with client certificates; the measured handshake (3.2 ms) was Python's | E05, E07 |
| `sharness.kms` | **Python v0 (E08), then Rust** | the KMS is the one place where memory hygiene decides the security: the design already notes that Python cannot guarantee erasure, that OpenSSL copies the key into its own heap, and that scrubbing `bytes` is best effort. A Rust KMS with zeroising types and `memfd_secret` through a thin syscall layer removes a class of caveats. v0 in Python first, to settle the protocol | after E08 |
| `sharness.bash` (the server) | **Python** | it is a launcher for one command at a time: cgroup, namespaces, uid, Landlock, exec, filter | E06 |
| `sharness-bash-client` | **a small static binary: Rust or Go** | the design requires it: the orchestrator's execute allowlist must not include an interpreter, and a static binary needs none. Rust for size and no runtime; Go if the team prefers it | E06 |
| the seccomp filters | **data** (a syscall list per component in the policy), compiled to BPF by a few lines of Python; libseccomp if available, raw BPF through `ctypes` if not | the filter is part of the policy and hashed with it | the next rows of [Containment](../../design/containment/index.md) |
| the policy language | **JSON** (canonical, hashed); YAML only for reading on the site | two implementations already agree on the bytes; a policy language is explicitly not wanted ([Components](../../design/components/index.md#as-little-code-as-possible)) | now |
| the Messages API front of `sharness.llm` | Python, then whatever the platform wants when it runs the component as a service | the API is HTTP and JSON; nothing language-specific | E07 |
| the browser experiments (a Linux kernel in a tab) | JavaScript and WebAssembly around an existing emulator; the kernel and rootfs built with the normal Linux toolchain | a page on this is being researched | planned |

## Two rules that follow

1. **Python until a caveat says otherwise.** Every component starts in Python because the experiments do and because the design's own figures were measured there. A component moves to Rust only for a stated reason (memory hygiene in the KMS; a static binary for the bash client), recorded on the roadmap.
2. **No runtime dependencies in the CLI** beyond `cryptography` for the components that seal and sign. The experiments stay standard-library only so a Claude session can install and run them anywhere Python is.

## What this does not decide

Whether the platform-provided versions of the components (topology E) share any code with these; the design says only that the protocol is the same. And nothing here is a commitment of sgit's maintainers about sgit's own language, which is Python today.

Sources: [Components: as little code as possible](../../design/components/index.md#as-little-code-as-possible); [Keys §7, memory hygiene](../../design/keys/index.md#7-where-the-private-key-lives-and-for-how-long); [Enforcing the process tree §2](../../design/process-tree/index.md#2-design) (the client as a static binary); the CLI's `CLAUDE.md`.
