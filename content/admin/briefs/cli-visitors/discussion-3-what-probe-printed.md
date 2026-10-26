Rule followed: outreach §3.1 (`probe` as the cheapest contribution); AGENTS.md §4 (every measurement with environment and date).

**Category:** Show and tell · **Pin:** yes

# What did `sharness-ai probe` print on your machine?

```
pip install git+https://github.com/SHarness-AI/SHarness-AI__CLI@dev
sharness-ai probe
```

`probe` is read-only. It prints what a process on your machine can do before any policy applies: uid and capabilities, the kernel and its Landlock ABI, whether `memfd_secret` and cgroups are there, seccomp and NoNewPrivs, and a one-line reading. It prints the names of proxy variables, never their values, and no hostnames or usernames.

Paste the output here with where it ran (laptop, container, CI runner, WSL2, a Claude Code session), and a sentence on whether the reading line matches what you expected. Every environment we have not seen is a row on [the machines page](https://sharness.ai/evidence/machines/index.html); a kernel where a probe says `allowed` where it should not is the most useful thing you can report. If you then run `sharness-ai hello --json`, open [a hello report](https://github.com/SHarness-AI/SHarness-AI__CLI/issues/new?template=hello-report.yml) too.
