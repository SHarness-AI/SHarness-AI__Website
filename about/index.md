# About and naming

**By Dinis Cruz.** Design session written up with Claude, 24 October 2026.

> **SHarness is unrelated to Sharness, the shell testing library** derived from Git's test suite (felipec/sharness).

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

## What is real today

Only the name, this site and a placeholder package. The `sharness-ai` package on PyPI reports its version and prints its help; nothing in the design is built yet. The status of every claim is on [Evidence](../evidence/index.md) and [What exists today](../shipped/index.html).

All content CC BY 4.0. Code under the repositories' licences.
