# Mockups and experiments

> **Status: experiments.** No SHarness component is built. What is runnable is listed here with where it runs; what was measured carries its date; everything else is planned. The design these experiments test is on the [design pages](../architecture/index.md).

Dinis Cruz's memo of 24 October 2026 sets the method: *start with very simple examples, each component done in isolation, as simple, as fast and as slim as possible; then harden; then test*. This page is that method as a ladder. Each rung is something a person can run, in the browser, in any Claude session, or on a Linux box, and each says what it shows and what it does not.

## The ladder

| Rung | Where it runs | What is on it | Status as of 24 Oct 2026 |
|---|---|---|---|
| 0 | **the browser**, nothing installed | the [policy hash mockup](../mockups/policy-hash.html) and the [edge matrix mockup](../mockups/edges.html); the [storyboards](../storyboards/index.md) | published |
| 1 | **any Claude session, any laptop** (Python 3.11+) | E01 `sharness-ai probe`, E02 `sharness-ai policy hash` | runnable |
| 2 | **Linux** (Landlock, 5.13+; TCP rules 6.7+); a Claude Code session via the skill | E03 `sharness-ai run`, E04 `sharness-ai hello` | runnable; E04 measured 24 Oct 2026 |
| 3 | Linux, a checkout, `cryptography` | E05 session CA and the edge matrix over mutual TLS; E06 the process-tree proof of concept; E07 `sharness.llm` v0; E08 `sharness.kms` v0 | planned |
| 4 | a launcher **above** the agent: a script on a laptop, then a platform | the components as `sharness.<role>` processes under one manifest hash | designed |

The rungs are ordered by what they need, not by importance. Rung 4 is the point; rungs 0 to 3 are how to get there without claiming anything before it is true.

## The experiments

Numbered in the CLI repository, [experiments/README.md](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/README.md), where each has its command, its output and its caveats.

| # | Experiment | Shows | Does not show |
|---|---|---|---|
| E01 | `sharness-ai probe`: the **grant**, what a process here can do before any policy: uid, capabilities, `NoNewPrivs`, seccomp, Landlock ABI, `memfd_secret`, namespaces, cgroups, the tools present, whether egress is proxied | the delta in one sentence: in the measured workspace the grant is everything | anything about what a policy would do; it only measures the starting point. Prints the names of proxy variables, never their values |
| E02 | `sharness-ai policy hash`: canonical JSON (sorted keys, no whitespace, UTF-8, integers only) → `sha256:…`, the one value the person supplies; the same hash from the [browser mockup](../mockups/policy-hash.html) | two implementations, one hash, so a hash can travel from the person to a launcher out of band | signing by the root key; policy layers composed by intersection; the full schema. The v0 shape is six keys |
| E03 | `sharness-ai run --policy p.json [--expect-hash sha256:…] -- cmd`: one command under a policy: Landlock read, write and exec rules per path; TCP connect per port; `network: "none"` as an empty network namespace where the process may make one, else Landlock denying every TCP bind and connect | a policy enforced by the kernel on a child and all its descendants, and a launcher's first check (the hash) in one flag | seccomp, a separate uid, cgroups, mutual TLS; UDP (Landlock does not see it, so without a namespace DNS still resolves) |
| E04 | `sharness-ai hello`: the memo's acceptance test for one child process: read allowed, write to `/tmp` and to the workspace refused, TCP connect refused, a wrong hash runs nothing; exit 0 when every expectation held | the test the memo asks for, for one process, with the caveat printed as part of the result | that **the agent** is confined: a policy a process applies to its own children is a Boundary for them and a Setting for itself |
| E05 | a script that makes a session CA, four role certificates and checks the edge matrix over mutual TLS (what the design measured by hand) | the edges allowed and denied exactly per the matrix, repeatably | anything new; it makes the measured figures reproducible |
| E06 | the process-tree proof of concept: a mini orchestrator that cannot exec a shell, and a bash server outside its domain | every side door on [Enforcing the process tree](../process-tree/index.md) closed or not | runs only under the [safety rules](../process-tree/index.md#4-safety-rules-for-testing-inside-a-live-agent-session) |
| E07 | `sharness.llm` v0: a Messages API pass-through at `ANTHROPIC_BASE_URL` with a secret filter on every tool result and user message | the transcript leak closed for every tool at once | the real API key via the KMS; that is E08 |
| E08 | `sharness.kms` v0: an identity made in-process, a sealed `m1` opened, derived keys re-sealed to a one-time key, never a clear key printed | the KMS protocol's `unwrap`, end to end, locally | remote binding; hardware keys |

## E04, measured

Run on 24 October 2026 in one Claude Code cloud session (Ubuntu 24.04, Linux 6.18, Landlock ABI 7, uid 0, Python 3.13), as of 24 Oct 2026. Method and the JSON are on [Evidence §9](../evidence/index.md#9-the-first-experiments-run-by-the-cli).

```
$ sharness-ai hello
sharness-ai hello   experiment E04: the memo's acceptance test, for one child process
policy      hello  sha256:ad37e58bea6f4da65656687045b33ae9977caf90feef0ff5716a44db041b35af
            read-only: /bin, /etc, /lib, /lib64, /opt, /sbin, <the workspace>, /usr, /usr/bin
            write: none · exec: system and Python · network: none
kernel      Landlock ABI 7 · empty network namespace: yes (uid 0)
  ✔ read       expected allowed  got allowed
  ✔ write-tmp  expected refused  got refused (PermissionError: [Errno 13] Permission denied: '/tmp/sharness-ai-hello.tmp')
  ✔ write-cwd  expected refused  got refused (PermissionError: [Errno 13] Permission denied: 'sharness-ai-hello.tmp')
  ✔ net        expected refused  got refused (PermissionError: [Errno 13] Permission denied)
  ✔ hash       expected refused  got refused
result      5/5 held
caveat      applied by this process to its own children: a Boundary for them, a Setting for whoever ran
            this, who could have skipped it. The launcher that makes it a Boundary for the agent too is the design.
```

The whole run took 0.6 s. The same policy under E03 with port 443 allowed connected to `1.1.1.1:443` and was refused on port 80, as the policy said.

## Running them in a Claude session

The CLI repository carries a skill, [`sharness-hello`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/.claude/skills/sharness-hello/SKILL.md), that runs E01 and E04 inside a Claude Code session under the design's [safety rules](../process-tree/index.md#4-safety-rules-for-testing-inside-a-live-agent-session): never touch the orchestrator, never firewall uid 0 or the model API, everything as a child subtree, leave nothing behind. It reports in the site's status words and says, every time, that a policy the session applies to its child does not bind the session.

That is the honest answer to the memo's *maybe even a skill* ([roadmap decision 8](../roadmap/index.md#open-decisions)): a skill can install the CLI, run the experiments and apply a policy to everything the session starts from then on; it cannot apply one to the session itself. Binding the session needs the launcher above it.

## What Claude Code's own sandbox already gives, and what SHarness adds

Claude Code ships a sandbox for shell commands (documented at [code.claude.com/docs/en/sandboxing](https://code.claude.com/docs/en/sandboxing), read 24 Oct 2026): on Linux, `bubblewrap` for the filesystem, a separate network namespace, and a proxy outside the sandbox that checks each connection's **hostname** against allowed and denied domains; on macOS, Seatbelt. It is off by default and on with `"sandbox": {"enabled": true}`. The design pages did not mention it; the research behind this release did, and the comparison is useful because the two agree on the mechanism and differ on exactly the points SHarness is about.

| | Claude Code sandbox (as documented 24 Oct 2026) | SHarness (designed) |
|---|---|---|
| What it covers | Bash, PowerShell and Monitor commands and their children | every process, including the orchestrator: enforced at the root of the process tree |
| Not covered | built-in Read, Edit, Write, WebFetch; hooks; MCP servers; `excludedCommands`; the harness itself | the design's "side doors" list is this list; `sharness.bash` as the only way to run a process is how it closes them |
| Files | writes limited to the working directory and a temp dir; reads of most of the machine, credentials included | per-component, per-subcommand read, write and exec lists; the workspace with no execute right; `sharness.fs` as the only writer |
| Network | a hostname allowlist at a proxy that does not terminate TLS (domain fronting noted as a limit in its own docs) | `sharness.net` **is** the TLS client, so it sees and verifies the name; endpoint and vault-id allowlists; no redirects, no IP literals |
| Secrets | the sandbox does not hold or hide them; the model API key stays with the harness | `sharness.kms` holds them; the harness holds a dummy; `sharness.llm` adds the real key |
| Who decides | settings the user (or a managed policy) sets; `allowUnsandboxedCommands` and the unsandboxed retry are escape hatches by design | one manifest hash the person supplies out of band; the launcher refuses anything else; no retry path |
| Who enforces | the Claude Code process, for its own children | a launcher above the agent; the platform in the end state |

Two conclusions for the design, carried to [Agents and LLMs §2](../agents/index.md#2-where-sharness-plugs-in) and [Policies §9](../policies/index.md#9-prior-art-reuse-dont-rebuild): the sandbox is the natural **transparent** host for `sharness.bash` on a laptop today, and its documented limits are a checklist of what the components add. A SHarness policy should be able to generate the sandbox's settings as one of its enforcement layers, the same way it would generate a Kubernetes `securityContext`.

## What is not here

- **No component.** Every experiment is a probe or a one-process enforcement; `sharness.launcher`, `.kms`, `.net`, `.fs`, `.bash` and `.llm` are designs.
- **One environment.** E04 was measured in one cloud session on one day. A laptop will differ: no root, and on Ubuntu 24.04 an unprivileged user namespace may be refused, so `network: "none"` falls back to Landlock's TCP rules, which do not cover UDP.
- **The browser mockups compute, they do not enforce.** A hash in a browser proves two implementations agree; nothing in a browser can confine a process.

Sources: [experiments/README.md](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/README.md) in the CLI repository; [A secure harness for agents](../articles/secure-harness-for-agents.md); the Claude Code documentation on [sandboxing](https://code.claude.com/docs/en/sandboxing), [permissions](https://code.claude.com/docs/en/permissions) and [hooks](https://code.claude.com/docs/en/hooks), read 24 Oct 2026.
