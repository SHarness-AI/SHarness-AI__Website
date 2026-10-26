Rule followed: outreach §3.1 (`probe` and `hello` as the first contribution); AGENTS.md §4 (a `hello` run from a new machine goes on the machines page).

**Title:** Run `hello --json` on a machine we have not seen (Debian 12, Fedora, Arch, WSL2, a rootless container) · **Labels:** good first issue, measurement

Every row on [the machines page](https://sharness.ai/evidence/machines/index.html) was run by the project. The claim that the kernel enforces a policy is only as good as the kernels it was checked on. This issue is for the first reports from elsewhere; it needs no code.

**What to do:**

```
pip install git+https://github.com/SHarness-AI/SHarness-AI__CLI@dev
sharness-ai hello --json
```

Open [a hello report](https://github.com/SHarness-AI/SHarness-AI__CLI/issues/new?template=hello-report.yml) and paste the JSON, with where it ran. The machines page says what we expect on each: Debian 12 (Landlock ABI 2, no TCP rules), Fedora and Arch (6 of 6), WSL2 (unknown: the kernel config decides), a container without `CAP_SYS_ADMIN` (files hold; the namespace is refused and Landlock's port rule takes over), a laptop as a normal user (the first run with no root at all).

**What done looks like:** one report per environment, linked from this issue; the row added to the machines page by the website's agents with your name if you want it; this issue closed when the five environments above each have a row.
