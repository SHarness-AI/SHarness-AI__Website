# Security reviews

> **Two reviews, as of 29 Oct 2026.** Each review is recorded with its scope, method and environment, its findings (each with the fix and the test that pins it), what was examined and found clean, and what was not examined. Findings are numbered `SF-` here; their state is kept on the [register](../risks/index.md) under the matching `SR-` number.

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

## Review 2: 29 October 2026, before the first release from `main`

**By** security@sharness, at the editor's request: the security pass the editor set as the condition for R7, the first release of the CLI from `main` to PyPI (v0.2.0).

**Scope.** The CLI at branch `claude/inspiring-sagan-7g1eh7` (`dev` at `8210807` plus `10a6063`, `4a8106c`, `10a14cb`): `sharness_ai/door/`, `sharness_ai/fs/`, `sharness_ai/net/` with the proxy, `sharness-ai shell` and `sharness_ai/launcher/` (the uid drop, `useradd`/`userdel`, the live page), and `.github/workflows/workflow.yml`, whose first run since review 1 is this release (SR-05). The notes cli@ wrote to this agent on `dev` (`5421d4e`, `cf2ea3d`, `4a0bdd3`, `63360be`, `10a6063`) named what to read first.

**Method.** Every file in scope read in full. Each suspected gap was reproduced before it was written down: the launcher and the shell as root with real `useradd`, Landlock and the proxy; the proxy against a listener on loopback; the release bump run on a worktree of `main` merged with the fixed branch, then the wheel built. Each fix was re-run the same way, and each test was run against the code before the fix to see it fail. `ruff` (the `S` rules) and `bandit -ll` clean before and after.

**Environment.** One Claude Code cloud session, 29 Oct 2026: Linux 6.18.44, Landlock ABI 7, uid 0, Python 3.13, `useradd` present, `openssl` present.

### Findings

"Fixed" means on the CLI branch `claude/elegant-hopper-ftyhqo` at `d16abae` with the named test in `tests/unit/test_security.py` (`Test_Review_2`); it reaches `dev` with cli@'s three commits above it, before R7.

| # | Weight | Where | Finding | Done |
|---|---|---|---|---|
| SF-26 | High | `launcher/Launcher.py` | the shell's only network row is the proxy's port, and Landlock's rules name ports, not addresses: the shell reached a listener on 127.0.0.2 at the proxy's port, and a connection to 1.1.1.1 at that port left the machine (it timed out rather than being refused), so the host allowlist could be skipped by anything that read `HTTPS_PROXY` | fixed: a network namespace for the shell, loopback only, the proxy's socket made inside it; refused where it cannot be made. [SR-28](../risks/index.md#the-register) |
| SF-27 | High | `launcher/Launcher.py` | a background process of the shell kept writing the workspace after the shell exited; `userdel` failed silently and the user stayed | fixed: every process of the uid killed on exit, `userdel` checked, the summary says what was not undone. [SR-30](../risks/index.md#the-register) |
| SF-28 | Medium | `net/proxy/Proxy.py` | the TLS name check read only the first piece of the hello; the hello sent in pieces carried another name to the upstream | fixed: the first record read whole, unreadable TLS cut. [SR-29](../risks/index.md#the-register) |
| SF-29 | Medium | `launcher/Launcher.py` | the package directory inside the workspace, or writable by the shell's uid, lets the shell change the code its next run, and the root launcher, imports | fixed: refused at launch. [SR-31](../risks/index.md#the-register) |
| SF-30 | Medium | `net/proxy/Proxy.py` | an allowed name resolving to loopback reached a loopback service through the proxy | accepted for v0.2.0: [SR-32](../risks/index.md#the-register) |
| SF-31 | Low | `net/proxy/Proxy.py` | the `Host` header inside TLS is not seen; on plain HTTP the caller's own `Host` is forwarded (reproduced) | accepted: [SR-33](../risks/index.md#the-register) |
| SF-32 | Low | `workflow.yml` | the release tags `main` as it is when the job starts, not the tested commit | open, a workflow change for the editor: [SR-34](../risks/index.md#the-register) |
| SF-33 | Low | `pyproject.toml` | the build backend is a range, not a pin | accepted: [SR-35](../risks/index.md#the-register) |
| SF-34 | Low | `launcher/Launcher.py` | as the caller's own uid (`--no-user`, or not root) nothing is killed by uid and the proxy answers any local process | accepted, the declared Setting: [SR-36](../risks/index.md#the-register) |
| SF-35 | Low | `door/Door.py`, `door/Session.py` | body cap times unbounded connections; a session directory another user owns | accepted: [SR-37](../risks/index.md#the-register) |

### Examined and found as documented

- **The uid drop** (cli@'s question in `63360be`): `setgroups([])`, then `setgid`, then `setuid` in the forked child, before `execve` with a clean environment of eleven named variables; no capability survives the change from uid 0, and no descriptor of the parent's (Python's are close-on-exec, and `run` closes everything above 2). The probe's own child in `check_access` does the same and writes one byte.
- **The door kit**: TLS 1.3 only, `CERT_REQUIRED` both ways, the session's own CA as the only trust anchor, the CA key deleted before `Session.new` returns, keys 0600 in a 0700 directory; the edge is checked before a byte of body is read; the handshake runs on the connection's thread under a timeout; a reason is one printable line, capped.
- **`sharness.fs`**: `..` refused after decoding, then the path walked with `openat` and `O_NOFOLLOW` from the root, writes atomic by directory descriptor and never executable. Tried: a symbolic link in the middle of the path is refused for write, append and read; a link as the last component is refused for append and read and, for write, replaced by the new file without being followed; the file outside the root was untouched in every case. The secret scan is linear (80 KB in 1.7 ms); a secret split across two appends is refused (`Test_Door_Review_3`). The scan sees clear shapes only, as the contract says.
- **The proxy's rows**: tried: `127.0.0.1`, `[::1]`, `::1`, `2130706433`, `0x7f.1`, `pypi.org:443`, a name with a NUL in it, `evil.pypi.org` and a look-alike punycode name are all refused with only `pypi.org` listed; `PYPI.ORG` and `pypi.org.` are the same host and allowed; a host must match the name grammar after lower-casing, and Latin-1 has no character that lowers to ASCII; the peer's uid is read from the socket table of the shell's own namespace now.
- **The live page**: every cell is written with `textContent`, the one selector built from data goes through `CSS.escape`, the page is on loopback under a 16-byte random token, and in the namespace the shell can no longer reach it.
- **The release workflow** (SR-05's first run): the publish job holds `id-token: write` and runs only pypa's pinned publisher on the build job's artifact; nothing of ours runs where the token is. The bump, run on `main` merged with the fixed branch, takes `v0.1.0` to `v0.2.0` in `pyproject.toml` and `sharness_ai/version` and passes its own check; the merge has no conflict; the wheel builds as `sharness_ai-0.2.0`. The push the job makes uses the workflow's token, which does not start another run.

### Not examined

- The PyPI side of Trusted Publishing and the repository settings (R15, SR-24): unchanged since review 1 and still the editor's.
- The release run itself: it happens when `dev` is merged to `main`. SR-05 stays *fixed, untested* until that run is green.
- `run.py`, `landlock.py`, `limits.py`, `policy.py` beyond the path the shell uses (review 1 covered them; no change since but `4a8106c`'s probe wording); the levels (`level/`); the bench.

### The answer for R7

**Go**, once `d16abae` is on `dev` and `dev`'s tests are green: the two High findings are fixed with tests, the Medium findings that change what the shell claims are fixed, and what stays is on the register with its reason. Without `d16abae` it is a **no-go**: `sharness-ai shell` would publish a host allowlist the shell can step around.

## Next review

When the launcher exists as a script (E06 and after), before any component is called a Boundary for the agent. Then on each release that adds a component. Each review is a new section on this page; the register grows, and nothing on it is removed.
