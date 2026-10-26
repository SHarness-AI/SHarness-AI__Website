# Contributing to sharness-ai

Thank you for looking. SHarness is at the **experiments** stage: the design is published at [sharness.ai](https://sharness.ai), this repository carries the experiments E01 to E04, E09 and E10, and **no SHarness component (launcher, kms, net, fs, bash, llm) is built**. The most useful things a stranger can do today are small and concrete, and three of them need no code.

## The cheapest contribution: a measurement

```
pip install git+https://github.com/SHarness-AI/SHarness-AI__CLI@dev
sharness-ai hello --json
```

Open [a hello report](https://github.com/SHarness-AI/SHarness-AI__CLI/issues/new?template=hello-report.yml) and paste the JSON. Every run from a kernel, a distribution or a container we have not seen goes on [the machines page](https://sharness.ai/evidence/machines/index.html), failures first, credited if you want. A probe that says `allowed` where the policy said `refused` is the most valuable report there is. `hello --json` and `probe` print no hostnames, usernames, paths outside the working directory's name, or the values of proxy variables.

## Three more ways in

- **Answer a Discussion:** which sandbox you run your agent in; which policy you would want to express; what `sharness-ai probe` printed on your machine.
- **Pick a `good first issue`:** each one can be done in one session from the issue text alone.
- **Write a policy** for a real tool or MCP server in the v0 shape (`experiments/policies/`): what it needs and nothing more, with its hash.

## How the work is run

The rules every agent and person on the project follows are in [AGENTS.md on the website](https://sharness.ai/admin/guidance/index.html); the short form that matters here:

- **Status words.** *Measured* only with a method, an environment and a date; everything else is *designed*, *proposed* or *planned*. *Runnable* means the code is here and its tests pass.
- **The threat model trusts the kernel.** Root and kernel compromise are out of scope; never claim protection against them. A policy a process applies to its own children is a Boundary for them and a Setting for itself: say which.
- **Code.** Python 3.11+, standard library only, no runtime dependencies. One idea per file; a module small enough to read in one sitting (a component at most 300 lines). Tests against the real thing, no mocks: `python -m pytest tests/unit`; a test that needs Landlock skips where it is absent, so the suite runs on any OS. Read [`security/risks`](https://sharness.ai/security/risks/index.md) before changing `run.py`, `landlock.py`, `limits.py`, `policy.py` or `build_guest.py`; a fix lands with a test in `tests/unit/test_security.py`.
- **Names.** Brand *SHarness*; command `sharness-ai` (never plain `sharness`, which is an unrelated shell test library); import `sharness_ai`; env prefix `SHARNESS_AI_`; components `sharness.<role>`. No model names in committed text.
- **Branches.** Work lands on `dev` through a pull request from your branch; CI runs the tests. Merging `dev` into `main` is a release to PyPI and is the editor's call; do not bump the version by hand, CI owns it.
- **A new measurement** goes to [Evidence](https://sharness.ai/evidence/index.html) with its method, environment and date: say so in the pull request and the website's agents will carry it over, or open a pull request there yourself.

## Security findings

**Never in a public issue.** Use the private route in [`SECURITY.md`](SECURITY.md): GitHub's private vulnerability reporting on this repository, with the version, the kernel (`sharness-ai probe`), the policy file and the command. A report that reproduces is answered with a fix or a written acceptance, and either way the finding goes on [the register](https://sharness.ai/security/risks/index.md). There is no bug bounty.

## Licences and credit

Code is Apache-2.0; the site's content is CC BY 4.0. Contributors are named in the release notes and, for measurements, on the machines page. The project is built in the open with AI agents, each writing under its own name ([who writes here](https://sharness.ai/project/about/index.html#who-writes-here)); contributions from agents are welcome on the same terms and say they are from an agent.

Rule followed (for the website's record): outreach §3.1; AGENTS.md §1, §3, §4; the brief's acceptance criterion 3 (a security finding goes to the route `SECURITY.md` names, never to a public issue).
