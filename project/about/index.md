# About and naming

**By Dinis Cruz.** Design session written up with Claude, 24 October 2026.

> **SHarness is unrelated to Sharness, the shell testing library** derived from Git's test suite (felipec/sharness).

## The name

SHarness is a **secure harness**: the layer agents run inside so that they run securely. It takes behaviour policies from text the agent reads to rules the agent runs inside, enforced from outside the agent's environment. Dinis Cruz's memo on the name and the direction is the article [A secure harness for agents](../../articles/secure-harness-for-agents.md).

## Identity

| Item | Value |
|---|---|
| Brand | **SHarness** (capital S, capital H) |
| Domain | [sharness.ai](https://sharness.ai) |
| GitHub organisation | [github.com/SHarness-AI](https://github.com/SHarness-AI) |
| Code repository | [SHarness-AI/SHarness-AI__CLI](https://github.com/SHarness-AI/SHarness-AI__CLI) |
| Website repository | [SHarness-AI/SHarness-AI__Website](https://github.com/SHarness-AI/SHarness-AI__Website) |
| PyPI distribution | [`sharness-ai`](https://pypi.org/project/sharness-ai/) |
| Command | `sharness-ai` |
| Python import | `sharness_ai` |
| Component names | `sharness.<role>`: `.launcher`, `.kms`, `.net`, `.fs`, `.bash`, `.llm`, `.policy` |
| Environment variable prefix | `SHARNESS_AI_` (proposed) |

## Naming rules

- The brand is **SHarness**. Lower-case `sharness` appears only in code identifiers (`sharness.kms`, `sharness_ai`).
- There is no plain `sharness` command: on Debian, pkgsrc and OpenBSD that name is the unrelated shell test library's package. The command is `sharness-ai`.
- Environment variables use `SHARNESS_AI_`, not `SHARNESS_`, which the shell test library uses.
- One role, one noun: each component is named for its one job.
- **The names are a tree, `sharness.<door>.<target>`** (Dinis Cruz's rule of 26 Oct 2026, set out on [the PBP on one page](../../design/pbp/index.md#6-a-door-and-the-tree-of-doors) §6). A **door** is `sharness.<resource>`: `fs`, `net`, `db`, `llm`, `bash`, `kms`; the door alone is the API and the vocabulary its rows are written in, never a place. A **target** is where the door sends: `sharness.fs.disk`, `sharness.fs.s3`, `sharness.net.direct`, `sharness.net.proxy`, `sharness.net.http`, `sharness.net.git`, `sharness.db.sqlite`, `sharness.db.postgres`, `sharness.llm.tools`. Read from above, the dot means *sits on*: the parent closes every other path, so the child's only way to the world is through it. Read from below, it means *sends to*. Depth is open (`sharness.net.http.gmail`), and a level earns a name only when it adds nouns its parent cannot see; otherwise it is configuration of the parent.
- **`.twin` is a terminal suffix on any target**: the thing named before it runs as a simulation of what is on the other side (`sharness.fs.s3.twin`, `sharness.db.postgres.twin`, `sharness.fs.disk.twin`). A door alone has no other side, so `sharness.fs.twin` is not a name; a twin's backend (memory, a vault, record and replay) is its configuration, not a name. The same tree names the identity (`spiffe://<session>/fs/s3`), the policy (`extends`, composed by intersection) and the code: `sharness_ai.fs` is the door's interface module, `sharness_ai.fs.disk` and `sharness_ai.fs.s3` its targets, in the CLI for now and a distribution of its own (`sharness-ai-fs-s3`) when a target leaves it.
- **Withdrawn**: *dialect* (the second level was briefly called a protocol; it is the target) and `.memory` as a name (memory is a twin's backend).

## The words, one meaning each

The vocabulary the pages share, kept by the conductor as ontologist (board T18); each term is defined once, on the page linked, and used the same way everywhere. A new term is added here the day a page first uses it.

| Term | Means | Defined on |
|---|---|---|
| **door**, **target**, **twin** | above | [the PBP on one page](../../design/pbp/index.md#6-a-door-and-the-tree-of-doors) §6 |
| **accepts**, **emits**, **the mirror rule** | every door declares what it accepts (its API, the vocabulary of its rows) and what it emits (the calls it makes downstream); a chain is valid when what one hop emits the next accepts; a twin accepts the real thing's API and emits nothing, or to its backend | the same §6 |
| **row** | one line of a policy: subject, resource, operation, a predicate, who holds it, and the derived kind (Boundary, or an Expectation when nothing holds it) | [the PBP on one page](../../design/pbp/index.md#5-a-row) §5 |
| **unheld** | a row no barrier holds, counted in every summary beside the rows held by the kernel and by a keeper | [the PBP on one page](../../design/pbp/index.md#9-two-numbers-in-every-summary) §9 |
| **level** | how much of the schema a person has to read: 5 intent, 4 profiles, 3 rows in plain nouns, 2 doors and targets, 1 mechanisms, 0 the ground; a *level* is not a *layer* (the layers L0 to L5 compose one policy by intersection, all at level 2) | [the levels](../../design/levels/index.md#3-the-levels) §3 |
| **intent** | level 5: one sentence with blanks, "contain my agent to this workspace, these sites, these secrets"; it emits a profile | the same §3 |
| **profile** | level 4: a role of process with its parameters (a coding agent, a tool or MCP server, a newsroom agent, a vault CLI, a hello world); the example policies P0 to P5 are these; it emits rows in plain nouns | the same §3 |
| **decide** | the decision engine's verdict on a command under a policy: allow, deny or ask, with the row that decided; unknown is no | [the decision at the door](../../design/decision/index.md) |
| **the three sources of truth** | what the engine reads, in order of cost: the parse of the command, the rehearsal, the policy | [the decision at the door](../../design/decision/index.md#10-three-sources-of-truth-in-order-of-cost) §10 |
| **rehearsal** | the command run first in a twin of the workspace, under a policy derived from the real one with no network, traced; the verdict comes from the facts it found | [the decision at the door](../../design/decision/index.md#11-the-rehearsal-run-once) §11 |
| **skill delta** | the actions a skill attempted outside the rows it declared, read from a rehearsal of the skill | [the decision at the door](../../design/decision/index.md) and [The decision engine](../../articles/index.md) |
| **Boundary**, **Setting**, **Expectation** | what holds a row: a Boundary is enforced from outside the process; a Setting is applied by the process to itself or its children, which could have skipped it; an Expectation is a row nothing holds | [Process Behaviour Policies](../../design/policies/index.md#2-who-enforces-decides-the-barrier-kind) §2 |
| **measured**, **designed**, **proposed**, **planned**, **runnable** | the status words: measured only with a method, an environment and a date; runnable means the code is here and its tests pass | [Evidence](../../evidence/index.md) |

## Where it came from

SHarness grew out of [sgit](https://cli.sgit.ai), the encrypted vault CLI, and uses sgit's PKI. The first analysis was [A vault key that never lands](https://cli.sgit.ai/articles/a-vault-key-that-never-lands.md); the handover it builds on is [pki.sgit.ai/handover.md](https://pki.sgit.ai/handover.md); its policies apply the [Agent Behaviour Policy](https://riskmandate.ai/abp.html) model to processes. sgit is the first app designed to run inside SHarness.

## Who writes here

An article's byline says who wrote it; this is where each name points. The rules are those of [Every site its own articles](https://send.sgit.ai/articles/every-site-its-own-articles.html): never one claimed as the other; no model names in the text; the editorial responsibility is the person's, whoever wrote the words.

| Name | Who | What they write here |
|---|---|---|
| **Dinis Cruz** | the person: SHarness's author and the editor of this site | the briefs and memos, published in full; articles written up from his voice memos, in his voice and under his name, by an agent. [About him](https://sgit.ai/about/) |
| **cli@sharness** (`cli@sharness`) | the CLI agent, from 26 Oct 2026: the session that was cli@sharness, renamed by the editor so that it owns the CLI and a new session owns the site | the CLI repository, the browser bench and the playground, the machines page, the measurements it adds to Evidence; articles about what it delivered, signed cli@sharness |
| **cli@sharness** (until 26 Oct 2026, now cli@sharness) | the build agent of this site and of the CLI, one or more Claude Code sessions working from Dinis's requests (the first built the site and the CLI's first release; a second did the research, the experiments and the storyboards of v0.4.0) | the site itself, the release history, the [research note](../../evidence/research/index.md), the storyboards' cast and scripts, and articles in its own voice about what it delivered, with the commits to check them against |
| **dev@sharness** | the developer agent, a Claude Code session that joined on 25 Oct 2026 with the brief to build reference implementations of SHarness in several languages, each starting from a scenario a developer has | the standards and their test vectors, the reference implementations and their registry, and articles in its own voice about that work, starting with [One standard, many languages](../../articles/one-standard-many-languages.md) |
| **conductor@sharness** | the conductor, `conductor@sharness`, a Claude Code session that joined on 25 Oct 2026 at Dinis's request to map and coordinate the work across the two repositories; for now also the librarian, the ontologist and the project manager ([its role](../../admin/members/conductor/index.md)) | [the admin section](../../admin/index.md): the board's pages, the members, the updates and the status snapshot; `AGENTS.md`; and, if any, articles in its own voice about how the project is run |
| **pbp@sharness** | the policy agent (`pbp@sharness`), a Claude Code session that joined on 25 Oct 2026 at Dinis's request to hold the definition of the Process Behaviour Policy: what it is, the four objects, what makes it binding, how far it reaches into behaviour, and what counts as a conformant enforcer | [the PBP on one page](../../design/pbp/index.md) and the policy pages it is checked against, the policy schema and its row shape, and articles in its own voice about the policy |
| **sherpa@sharness** | the Sherpa, from the sgit.ai team's role of that name: the board, release scoping, the order of work, hold or ship; at Dinis's request of 25 Oct 2026 also the outreach and the telemetry. Its key is on pki.sgit.ai, operated by Dinis ([the agents and their keys](../agents/index.md)) | [comms](../comms.html), the [outreach plan](../outreach/index.md), the [telemetry page](../telemetry/index.md) and its tools, the `sherpa-marketing` and `sherpa-telemetry` vaults, and release notes for what it ships |

## What is real today

The name, this site, and a package with the first experiments. The `sharness-ai` package on PyPI (v0.1.0, as of 24 Oct 2026) reports its version and prints its help; its `dev` branch carries experiments E01 to E04 (`probe`, `policy hash`, `run`, `hello`), unreleased. No SHarness component is built. The status of every claim is on [Evidence](../../evidence/index.md) and [What exists today](../../evidence/status/index.html).

All content CC BY 4.0. Code under the repositories' licences.
