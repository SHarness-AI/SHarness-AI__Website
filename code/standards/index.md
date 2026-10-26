# Standards and their reference implementations

> **Status: the first standard written, as of 26 Oct 2026.** Most of SHarness is a specification, not code: the policy's shape and hash, the manifest and the edges, the protocols of the components, the acceptance test ([One standard, many languages](../../articles/one-standard-many-languages.md)). This page is the registry: one row per standard with its version and its test vectors, one row per implementation with its language, where it lives, what it passes and who reviewed it. A row says *runnable* only with the commit and the test run that make it so. Kept by dev@sharness.

## 1. How a standard is published here

Each standard has one page with four things: a **version** of its own (independent of any implementation's); the **normative text**, a list of musts; the **test vectors**, as files an implementation's CI fetches from this site (`vectors.json` lists them, with the expected hash or the reason for refusal); and the **registry row** of every implementation. The reference implementation (the Python CLI) is the oracle: `tools/gen_vectors.py` runs every case through it and refuses to publish a vector the oracle disagrees with. A change to a standard is a new version with its own vectors, never a silent edit; the old version's page stays.

What a specification *is* for SHarness, and the four parts a spec needs before it is more than an Expectation (schema, canonical form and hash, composition, conformance), is pbp@sharness's definition on [the PBP on one page §8](../../design/pbp/index.md#8-what-a-spec-means-here). The pages here are the second part made concrete, standard by standard; the conformance statement (which probes an enforcer must refuse, how it reports barrier kinds) is pbp@sharness's and is referenced, not restated.

## 2. The standards

| Standard | Version | What it fixes | Vectors | Status |
|---|---|---|---|---|
| [policy v0: canonical form and hash](policy-v0/index.md) | v0 | the v0 shape, canonical JSON, `sha256:` over the bytes, what is refused so that every language hashes the same, the environment contract | 13 accept, 15 refuse ([`vectors.json`](policy-v0/vectors.json)) | written; two implementations plus the oracle pass every vector |
| the acceptance test (`hello`'s six expectations and the caveat line) | not yet versioned | which probes a conformant enforcer must refuse; how the result reports what held | none yet | pbp@sharness's conformance statement; the Python `hello` is the only runnable form |
| the manifest and the edges | not yet written | the matrix, the certificate profile, the session CA | | designed on [Architecture](../../design/architecture/index.md) |
| the KMS protocol | not yet written | the five operations, the `unwrap` schemas, the checks in order, the envelope | | designed on [Keys §3](../../design/keys/index.md#3-the-kms-protocol); E08 settles it first |
| the `net`, `fs`, `llm` and `bash` protocols | not yet written | the request schemas, the business rules, the profiles | | designed on [the component pages](../../components/index.md) |
| a door's two schemas: what it accepts and what it emits, per door and per target | not yet written | the contract on each edge of the manifest, checked by hash (the mirror rule); the vocabulary a door's rows are written in | | pbp@sharness's [tree of doors](../../design/pbp/index.md#6-a-door-and-the-tree-of-doors), 26 Oct 2026; one page per `sharness.<door>.<target>` once a door exists |
| a door's conformance suite against its twin | not yet written | the refusals a target must give, run first against the twin that has the real thing's signature; `twin` or `live` as a separate measured fact | none yet | [T20](../../admin/board/index.md#t20): the first pair is `sharness.fs.s3` against the AWS twin, once that door is designed |

## 3. The implementations

| Implementation | Language | Where | Passes | Status | Reviewed |
|---|---|---|---|---|---|
| `sharness-ai`, the CLI | Python 3.11+ | [SHarness-AI__CLI](https://github.com/SHarness-AI/SHarness-AI__CLI), `sharness_ai/policy.py` | policy v0, as the oracle; `hello`, 6 of 6 measured 24 and 25 Oct 2026 | runnable; E01 to E04, E09, E10 | security@sharness, review 1 (25 Oct 2026) |
| the policy-hash mockup | JavaScript in the browser | [explain/mockups/policy-hash.html](../../explain/mockups/policy-hash.html) | the hash of every accept vector (checked by hand, 25 Oct 2026); it has no shape check, so it refuses only what canonicalisation refuses | runnable for the hash | not reviewed |
| `sharness-ai` for Node and the browser | JavaScript, Node 20+ | SHarness-AI__JS once the editor creates it ([R21](../../admin/board/index.md#r21)); until then the branch `claude/js-reference` of the CLI repository | policy v0: 13 accept, 15 refuse (`npm test`, Node 22, 26 Oct 2026) | runnable: `policy hash`, `policy check`; nothing else | not reviewed |
| `sharness-ai` in Go | Go 1.22+ | SHarness-AI__Go once created (R21); until then the branch `claude/go-reference` of the CLI repository | policy v0: 13 accept, 15 refuse (`go test`, Go 1.24, 26 Oct 2026); a static binary of 2.4 MB | runnable: `policy hash`, `policy check`; nothing else | not reviewed |
| `sharness-ai` in Rust | Rust | SHarness-AI__Rust once created (R21); until then the branch `claude/rust-reference` of the CLI repository | nothing yet | the common structure only; the bash client and the KMS are its first targets | |

Every implementation's CI runs the vectors twice: the copy vendored in the repository (what the commit was written against) and the copy published here (the standard as it is now), so a change to the standard is seen by every implementation on its next run, and a vendored copy that drifts is seen too.

## 4. How the doors change the registry

pbp@sharness's rule of 26 Oct 2026, from the editor: the components are **doors**, named as a tree, `sharness.<door>.<target>`, where the second name is where the door sends (`sharness.fs.s3`, `sharness.db.sqlite`, `sharness.net.proxy`), every door declares what it accepts and what it emits, and a twin is a target with the real thing's signature. For the registry that means three things. A standard is written per door (its accepts and emits) and its vectors per target, run first against the target's twin. An implementation's row names the targets it carries, with `twin` or `live` as a measured fact beside each, never implied by a passing suite. And the module paths the vectors cite are the dotted names, the same in every language: `sharness_ai/fs/s3`, `sharness_ai.db.sqlite`, and their equivalents in the Go and JavaScript trees, so the brief on [one repository per language](../../admin/briefs/2026-10-26__brief__one-repository-per-language/index.md) carries the tree as the layout of every implementation.

## 5. What this page does not claim

- No implementation is a SHarness component. Three languages can hash and check a policy; none can enforce one except Python, and that for a child process, as a Setting for the process that applies it.
- "Passes" is a test run on one machine on one date, named in the row; it is not a measurement of enforcement.
- "Reviewed" is a second reader of the code, named; a blank cell means nobody has read it but its author.

Sources: [One standard, many languages](../../articles/one-standard-many-languages.md); [the PBP on one page](../../design/pbp/index.md); [Languages](../languages/index.md); the brief [one repository per language](../../admin/briefs/2026-10-26__brief__one-repository-per-language/index.md); `tools/gen_vectors.py` on this site.
