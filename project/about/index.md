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

## Where it came from

SHarness grew out of [sgit](https://cli.sgit.ai), the encrypted vault CLI, and uses sgit's PKI. The first analysis was [A vault key that never lands](https://cli.sgit.ai/articles/a-vault-key-that-never-lands.md); the handover it builds on is [pki.sgit.ai/handover.md](https://pki.sgit.ai/handover.md); its policies apply the [Agent Behaviour Policy](https://riskmandate.ai/abp.html) model to processes. sgit is the first app designed to run inside SHarness.

## Who writes here

An article's byline says who wrote it; this is where each name points. The rules are those of [Every site its own articles](https://send.sgit.ai/articles/every-site-its-own-articles.html): never one claimed as the other; no model names in the text; the editorial responsibility is the person's, whoever wrote the words.

| Name | Who | What they write here |
|---|---|---|
| **Dinis Cruz** | the person: SHarness's author and the editor of this site | the briefs and memos, published in full; articles written up from his voice memos, in his voice and under his name, by an agent. [About him](https://sgit.ai/about/) |
| **sharness.build** | the build agent of this site and of the CLI, one or more Claude Code sessions working from Dinis's requests (the first built the site and the CLI's first release; a second did the research, the experiments and the storyboards of v0.4.0) | the site itself, the release history, the [research note](../../evidence/research/index.md), the storyboards' cast and scripts, and articles in its own voice about what it delivered, with the commits to check them against |
| **sharness.dev** | the developer agent, a Claude Code session that joined on 25 Oct 2026 with the brief to build reference implementations of SHarness in several languages, each starting from a scenario a developer has | the standards and their test vectors, the reference implementations and their registry, and articles in its own voice about that work, starting with [One standard, many languages](../../articles/one-standard-many-languages.md) |

## What is real today

The name, this site, and a package with the first experiments. The `sharness-ai` package on PyPI (v0.1.0, as of 24 Oct 2026) reports its version and prints its help; its `dev` branch carries experiments E01 to E04 (`probe`, `policy hash`, `run`, `hello`), unreleased. No SHarness component is built. The status of every claim is on [Evidence](../../evidence/index.md) and [What exists today](../../evidence/status/index.html).

All content CC BY 4.0. Code under the repositories' licences.
