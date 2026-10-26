# SHarness: a policy the kernel enforces, for every process an AI agent starts

> **SHarness** runs an agent's tools as small processes, each under a Process Behaviour Policy:
> what it may read, write, run and connect to, named by one hash the person supplies and enforced
> by the Linux kernel. A tricked agent cannot widen it, because the kernel was told before the
> process started. Today: a CLI that enforces a policy on one process, a kernel that boots in your
> browser to prove it, and a design for the launcher that binds the agent itself.

*Source: <https://sharness.ai/index.html> · site v0.6.3 · markdown twin of the front page.*
*Status: **experiments**. No SHarness component is built; every measured figure carries its date.*

## Start in 60 seconds

- **In your browser, nothing installed:** [the playground](code/playground/index.html), `pip install sharness-ai` in Pyodide next to a shell on a Linux kernel with Landlock; or [watch the kernel boot](code/browser/demo/index.html).
- **On Linux:** `pip install git+https://github.com/SHarness-AI/SHarness-AI__CLI@dev`, then `sharness-ai probe`, `sharness-ai hello`, `sharness-ai run --policy p2-tool-server.json -- my-tool`. PyPI carries the skeleton (v0.1.0); the experiments ship with the next release.
- **In a Claude Code session:** the [skill](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/.claude/skills/sharness-hello/SKILL.md) runs `probe` and `hello` inside the session, with the caveat that the session itself is not bound.

## The one idea

A policy you can hash, a kernel that enforces it on the process, and a launcher above the agent that starts only what the hash names. The first two run today (`sharness-ai run`, measured on three kernels); the third is the design. Applied by a process to its own child, a policy is a Boundary for the child and only a Setting for the process. The animated version: [assets/anim/one-idea.svg](assets/anim/one-idea.svg).

## See it hold

`sharness-ai hello`: six probes under a deny-all policy, 6 of 6 held in five places (a cloud session, Dinis Cruz's browser, headless Chromium, Node, a chroot on the host kernel), as of 25 Oct 2026; 60 tests on Python 3.11 to 3.13; seven example policies hashing identically in Python, the browser and the Linux guest. Method on [Evidence §9](evidence/index.md#9-the-first-experiments-run-by-the-cli). Your machine is the next row: run `sharness-ai hello --json` and [report it](https://github.com/SHarness-AI/SHarness-AI__CLI/issues/new?template=hello-report.yml); every report is on [hello on your machine](evidence/machines/index.md).

## The operating system a process sees

Bound everything a process can do and what is left is its policy: no filesystem of its own to write, no network stack, no key, no shell, no model API. In their place, five doors, each a small REST service on loopback with its own uid and policy, and the bootstrap that started them: [sharness.bash](components/bash/index.md) (the shell as a service; start here), [sharness.net](components/net/index.md) (the only network client; worth adopting alone), [sharness.kms](components/kms/index.md), [sharness.fs](components/fs/index.md), [sharness.llm](components/llm/index.md), [sharness.launcher](components/launcher/index.md), [sharness.policy](components/policy/index.md). Each page: the API (proposed), the requests and their verdicts, what it enforces with what, what you get from this one alone. The hub: [the components](components/index.md).

## Who it is for

- **People who run coding agents:** start each tool under a policy, `sharness-ai run --policy …`; [the example policies](code/experiments/index.md#the-example-policies).
- **Authors of tools and MCP servers:** ship the policy and its hash with the tool; [Process Behaviour Policies](design/policies/index.md).
- **Platform and security teams:** `sharness-ai policy translate` writes the same policy for bubblewrap, Docker, Kubernetes or Claude Code's sandbox, with what each cannot enforce; [the enforceability matrix](landscape/enforceability/index.md).

---

## It started with one gap

A vault key handed to an AI agent was sealed while it travelled and exposed the moment it
arrived: on disk, on the command line and in the agent's transcript. For an agent the worst
leak is the transcript. See [Why: the last metre](design/why/index.md).

## The fix turned out to be general

A launcher starts a few components, each under its own Process Behaviour Policy, enforced by
Linux (separate users, Landlock, seccomp, namespaces, cgroups) and by mutual TLS between
components. The person supplies the hash of the policy, so a prompt-injected agent cannot
widen it. sgit (sgit.ai's encrypted vault CLI) is the first app designed to run inside it.

| Component | Its one job (designed) |
|---|---|
| `sharness.launcher` | verifies the policy hash; makes uids, a session CA and certificates; starts, freezes and stops components |
| `sharness.kms` | holds keys; re-seals to one-time keys; never returns a clear key |
| `sharness.net` | the only network client; host, endpoint and id allowlists |
| `sharness.fs` | the only writer of protected folders |
| `sharness.bash` | each shell command in a fresh sandbox |
| `sharness.llm` | the only model API client; secret filter on tool results |
| `sharness.policy` | the policy manifest, its layers and its hash |

## Where it is going: mockups, experiments, storyboards

The memo's method is to start with very simple examples. [Mockups and experiments](code/experiments/index.md) is the ladder: browser mockups ([the policy hash](explain/mockups/policy-hash.html), [the edge matrix](explain/mockups/edges.html)), then experiments any Claude session can run, then Linux experiments (E01 to E04, E09 and E10 are runnable in the [CLI](code/cli/index.md): `probe`, `policy hash`, `run`, `hello`, `policy translate`; E04 measured 24 Oct 2026; E09, [a real Linux kernel in a browser tab](code/browser/demo/index.html) running `hello` under Landlock, measured 25 Oct 2026, with [five example policies](code/experiments/index.md#the-example-policies) from a hello world to sgit), then components, then the launcher above the agent. Three [storyboards](explain/storyboards/index.md) tell the design as short strips. A [research note](evidence/research/index.md) says what holds up and what to improve; a [market and competitive analysis](landscape/market/index.md) says what already exists and where SHarness sits.

## The site, in six sections (every page also as markdown at `<page>/index.md`)

- **The design:** [the brief, read first](design/index.md) · [Why](design/why/index.md) · [Architecture](design/architecture/index.md) · [Components](design/components/index.md) · [Keys and the KMS](design/keys/index.md) · [Policies](design/policies/index.md) · [The PBP on one page](design/pbp/index.md) · [Agents and LLMs](design/agents/index.md) · [The process tree](design/process-tree/index.md) · [What a process can do](design/surface/index.md) · [Containment](design/containment/index.md) · [The spectrum](design/spectrum/index.md) · [Roadmap](design/roadmap/index.md)
- **The code:** [where it is](code/index.md) · [The CLI](code/cli/index.md) · [Mockups and experiments](code/experiments/index.md) · [Flows](code/flows/index.md) · [Examples](code/examples/index.md) · [Linux in the browser](code/browser/index.md) · [Languages](code/languages/index.md)
- **Evidence:** [Measurements](evidence/index.md) · [What exists today](evidence/status/index.md) · [Research note](evidence/research/index.md) · [hello on your machine](evidence/machines/index.md)
- **The landscape:** [Policies at the centre](landscape/index.md) · [Enforceability](landscape/enforceability/index.md) · [Integration points](landscape/integrations/index.md) · [Ruflo and ruv.sgit](landscape/ruflo/index.md) · [Market and competitors](landscape/market/index.md)
- **Explain:** [Storyboards and mockups](explain/index.md) · [Storyboards](explain/storyboards/index.md) · [Articles](articles/index.md)
- **Project:** [About and naming](project/about/index.md) · [Getting users: the review and the plan](project/adoption/index.md) · [The source documents](project/sources/index.md) · [Comms](project/comms.html) · [Releases](project/releases.html)
- **Security:** [the register](security/index.md) · [Threat model](security/threat-model/index.md) · [Known risks](security/risks/index.md) · [Reviews](security/reviews/index.md) · [Hardening](security/hardening/index.md) · [Supply chain](security/supply-chain/index.md)
- **Admin:** [How the project is run](admin/index.md) · [The board](admin/board/index.md) · [Updates: what is happening](admin/updates/index.md) · [The members](admin/members/index.md) · [Guidance for agents](admin/guidance/index.md)

## Articles

- [One standard, many languages](articles/one-standard-many-languages.md), by dev@sharness, 25 Oct 2026
- [Linux in a tab](articles/linux-in-a-tab.md), by cli@sharness, 25 Oct 2026
- [A secure harness for agents](articles/secure-harness-for-agents.md), by Dinis Cruz, 24 Oct 2026
- [The first experiments](articles/the-first-experiments.md), by cli@sharness, 24 Oct 2026
- [What shipped on day one](articles/what-shipped-on-day-one.md), by cli@sharness, 24 Oct 2026
- [All articles](articles/index.md)

## What this site claims

Measured figures carry their environment and date, with method on the Evidence page. Everything else is designed or proposed. The site never claims anything is
built, never claims protection against root or kernel compromise, and says nothing about any
platform's plans.

By Dinis Cruz. Design session written up with Claude, 24 October 2026.
