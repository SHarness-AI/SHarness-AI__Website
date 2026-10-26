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

**The names are a tree: `sharness.<door>.<target>`.** Dinis Cruz's rule of 26 Oct 2026. The first name is the door whose rows it holds and whose nouns it speaks: `fs` is paths, operations and content whatever the storage; `net` is hosts, ports and endpoints; `db` is tables, rows and values; `llm` is the model, its tools and its tokens; `bash` and `kms`. The second name is the **target**: where the door sends what it holds. **The door alone is the API, never a target**: `sharness.fs` is the vocabulary and the request schema, and every leaf names where it sends. For `fs`: `.disk` (the local disk as storage, the one target the kernel also bounds, with Landlock), `.s3`, `.azure`, a vault. For `net`: `.direct` (the kernel's socket to the internet), `.proxy` (an upstream proxy: Zscaler, Cloudflare, the proxy an agent session already runs behind), or another harness's `net` on another machine. For `db`: `.sqlite` (the local file), `.postgres`, `.mysql`, `.mongo`, `.neo4j`. So `sharness.fs.s3`, not `net.s3`: S3 is where the file system's writes go; the transport it uses is an edge (`fs.s3` reaches S3 through `net`), not its name. Read from above, the dot means **sits on**: the parent closes every other path, so the child's only way to the world is through it. Read from below, it means **sends to**. Depth is open (`sharness.net.http.gmail`), and a level earns a name only when it adds nouns its parent cannot see; otherwise it is configuration of the parent. A door whose rows name two parents goes under the one whose nouns dominate, with an edge to the other: git's rows are remote, branch, ref and the push, the irreversible step and a network act, so `sharness.net.git`, with an edge to `fs` for the working tree; every tool call passes through the model door, so `sharness.llm.tools`.

**Three trees are one.** The architecture already puts the role in the certificate's SAN URI and chains policies by parent hash. With dotted names the name tree, the identity tree (`spiffe://<session>/fs/s3`) and the policy tree (`extends`, composed by intersection) are the same tree, and so is the code tree: `sharness_ai.fs` is the door's interface module, `sharness_ai.fs.disk` and `sharness_ai.fs.s3` its implementations and the twin a sibling, in the CLI for now, a distribution of its own (`sharness-ai-fs-s3`) when a target leaves it, the component size target per target. That is what lets a target run on another machine, in another language, from another vendor, and still be addressed, authenticated and bounded by one path. The cost is one process per name: a mutual TLS handshake between two local processes measured about 3.2 ms (24 Oct 2026), and it stops mattering when the target is remote.

**Every target has the signature of the real thing, and there are three kinds of it.** The *real system* (S3, Postgres, the internet). A *relay*, which forwards to a real system and may be a chain: a laptop's `net` to a server's `net` to an enterprise proxy to the internet is the fractal as a chain of relays with one signature. A *twin*, which terminates and behaves like the end state ([twins.sgit.ai](https://twins.sgit.ai): an interface to a real thing with a swappable backend, vault, disk, memory or live, valued for whether it is connected). The door's code is the same for all three; the name says which. **`.twin` is a terminal suffix on any name**, Dinis Cruz's rule of 26 Oct 2026: it means the thing named before it is now running as a simulation of what is on the other side. `sharness.fs.s3.twin` is the S3 target simulated ([the AWS twin](https://aws.twin.sgit.ai) answers S3's REST-XML with boto3 unchanged, as of 26 Oct 2026); `sharness.db.postgres.twin`; `sharness.net.direct.twin`, the internet recorded and replayed; `sharness.fs.disk.twin`, the local disk simulated, memory-backed by default. The suffix attaches to a target, so `sharness.fs.twin` is not a name: a door alone is an API, and an API has no other side to simulate. The twin's own backend (memory, a vault, record and replay) is its configuration below the suffix, not a name in the tree. The door above does not know, because the twin accepts the real thing's API (the mirror rule, below), and it carries the code a twin needs to replicate enough end state to be indistinguishable. Because the name is in the policy, a twin run hashes differently from a live run, and the manifest says so in plain text: `sharness.db.postgres.twin` in the invocation layer reads as a development world without decoding anything. The twins site's naming ruling holds here: a twin holds no credentials; the door (their execution broker) holds credentials and enforces. That broker's two open costs, that holding credentials makes it a target and that enforcement needs one interpreter per provider and capability, are what `kms` and the tree of targets answer.

**Development and production are one policy tree with different target rows.** The vendor ships a door and its rows once. The invocation layer names the targets: in development, `fs.disk.twin`, `db.sqlite` and `fs.s3.twin`; in production, `fs.disk`, `db.postgres` and `fs.s3`. Same code, same vendor rows, two hashes, and the hash of a run says which world it ran in. Connectedness is read off the policy (a door's `hello` prints its targets and `twin` or `live` for each), never guessed afterwards; every door's conformance suite runs against twins before it touches a real system; and a twin is itself a process under its own PBP, reached only through `net`.

**Two schemas per door, and the mirror rule.** Every door is a service, so it declares what it **accepts** (its API, which is also the vocabulary its rows are written in) and what it **emits** (the calls it makes downstream). A chain is valid when what hop N emits is accepted by hop N+1; the manifest's edge list already names the hops, so each edge carries a contract and the launcher checks it by hash before anything starts. This is why the [enforceability matrix](../../landscape/enforceability/index.md) comes out the way it does: a hop can hold a row only in the nouns of what it accepts. `net` accepts TCP and `CONNECT`, so it cannot hold a URL row; `net.http` accepts HTTP, so it can; each hop lowers the abstraction one step toward the kernel. A twin is a process whose accepts equals the real thing's API and whose emits is empty, or goes to its backend. One process may implement several hops, and the cost is exact: the barrier between fused hops becomes an Expectation, because they are one process, and the fused process's reach is the union of theirs. So split where the domain changes (a different credential or trust), where the language changes, or where the machine changes; never fuse across `kms`; fuse freely inside one trust domain when the service count hurts. The shape already exists in several places, none of which states the rule: [`sharness.net`](../../components/net/index.md) accepts two inbound schemas (`CONNECT` on the proxy port; `POST /v0/fetch` by value) and emits TLS to the host; the [KMS protocol](../keys/index.md) is a mirror API written as request and response bodies (`init`, `public`, `unwrap`, `seal_to`, `destroy`), what `net` emits being what `kms` accepts, and [topologies D and E](../architecture/index.md#deployment-topologies) chain it to a cloud function and a cloud KMS under the same contract; the playground's interceptor is a relay with a veto; an agent session itself runs behind an upstream proxy; and the twins' S3 container is the production example, one S3 face over a vault, disk, memory or real S3, switched "per environment" at the cost of an endpoint, stacked as "the twin-of-a-twin structure made concrete" ([twins.sgit.ai/built](https://twins.sgit.ai/built/index.html), read 26 Oct 2026).

**A target holds its rows in one of two modes.** *Proxy*: the door is the only path; the app sends structured requests (`select` table, columns, filter), never a query string, and the door holds the rows. *Translate*: the system enforces natively and the door holds only the credential and checks the configuration against the hash (Postgres row-level security, grants and views; a bucket policy). Each target is a row of the [enforceability matrix](../../landscape/enforceability/index.md). One rule keeps a door small: **never parse SQL or Cypher in the door**; structured requests in, or native enforcement.

**The roster, all proposed, none built:**

| Door | Its nouns | Targets first | Later |
|---|---|---|---|
| `sharness.fs` | path, operation, content | `.disk`, `.disk.twin`, `.s3`, `.s3.twin` | `.azure`, a vault |
| `sharness.net` | host, port, endpoint, id | `.direct`, `.direct.twin`, `.proxy`, `.http` (method, host, path pattern, headers, body schema, response size), `.git` (remote, branch, ref, push; never force, never main), `.smtp` | `.ftp`, `.http.gmail`, `.http.slack` |
| `sharness.db` | table or collection or label, row, column, value, count, total per interval | `.sqlite` (the first: the `sqlite3` module is in Python's standard library, so it is buildable under the no-dependency rule and would be the first door that is runnable), `.postgres` (translate: row-level security), `.postgres.twin` | `.mysql`, `.mongo`, `.neo4j`, `.redshift` |
| `sharness.llm` | model, tool list, tokens | `.tools` (tool name, argument predicates, calls per run: where "refund at most 100" lives for a tool that is not a database) | |
| `sharness.bash`, `sharness.kms` | command, profile; key id, operation | none yet | |

A door earns a name when it has nouns the door below cannot see, it can be the only path to the resource, and at least one target holds its rows as a Boundary. Anything else is configuration of an existing door. Not a door: a guardrail that judges intent on an allowed channel, which a kernel bound cannot do; the [landscape](../../landscape/index.md) says to consume such decisions at `llm`, not to build one.

> **Corrected a third time, 26 Oct 2026.** Site v0.5.32 to v0.5.40 said the undecorated door is the local one (`sharness.fs` the disk, `sharness.net` direct). Dinis Cruz's question: is there a `sharness.fs.disk`? Yes: the door alone is the API, every leaf is a target, so `fs.disk`, `fs.disk.twin`, `net.direct`, `net.direct.twin`. Withdrawn above. The paragraph "Three trees are one", dropped by mistake in v0.5.32's rewrite, is back.
>
> **Corrected again, 26 Oct 2026.** Site v0.5.32 to v0.5.38 said there is no `sharness.fs.twin` and put `.memory` in the tree as a target. Dinis Cruz's rule: `.twin` is a terminal suffix on any name, meaning the thing named before it runs as a simulation of what is on the other side; memory is a twin's backend, not a name. Withdrawn above. (v0.5.38 announced this change and carried only its version bump: a release script run after a failed edit, pbp's mistake.)
>
> **Corrected 26 Oct 2026, the same day.** Site v0.5.30 and v0.5.31 called the second level a *dialect* (a protocol) and said the twin had no place in the tree, only as an endpoint in a policy row. Dinis Cruz's correction: the second level is the *target*, where the door sends, and a twin is a target in its own right when it is the storage (`fs.memory`), with the real thing's signature and the code that needs. The endpoint reading was half of it and is kept above. "Dialect" is withdrawn.

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

How a person meets all of this without reading it is [the levels](../levels/index.md): six levels of one policy, each written in its own nouns and compiled into the one below, the simplest as binding as the deepest. Proposed, 26 Oct 2026.

### The two numbers

ABP's number is **unbounded excess**: reach nobody asked for and nothing bounds. A PBP adds a second: **unheld rows**, the mandate rows no Boundary holds. `hello` reports probes held; the policy summary should report rows held by the kernel, rows held by a door, and rows unheld, the way the newsroom counted its checks (1 boundary, 34 settings, 22 expectations). The second number is the business case for the next door.

## 10. Naming

**Process** because the process is the unit the kernel enforces on, the unit of the layers, and the word in ABP's lexicon (`execute.process.host`). **Behaviour** for lineage with ABP, and because the policy reaches the behaviour rows, not only the capability rows. One collision to say once: in endpoint security, "process behaviour" means detection after the fact; a PBP is prevention before `execve`. File and network behaviour policies are not peer names: they are the `files` and `network` sections of a PBP, or the PBPs of `sharness.fs` and `sharness.net`. Three top-level acronyms would be three schemas and three hashes for one idea.

## 11. What this page does not claim

- Behaviour rows, doors and targets, the predicate language, composition by intersection and the conformance matrix as a test are **proposed**; the v0 schema, the hash and `hello` are the only runnable parts.
- A PBP never protects against root or a compromised kernel; the kernel is trusted.
- A policy applied by a process to its own children is a Setting for that process; only a launcher above it, not yet code, makes it a Boundary for the process too.
- No product named on the landscape pages has agreed to anything; "valid enforcer" is a test, not an endorsement.

Sources: [twins.sgit.ai](https://twins.sgit.ai) (the twin, the discipline of reality, the naming ruling) and [aws.twin.sgit.ai](https://aws.twin.sgit.ai) (the AWS twin's status, 26 Oct 2026); [Process Behaviour Policies](../policies/index.md) §1 to §6 and §11; [the landscape thesis](../../landscape/index.md); [Agent Behaviour Policies](https://riskmandate.ai/abp.html) and [the four objects](https://abp.sgit.ai/model/index.html); Dinis Cruz's [memo of 24 Oct 2026](../../articles/secure-harness-for-agents.md) and his direction of 25 and 26 Oct 2026 (the policy must go all the way to the business logic; it is the user who defines the policy; harness on harness; the doors as a tree of dotted names, `sharness.<door>.<target>`, the target being where the door sends; `.twin` as the terminal suffix that means simulated; two schemas per door and the mirror rule); [Hope or enforcement](https://newsroom.sgit.ai/articles/hope-or-enforcement.html) and [Behaviour policies from the checks](https://newsroom.sgit.ai/articles/behaviour-policies-from-the-checks.html) on newsroom.sgit.ai.
