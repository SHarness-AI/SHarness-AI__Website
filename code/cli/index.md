# The CLI: sharness-ai

> **Status: experiments, with three MVPs runnable, as of 28 Oct 2026.** A Python package, `sharness-ai`, that will carry the SHarness launcher and components. Today it carries the experiments and three MVPs on its `dev` branch: the levels in the terminal (MVP 1: `contain`, `profile`, `explain`), the first door, `sharness.fs` (MVP 2: `session`, `fs`, `door conformance`) and the network door with a shell under the harness (MVP 3: `net`, `shell`). Source: [SHarness-AI/SHarness-AI__CLI](https://github.com/SHarness-AI/SHarness-AI__CLI). The command is `sharness-ai`.

## What exists, as of 26 Oct 2026

| Where | What |
|---|---|
| [PyPI, v0.2.0](https://pypi.org/project/sharness-ai/) | released 29 Oct 2026 from `dev` at the go of security review 2: `sharness-ai` as the only command, the experiments and MVP 1, MVP 2 and MVP 3 below |
| the `dev` branch | `sharness-ai` as the only command; the experiments E01 to E05, E09 and E10; MVP 1, MVP 2 and MVP 3 below; `doctor` and `help --format json`; 243 tests, all passing in website@'s run on Python 3.13 as root, 29 Oct 2026 (`dev` f9e51c8, from a virtualenv under `/opt`: one test starts a shell as a temporary user, which needs an interpreter that user can reach, so a virtualenv under a root-only directory fails it). Released to PyPI as v0.2.0 on 29 Oct 2026 ([R7](../../admin/board/index.md)); later work lands here first |

```
$ pip install sharness-ai            # v0.2.0: the experiments and the MVPs
$ pip install git+https://github.com/SHarness-AI/SHarness-AI__CLI@dev     # the latest, before the next release
$ sharness-ai help                   # every command, read from the parser itself
```

The command surface on `dev`, from `sharness-ai help --format json` (the parser is the source; this table is read from it):

| Command | What it does | Status |
|---|---|---|
| `sharness-ai` (no arguments) | the guide: where you are, the ladder, what to do next | runnable |
| `contain` | level 5: one sentence (a workspace, sites, secrets) compiled to the kernel and run | runnable (MVP 1) |
| `profile list\|show` | level 4: the roles a vendor ships, with the blanks a person fills | runnable (MVP 1) |
| `explain FILE` | any document, drawn down the levels to the kernel, hash by hash | runnable (MVP 1) |
| `doctor` | can a policy hold here? eight checks in order, each with what to do about it | runnable |
| `help [--format json]` | every command, from the parser; JSON for a page or a diff between releases | runnable |
| `probe` | E01: the grant, what a process here can do before any policy | runnable |
| `policy hash\|check\|show\|translate\|new\|edit` | E02 and E10: the policy, its hash, its drawing, its form in another enforcer | runnable |
| `run --policy FILE [--expect-hash H] -- CMD` | E03: one command under a policy (Linux, Landlock) | runnable |
| `hello` | E04: the acceptance test, six probes under one policy | runnable |
| `session new\|show` | E05: a session CA and one identity per role (openssl), the CA key destroyed | runnable (MVP 2) |
| `fs serve\|hello\|put\|append\|get\|rm\|ls\|log` | `sharness.fs`, the only writer: serve the door or call it as the app | runnable (MVP 2), a Setting |
| `door conformance NAME` | a door's vectors against a fresh instance, the twin first | runnable (MVP 2) |
| `components` | the operating system a process sees: the map, with status | runnable |
| `net serve\|hello\|log` | `sharness.net`, the only network client: an allowlisting proxy on loopback for one uid, and its admin door | runnable (MVP 3) |
| `shell [--workspace D --sites H -- CMD]` | an interactive shell under the harness: a unique user (as root), the proxy's port as its only network row | runnable (MVP 3) |
| `launcher` | the map; its first slice is `shell` | runnable, a first slice |
| `bash`, `kms`, `llm` | the map and the proposed surface; exit 69 | designed, not built |

Requires Python 3.11 or later. No runtime dependencies: Landlock is reached through `ctypes`, hashing through `hashlib`, TLS through `ssl`; MVP 2 and 3 call the `openssl` program for the session's certificates, and `shell` calls `useradd` and `userdel` where it runs as root. The map of what each experiment shows and does not show is [Mockups and experiments](../experiments/index.md).

## MVP 1: the levels in the terminal

A policy can be written at five levels, and each compiles to the one below it ([the levels](../../design/levels/index.md)). `contain` takes the top one, a sentence (the screen, abridged):

```
$ sharness-ai contain --workspace . --sites github.com -- my-agent
  you said        contain my-agent to /home/me/project, github.com, no secrets
  it became       profile coding-agent (4) → 13 path rows + network + caps (3) → one door, the kernel (2) → 14 kernel rules (1)
  the name        sha256:…   every level below is recomputed from it
  not held        github.com: held as port 443; the host name is not held until sharness.net runs here
  not covered     UDP (DNS) unless an empty network namespace applied · Unix sockets by path · the inherited environment
```

The sentence (level 5) fills a profile's blanks (level 4: six profiles, P0 to P5 as templates); the profile becomes rows in plain nouns (level 3: `network.sites` instead of ports); the rows become the v0 policy (level 2, where the kernel is the only door) and what the kernel is told (level 1). Each level has its own hash, and the run goes ahead only with `--expect-hash` on the level-2 hash the chain computed. `explain FILE` draws the same chain box by box; `--save FILE` keeps the sentence. What the kernel cannot hold yet is said in words, never hidden: a host name compiles to its port, so **every host on that port is reachable** until `sharness.net` exists. Vectors for each level (l3: 9 accept, 6 refuse; l4: 9 and 4; l5: 5 and 5) are generated from the Python package as the oracle. Not done: the count of "things you did not ask for", which needs the grant measured against the mandate.

## MVP 2: the first door

`sharness.fs` runs as a loopback service under mutual TLS 1.3, over the local disk (`fs.disk`) or a dictionary with the same face (`fs.disk.twin`), with the door kit every later door will share: the session, the contract (`ACCEPTS.json`, `EMITS.json`, both hashed), the closed predicate language, verdicts that name the row that decided, one audit line per request. What it accepts, what it refuses and its known issues: [sharness.fs](../../components/fs/index.md). It is a Setting for the app until the launcher gives it its own uid.

## The first version, as proposed

The memo says one CLI project for now, components split out later if one is useful on its own ([roadmap decision 7](../../design/roadmap/index.md#open-decisions)). So the first version of `sharness-ai` is one package whose subcommands are the experiments today and the components tomorrow, in the order the ladder sets:

```
sharness-ai probe                                  E01  the grant                         runnable
sharness-ai policy hash|check FILE                 E02  the one value the person supplies  runnable
sharness-ai run --policy FILE [--expect-hash H] -- CMD…   E03  one command under a policy  runnable
sharness-ai hello                                  E04  the acceptance test, one process   runnable

sharness-ai session new|show                       E05  session CA + role certs + the edge matrix      runnable
sharness-ai contain|profile|explain                MVP 1  the levels, a sentence down to the kernel  runnable
sharness-ai fs serve|put|get|…                     MVP 2  sharness.fs, the first door (a Setting)     runnable
sharness-ai net serve · sharness-ai shell          MVP 3  sharness.net and the launcher's first slice   runnable
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

## MVP 3: the network door and a shell under the harness

`sharness-ai shell` starts a command, by default a shell, as a unique system user (where it runs as root; `--no-user` runs it as the caller, a Setting), with a policy whose only network row is the port of `sharness.net`, an HTTP proxy that holds the host allowlist and checks the server name inside the TLS hello against the CONNECT host. The kernel holds the port, the proxy holds the hosts, and the proxy answers only that user, so for the shell it starts the host allowlist is outside its reach: a Boundary. Since security review 2 (29 Oct 2026) the shell runs in a network namespace of its own, loopback only, so UDP has no route, and on exit every process of its user is killed before the user is removed. What it does not cover is named in the CLI's `REALITY.md`: Unix sockets by path, TLS termination, the fs door for the workspace. Checked by website@ on 28 Oct 2026: [sharness.net](../../components/net/index.md#update-28-oct-2026) and [sharness.launcher](../../components/launcher/index.md). Unreleased, like the rest of `dev`.

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
