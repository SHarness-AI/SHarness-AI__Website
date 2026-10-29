# What exists today, and what does not

> **The honest column, as of 28 Oct 2026.** SHarness is at the design stage with the first experiments runnable, and three MVPs: the levels in the terminal; the first door, `sharness.fs`, a Setting until the launcher exists; and the network door with a shell under the harness, `sharness-ai shell`, the launcher's first slice. What exists as running code is listed here and kept apart from the design, so a reader, human or agent, can tell what they can rely on.

## Exists, and can be checked

| Thing | Where to check it |
|---|---|
| **The `sharness-ai` package on PyPI**, v0.1.0: reports its version and prints its help | [pypi.org/project/sharness-ai](https://pypi.org/project/sharness-ai/) |
| **Experiments E01 to E04, E09 and E10** (and E11 to E13, the three MVPs below; `probe`, `policy hash`, `run`, `hello`, the harness under a second kernel in Node, in a browser tab and through chroot, `policy translate`), with the CLI's tests (229 on 28 Oct 2026) run in CI on Python 3.11 to 3.13 on every push to the CLI's `dev` branch; unreleased to PyPI | [the code](../../code/index.md) · [experiments/README.md](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/README.md) · E04 and E09 measured on [Evidence §9](../index.md#9-the-first-experiments-run-by-the-cli) |
| **MVP 1, the levels in the terminal**: `contain` (a sentence), `profile` (six profiles with blanks), `explain` (any document down to the kernel, one hash per level), with vectors per level; on the CLI's `dev` | [The CLI §MVP 1](../../code/cli/index.md#mvp-1-the-levels-in-the-terminal) · [the levels](../../design/levels/index.md) |
| **MVP 2, the first door, `sharness.fs`**: the door kit (session CA by openssl, mutual TLS 1.3, contracts, rows, verdicts, audit) over the disk and its twin, 18 conformance vectors; a Setting for the app until the launcher gives it its own uid; known issues, three of five fixed by 28 Oct 2026 | [sharness.fs](../../components/fs/index.md) · [the issues](../../components/fs/index.md#5-known-issues-as-of-28-oct-2026) |
| **MVP 3, the network door and a shell under the harness (E13)**: `sharness-ai net serve` (an allowlisting proxy for one uid), `sharness-ai shell` (a unique user, the door, a policy whose only network row is the proxy's port); a Boundary for that shell where run as root, a Setting otherwise; checked by website@ on 28 Oct 2026 | [sharness.net](../../components/net/index.md) · [sharness.launcher](../../components/launcher/index.md) |
| **A real Linux kernel in a tab** running `probe`, `hello` and `run`: the E09 page | [open it](../../code/browser/demo/index.html) · [the write-up](../../code/browser/index.md) · [the article](../../articles/linux-in-a-tab.md) |
| **The playground**: `pip install sharness-ai` in Pyodide, a shell on the Linux guest on a network the page provides, one policy hashed three ways, and an interceptor that decodes every packet and vetoes hosts outside an allowlist | [open it](../../code/playground/index.html) |
| **Seven example policies** (two minimal, five profiles P0 to P4 from a hello world to sgit) **and a skill** for Claude Code sessions | [the policies](../../code/experiments/index.md#the-example-policies) · [Examples](../../code/examples/index.md) |
| **Two browser mockups** that compute and enforce nothing | [the policy hash](../../explain/mockups/policy-hash.html) (the same hash as the CLI) · [the edge matrix](../../explain/mockups/edges.html) |
| **Three storyboards**, data drawn by the storyboards.sgit.ai kit | [Storyboards](../../explain/storyboards/index.md); what they show is the design, not something built |
| **The design, published for review**, with the brief and four drawn diagrams | [The brief](../../design/index.md) · [the source documents, verbatim](../../project/sources/index.md) |
| **Measurements behind the design** | [Evidence](../index.md): one Claude agent workspace, with method and date |
| **This site, its gate and its deploy pipeline** | [SHarness-AI/SHarness-AI__Website](https://github.com/SHarness-AI/SHarness-AI__Website) · [how it is built](../../project/engineering.html) |

## Not here yet

| Missing | Status |
|---|---|
| **Any SHarness component but `sharness.fs`, `sharness.net` and the launcher's first slice** (kms, bash, llm; the launcher's manifest) | Not built. Designed on [Components](../../design/components/index.md). `sharness.fs` runs as an MVP, a Setting, until the launcher gives it its own uid; `sharness.net` is a Boundary only for the shell `sharness-ai shell` starts. |
| **A CLI release beyond `--version`** | v0.1.0 on PyPI is the skeleton and the pipeline; the experiments are on `dev`, unreleased ([R7](../../project/comms.html#r7)). |
| **The launcher above the agent** | Not built. Every experiment applies a policy to a child process; nothing yet binds the agent itself. |
| **The process-tree proof of concept** (E06) | Started, not completed, not run. See [Enforcing the process tree](../../design/process-tree/index.md). |
| **seccomp, the `cpu` cgroup, read-only binds** | Available in the measured kernel; not yet applied by the CLI or measured (memory and pids caps are, since 25 Oct 2026). See [Containment](../../design/containment/index.md). |
| **The newsroom's agents' policies** | The second user in the memo. First drafts exist in the v0 shape (P3 the newsroom agent, P4 sgit, [here](../../code/experiments/index.md#the-example-policies)); hosts, uids and signing are not in v0. |
| **Markdown twins for the hand-written pages** | Every page has a twin except the front page's sections, the mockups and the three project pages (engineering, comms, releases). |
