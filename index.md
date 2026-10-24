# SHarness — a secret lives in one place; a tricked process can only do its one job

> **SHarness** runs agents and their tools as small, single-purpose processes, each locked
> down by the kernel and talking only over allowed, mutually authenticated connections, so a
> secret lives in one place and a tricked process can only do its one job.

*Source: <https://sharness.ai/index.html> · site v0.2.0 · markdown twin of the front page.*
*Status: **design**. Nothing described here is built yet.*

---

## It started with one gap

A vault key handed to an AI agent was sealed while it travelled and exposed the moment it
arrived: on disk, on the command line and in the agent's transcript. For an agent the worst
leak is the transcript. See [Why: the last metre](why/index.md).

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

## Pages (each also available as markdown at `<page>/index.md`)

- [Why: the last metre](why/index.md) · [Architecture](architecture/index.md) · [Components](components/index.md)
- [Keys and the KMS](keys/index.md) · [Process Behaviour Policies](policies/index.md) · [Agents and LLMs](agents/index.md)
- [Enforcing the process tree](process-tree/index.md) · [Evidence](evidence/index.md) · [Roadmap and open decisions](roadmap/index.md)
- [About and naming](about/index.md) · [The source documents](documents/index.md)

## What this site claims

Measured figures come from one Claude agent workspace, as of 24 Oct 2026, with method on the
Evidence page. Everything else is designed or proposed. The site never claims anything is
built, never claims protection against root or kernel compromise, and says nothing about any
platform's plans.

By Dinis Cruz. Design session written up with Claude, 24 October 2026.
