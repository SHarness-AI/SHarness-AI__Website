# Security reviews

> **One review so far, as of 25 Oct 2026.** Each review is recorded with its scope, method and environment, its findings (each with the fix and the test that pins it), what was examined and found clean, and what was not examined. Findings are numbered `SF-` here; their state is kept on the [register](../risks/index.md) under the matching `SR-` number.

## Review 1: 25 October 2026

**By** security@sharness, the project's security agent (an AI agent working in a Claude Code cloud session, as the build agent does; Dinis Cruz asked for the review and decides every acceptance).

**Scope.** The CLI repository at `dev` commit `ebd1445`: every module in `sharness_ai/`, the seven example policies, `experiments/browser/` (the guest build, the runners, the playground), the skill, both workflows. The website repository at `dev` v0.5.8: the deploy workflow, the gate, every page that loads a script. The GitHub settings visible through the API (branches, collaborators, tags, workflow runs). The two composite actions the release pipeline used, read at the commit they were pinned to.

**Method.** Every file read in full. Each suspected gap was tried before it was written down, as a child process under a policy in the review's own session, so each finding below is an observed behaviour of the code as it was, not a reading of it. Each fix was then tried the same way and given a test. The scanners ruff (with bandit's rule set), bandit and zizmor were run before and after; they found none of the High findings, which is the usual shape: the holes were in what the code meant, not in how it was written.

**Environment.** One Claude Code cloud session: Ubuntu 24.04, Linux 6.18.44, Landlock ABI 7, uid 0, Python 3.13.17, cgroups v1 with a unified mount. The same kind of session as the measurements on [Evidence](../../evidence/index.md).

### Findings

The weight is the reviewer's judgement of what the finding would cost someone relying on the code as documented. "Fixed" means on the CLI's `dev` branch with the named test in `tests/unit/test_security.py`, unless another place is named.

| # | Weight | Where | Finding | Done |
|---|---|---|---|---|
| SF-01 | High | `run.py`, `landlock.py` | the Landlock rights granted on a writable path included execute, while the documentation and the profiles said the workspace is never executable. The test that existed checked the policy text, not the kernel | fixed: `landlock.access_write()`; `test_a_writable_path_is_not_executable` |
| SF-02 | High | `run.py` | a writable path that is a symlink binds the rule to its target, so the kernel grants more than the page says; a cloned repository can carry the link | fixed: refused before forking; re-checked by the child on the bound descriptor; `test_a_symlinked_writable_path_is_refused_before_anything_runs` |
| SF-03 | High | `run.py` | with `network: "none"` and neither a network namespace nor Landlock TCP rules available (kernels before 6.7 without a usable user namespace), the command ran with the network and nothing said so; ports likewise on ABI < 4 | fixed: a refusal, or `--best-effort` with the gap on stderr; `test_network_none_without_namespace_or_tcp_rules_is_refused` |
| SF-04 | High | `limits.py`, `run.py` | `max_pids` relied on `RLIMIT_NPROC`, which the kernel does not apply to uid 0; without a pids cgroup a root child's count was unlimited and the result said otherwise | fixed: a refusal without the cgroup; `test_max_pids_as_root_without_a_cgroup_is_refused`, `test_nproc_does_not_bind_root` |
| SF-05 | High | `.github/workflows/workflow.yml` | the publish job ran a composite action from another repository that fetched an installer over the network and installed unpinned packages, in the job holding the PyPI OIDC token; its inner actions were pinned by tag | fixed: inline bump, separate build and publish jobs, GitHub's and pypa's actions pinned to commits, attestations. Untested until the next push to `main` |
| SF-06 | Medium | `hello.py` | the runner was started with `python -m`, which puts the current directory first on the import path; a package folder of the same name in the workspace would be imported by the process that applies the policy | fixed: `-P -s`; `test_a_planted_package_in_the_workspace_is_not_imported` |
| SF-07 | Medium | `experiments/browser/build_guest.py` | the guest's packages and BIOS were downloaded without verification, the BIOS from a branch; the chroot form runs them as root on the host | fixed: sha256 for every file, refused on mismatch, BIOS from one commit, https only; `test_guest_build_pins_every_download` |
| SF-08 | Medium | Landlock | Unix-domain sockets by path are reachable under `network: "none"`; neither Landlock nor the empty network namespace covers them | accepted and declared on stderr, in `policy check`'s advice and in `hello`; `test_unix_socket_gap_is_declared` |
| SF-09 | Medium | `hello.py` | any failure of a probe counted as the policy's refusal, including failures the environment would have produced without a policy | fixed: a control run and an *inconclusive* state |
| SF-10 | Medium | `run.py` | a descriptor opened before the policy stayed usable after it | fixed: every descriptor above 2 closed in the child; `test_inherited_descriptors_are_closed` |
| SF-11 | Medium | the v0 schema | the child inherits the applying process's whole environment | open: a policy row is proposed on [SR-11](../risks/index.md#the-register); declared on stderr meanwhile |
| SF-12 | Low | `policy.py` | hashes diverged between Python and JavaScript for integers above 2^53; a lone surrogate ended in a traceback | fixed: refused; the browser canonicaliser is run under test |
| SF-13 | Low | `policy.py` | a duplicate key kept the last value silently | fixed: refused on load |
| SF-14 | Low | `policy.py` | paths with `..`, `.`, trailing or doubled slashes, and control characters in paths and ids were accepted | fixed: refused |
| SF-15 | Low | `translate.py` | unquoted paths in the Kubernetes YAML; a `:` in a path not expressible for docker | fixed: JSON-quoted; noted |
| SF-16 | Low | `policy.py` | a boolean accepted as a port | fixed |
| SF-17 | Low | `cli.py` | a missing policy file ended in a traceback | fixed: exit 2 |
| SF-18 | Low | `experiments/browser/boot_browser.mjs` | the local static server followed `..` above the folder it served | fixed |
| SF-19 | Low | `experiments/browser/playground.js` | a runtime's output was written into the page as HTML | fixed: text nodes |
| SF-20 | Low | this site | the storyboards kit's script loaded without the integrity string the kit publishes | fixed: `integrity` and `crossorigin`; the gate checks it |
| SF-21 | Low | the skill | installing from a moving branch | fixed: a named commit |
| SF-22 | Info | `run.py` | `SHARNESS_AI_POLICY_HASH` is a statement the child cannot verify | documented |
| SF-23 | Info | `run.py` | what could not be applied was visible only with `--verbose` | fixed: stderr every run |
| SF-24 | Medium | GitHub settings | `main` and `dev` unprotected; one administrator; a push to `main` publishes | open: [Hardening §3](../hardening/index.md#3-the-repositories-and-the-accounts-settings-only-a-person-can-change) |
| SF-25 | Low | `code/playground/` | Pyodide from a CDN with no integrity string | accepted and declared: [SR-25](../risks/index.md#the-register) |

### Examined and found as documented

- `policy_hash`: SHA-256 over canonical JSON with sorted keys, no whitespace, UTF-8; the seven examples hash identically in Python and in the browser's canonicaliser (now under test).
- `--expect-hash`: the file is loaded once, hashed, checked and enforced as the same object, so there is no window between the check and the use.
- `landlock.py`: the ruleset attributes grow with the ABI as the kernel documents; rights not handled by the running ABI are masked; `no_new_privs` is set before `restrict_self`; the ruleset descriptor is closed after.
- `probe`: prints the names of proxy variables and never their values (tested); reads only `/proc/self`, `/proc/config.gz`, `/sys/fs/cgroup` and the tools on `PATH`.
- `translate`: the bwrap and docker lines quote every argument with `shlex.quote`; the Claude Code settings are JSON; the notes name what each target does not enforce.
- `build_wheel.py`: the RECORD hashes every file; the wheel's version says `+dev.<commit>`, so it cannot be mistaken for a release.
- `write_cpio`: deterministic (fixed inode numbers, zero gzip timestamp), under test.
- the skill's safety rules: child subtrees only; nothing written outside a temporary directory.
- the website's gate: version agreement, internal links, canonical host, a key-leak tripwire, dated figures, the newsroom format; the deploy workflow's actions pinned to commits; `persist-credentials: false` where nothing pushes.
- the GitHub settings that could be read: both repositories have one collaborator, Dinis Cruz, as admin; two tags on the CLI; the `tests` workflow green on the last two pushes to `dev`.

### Not examined

- The design's cryptography (the KMS protocol, the sealing envelope, the session CA) beyond reading it: nothing of it is code yet, and a protocol review belongs with E05 and E08.
- The kernel's Landlock implementation itself; this review trusts the kernel, as the design does.
- GitHub settings the API does not show to this session: rulesets, the Actions permission policy, secret scanning and push protection, Pages' environment rules, the organisation's two-factor requirement. These are on the lock-down list as things to set and then confirm.
- The PyPI side of Trusted Publishing: the publisher's configuration was not visible; the lock-down list asks for it to be bound to an environment.
- A run of the rewritten release pipeline. It runs on the next push to `main`; a `workflow_dispatch` dry run builds and stops.
- sgit, and anything on the *.sgit.ai sites.

## Next review

When the launcher exists as a script (E06 and after), before any component is called a Boundary for the agent. Then on each release that adds a component. Each review is a new section on this page; the register grows, and nothing on it is removed.
