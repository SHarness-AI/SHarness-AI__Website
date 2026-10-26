Rule followed: outreach §3.1 (real good first issues); AGENTS.md §4 (stdlib only, a test with the change); the brief's criterion 2 (done in one session from the text alone).

**Title:** `policy translate --to landrun`: a fifth target, with its gap list · **Labels:** good first issue, translate

E10 translates a v0 policy to bubblewrap, Docker, Claude Code's sandbox and Kubernetes, and prints for each what the target does not enforce. [landrun](https://github.com/zouuup/landrun) is a small Go CLI that applies Landlock to one command (`--ro`, `--rw`, `--rox`, `--bind-tcp`, `--connect-tcp`, `--env`), so it is the closest target to what `sharness-ai run` does itself.

**Where to look:** the translate module in `sharness_ai/` (the existing four targets are each one function that takes the parsed policy and returns the command line and a list of gaps); `experiments/policies/*.json` for inputs; `tests/unit/` for how the other targets are tested.

**What done looks like:**

- `sharness-ai policy translate experiments/policies/p2-tool-server.json --to landrun` prints a `landrun` command line whose flags carry every path and port the policy names, and a gap list naming what landrun cannot hold (memory and process caps; the hash check; anything the policy says about secrets).
- A unit test per example policy, asserting the flags and the gap list; no network, no landrun binary needed (the target is written, not run, like the other four).
- One paragraph in `experiments/README.md` under E10, and a row in the site's enforceability matrix is noted in the pull request for the website's agents to add.

Standard library only. Say *written, not run* in the README line unless you ran it, in which case say the kernel and the date.
