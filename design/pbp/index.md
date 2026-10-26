# The Process Behaviour Policy, on one page

> **Status: proposed, as of 26 Oct 2026.** This page states what a Process Behaviour Policy is, so that every other page, the CLI and any other enforcer can be checked against one definition. It names what exists (the v0 of six keys, runnable and measured) and what is proposed (the rest). No SHarness component is built. By pbp@sharness, the policy agent of this site, from Dinis Cruz's direction of 25 Oct 2026.

## 1. What it is

A **Process Behaviour Policy (PBP)** is the [Agent Behaviour Policy](https://riskmandate.ai/abp.html) model applied to one process: a written description of what the process is allowed to do, hashed to one name the person supplies from outside, and enforced by something the process does not include. An ABP *describes* an agent's behaviour; a PBP is that description *executed*, underneath the agent. SHarness is one enforcer of PBPs, built to be read; any environment that holds the same rows is another.

## 2. The four objects, for a process

The hashed file is one of four objects, not the whole policy. The same four at every layer is what makes the model fractal.

| Object | For a process | Where it comes from today |
|---|---|---|
| **Mandate** | the rows: what the process may read, write, execute, connect to, spend, and what it may do with each | the policy file, written by the person (or shipped with the code and narrowed by the person); **this is what is hashed** |
| **Grant** | what the process can actually do before the policy: uid, capabilities, Landlock ABI, namespaces, egress | `sharness-ai probe` (E01); measured |
| **Delta** | grant minus mandate, derived, never written by hand | probe's reading line; proposed as a table |
| **Barrier** | per row: what holds it, and of which kind | the enforcement map and `policy translate`'s gap notes (E10); proposed as a column of the policy summary |

Barrier kinds are ABP's: **None**, **Expectation** (prose), **Setting** (the subject could flip it), **Boundary** (enforced above the subject). A process is the one subject where almost every row can be a Boundary, because the kernel is told before the process starts.

## 3. The three things that make it binding

A PBP is binding only when all three hold. Lose one and it is an ABP again: a policy the subject reads.

1. **The text.** A small JSON object; canonical JSON (sorted keys, no whitespace, integers only) so the same policy hashes the same in every language. Measured identical in Python, the browser and a Linux guest, 25 Oct 2026.
2. **The hash, from outside.** The person supplies `sha256:…`; the enforcer refuses anything else (`--expect-hash`, exit 125). A prompt-injected agent cannot widen what it cannot rename.
3. **An enforcer the subject does not include.** The kernel, or a separate process. *Who enforces decides the barrier kind*: a policy a process applies to its own child is a Boundary for the child and a Setting for the process. Every result says which.

A skill that loads a PBP into an agent gives Boundaries to the agent's children and a Setting to the agent. That is a true on-ramp and the caveat travels with it.

## 4. Two kinds of rows, one policy

**Capability rows** bound what the process can reach: path prefixes for read, write and exec; TCP ports; no network; memory and process-count caps; no new privileges; later uids, seccomp and syscalls. The kernel holds them (Landlock, rlimits, cgroups, namespaces). These are v0, runnable.

**Behaviour rows** bound what the process does with a reach it has: append only to this file; edit only this section; content valid against this schema; this field within this range, never negative; copy this file only after that one exists; connect only to this host, this endpoint, this vault id; edit only this row of this table; at most N per interval; this operation only with fresh approval. A door holds them ([the components](../../components/index.md) are the doors): `sharness.fs` for files, `sharness.net` for the network, `sharness.kms` for keys, a door the business writes for its own rule. Proposed.

**The rule that joins them.** A behaviour row is a Boundary only when the subject has no path to the resource except through the door that holds the row. So every behaviour row has preconditions made of capability rows: the side doors closed by the kernel, one door, a separate process, and an edge to that process. `append_only: /work/ledger.txt` for the app requires that the app's `files.write` excludes that path and that the app has an edge to `fs`. `policy check` should compute this: a behaviour row whose preconditions are not met is well formed and gets barrier kind **Expectation**, not an error. That is "what can currently be controlled", derived from the policy rather than hoped.

**What that means for the richness of the policy.** The person writes the mandate all the way down to the business logic, and the policy says, row by row, who holds it. Rows no door holds in this deployment stay in the policy as Expectations, counted. The policy never claims a row is held when nothing holds it.

## 5. A row

```yaml
- subject:  app                      # the process bound
  resource: /work/ledger.txt         # a path, a port, a host, a table, a key id
  op:       write                    # read | write | exec | connect | unwrap | …
  where:    { append_only: true, content: { schema: ledger-line.json, amount: { min: 0, max: 10000 } } }
  held_by:  fs                       # kernel | <component> | none
  kind:     boundary                 # derived, never written: boundary | setting | expectation | none
  requires: [ app.files.write excludes /work/ledger.txt, edge app->fs ]   # derived
```

`where` is a **closed, declarative predicate language**: append only; a section by marker or line range; content by JSON Schema; a numeric field by range; count and rate per interval; ordering by "after this path exists"; "requires fresh approval". Anything else is a custom door under its own PBP, not an extension of the language. A policy that can express arbitrary logic is code, and code in the policy is a rules engine in the trusted path.

Hosts, URLs, tables and rows are door rows by construction: the kernel sees paths and ports. The [enforceability matrix](../../landscape/enforceability/index.md) says this per predicate kind, so nobody expects `translate --to docker` to carry "this row of this table". Where a target holds a behaviour row natively (a database's row-level security the app's credentials cannot change, a bucket policy), `translate` emits it and it counts as a Boundary there.

## 6. A door, and the tree of doors

A **door** is a process that holds one resource's behaviour rows: it receives a request and the policy hash, answers allow or deny against the rows for that subject, and emits an audit line (never a secret). It runs under its own PBP, so it is itself bounded, and it stays within the size target (a component ≤ 300 lines) because it holds one resource's rows, not a rules engine. A business writes the door for "transaction amount within range, daily total under X" as its own small component. The door's request protocol is [the components'](../../components/index.md#2-everything-is-a-request): a small REST API on loopback under mutual TLS, so any language can call one and any language can be one. Proposed.

**The names are a tree, and the dot means "sits on".** Dinis Cruz's rule of 26 Oct 2026. `sharness.<resource>` is a door: a resource class and its row vocabulary (`fs`, `net`, `db`, `llm`, `bash`, `kms`). `sharness.<resource>.<dialect>` is one concrete system that speaks the parent's vocabulary plus its own nouns, and **sits on** its parent: the parent closes every other path, so the child's only way to the world is through it. `sharness.net.http` reaches the network only through `net`; `sharness.db.sqlite` writes its file only through `fs`; `sharness.db.postgres` connects only through `net`, with the password in `kms`. Depth is open (`sharness.net.http.gmail` is a profile of HTTP), and a level earns a name only when it adds nouns its parent cannot see; otherwise it is configuration of the parent. A door whose rows name two parents goes under the one whose nouns dominate, with an edge to the other: git's rows are remote, branch, ref and the push, the irreversible step and a network act, so `sharness.net.git`, with an edge to `fs` for the working tree; every tool call passes through the model door, so `sharness.llm.tools`.

**Three trees are one.** The architecture already puts the role in the certificate's SAN URI and chains policies by parent hash. With dotted names the name tree, the identity tree (`spiffe://<session>/net/http`) and the policy tree (`extends`, composed by intersection) are the same tree. That is what lets a dialect run on another machine, in another language, from another vendor, and still be addressed, authenticated and bounded by one path. The cost is one process per name: a mutual TLS handshake between two local processes measured about 3.2 ms (24 Oct 2026), and the cost stops mattering when the dialect is remote. The same tree is the code tree: module `sharness_ai.db.sqlite` in the CLI for now, a distribution `sharness-ai-db-sqlite` when a dialect leaves it, the component size target per dialect.

**A dialect holds its rows in one of two modes.** *Proxy*: the door is the only path; the app sends structured requests (`select` table, columns, filter), never a query string, and the door holds the rows. *Translate*: the system enforces natively and the door holds only the credential and checks the configuration against the hash (Postgres row-level security, grants and views; a bucket policy). Each dialect is a row of the [enforceability matrix](../../landscape/enforceability/index.md). One rule keeps a door small: **never parse SQL or Cypher in the door**; structured requests in, or native enforcement.

**The roster, all proposed, none built:**

| Door | Its nouns | Dialects first | Later |
|---|---|---|---|
| `sharness.fs` | path, operation, content | `.s3` | |
| `sharness.net` | host, port, endpoint, id | `.http` (method, host, path pattern, headers, body schema, response size), `.git` (remote, branch, ref, push; never force, never main), `.smtp` | `.ftp`, `.http.gmail`, `.http.slack` |
| `sharness.db` | table or collection or label, row, column, value, count, total per interval | `.sqlite` (the first: the `sqlite3` module is in Python's standard library, so it is buildable under the no-dependency rule and would be the first door that is runnable), `.postgres` (translate: row-level security) | `.mysql`, `.mongo`, `.neo4j`, `.redshift` |
| `sharness.llm` | model, tool list, tokens | `.tools` (tool name, argument predicates, calls per run: where "refund at most 100" lives for a tool that is not a database) | |
| `sharness.bash`, `sharness.kms` | command, profile; key id, operation | none yet | |

A door earns a name when it has nouns the door below cannot see, it can be the only path to the resource, and at least one dialect holds its rows as a Boundary. Anything else is a profile of an existing door. Not a door: a guardrail that judges intent on an allowed channel, which a kernel bound cannot do; the [landscape](../../landscape/index.md) says to consume such decisions at `llm`, not to build one.

**The twin is below the dialect, not a dialect.** [twins.sgit.ai](https://twins.sgit.ai) places a twin at the real system's boundary ("a consuming system only ever sees a twin"), as an interface to a real thing with a swappable backend (vault, disk, memory, live), valued for whether it is connected. So `sharness.fs.s3` speaks S3 to an endpoint, and the endpoint is AWS or [the AWS twin](https://aws.twin.sgit.ai); the dialect cannot tell and must not. There is no `sharness.fs.twin`: a twin is not a protocol, and the twins site's naming ruling keeps the twin (no credentials) apart from the broker (holds credentials, enforces permissions). That broker, as the twins site defines it, is a door with a dialect; its two open costs, that holding credentials makes it a target and that enforcement needs one interpreter per provider and capability, are what `kms` and the dialect tree answer. The twin goes in the dialect's **policy, as the target**: the live policy and the twin policy share every vendor-shipped row and differ in the invocation layer that names the endpoint, so the same code runs under two hashes, connectedness is recorded by hash (a dialect's `hello` prints `target: twin` or `target: live`), every dialect's conformance suite runs against its twin before it ever touches the real system (the AWS twin answers S3's REST-XML with boto3 unchanged, as of 26 Oct 2026, so `sharness.fs.s3`'s refusals can be exercised with no account), and the twin is itself a process under its own PBP, reached only through `net`. **The undecorated door is the local one**: `sharness.fs` is the local disk (paths, Landlock) and `sharness.db.sqlite` the local file; a dialect names a protocol to a remote system. No `fs.local` or `fs.disk`.

## 7. The fractal

The enforcer of a row is a subject one layer up. The app's append-only row is held by `sharness.fs`; `sharness.fs`'s own capability rows (write only the clone root, no network, no fork) are held by the kernel, applied by the launcher; the launcher's policy is held by whoever starts it, a platform or a person. Compromise `sharness.fs` and the damage is bounded by its PBP, not by the app's. Layers compose by **intersection**, so no layer can widen a parent: the vendor ships L2 to L4 with the code, the organisation L0 and L1, the person L5. Same four objects, same row shape, same rule at every layer. Harness on harness.

## 8. What "a spec" means here

Four parts. A spec that nobody enforces is an Expectation, so the fourth part is not optional.

| Part | What | Status |
|---|---|---|
| **Schema** | the row shape above; the v0 of six keys (also on [the manifest's page](../../components/policy/index.md)) (`pbp`, `id`, `files`, `network`, `process`, `notes`) is the runnable subset | v0 runnable; the full schema proposed on [Policies](../policies/index.md) §4 |
| **Canonical form and hash** | RFC 8785 target; sorted keys, no whitespace, integers only; `sha256:` over the bytes | runnable; measured identical in three implementations, 25 Oct 2026 |
| **Composition** | layers by parent hash, effective policy = intersection; a child never widens | proposed; `layer` is a label in v0 |
| **Conformance** | the probes a conformant enforcer must refuse (`sharness-ai hello`, six today), plus the matrix of which rows it holds as which kind, reported honestly | E04 runnable and measured; the matrix is written for five enforcers, none run as a conformance test |

An enforcer is conformant when it runs the suite and reports barrier kinds truthfully, Expectations included. Any product that does is a valid enforcer of PBPs under one hash. That is what lets someone take one row and start.

## 9. Two numbers in every summary

ABP's number is **unbounded excess**: reach nobody asked for and nothing bounds. A PBP adds a second: **unheld rows**, the mandate rows no Boundary holds. `hello` reports probes held; the policy summary should report rows held by the kernel, rows held by a door, and rows unheld, the way the newsroom counted its checks (1 boundary, 34 settings, 22 expectations). The second number is the business case for the next door.

## 10. Naming

**Process** because the process is the unit the kernel enforces on, the unit of the layers, and the word in ABP's lexicon (`execute.process.host`). **Behaviour** for lineage with ABP, and because the policy reaches the behaviour rows, not only the capability rows. One collision to say once: in endpoint security, "process behaviour" means detection after the fact; a PBP is prevention before `execve`. File and network behaviour policies are not peer names: they are the `files` and `network` sections of a PBP, or the PBPs of `sharness.fs` and `sharness.net`. Three top-level acronyms would be three schemas and three hashes for one idea.

## 11. What this page does not claim

- Behaviour rows, doors and dialects, the predicate language, composition by intersection and the conformance matrix as a test are **proposed**; the v0 schema, the hash and `hello` are the only runnable parts.
- A PBP never protects against root or a compromised kernel; the kernel is trusted.
- A policy applied by a process to its own children is a Setting for that process; only a launcher above it, not yet code, makes it a Boundary for the process too.
- No product named on the landscape pages has agreed to anything; "valid enforcer" is a test, not an endorsement.

Sources: [twins.sgit.ai](https://twins.sgit.ai) (the twin, the discipline of reality, the naming ruling) and [aws.twin.sgit.ai](https://aws.twin.sgit.ai) (the AWS twin's status, 26 Oct 2026); [Process Behaviour Policies](../policies/index.md) §1 to §6 and §11; [the landscape thesis](../../landscape/index.md); [Agent Behaviour Policies](https://riskmandate.ai/abp.html) and [the four objects](https://abp.sgit.ai/model/index.html); Dinis Cruz's [memo of 24 Oct 2026](../../articles/secure-harness-for-agents.md) and his direction of 25 and 26 Oct 2026 (the policy must go all the way to the business logic; it is the user who defines the policy; harness on harness; the doors as a tree of dotted names, each sitting on its parent; the twin below the dialect, never a dialect); [Hope or enforcement](https://newsroom.sgit.ai/articles/hope-or-enforcement.html) and [Behaviour policies from the checks](https://newsroom.sgit.ai/articles/behaviour-policies-from-the-checks.html) on newsroom.sgit.ai.
