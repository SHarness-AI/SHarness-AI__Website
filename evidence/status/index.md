# What exists today, and what does not

> **The honest column, as of 25 Oct 2026.** SHarness is at the design stage with the first experiments runnable. What exists as running code is listed here and kept apart from the design, so a reader, human or agent, can tell what they can rely on.

## Exists, and can be checked

| Thing | Where to check it |
|---|---|
| **The `sharness-ai` package on PyPI**, v0.1.0: reports its version and prints its help | [pypi.org/project/sharness-ai](https://pypi.org/project/sharness-ai/) |
| **Experiments E01 to E04** (`probe`, `policy hash`, `run`, `hello`), with 34 tests, on the CLI's `dev` branch; unreleased to PyPI | [the code](../../code/index.md) · [experiments/README.md](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/README.md) · E04 measured on [Evidence §9](../index.md#9-the-first-experiments-run-by-the-cli) |
| **Two example policies and a skill** for Claude Code sessions | [Examples](../../code/examples/index.md) |
| **Two browser mockups** that compute and enforce nothing | [the policy hash](../../explain/mockups/policy-hash.html) (the same hash as the CLI) · [the edge matrix](../../explain/mockups/edges.html) |
| **Three storyboards**, data drawn by the storyboards.sgit.ai kit | [Storyboards](../../explain/storyboards/index.md); what they show is the design, not something built |
| **The design, published for review**, with the brief and four drawn diagrams | [The brief](../../design/index.md) · [the source documents, verbatim](../../project/sources/index.md) |
| **Measurements behind the design** | [Evidence](../index.md): one Claude agent workspace, with method and date |
| **This site, its gate and its deploy pipeline** | [SHarness-AI/SHarness-AI__Website](https://github.com/SHarness-AI/SHarness-AI__Website) · [how it is built](../../project/engineering.html) |

## Not here yet

| Missing | Status |
|---|---|
| **Any SHarness component** (launcher, kms, net, fs, bash, llm) | Not built. Designed on [Components](../../design/components/index.md). |
| **A CLI release beyond `--version`** | v0.1.0 on PyPI is the skeleton and the pipeline; the experiments are on `dev`, unreleased ([R7](../../project/comms.html#r7)). |
| **The launcher above the agent** | Not built. Every experiment applies a policy to a child process; nothing yet binds the agent itself. |
| **The process-tree proof of concept** (E06) | Started, not completed, not run. See [Enforcing the process tree](../../design/process-tree/index.md). |
| **seccomp, the `cpu` cgroup, read-only binds** | Available in the measured kernel; not yet applied by the CLI or measured (memory and pids caps are, since 25 Oct 2026). See [Containment](../../design/containment/index.md). |
| **The newsroom's agents' policies** | The second user in the memo; their file and network behaviour policies are not written. |
| **Markdown twins for the hand-written pages** | Every page has a twin except the front page's sections, the mockups and the three project pages (engineering, comms, releases). |
