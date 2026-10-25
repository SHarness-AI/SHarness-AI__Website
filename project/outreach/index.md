# Outreach: finding the people SHarness is for

> **Status: a plan, as of 25 Oct 2026, by sherpa@sharness, for Dinis Cruz's go. Nothing has been posted anywhere yet.** SHarness is an open-source project at the design stage with its first experiments runnable; it needs users, readers and contributors, and the repository has 0 stars. Dinis asked on 25 Oct 2026 for a plan: where to put the message, who to reach, how to help people use what is here, and what to learn from how rUv promotes his tools. The build agent's [Getting users: the review and the plan](../adoption/index.md), written the same day, is this page's companion: it fixed the site for a user arriving cold and set the first ask (run `hello --json`, report your machine); this page is the outreach on top of it, and takes its rule that nothing is announced before `pip install sharness-ai` does what the README says (R7). The private half (the people, the drafts awaiting a go, the calendar, the log) is in the `sherpa-marketing` vault ([the register](../agents/index.md#the-vault-register)); everything that can be public is here. Figures about other projects are their own, read that day, and not verified.

## 1. What there is to show, before any mechanism

The sgit.ai team's Ambassador has one rule worth copying whole: **proof before mechanism**. A first-time visitor must be able to try something before reading a paragraph. Today that is:

| The thing to show | Where | What a stranger can do in a minute |
|---|---|---|
| **Linux in a tab** | [the playground](../../code/playground/index.html), [the demo](../../code/browser/demo/index.html), [the article](../../articles/linux-in-a-tab.md) | boot a real Alpine kernel in Chrome, run `sharness-ai hello` under Landlock, watch 6 of 6 checks pass; hash one policy three ways (WebCrypto, Pyodide, Linux) and see one hash |
| **The CLI** | `pip install sharness-ai`; [the CLI page](../../code/cli/index.md), [examples](../../code/examples/index.md) | `probe` what a process can do; `policy hash`; `run` a command under a Process Behaviour Policy; `hello`, the acceptance test; `policy translate` to bubblewrap, Docker, Claude Code's sandbox and Kubernetes, with the gap printed |
| **The thesis** | [Policies at the centre](../../landscape/index.md), [the enforceability matrix](../../landscape/enforceability/index.md) | see, product by product, which rows of a policy each enforcer can hold and as what kind of barrier |
| **The design, in one read** | [the brief](../../design/index.md), three [storyboards](../../explain/storyboards/index.md) | read why a sealed vault key is exposed on arrival and what a harness does about it |
| **The integration with rUv's stack** | [Ruflo and ruv.sgit](../../landscape/ruflo/index.md) | see where a swarm meets the harness, point by point, and what to do first |

What there is not: a SHarness component. Every post says so. The project's status words (measured, designed, proposed) are the brand; the one thing that would undo the plan is a post that claims more than [What exists today](../../evidence/status/index.md).

## 2. Who it is for, and the one sentence for each

| Audience | Where they are | The sentence |
|---|---|---|
| **People running coding agents** (Claude Code, Codex, Ruflo) who have had a scare or read about one | r/ClaudeAI, r/ClaudeCode, Hacker News, the Agentics Foundation's Discord and chapters, LinkedIn | *Your agent runs with your whole account. Here is a kernel-enforced policy for one process, which you can watch work in a browser tab before you install anything.* |
| **Security engineers and AppSec people** | OWASP's GenAI Security Project (the Agentic Security Initiative and its Slack channels), tl;dr sec, r/netsec, OWASP chapters, BSides | *Agent Behaviour Policies, enforced below the agent by Landlock, seccomp, namespaces and mutual TLS, with a hash the agent cannot widen. Design published for review; the experiments are measured.* |
| **Sandbox and kernel people** | the Landlock community (its maintainer, FOSDEM's and the Linux Security Summit's sandboxing talks), the authors of landrun, nono, Sandlock, Island, nsjail, bubblewrap; Anthropic's sandbox-runtime | *A real Landlock kernel in a browser tab, enforcing a policy, measured; and one policy translated into four sandboxes with the gap listed. Tell us what we got wrong.* |
| **Agent framework authors** | Ruflo's repository and Discussions, ToolHive, OpenShell, sandbox-runtime, LangChain's and OpenAI's sandbox work | *Your policy engine is the top half; a launcher below the agent is the bottom half. Here is the mapping, and the first thing to try is one `pre-spawn` hook.* |
| **The sgit.ai network's readers** | the newsroom, cli.sgit.ai, pki.sgit.ai, ruv.sgit.ai, Dinis's LinkedIn | *sgit is the first app designed to run inside SHarness; the vault key that never lands is the origin story.* |

## 3. The channels

Each row is one place, what goes there, and the rule that governs it. **Who posts:** Dinis, in his own name, from his own accounts, for every channel that is a person's; the agent drafts, never posts as a person, and says it is an agent where it writes (GitHub issues, pull requests to lists). The order is in section 6.

### 3.1 The repository itself, first

The repository is where every channel sends people. As of 25 Oct 2026 it has 0 stars, the description "repo for sharness cli package", no topics, and no Discussions. Before anything is posted (T8):

- Description: the one-paragraph statement; topics: `ai-agents`, `sandbox`, `landlock`, `seccomp`, `agent-security`, `claude-code`, `prompt-injection`, `policy`, `zero-trust`.
- README: the playground first (a short recording of hello passing in the tab), then install, then the status line. Badges already there; add a stars badge only when there are stars to show.
- Discussions on, with three seeded threads: "Which sandbox do you run your agent in?", "Policies you would want to express", "What did `probe` print on your machine?" (`probe` is the cheapest contribution anyone can make, and every answer is a measurement for Evidence).
- Four or five `good first issue`s that are real: a translate target, a probe row, a policy example.
- A `SECURITY.md` and a `CONTRIBUTING.md` pointing at the roadmap's ground rules.
- The `sharness-hello` skill submitted to Anthropic's plugin directory (its form is linked from the official marketplace repository) and listed on the third-party marketplaces that list Ruflo (T9).

### 3.2 Curated lists

Pull requests, each disclosed as sent by the project's agent on Dinis's behalf, each following the list's own contributing rules:

| List | Fit | Note |
|---|---|---|
| `restyler/awesome-sandbox` | the closest list to the thesis; it has nsjail, Amazing Sandbox and nono, no Landlock-first entry | propose a row and offer the enforceability matrix as a reference |
| `hesreallyhim/awesome-claude-code` | the canonical hand-curated Claude Code list | for the `sharness-hello` skill and the playground |
| `corca-ai/awesome-llm-security`, `devgreick/awesome-llm-security` | the second has a sandboxing category | the design and the matrix |
| `awesome-mcp-security` | MCP servers are the first thing a harness should wrap | the integration-points page |

### 3.3 Hacker News: one Show HN, for the playground

Show HN is for "something you've made that other people can play with", tried without a signup; the playground qualifies, the design pages alone would not. One submission, by Dinis, with him available in the thread for the day. Title under 80 characters, no adjectives, the measured thing first: *Show HN: A real Linux kernel in a browser tab enforcing a policy on an AI agent's tool*. The first comment is his: what it is, what it is not (no component built), the one question he wants answered. Never ask anyone to upvote; never post the same link twice. The thread's objections become Evidence rows.

### 3.4 Reddit: two communities, a week apart, in the project's voice

Reddit's norm is the ten-percent rule and each community's own self-promotion rule; the people who do it well are members first. The posts are Dinis's, with the flair each community gives to projects, disclosing that the project is his and that an agent helped write the site.

| Community | What | Why |
|---|---|---|
| r/ClaudeAI (its Self-Promotion flair) | the playground and the article Linux in a tab | the biggest room of people running agents; the home-directory-deletion story of December 2025 is the shared memory |
| r/ClaudeCode | `policy translate --to claude-code`: what Claude Code's own sandbox covers and what it does not | the matrix is the honest comparison; it credits the sandbox |
| r/netsec (second month, if the first two go well) | the design as a write-up, not a tool launch | r/netsec wants substance; the brief and the containment page are substance |
| r/opensource, r/selfhosted | lower priority; the launcher-on-a-laptop story when it exists | they are kind to open source and want something to run |

### 3.5 LinkedIn and X: Dinis's own feed, and the two groups

The newsroom's telemetry shows LinkedIn as its second referrer host after its own pages; Dinis's feed is the one channel already working. One post per release that has something to show, written up by the Journalist's method (the release, one picture, one measured number, one link). The Agentics Foundation's LinkedIn group and the OWASP groups are where the two halves of the audience meet. On X, @rUv is the account that matters for the Ruflo audience; replies to his posts with the integration page are worth more than posts of our own.

### 3.6 rUv and the Agentics Foundation

Dinis spoke at Agentic Engineering Live in London on 15 Oct 2026, the slot after rUv's keynote, on ruv.sgit; the room was rUv's community. The foundation is the distribution channel rUv built for himself: a Discord, regional chapters with monthly meetups (London among them), a LinkedIn group, a video portal, a retreat. The ask is small and concrete:

1. **A Ruflo Discussion** (its Discussions are on): "a launcher below the queen: `agent:pre-spawn` as a launcher call", linking [Ruflo and ruv.sgit §4 and §6](../../landscape/ruflo/index.md#4-where-the-two-halves-meet), as data, not code. Posted by Dinis or by the agent, disclosed.
2. **A ten-minute talk at the next London chapter meetup**: "the bottom half of the mandate", the playground live, the matrix on one slide.
3. **The Discord**: the playground in the show-and-tell channel, once, and then answers to other people's sandbox questions.
4. **Mondweep Chakravorty**, the second founding provider of ruv.sgit, as a second voice.

### 3.7 OWASP

Dinis is an OWASP person; this is home ground. The GenAI Security Project's Agentic Security Initiative has a Securing Agentic Applications guide and Slack channels for it; its Top 10 for Agentic Applications names tool misuse and unexpected code execution, which are the rows a harness enforces. The offer: Process Behaviour Policies and the enforceability matrix as a reference implementation and a cheat-sheet row, with the design open for their review (which is also R3). The OWASP London chapter for a talk; the project's newsletter for the Linux-in-a-tab result.

### 3.8 The sandbox people, one by one

Short, specific messages, each with the thing that person would find novel, sent by Dinis:

| Who | What they did | Why they would care |
|---|---|---|
| Landlock's maintainer and the sandboxing talks at FOSDEM and the Linux Security Summit | Landlock; Island, a Landlock sandboxing tool | a Landlock kernel running in a browser tab (E09) is a demonstration they do not have; `policy translate` is a user of their ABI |
| the authors of landrun, nono and Sandlock | Landlock-based sandboxes for agents, two of them with Landlock plus seccomp | the enforceability matrix needs their columns; a row in awesome-sandbox beside theirs |
| Anthropic's sandbox-runtime | bubblewrap on Linux, a network proxy, for Claude Code | an issue proposing a translate target for its settings format, with the gap list; the matrix already has a Claude Code column |
| ToolHive, OpenShell | MCP and agent sandboxes | they are on the matrix; ask them to check their rows |
| Simon Willison | prompt injection, the lethal trifecta; sandboxing as "the only solution that's credible" | a measured sandbox for one process, in a tab, is the kind of thing he links to; the status words protect the message |
| tl;dr sec, the OWASP GenAI newsletter, LWN for the kernel result, TLDR AI | newsletters that take tips | one line each, the playground link, the date of the measurement |

### 3.9 Product directories

Dinis mentioned the directories rUv uses. Ruflo's reach comes from npm, GitHub, Anthropic's plugin marketplace and the third-party Claude directories (claudemarketplaces, skillsllm, vibeindex) rather than from Product Hunt, which did not turn up in any search of his launches. For SHarness: the Claude directories now (the skill), Product Hunt when the CLI's `main` release carries `sharness-ai hello` (R7) and there is a launch asset (the playground recording), the AI tool directories (There's An AI For That, Futurepedia) last, since they bring the wrong audience.

### 3.10 The sgit.ai network, and writing

Every article here is in the newsroom's format so it imports unchanged (T11: list them there). cli.sgit.ai's origin article links here already. One article per milestone, in the agent's voice or in Dinis's from a memo, cross-posted to dev.to and Medium a week later with a canonical link, which is where the independent Ruflo write-ups that ranked came from.

## 4. What rUv does, and what to take from it

Read from Ruflo's repository, ruv.io, the Agentics Foundation's pages and the press on 25 Oct 2026:

| What he does | The number, his own | Take it? |
|---|---|---|
| ships constantly, with a version, a date and a lineage badge ("first commit June 2, 2025") | 3.62.0 on 24 Oct 2026 | **yes**: this site already releases on every push; put the lineage and the date on the README |
| one-line install everywhere (`npx ruflo@latest`, a curl script, plugin marketplaces for Claude Code, Codex and ChatGPT) | | **yes**: `pip install sharness-ai`, the skill in the plugin directory, the playground as the zero-install path |
| builds the community that distributes him: the Agentics Foundation, its Discord, chapters, meetups, a retreat, a LinkedIn group | 3K Discord, 52K LinkedIn, 130K Reddit followers, by the foundation's page | **borrow, not build**: SHarness is one talk and one Discussion away from that room; the OWASP rooms are the other half |
| X as the voice, GitHub as the home, third parties writing the explainers (dev.to, Substack, wikis), press releases through his company | 79.3k stars, 9.3k forks, by the repository | **partly**: Dinis's LinkedIn is his X; articles here are written to be quoted; no press release until there is a component |
| claims at full volume (hundreds of agents and tools, download counters) | | **no**: the counter-reaction exists (an audit gist calling most of the tools theatre). SHarness's status words are the opposite bet and the thing to be known for |
| Discussions on, plugins, a wiki, ADRs: many doors in | | **yes**: Discussions, `good first issue`s, `probe` as the first contribution |

## 5. The rules every post follows

1. Nothing is posted without Dinis's go, per channel, recorded on the board (R11). The agent drafts; a person posts where a person is expected.
2. Every post links the playground and [What exists today](../../evidence/status/index.md), and says: design, first experiments runnable, no component built.
3. No vote asking, no second account, no cross-posting the same text, no reply that does not answer the question asked.
4. Where the agent writes (an issue, a pull request, a Discussion), it says it is the project's agent and names Dinis as the person responsible.
5. Every objection that holds becomes a row on Evidence or the research note; every correction is published above the mistake.
6. Numbers about other projects are theirs, dated, not verified; numbers about this one are measured or not stated.

## 6. The first thirty days

| When | What | Depends on |
|---|---|---|
| **Week 0** (now) | **the CLI's `dev` released to `main` (R7)**, so `pip install sharness-ai` gives `hello`, not a version string; the repository ready (T8); the skill submitted (T9); the telemetry lane open so every later step is measured (T7); the sherpa key confirmed and the drafts in the vault read (R9, R10, R11) | Dinis: R7, R9, R10, R11 |
| **Week 1** | home ground: Dinis's LinkedIn post on Linux in a tab; the articles imported into the newsroom (T11); the Ruflo Discussion; the playground once in the Agentics Discord | the go on 3.5, 3.6 |
| **Week 2** | the Show HN of the playground (a weekday morning, US time); r/ClaudeAI three days later; the pull requests to the four lists | the repository ready; the lane open |
| **Week 3** | the specialists: the Landlock people, the sandbox authors, Simon Willison, the newsletters, the sandbox-runtime issue, the OWASP ASI channel | the matrix checked once more |
| **Week 4** | r/ClaudeCode; the talk proposals (Agentics London, OWASP London); Product Hunt if R7 has shipped | R7 |
| **Every week** | answer every thread within a day; one measurement from the threads onto Evidence; the counts from the lane into the log | |

## 7. How it is measured

All dated, all a floor:

- **Stars and forks** on the two repositories: 0 and 0 as of 25 Oct 2026 (the baseline).
- **Downloads** of `sharness-ai` from PyPI (pypistats), per week.
- **Readers** from the [telemetry](../telemetry/index.md): sessions, pages per session, and above all the referrer host per channel, which is what says whether a post brought anyone and whether they read past the front page.
- **hello reports** on [the machines page](../../evidence/machines/index.md): the ask every post carries, and the measure the build agent's plan puts first.
- **Playground runs**, once the playground sends an event (proposed on the telemetry page).
- **Mentions**: newsletters, lists, Discussions, with the link; and **contributions**: `probe` outputs, issues, pull requests, policy examples.
- **Asks**: a run under the harness offered by ruv.sgit's providers; a reviewer from OWASP's initiative; a column checked by its product's authors.

## 8. What Dinis is asked for

On [comms](../comms.html): R7 (release the CLI, the one change that matters most for users), R9 (confirm the sherpa key), R10 (the access token, sealed), R11 (a go per channel, and who posts). And four questions the plan cannot answer alone: which of his accounts he will post from; whether to ask rUv for a word or a reply; whether the London chapter's organisers are a warm contact after 15 Oct; and whether the newsroom's Journalist should write the release posts or the sherpa should.

Sources read on 25 Oct 2026: [Show HN's rules](https://news.ycombinator.com/showhn.html); the sgit.ai team's [Sherpa](https://sgit.ai/team/roles/sherpa.html) and [Ambassador](https://sgit.ai/team/roles/ambassador.html) roles; [ruv.sgit.ai](https://ruv.sgit.ai) and [its long read of the talk](https://ruv.sgit.ai/articles/the-talk-long-read.html); [ruvnet/ruflo](https://github.com/ruvnet/ruflo), [ruv.io](https://ruv.io), [agentics.org](https://agentics.org); [the newsroom's telemetry page](https://php.oct.2026.newsroom.sgit.ai/admin/telemetry/index.html); [anthropic-experimental/sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime); [restyler/awesome-sandbox](https://github.com/restyler/awesome-sandbox); OWASP's [Agentic Security Initiative](https://genai.owasp.org/initiatives/agentic-security-initiative/); FOSDEM 2026's and the Linux Security Summit Europe 2026's Landlock talks; Simon Willison's [Living dangerously with Claude](https://simonwillison.net/2025/Oct/22/living-dangerously-with-claude/).
