# Research note: the published design, read in full

> **Status: a review, as of 24 Oct 2026.** Everything published about SHarness was read end to end by a second agent session on 24 October 2026: the eleven design pages, the two articles, the memo, the eight documents of the design pack, the CLI repository, and the sites and documentation the design points at. This page says what holds up, what to improve, what was improved in this release, and what is still open. Written by sharness.build; the editorial responsibility is Dinis Cruz's.

## 1. What was read

| Source | What | Read |
|---|---|---|
| sharness.ai v0.3.1 | the front page, eleven design pages with their markdown twins, `llms.txt`, the honest column, the CLI page, comms and release history | all of it |
| the two articles | *A secure harness for agents* (from voice memo 01) and *What shipped on day one* | both, and the memo transcript |
| the design pack | the brief for the site and documents 00 to 07, verbatim under `briefs/` | all eight, against the pages ported from them |
| SHarness-AI__CLI | `dev` at commit `0a53a7c`: the package skeleton, the pipeline, the README | all of it |
| storyboards.sgit.ai and api.storyboards.sgit.ai | the format, the quick start, the render guide, the catalogue, the pki series' storyboards and cast, the site repository's README | the parts needed to author storyboards for this site |
| Claude Code documentation | hooks (`PreToolUse`, `updatedInput`), permissions (deny rules, `Bash` as a bare deny), sandboxing | the pages, 24 Oct 2026 |
| this session's own environment | the grant, with the probe (E01): uid 0, all capabilities, Landlock ABI 7, `memfd_secret`, Claude Code 2.1.310 | read-only, names of variables only |

## 2. What holds up

- **The claim labels.** *Measured*, *designed*, *not yet measured*, each with a date and a method, on every page. Nothing read on the site claims to be built. This is rarer than it should be and is the site's main asset; everything in this release keeps it.
- **The threat model is stated and kept to.** Kernel trusted, root out of scope, said on every page where it matters, and the one row of the prompt-injection walkthrough that is *not stopped locally* is printed in the same table as the rows that are.
- **The architecture is one idea applied consistently.** One role, one uid, one policy, one certificate; the edge matrix; the KMS that never returns a clear key; the hash from outside the agent. The pages agree with each other and with the pack.
- **Markdown twins and `llms.txt`.** An agent reads the same text as a person, and the gate fails the release if they drift. The storyboards in this release follow the same rule.
- **The evidence is reproducible in shape.** Each figure has a method; the probes' leftovers are listed; the variance between runs is given.

## 3. What to improve, and what this release did about it

| # | Finding | Done in v0.4.0 | Still open |
|---|---|---|---|
| 1 | **Nothing was runnable.** The design asked for *very simple examples first* and the package did nothing. | E01 to E04 in the CLI (`probe`, `policy hash`, `run`, `hello`), with tests; E04 measured; the ladder on [Mockups and experiments](../experiments/index.md) | E05 to E08; the launcher |
| 2 | **Claude Code's own sandbox was missing from the design** as prior art and as a plug-in point. It does, for Bash, much of what `sharness.bash` would do, and its documented limits (hooks, MCP servers and excluded commands run unsandboxed; hostname-only filtering; an unsandboxed retry) are exactly the side doors the design lists. | the comparison on [Mockups and experiments](../experiments/index.md#what-claude-codes-own-sandbox-already-gives-and-what-sharness-adds); rows on [Agents and LLMs §2](../agents/index.md#2-where-sharness-plugs-in) and [Policies §9](../policies/index.md#9-prior-art-reuse-dont-rebuild) | generating the sandbox's settings from a policy, as one enforcement layer |
| 3 | **An open question had been answered by the documentation.** Agents §2 said a `PreToolUse` hook rewriting a Bash call was *believed yes: verify*. The hooks documentation (read 24 Oct 2026) states `updatedInput` replaces the whole tool input before it runs, and permission rules are evaluated against the rewritten input. | Agents §2 updated; the item moved off Evidence's not-yet-measured list as *documented, not yet exercised* | exercising it on a pinned version |
| 4 | **The policy schema had no version two implementations could hash.** The full schema on Policies §4 is right as a target and too large to start with. | a v0 shape (six keys, integers only) hashed identically by the CLI and by the [browser mockup](../mockups/policy-hash.html); on [The CLI](../cli/index.md#the-v0-policy) | layers by intersection; signing by the root key |
| 5 | **The design had no short form.** Eleven pages, no way in for someone with ten minutes. | three [storyboards](../storyboards/index.md) in the storyboards.sgit.ai kit: the last metre, its one job, hello world inside; each with a markdown script | a fourth on the KMS protocol; the series listed on storyboards.sgit.ai |
| 6 | **The site repository's README called the command `sharness`.** The site and the roadmap say `sharness-ai`. | fixed | |
| 7 | **The CLI page was hand-written HTML with no markdown twin**, listed as missing on the honest column. | the page is now markdown, generated like the design pages | the status and admin pages still have no twin |
| 8 | **The memo's *maybe a skill* had no concrete answer.** | the `sharness-hello` skill in the CLI repository runs E01 and E04 inside a session under the safety rules, and says every time what it does not bind | a skill that installs a launcher above the session: not possible from inside it |
| 9 | **The observed environment moves.** Evidence §7 observed Claude Code 2.1.42; this session ran 2.1.310, with the egress proxy on a different port. Figures tied to a version need the version beside them. | noted on Evidence §9 | re-run the §7 observation when the design is next revised |
| 10 | **Two small things in the published pack** (a broken link, `harness.<role>` in one diagram) are known and listed. | unchanged, by the rule that the pack is verbatim | fix in the pack's next revision (T2) |

## 4. What is still open, in the order to take it

1. **E06, the process-tree proof of concept.** It is the one experiment the design marks *not yet run*, and it decides whether `sharness.bash` can be made impossible to skip. Run it under the safety rules, in a child subtree, and publish every side door's result on Evidence.
2. **E05, the edges as a script.** The mutual TLS measurements exist; making them a command makes them repeatable on a laptop and in Docker.
3. **E08 before E07.** `sharness.llm` needs the real API key from somewhere; a local `sharness.kms` v0 that opens a sealed `m1` and re-seals derived keys is the smaller piece and unblocks the other.
4. **The launcher, as a script above the agent, on a laptop.** The first place the caveat printed by `hello` stops applying: a script starts Claude Code under a policy it cannot widen. Disposable users per session, measured at about 49 ms each in the cloud workspace, belong here.
5. **Policies for the newsroom's agents.** The memo's second user. Their file and network behaviour policies written down are the first real test of the schema.
6. **seccomp, read-only bind mounts, AWS KMS compatibility**: still on the not-yet-measured list.

## 5. What this note does not claim

- The review is one agent's reading on one day. R3 on the [comms board](../admin/comms.html), a review of the design pages by a person, is still open.
- Nothing measured here changes the design's figures; it adds one experiment's result in one environment.
- The comparison with Claude Code's sandbox is against its documentation on 24 Oct 2026, not against its code, and says nothing about any platform's plans.

Sources: every page of this site at v0.3.1; the design pack under [the source documents](../documents/index.md); [experiments/README.md](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/README.md); the Claude Code documentation on [hooks](https://code.claude.com/docs/en/hooks), [permissions](https://code.claude.com/docs/en/permissions) and [sandboxing](https://code.claude.com/docs/en/sandboxing); [api.storyboards.sgit.ai/docs](https://api.storyboards.sgit.ai/docs/index.html).
