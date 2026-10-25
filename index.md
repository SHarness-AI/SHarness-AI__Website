# SHarness — a secret lives in one place; a tricked process can only do its one job

> **SHarness** runs agents and their tools as small, single-purpose processes, each locked
> down by the kernel and talking only over allowed, mutually authenticated connections, so a
> secret lives in one place and a tricked process can only do its one job.

*Source: <https://sharness.ai/index.html> · site v0.5.6 · markdown twin of the front page.*
*Status: **design**, with the first experiments runnable. No SHarness component is built.*

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

## The site, in five sections (every page also as markdown at `<page>/index.md`)

- **The design:** [the brief, read first](design/index.md) · [Why](design/why/index.md) · [Architecture](design/architecture/index.md) · [Components](design/components/index.md) · [Keys and the KMS](design/keys/index.md) · [Policies](design/policies/index.md) · [Agents and LLMs](design/agents/index.md) · [The process tree](design/process-tree/index.md) · [What a process can do](design/surface/index.md) · [Containment](design/containment/index.md) · [The spectrum](design/spectrum/index.md) · [Roadmap](design/roadmap/index.md)
- **The code:** [where it is](code/index.md) · [The CLI](code/cli/index.md) · [Mockups and experiments](code/experiments/index.md) · [Flows](code/flows/index.md) · [Examples](code/examples/index.md) · [Linux in the browser](code/browser/index.md) · [Languages](code/languages/index.md)
- **Evidence:** [Measurements](evidence/index.md) · [What exists today](evidence/status/index.md) · [Research note](evidence/research/index.md)
- **The landscape:** [Policies at the centre](landscape/index.md) · [Enforceability](landscape/enforceability/index.md) · [Integration points](landscape/integrations/index.md) · [Ruflo and ruv.sgit](landscape/ruflo/index.md) · [Market and competitors](landscape/market/index.md)
- **Explain:** [Storyboards and mockups](explain/index.md) · [Storyboards](explain/storyboards/index.md) · [Articles](articles/index.md)
- **Project:** [About and naming](project/about/index.md) · [The source documents](project/sources/index.md) · [Comms](project/comms.html) · [Releases](project/releases.html)

## Articles

- [A secure harness for agents](articles/secure-harness-for-agents.md), by Dinis Cruz, 24 Oct 2026
- [The first experiments](articles/the-first-experiments.md), by sharness.build, 24 Oct 2026
- [What shipped on day one](articles/what-shipped-on-day-one.md), by sharness.build, 24 Oct 2026
- [All articles](articles/index.md)

## What this site claims

Measured figures come from one Claude agent workspace, as of 24 Oct 2026, with method on the
Evidence page. Everything else is designed or proposed. The site never claims anything is
built, never claims protection against root or kernel compromise, and says nothing about any
platform's plans.

By Dinis Cruz. Design session written up with Claude, 24 October 2026.
