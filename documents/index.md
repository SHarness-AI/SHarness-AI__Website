# The source documents

> **Published verbatim for review.** These are the documents this site was built from, as received on 24 October 2026. The raw markdown is the source of truth; the site's pages port them with the naming rules applied.

## The brief for this site

| Document | What it is |
|---|---|
| [BRIEF-for-website-agent.md](../briefs/sharness-brief-pack/BRIEF-for-website-agent.md) | identity, seed text, page structure, claim rules, naming rules and open decisions for sharness.ai |

## The design pack (read in order)

| # | Document | What it settles | Ported to |
|---|---|---|---|
| 00 | [00-README.md](../briefs/sharness-brief-pack/docs/00-README.md) | problem, goals, threat model, glossary, decisions, end state | [Why](../why/index.md), [Roadmap](../roadmap/index.md) |
| 01 | [01-architecture.md](../briefs/sharness-brief-pack/docs/01-architecture.md) | the original four components, edges, mutual TLS with a session CA, command flows, deployment topologies, refactor path in sgit | [Architecture](../architecture/index.md), [Components](../components/index.md), [Roadmap](../roadmap/index.md) |
| 02 | [02-sealed-key-flow-and-kms.md](../briefs/sharness-brief-pack/docs/02-sealed-key-flow-and-kms.md) | the sealed handover, the KMS protocol, where keys live and for how long | [Keys and the KMS](../keys/index.md) |
| 03 | [03-process-behaviour-policy.md](../briefs/sharness-brief-pack/docs/03-process-behaviour-policy.md) | Process Behaviour Policies: schema, layers, hashing, enforcement map, learning from traces, prompt-injection walkthrough | [Process Behaviour Policies](../policies/index.md) |
| 04 | [04-environment-evidence.md](../briefs/sharness-brief-pack/docs/04-environment-evidence.md) | every probe and measurement, with method and caveats | [Evidence](../evidence/index.md) |
| 05 | [05-sharness.md](../briefs/sharness-brief-pack/docs/05-sharness.md) | the generalisation: naming, components, transparent vs harness-aware apps, minimal code | [Architecture](../architecture/index.md), [Components](../components/index.md), [About](../about/index.md) |
| 06 | [06-llm-and-the-agent-loop.md](../briefs/sharness-brief-pack/docs/06-llm-and-the-agent-loop.md) | how an agent message flows (observed), `sharness.llm`, `sharness.bash`, the dual-LLM split | [Agents and LLMs](../agents/index.md) |
| 07 | [07-enforcing-the-process-tree.md](../briefs/sharness-brief-pack/docs/07-enforcing-the-process-tree.md) | every process through `sharness.bash`; side doors; safe testing; proof of concept not yet run | [Enforcing the process tree](../process-tree/index.md) |

## Known issues in the pack

Published as received, so these remain in the raw files:

- `00-README.md` links `05-the-sharness.md`; the file is `05-sharness.md`.
- Documents 01–04 use the sgit-specific component names (sgit-cli, sgit-fs, sgit-net, sgit-kms); document 05's diagram uses `harness.<role>` where the rest of the pack uses `sharness.<role>`. The site's pages use `sharness.<role>` throughout.
- The pack lists the command name as open; it was settled as `sharness-ai` the same day (see [Roadmap](../roadmap/index.md)).

All content CC BY 4.0.
