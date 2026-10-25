# The CLI: sharness-ai

> **Status: experiments.** A Python package, `sharness-ai`, that will carry the SHarness launcher and components. Today it carries the first experiments. Source: [SHarness-AI/SHarness-AI__CLI](https://github.com/SHarness-AI/SHarness-AI__CLI). The command is `sharness-ai`.

## What exists, as of 24 Oct 2026

| Where | What |
|---|---|
| [PyPI, v0.1.0](https://pypi.org/project/sharness-ai/) | reports its version and prints its help; also installs a `sharness` shorthand, removed on `dev` |
| the `dev` branch | the proposed scope in the README; `sharness-ai` as the only command; experiments E01 to E04 (`probe`, `policy hash`, `policy check`, `run`, `hello`), their tests, the `sharness-hello` skill. Not released until `dev` is merged to `main` |

```
$ pip install sharness-ai            # v0.1.0: version and help only
$ pip install git+https://github.com/SHarness-AI/SHarness-AI__CLI@dev     # the experiments, unreleased
$ sharness-ai --version
sharness-ai v0.1.0
$ sharness-ai
usage: sharness-ai [-h] [--version] command ...
  probe     E01: the grant, what a process here can do before any policy
  policy    E02: hash or check a Process Behaviour Policy (v0)
  run       E03: run one command under a policy (Linux, Landlock)
  hello     E04: the memo's acceptance test, for one child process
```

Requires Python 3.11 or later. No runtime dependencies: Landlock is reached through `ctypes`, hashing through `hashlib`, nothing else is needed. The map of what each experiment shows and does not show is [Mockups and experiments](../experiments/index.md).

## The first version, as proposed

The memo says one CLI project for now, components split out later if one is useful on its own ([roadmap decision 7](../../design/roadmap/index.md#open-decisions)). So the first version of `sharness-ai` is one package whose subcommands are the experiments today and the components tomorrow, in the order the ladder sets:

```
sharness-ai probe                                  E01  the grant                         runnable
sharness-ai policy hash|check FILE                 E02  the one value the person supplies  runnable
sharness-ai run --policy FILE [--expect-hash H] -- CMD…   E03  one command under a policy  runnable
sharness-ai hello                                  E04  the acceptance test, one process   runnable

sharness-ai edges                                  E05  session CA + role certs + the edge matrix      planned
sharness-ai tree                                   E06  the process-tree proof of concept               planned
sharness-ai llm   --listen :port --policy FILE     E07  sharness.llm v0, where ANTHROPIC_BASE_URL points  planned
sharness-ai kms   --policy FILE                    E08  sharness.kms v0: init, public, unwrap, seal_to, destroy  planned

sharness-ai launch --manifest m.json --expect-hash sha256:M -- claude …     the launcher: above the agent   designed
```

Three rules for the package, carried from the design:

- **Stdlib only, small modules.** Each module small enough to read in one sitting: the design's targets are launcher ≤ 400 lines, each component ≤ 300, a shared library ≤ 400. `landlock.py` is about 150 lines; `run.py` about 130.
- **Status words in the code too.** `--help` says *experiments*; `hello` prints its caveat every run; nothing says *sandboxed* about the agent.
- **Child subtree only.** Every command that enforces anything forks a child and applies the policy there. The shell you run it from is never restricted. That is the safety rule for testing in a live session, built into the tool.

## The v0 policy

`run` and `hello` take a v0 Process Behaviour Policy: six keys, integers only, hashed as canonical JSON. It is the smallest shape that can be enforced by Landlock and hashed identically by Python and the browser; the full schema is on [Process Behaviour Policies §4](../../design/policies/index.md#4-schema) and v0 grows towards it, never away from it.

```json
{"pbp": 1, "id": "deny-all-example", "layer": "invocation",
 "files":   {"read": ["/usr", "/lib", "/lib64", "/bin", "/etc"], "write": [], "exec": ["/usr", "/bin"]},
 "network": "none",
 "process": {"no_new_privs": true}}
```

Its hash, from `sharness-ai policy hash` and from the [browser mockup](../../explain/mockups/policy-hash.html): `sha256:ab1d3e4e779313274f7a1d3ef3e46f6eacef038d8cfaa6198151a45cd82dcc76`.

## Why sharness-ai, not sharness

Plain `sharness` is the Debian, pkgsrc and OpenBSD package name of an unrelated shell test library, so SHarness does not use it as a command. `sharness-ai` matches the PyPI distribution. Environment variables use the prefix `SHARNESS_AI_` (proposed); `run` sets `SHARNESS_AI_POLICY_HASH` and `SHARNESS_AI_POLICY_ID` for the child.

## Where the version lives

One file owns it: `sharness_ai/version`. `sharness-ai --version` reads that file at import time; CI writes it, together with the version in `pyproject.toml`, on every release. The same convention as sgit.

## How it is released

Day-to-day work lands on `dev`, the default branch. Merging `dev` into `main` cuts a release: every push to `main` runs `.github/workflows/workflow.yml` in the CLI repository.

| Job | What it does |
|---|---|
| Run Unit Tests | `pytest tests/unit` with coverage, on Python 3.11. Tests that need Landlock skip where the kernel lacks it. A failure stops the release |
| Increment Tag | bumps the middle number (`v0.N.0` → `v0.N+1.0`), writes it to the version file, `pyproject.toml` and the README badge, commits, and tags |
| Publish to: PYPI | builds with Poetry and uploads through Trusted Publishing: GitHub's OIDC token is exchanged for a short-lived PyPI token, so no API key is stored anywhere |

Why one workflow file: PyPI's trusted publisher for `sharness-ai` is bound to the repository and the workflow filename (`workflow.yml`). The publish job therefore lives in that file, not in a reusable workflow it calls. Renaming the file breaks publishing until the PyPI configuration is updated to match.

## For agents working in the repository

The repository carries a `CLAUDE.md` with the ground rules (status words, threat model, stdlib only, tests, names, releases) and the skill `sharness-hello` that runs E01 and E04 inside a Claude Code session under the design's safety rules.
