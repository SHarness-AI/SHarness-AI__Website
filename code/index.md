# The code: where it is and what it does

> **Status: experiments, as of 25 Oct 2026.** The site publishes the design; the code lives in one repository, [SHarness-AI/SHarness-AI__CLI](https://github.com/SHarness-AI/SHarness-AI__CLI), and today it carries the first four experiments, not a component. This page is the map: the package, its modules, the commands, and where each thing on this site has code behind it.

## Where everything is

| What | Where | Status |
|---|---|---|
| the `sharness-ai` package | [`sharness_ai/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/sharness_ai) on the `dev` branch; v0.1.0 on [PyPI](https://pypi.org/project/sharness-ai/) carries only `--version` | runnable from the repository; unreleased |
| the experiments, numbered | [`experiments/README.md`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/README.md) | E01 to E04 runnable; E05 to E08 planned |
| the example policies | [`experiments/policies/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/experiments/policies) | runnable |
| the skill for a Claude Code session | [`.claude/skills/sharness-hello/SKILL.md`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/.claude/skills/sharness-hello/SKILL.md) | runnable |
| the tests | [`tests/unit/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/tests/unit), 29 tests; Landlock tests skip where it is absent | green on 25 Oct 2026 |
| the ground rules for agents working in the repository | [`CLAUDE.md`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/CLAUDE.md) | |
| the release pipeline | [`.github/workflows/workflow.yml`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/.github/workflows/workflow.yml): tests, version bump, tag, PyPI by Trusted Publishing | runs on a push to `main` |
| the browser mockups | this site, [`explain/mockups/`](https://github.com/SHarness-AI/SHarness-AI__Website/tree/dev/explain/mockups): hand-written HTML, no build | published |
| the storyboards' data | this site, [`content/storyboards/`](https://github.com/SHarness-AI/SHarness-AI__Website/tree/dev/content/storyboards) | published |
| this site's build tools | [`tools/`](https://github.com/SHarness-AI/SHarness-AI__Website/tree/dev/tools): the generators and the gate, Python standard library and Node | |

## The package, module by module

Standard library only. Each module is meant to be read in one sitting; the design's size targets are launcher ≤ 400 lines, each component ≤ 300, a shared library ≤ 400.

| Module | Lines | Does | Experiment |
|---|---|---|---|
| `cli.py` | 98 | the argument parser and the dispatch: `probe`, `policy hash`, `policy check`, `run`, `hello` | |
| `probe.py` | 138 | the grant: reads `/proc/self/status`, the Landlock ABI, `memfd_secret`, the namespaces, cgroups, the kernel config, the tools present, the names of proxy variables | E01 |
| `policy.py` | 116 | a v0 policy: load, check the shape, canonicalise (sorted keys, no whitespace, integers only), hash | E02 |
| `landlock.py` | 157 | Landlock through `ctypes`: the ABI, a ruleset, path rules, port rules, `restrict_self` | E03 |
| `run.py` | 133 | fork, apply the policy in the child (network namespace, `no_new_privs`, Landlock), exec; `--expect-hash` | E03 |
| `hello.py` | 118 | the acceptance test: a deny-all policy for the running interpreter, five probes, the caveat | E04 |
| `_version.py` | 17 | the version, read from the file CI maintains | |

Counts from `wc -l` on 25 Oct 2026. How a command moves through these modules is on [Flows](flows/index.md).

## The commands

```
sharness-ai probe [--json]                                E01  the grant
sharness-ai policy hash|check FILE                        E02  the one value the person supplies
sharness-ai run --policy FILE [--expect-hash H] -- CMD…   E03  one command under a policy
sharness-ai hello [--json]                                E04  the acceptance test, one child process
```

Install and use: [The CLI](cli/index.md). Each command's output and caveats: [Examples](examples/index.md). What each shows and does not show: [Mockups and experiments](experiments/index.md).

## What has code behind it, and what does not

| On this site | Code | Where |
|---|---|---|
| the v0 Process Behaviour Policy and its hash | yes | `policy.py`; the [browser mockup](../explain/mockups/policy-hash.html) reproduces it |
| Landlock file, exec and port rules; `network: "none"` | yes | `landlock.py`, `run.py` |
| the grant and the delta | yes | `probe.py` |
| the memo's acceptance test | yes, for one child process | `hello.py` |
| the launcher, `sharness.kms`, `.net`, `.fs`, `.bash`, `.llm` | **no** | designed on [Components](../design/components/index.md); E05 to E08 are the next pieces |
| mutual TLS with a session CA; the edge matrix | measured by hand, not yet a command | E05 |
| seccomp, cgroups, scoping, the execute allowlist | **no** | [Containment](../design/containment/index.md) says which rows are designed |

## Next in the code, in order

The [research note](../evidence/research/index.md#4-what-is-still-open-in-the-order-to-take-it) sets the order: the memory and pids caps in `run` (one row of [Containment](../design/containment/index.md) moves to measured), then E06 (the process tree), E05 (the edges as a script), E08 (`sharness.kms` v0) before E07 (`sharness.llm` v0), then the launcher as a script above the agent on a laptop. The languages for each are on [Languages](languages/index.md).
