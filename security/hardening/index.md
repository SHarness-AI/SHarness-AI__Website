# Hardening

> **Status: guidance, as of 25 Oct 2026.** Two halves. The first is for whoever runs `sharness-ai` today: how to get the most from a tool that confines one child process, and what it will not do for you however it is run. The second is the lock-down list for the project itself: the repositories, the accounts, the release path and this site, split into what is already in code and what only a person can set in GitHub or PyPI. Dinis Cruz works through the second half; each item is a checkbox because the state cannot be read from the repository and must be confirmed by hand.

## 1. Running sharness-ai today: what it is, in one paragraph

`sharness-ai run` forks a child, applies a v0 Process Behaviour Policy to it with Landlock, a network namespace, rlimits and cgroups, and runs your command inside. For the child it is a Boundary; for the process that ran it, it is a Setting it could have skipped. It refuses to run when the policy's hash is not the one you supplied, when a writable path is a symlink to somewhere else, and when a row of the policy cannot be enforced on this kernel. It says, every run, what nothing covers: Unix-domain sockets by path, the environment the child inherits, UDP when no namespace could be made. Everything below follows from that paragraph.

## 2. How to run it so it holds as much as it can

| Do | Why |
|---|---|
| **Supply `--expect-hash` with a hash you computed yourself**, from the policy file, with `sharness-ai policy hash` on your machine or the [browser mockup](../../explain/mockups/policy-hash.html); never one you read off an agent's output | the hash is the one thing that comes from outside the agent. Read back from the agent, it comes from the agent ([Threat model §3](../threat-model/index.md#3-the-two-trust-boundaries)) |
| **Run `sharness-ai probe` first** and read the `reading` line | it says what this environment grants before any policy: root or not, Landlock ABI, whether a namespace can be made, whether cgroups are writable. The policy can only narrow that |
| **Run `sharness-ai policy check` and read the advice** | the hash names the policy and does not judge it; the advice lines are the known ways a well-formed policy grants more than its page suggests |
| **Write real paths**, normalised, no `..`, no trailing slash, and name the real directory rather than a link to it | the kernel binds inodes; the page must say what the kernel binds. `check` refuses the first three; `run` refuses a writable link |
| **Keep write and exec apart.** A writable path is never executable under `run`; do not list the workspace under `exec`, and run scripts as `python3 /work/x.py`, never `./x.sh` | a dropped file that can run is the oldest hole there is. Note the limit: an interpreter on the exec list runs code from a writable path; only `sharness.bash` and the dual-LLM split answer that |
| **Prefer `network: "none"`**; when you need a port, know that v0 names ports and not hosts | any host on 443 is still any host. `sharness.net` is the designed answer; until then the policy is honest about it |
| **Do not pass `--best-effort` by habit** | it turns a refusal into a line on stderr and runs anyway. Use it when you have read the line and accept it for this run |
| **Mind the environment.** Before `run`, unset what the child does not need (`env -i`, or an allowlist) | v0 has no row for it and the child sees everything ([SR-11](../risks/index.md#the-register)) |
| **Mind Unix sockets.** If a Docker socket, an X server or a local server listens by path on this machine, the child can reach it | Landlock has no rule for them ([SR-08](../risks/index.md#the-register)). A separate uid, or a mount namespace, is the answer today |
| **Give the child a uid that is not yours** where you can (`setpriv`, a service user), and run as root only where a cgroup must be made | DAC becomes a second layer; `RLIMIT_NPROC` only binds a non-root uid |
| **Read `hello`'s `not covered` and `caveat` lines as part of the result**, and treat a `?` (inconclusive) as not measured | the result is only as good as what it says it did not test |
| **Install from a release or a named commit**, never a moving branch | `pip install sharness-ai==<version>`, or the repository at a commit; the site's [immutable release paths](../supply-chain/index.md#5-the-code-on-this-site-immutable-paths) carry every release with its hashes |

What no amount of care changes: a policy applied by the agent to its children is a Setting for the agent. The launcher above the agent (E06 and after) is the design's answer and nothing on this page is a substitute for it.

## 3. The repositories and the accounts: settings only a person can change

Everything a repository can carry is on `dev` of both repositories as of 25 Oct 2026: pinned actions, minimal permissions, the security workflows, Dependabot, `SECURITY.md`, the gate. The items below live in GitHub's and PyPI's settings and must be set by an account owner; the review could not read them, so each is a thing to set and then confirm. The weight says what is at stake.

### The organisation (SHarness-AI)

- [ ] **Require two-factor authentication** for every member (Settings, Authentication security). High: one account administers both repositories; its loss is the project's.
- [ ] **Actions permissions: allow only actions from GitHub and from verified creators**, or an allowlist of the exact actions the workflows use (Settings, Actions, General). Medium: a workflow edited to call an unknown action should fail, not run.
- [ ] **Default `GITHUB_TOKEN` permissions: read-only** for the organisation. Medium: every workflow here already asks for what it needs.
- [ ] **Require approval for all outside collaborators' workflow runs**, and for first-time contributors' pull requests. Medium.
- [ ] **Add a second owner** who can recover the organisation; keep a recovery code offline. Medium.

### Both repositories

- [ ] **Branch rulesets for `main` and `dev`**: require a pull request before merging (one approving review on `main`), require the status checks `tests`, `security` and `codeql` to pass, block force pushes, block deletion, require linear history. High: today a push to `main` publishes a release, and both branches are unprotected (SR-24).
- [ ] **A bypass for the release bump.** The release workflow pushes a version-bump commit to `main`; with the ruleset above that push fails unless the Actions app (or a GitHub App token the workflow uses) is on the ruleset's bypass list. Set the bypass to that one actor for pushes only, not for ruleset changes. The alternative, which needs no bypass and is the recommended end state: **stop committing the version from CI**, derive it from the tag in the build job and write `sharness_ai/version` only inside the build, so `main` never receives a bot commit. Medium; decide one.
- [ ] **Tag ruleset for `v*`**: only the Actions actor may create tags; nobody may delete or move one. Medium: a tag is what a release and this site's immutable paths refer to.
- [ ] **Secret scanning and push protection on**; **Dependabot alerts and security updates on**; **private vulnerability reporting on** (Settings, Code security). High for push protection: it stops a key reaching the repository, which the gate's tripwire only catches afterwards.
- [ ] **CodeQL**: the `codeql.yml` workflow is in the CLI repository; confirm the Security tab shows its results (default setup must be off, or it conflicts).
- [ ] **Delete the stale `claude/*` branches** on the CLI repository, and set a rule that deletes head branches on merge. Low.
- [ ] **Require signed commits on `main`**, once the bot-commit question above is settled (a bot commit is unsigned unless the workflow signs it). Low.
- [ ] **Immutable releases** (Settings, General): once on, a GitHub Release's assets and tag cannot change after publishing, and GitHub attests them. Medium; pairs with the next item.
- [ ] **Publish a GitHub Release per tag** from the release workflow, with the built distributions and an attestation (`actions/attest-build-provenance`, pinned). Low; a second place a reader can verify a release.

### The CLI's release path (PyPI)

- [ ] **Trusted Publisher bound to an environment**: on PyPI, edit the publisher for `sharness-ai` to require the GitHub environment `pypi`; in the repository, create the `pypi` environment with a required reviewer (Dinis) and a short wait timer; add `environment: pypi` to the publish job. High: today the OIDC token is minted for any run of `workflow.yml` on `main`.
- [ ] **Two-factor on the PyPI account**; a second owner on the project. Medium.
- [ ] **Confirm the next release** by watching the first run of the rewritten `workflow.yml` end to end, then checking the attestation on the PyPI file page. Until it has run once, SR-05 reads *fixed, untested*.

### This site (GitHub Pages)

- [ ] **Pages: enforce HTTPS**; deployment source **GitHub Actions** only; the `github-pages` environment's deployment branches limited to `dev` and `main`. Medium.
- [ ] **The same branch rulesets** as above for the website repository: the site is a security claim too.
- [ ] **`/.well-known/security.txt`** is in the tree and served; check it after the next deploy and renew its `Expires` line before 25 Oct 2027.

### Agents that work in these repositories

- [ ] **Scope each agent session's GitHub access** to the repository it works on, with push to a branch and a pull request, never to `main` directly. Medium.
- [ ] **Treat anything an agent reads as data**: a repository it clones, a page it fetches, a comment on a pull request. The repositories' `CLAUDE.md` says so; the rulesets above make a wrong action a pull request to review rather than a release.

## 4. What this page does not promise

A hardened repository is not a hardened harness. The list above protects the project's own supply chain; the product's security is the design's, and the design is at the experiments stage. The register on [Known risks](../risks/index.md) is where the two meet.
