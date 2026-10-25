# The code: where it is and what it does

> **Status: experiments, as of 25 Oct 2026.** The site publishes the design; the code lives in one repository, [SHarness-AI/SHarness-AI__CLI](https://github.com/SHarness-AI/SHarness-AI__CLI), and today it carries experiments, not a component. This page is the map: the package, its modules, the commands, and where each thing on this site has code behind it.

## Where everything is

| What | Where | Status |
|---|---|---|
| the `sharness-ai` package | [`sharness_ai/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/sharness_ai) on the `dev` branch; v0.1.0 on [PyPI](https://pypi.org/project/sharness-ai/) carries only `--version` | runnable from the repository; unreleased |
| the experiments, numbered | [`experiments/README.md`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/README.md) | E01 to E04, E09 and E10 runnable; E05 to E08 planned |
| the example policies: two minimal, five profiles P0 to P4 | [`experiments/policies/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/experiments/policies) | runnable; run natively 25 Oct 2026 |
| the playground: `sharness-ai` in Pyodide and in a shell on the Linux guest | [`experiments/browser/playground.js`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/browser/playground.js), one ES module; served on this site at [code/playground](playground/index.html); `test_playground.mjs` drives both tabs | runnable; 11 of 11 checks 25 Oct 2026 |
| E09, the harness under a second kernel: the guest build, the Node and browser runners, the chroot form | [`experiments/browser/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/experiments/browser): `build_guest.py` (standard library), `init.sh`, `page.html`, `boot_node.mjs`, `boot_browser.mjs`, `chroot_native.sh`; v86 pinned in its own `package.json` | runnable; measured 25 Oct 2026 ([Linux in the browser](browser/index.md)) |
| the skill for a Claude Code session | [`.claude/skills/sharness-hello/SKILL.md`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/.claude/skills/sharness-hello/SKILL.md) | runnable |
| the tests | [`tests/unit/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/tests/unit), 92 tests (32 of them the security tests that pin each finding of the 25 Oct 2026 review), run on every push to `dev` by `tests.yml` on Python 3.11, 3.12 and 3.13; Landlock tests skip where it is absent | green on 25 Oct 2026 |
| the ground rules for agents working in the repository | [`CLAUDE.md`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/CLAUDE.md) | |
| the code published on this site at immutable paths, with a manifest of hashes and a `latest` | [`code/releases/`](releases/index.md): `releases.json`, `latest.json`, `vN/vN.M/vN.M.P/`, `dev/`; `tools/releases.py` cuts and checks them | v0.1.0 and the dev snapshot, 25 Oct 2026 |
| the release pipeline | [`.github/workflows/workflow.yml`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/.github/workflows/workflow.yml): tests, version bump, tag, PyPI by Trusted Publishing | runs on a push to `main` |
| the browser mockups | this site, [`explain/mockups/`](https://github.com/SHarness-AI/SHarness-AI__Website/tree/dev/explain/mockups): hand-written HTML, no build | published |
| the storyboards' data | this site, [`content/storyboards/`](https://github.com/SHarness-AI/SHarness-AI__Website/tree/dev/content/storyboards) | published |
| this site's build tools | [`tools/`](https://github.com/SHarness-AI/SHarness-AI__Website/tree/dev/tools): the generators and the gate, Python standard library and Node | |

## The package, module by module

Standard library only. Each module is meant to be read in one sitting; the design's size targets are launcher ≤ 400 lines, each component ≤ 300, a shared library ≤ 400.

| Module | Lines | Does | Experiment |
|---|---|---|---|
| `cli.py` | 133 | the argument parser and the dispatch: `probe`, `policy hash`, `policy check`, `run`, `hello` | |
| `probe.py` | 147 | the grant: reads `/proc/self/status`, the Landlock ABI, `memfd_secret`, the namespaces, cgroups, the kernel config, the tools present, the names of proxy variables | E01 |
| `policy.py` | 234 | a v0 policy: load (no duplicate keys, no oversized file), check the shape (normalised printable paths, the caps, integers JavaScript keeps exact), canonicalise, hash, advise | E02 |
| `translate.py` | 187 | the policy as bubblewrap, `docker run`, a Claude Code sandbox `settings.json`, a Kubernetes Pod and NetworkPolicy; each with what it does not enforce | E10 |
| `landlock.py` | 174 | Landlock through `ctypes`: the ABI, a ruleset, path rules, port rules, `restrict_self` | E03 |
| `run.py` | 251 | fork, close inherited descriptors, apply the policy in the child (network namespace, caps, `no_new_privs`, Landlock with write never executable), exec; `--expect-hash`; refuses a row it cannot enforce and a writable symlink; says what is not covered | E03 |
| `limits.py` | 124 | the caps: `RLIMIT_AS` and `RLIMIT_NPROC`, and a memory and pids cgroup (v1 or v2) where `/sys/fs/cgroup` is writable | E03 |
| `hello.py` | 170 | the acceptance test: a deny-all policy for the running interpreter with a 128 MiB cap, six probes with a control for ambiguous refusals, the not-covered line, the caveat | E04 |
| `_version.py` | 17 | the version, read from the file CI maintains | |

Counts from `wc -l` on 25 Oct 2026, after the security review's fixes. How a command moves through these modules is on [Flows](flows/index.md).

## The commands

```
sharness-ai probe [--json]                                E01  the grant
sharness-ai policy hash|check FILE                        E02  the one value the person supplies
sharness-ai policy translate FILE --to T [-- CMD…]        E10  the policy in another enforcer's form, and the gap
sharness-ai run --policy FILE [--expect-hash H] -- CMD…   E03  one command under a policy
sharness-ai hello [--json]                                E04  the acceptance test, one child process
cd experiments/browser && npm run node|browser|native     E09  the same, under a second kernel (v86) or through chroot
```

Install and use: [The CLI](cli/index.md). Each command's output and caveats: [Examples](examples/index.md). What each shows and does not show: [Mockups and experiments](experiments/index.md).

## What has code behind it, and what does not

| On this site | Code | Where |
|---|---|---|
| the v0 Process Behaviour Policy and its hash | yes | `policy.py`; the [browser mockup](../explain/mockups/policy-hash.html) reproduces it |
| Landlock file, exec and port rules; `network: "none"` | yes | `landlock.py`, `run.py` |
| the grant and the delta | yes | `probe.py` |
| the memo's acceptance test | yes, for one child process | `hello.py`; also under a second kernel in Node and in a tab, [E09](browser/index.md) |
| the launcher, `sharness.kms`, `.net`, `.fs`, `.bash`, `.llm` | **no** | designed on [Components](../design/components/index.md); E05 to E08 are the next pieces |
| mutual TLS with a session CA; the edge matrix | measured by hand, not yet a command | E05 |
| memory and process-count caps (rlimits and cgroups) | yes | `limits.py`, measured 25 Oct 2026 |
| seccomp, the `cpu` cgroup, scoping, the execute allowlist | **no** | [Containment](../design/containment/index.md) says which rows are designed |

## Next in the code, in order

The [research note](../evidence/research/index.md#4-what-is-still-open-in-the-order-to-take-it) sets the order: E06 (the process tree), E05 (the edges as a script), E08 (`sharness.kms` v0) before E07 (`sharness.llm` v0), then the launcher as a script above the agent on a laptop. The languages for each are on [Languages](languages/index.md).
