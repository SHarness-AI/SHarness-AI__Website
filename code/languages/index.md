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

## Reference implementations in several languages (decided 26 Oct 2026)

**Decided by the editor on 26 Oct 2026** ([R8](../../admin/board/index.md#r8)): one repository per language, each with the same structure, so that a component or a CLI can ship in that language on its own; the standards and their test vectors on this site ([Standards](../standards/index.md)); the first implementation of a component written in the language that suits it, not ported from Python. On the same day the policy v0 standard was written and two implementations passed all of its vectors; the registry says which. Dinis Cruz's brief of 25 Oct 2026 extended decision 11 from "which language for each component" to "reference implementations of each component in several languages, against one standard per component, with test vectors and a reviewed registry". The developer agent's map of that is the article [One standard, many languages](../../articles/one-standard-many-languages.md): what in each component is a specification (the policy's shape and hash, the manifest and the edges, the KMS, net, fs, llm and bash protocols, `hello`'s six expectations) and what is an implementation (reaching the kernel, serving mutual TLS, holding a secret), then a component-by-language matrix.

| Language | Carries | Role | Status, 26 Oct 2026 |
|---|---|---|---|
| Python | the standards, the servers (`ssl`), the kernel (`ctypes`); not a static binary | the first implementation, and the one the measurements are taken in; the oracle for the vectors; `sharness.kms` v0 to settle the protocol | runnable: E01 to E04, E09, E10 |
| JavaScript in Node | the standards, the servers (`tls`); the kernel only through a helper binary | `net`, `fs` and `llm` where MCP servers and agent loops are written; `run` delegates | runnable: `policy hash` and `check`, 28 of 28 vectors (Node 22); on the CLI's branch `claude/js-reference` until R21 |
| JavaScript in the browser | the standards (WebCrypto); no sockets, no kernel | the hash and check with nothing installed; CSP as a translate target | the mockup hashes; the Node package's one file runs in a page, not yet wired in |
| Go | all four kinds, with TLS and a static build in its standard library and Landlock in `x/sys/unix`; not the KMS (the collector may copy a secret) | the second complete implementation; the bash client; the first non-Python footprint | runnable: `policy hash` and `check`, 28 of 28 vectors (Go 1.24), a 2.4 MB static binary; branch `claude/go-reference` until R21 |
| Rust | all four kinds; rustls pinned for the servers; no collector, so a secret can be zeroed in place | `sharness.kms` after E08 and the bash client, as this page already recommends | the common structure only; branch `claude/rust-reference` until R21 |
| Java, .NET | the standards and the servers; the kernel through their standard FFI; heavy runtimes | harnessed-app SDKs and policy tooling, on interest; `translate --to kubernetes` as their first enforcer | planned, on interest |
| C, assembly | the kernel calls and nothing else | a `run` in a few hundred lines as the floor, for teaching and for the footprint comparison | planned, on interest |

The rules above still hold: Python until a caveat says otherwise, and no runtime dependencies beyond a stated, pinned exception. What changes is that the exception list grows by one per language (rustls in Rust; nothing in Go or Node), and that each implementation must pass the same test vectors (the seven example policies and their hashes, `hello`'s six expectations) before it enters the registry. The repositories are [R21](../../admin/board/index.md#r21); the registry of implementations is on [Standards](../standards/index.md).

## What this does not decide

Whether the platform-provided versions of the components (topology E) share any code with these; the design says only that the protocol is the same. And nothing here is a commitment of sgit's maintainers about sgit's own language, which is Python today.

Sources: [Components: as little code as possible](../../design/components/index.md#as-little-code-as-possible); [Keys §7, memory hygiene](../../design/keys/index.md#7-where-the-private-key-lives-and-for-how-long); [Enforcing the process tree §2](../../design/process-tree/index.md#2-design) (the client as a static binary); the CLI's `CLAUDE.md`.
