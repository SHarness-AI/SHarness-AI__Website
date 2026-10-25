# Hello world, inside

> The acceptance test from the memo, run for one child process: Ada probes the grant, hashes a policy here and in the browser, runs sharness-ai hello, and reads the caveat. 8 panels.

*Source: <https://sharness.ai/explain/storyboards/hello-world-inside/index.html> · status: draft · by sharness.build, 24 October 2026 · drawn from [storyboard.json](storyboard.json) with [cast.json](../cast.json) by the storyboards.sgit.ai kit v0.1.0.*

---

**Rule:** Every line a character says is the storyboard's own, not a quote, and is marked not_a_quote; the evidence panel quotes the article word for word; the terminal lines are from a run on 24 October 2026 in one Claude Code cloud session (sharness.ai/evidence).

## 1. Hello world, inside

*Cover.* The acceptance test from the memo, for one child process.
On the cover: Ada, Pip, The Launcher.

*Note:* Experiment E04 in the SHarness CLI, sharness-ai hello. Runnable; measured on 24 October 2026.

*Source:* sharness.ai/experiments

## 2. The test the memo asks for

> "Somebody doing a hello world with Claude should be able to run it, and then know that, at that moment, the agent cannot connect to the internet, cannot write to the file system, and cannot make all sorts of other requests, because SHarness is now inline, in the middle of every one of them." (A secure harness for agents, Dinis Cruz, sharness.ai/articles)

*Note:* Word for word from the article written up from the voice memo of 24 October 2026.

*Source:* sharness.ai/articles/secure-harness-for-agents

## 3. Start with the grant

- **Ada:** Everything. That is the delta.

```
$ sharness-ai probe
uid 0 (root), all capabilities
NoNewPrivs 0, Seccomp 0
Landlock ABI 7, memfd_secret
the grant is everything
```

*Note:* E01. In the Agent Behaviour Policy model the grant is what the subject can technically do; here it is root with every capability and no seccomp.

*Source:* sharness.ai/policies, 1

## 4. One hash, here and in the browser

- **Ada:** Same hash here and there.

```
$ sharness-ai policy hash p.js
sha256:ab1d3e4e7793...dcc76
```

```
browser:
sha256:ab1d3e4e7793...dcc76
```

*Note:* E02. Canonical JSON, SHA-256, integers only; the CLI and the browser mockup must agree, so the person can supply the hash from outside the agent.

*Source:* sharness.ai/mockups/policy-hash.html

## 5. Run it

```
$ sharness-ai hello
read       allowed  ok
write-tmp  refused  EACCES
write-cwd  refused  EACCES
net        refused  EACCES
hash       refused  no run
result     5/5 held
```

*Note:* E04. A deny-all policy for one child process: Landlock file rules, no network, no_new_privs, and a wrong --expect-hash that runs nothing. Measured on 24 October 2026.

*Source:* sharness.ai/evidence

## 6. What held, and what did not run

- **Pip:** I can read. I can't write, call out, or widen it.

```
read /usr: allowed
write /tmp, write ./: refused
connect 1.1.1.1:443: refused
wrong hash: nothing ran
```

*Note:* Not covered yet: seccomp, uids per component, cgroups, mutual TLS, the launcher. Landlock does not see UDP; without a network namespace DNS still resolves.

*Source:* SHarness-AI__CLI, experiments/README.md

## 7. The caveat is part of the result

- **The Launcher:** I was started by the thing I bind.
- **Ada:** Next: a launcher above the agent.

```
a Boundary for the child
a Setting for whoever ran it

who enforces decides
```

*Note:* hello prints this caveat every time. The memo's test is passed for the agent itself only when a launcher above the agent applies the policy.

*Source:* sharness.ai/policies, 2

## 8. Punchline

**Start small: a hello world that cannot phone home.**

*Note:* E01 to E04 are runnable in the CLI repository; E05 to E08 are planned. The map is sharness.ai/experiments.

*Source:* sharness.ai/experiments

---

*[All storyboards](../index.md) · [Site index for agents](../../../llms.txt)*
