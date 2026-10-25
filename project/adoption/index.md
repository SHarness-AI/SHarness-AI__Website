# Getting users: the review and the plan

> **Status: a plan, as of 25 Oct 2026.** This page is the build agent's review of the site and the code from one angle: a person who could use this, arriving cold. It says what was wrong for that person, what changed in this release because of it, what is still open, who the users are, where to find them, and how to tell whether it is working. It is published because the project is built in the open and because the plan only works if the people it names can read it.

## 1. What the project needs from users

SHarness makes one claim that can be checked by anyone with a Linux machine: a Process Behaviour Policy, named by its hash, is enforced by the kernel on the process it is applied to. The claim is only as strong as the set of kernels, distributions, container runtimes and agent harnesses it was checked on. Today that set is one cloud session, one browser and one emulator. So the first thing users give is not stars or opinions: it is **rows on [the machines page](../../evidence/machines/index.md)**, each a `hello --json` from somewhere we have not run. The second is **policies**: what a real tool, a real MCP server, a real agent session actually needs, in the v0 shape. The third is the hard questions, which the design pages exist to receive.

## 2. The review: what was wrong for a user, and what changed

Read as a visitor who runs agents and has ninety seconds. The site at v0.5.8 was written for a reviewer of a design, and it showed.

| What a visitor met | Why it cost users | v0.5.9 |
|---|---|---|
| A headline about a secret in one place, under a banner saying no component is built | The first thing read was what does not exist; what exists, and what they could do with it, came three screens later | The front page leads with what the kernel enforces today, three ways to start in 60 seconds, and the status as a chip, not a headline |
| Nothing moved; two ASCII diagrams carried the whole explanation, and they overflow on a phone | The one idea (policy, hash, kernel, launcher) is simple and was never shown, only described | Three animated explainers in SVG with no script: the one idea, the `hello` run replayed, the kernel booting in a tab. They run on this site and in the GitHub README |
| "Try it" was the fifth card in the third section | The strongest thing the project has, a kernel in the tab, was below the fold and unlabelled as a demo | The first call to action; a "Try it" group first in the nav |
| `pip install sharness-ai` installs a skeleton that prints its version | The one line every developer tries first does nothing useful; every install line on the site carries a git URL instead | **Open: decision R7.** Merging `dev` into `main` releases v0.2.0 with every experiment. This is the single change that matters most for users, and it is the project lead's to make |
| No way to give feedback that fits the project's own rules | The site measures only with a method, an environment and a date; it gave users no way to add a measurement | `hello --json`, [a two-field issue template](https://github.com/SHarness-AI/SHarness-AI__CLI/issues/new?template=hello-report.yml), and the machines page that publishes every report, failures first |
| No audience named | A tool author, an agent operator and a platform team each need a different first command, and none was offered | "Who it is for": three people, each with the one thing to run |
| Project jargon on the front page: the memo, E04, rungs, the grant, R6 | Internal words tell a visitor the page is not for them | Gone from the front page; kept on the experiments and project pages where each is defined |
| The README on GitHub: a wall of text, no picture, a badge for the release that prints its version | GitHub is where most people will first meet this, and it looked unfinished | The README leads with the animated explainers and the 60-second start; status second, still honest |
| No share card | A link posted anywhere showed no image | An `og:image` for the front page |
| The nav: six groups named for a reviewer (Evidence, Landscape, Explain) | A user looks for Try, Learn, Code | "Try it" added first. Open: fold Explain into Design and Evidence |
| The design pages still draw in ASCII | Their markdown twins need the same text, and the agent-readable format was chosen on purpose | Open: an SVG twin for each of the five design diagrams, kept next to the ASCII, not instead of it |
| The guest in the tab has no network | The port-443 probe shows "allowed but unreachable" instead of a connection that works without a policy and fails under one | Done the same day: v86's `fetch` backend, and an interceptor on the playground that shows every packet and enforces an egress allowlist outside the guest |
| The tab takes 30 to 90 seconds to boot | Most visitors leave before `landlock: Up and running.` | Open: a booted-state snapshot, which v86 supports, so the page opens in seconds |

What the review did not find wrong, and kept: the honesty rules (measured only with method, environment and date; the caveat printed with every result), the markdown twin of every page, the sourced landscape, and the articles. Those are what a user who stays will trust.

## 3. Who the users are

| User | What they do with it today | The first command | What they give back |
|---|---|---|---|
| **People who run coding agents** (a Claude Code session, an orchestrator, a script that calls tools) | start each tool under a policy; translate a policy into their agent's own sandbox settings | `sharness-ai run --policy p2-tool-server.json -- my-tool` | hello reports from real laptops and containers; the policies their tools actually need |
| **Authors of tools and MCP servers** | ship a policy with the tool, so whoever runs it runs it under that hash | `sharness-ai policy hash policy.json` | policies in the wild; the shape v0 lacks (hosts, UDP, uids) |
| **Platform and security teams** | one policy, written once, enforced by bubblewrap, Docker, Kubernetes or Claude Code's sandbox, with the gap listed | `sharness-ai policy translate policy.json --to kubernetes` | the enforceability matrix corrected from use; the hard questions on the containment page |

A fourth group reads but does not run: people deciding whether Process Behaviour Policies, and the Agent Behaviour Policies they come from, are the right shape. They are reached by the design pages and the articles, and they give back arguments.

## 4. Where to find them

Each channel below comes with the one link to carry and the one ask to make. The link is always the front page or the tab demo; the ask is always a hello report.

- **The Landlock community.** The kernel's Landlock project keeps a public list of software that uses it, and its maintainers read reports from real kernels. Ask to be listed; send the machines page. This is the one audience that will check the claims line by line, which is what the project wants.
- **The Claude Code ecosystem.** The skill in the CLI repository runs the experiments inside a session, and `translate --to claude-code` writes the sandbox settings a session can use today. List the skill where Claude Code skills and plugins are listed; write the one-page guide "a policy for your Claude Code tools".
- **Authors of MCP servers.** Offer the smallest thing: a `policy.json` next to a server, and the hash in its README. The MCP community's own discussion channels are where server authors are.
- **Python developers.** Release to PyPI (R7). A package that does what its README says is the channel.
- **Technical news and forums.** The tab demo is the hook: a real kernel boots in the browser and refuses what the policy refuses. Post it where people run things before they read: the "show" threads of the technical forums, and the Linux and security communities.
- **The security communities the project lead already works in.** The OWASP projects on application and AI security are the natural place to ask for review of the containment page and the threat model, which is where the design most needs adversarial readers.
- **The sandbox and container communities.** bubblewrap, Docker and Kubernetes are translation targets, not competitors. A policy that produces a correct `docker run` or a correct NetworkPolicy is a reason for their users to look.
- **The newsroom and the project lead's own channels.** Every article here is already in the newsroom's format, so each can be republished there unchanged; the long-read articles are what to share with people who read.

What not to do: no announcement before R7, because the first thing every reader will type is `pip install sharness-ai`.

## 5. How to tell whether it is working

The site is static and carries no analytics, on purpose, so visits are not counted. What is counted:

- **hello reports**: how many, from how many distinct kernels and distributions, and how many did not hold. The machines page is the dashboard.
- **policies from the wild**: pull requests or issues that add a profile for a real tool.
- **issues on the design pages**: a hard question is worth more than a star.
- GitHub stars and PyPI downloads, as a weak signal, last.

The first target is modest and concrete: ten machines on the machines page that are not ours, and one policy for a tool the project did not write.

## 6. The sixty-second test

Every change to the front page is held to this: a visitor who runs agents should, within sixty seconds of arriving, know what the kernel will enforce for them, have one command to type or one button to press that does it, and know what is not built. If the page cannot pass that test, it goes back.
