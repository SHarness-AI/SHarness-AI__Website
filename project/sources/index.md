# The source documents

> **Published verbatim for review.** These are the documents this site was built from, as received on 24 October 2026. The raw markdown is the source of truth; the site's pages port them with the naming rules applied.

## The brief for this site

| Document | What it is |
|---|---|
| [BRIEF-for-website-agent.md](sharness-brief-pack/BRIEF-for-website-agent.md) | identity, seed text, page structure, claim rules, naming rules and open decisions for sharness.ai |

## The design pack (read in order)

| # | Document | What it settles | Ported to |
|---|---|---|---|
| 00 | [00-README.md](sharness-brief-pack/docs/00-README.md) | problem, goals, threat model, glossary, decisions, end state | [Why](../../design/why/index.md), [Roadmap](../../design/roadmap/index.md) |
| 01 | [01-architecture.md](sharness-brief-pack/docs/01-architecture.md) | the original four components, edges, mutual TLS with a session CA, command flows, deployment topologies, refactor path in sgit | [Architecture](../../design/architecture/index.md), [Components](../../design/components/index.md), [Roadmap](../../design/roadmap/index.md) |
| 02 | [02-sealed-key-flow-and-kms.md](sharness-brief-pack/docs/02-sealed-key-flow-and-kms.md) | the sealed handover, the KMS protocol, where keys live and for how long | [Keys and the KMS](../../design/keys/index.md) |
| 03 | [03-process-behaviour-policy.md](sharness-brief-pack/docs/03-process-behaviour-policy.md) | Process Behaviour Policies: schema, layers, hashing, enforcement map, learning from traces, prompt-injection walkthrough | [Process Behaviour Policies](../../design/policies/index.md) |
| 04 | [04-environment-evidence.md](sharness-brief-pack/docs/04-environment-evidence.md) | every probe and measurement, with method and caveats | [Evidence](../../evidence/index.md) |
| 05 | [05-sharness.md](sharness-brief-pack/docs/05-sharness.md) | the generalisation: naming, components, transparent vs harness-aware apps, minimal code | [Architecture](../../design/architecture/index.md), [Components](../../design/components/index.md), [About](../about/index.md) |
| 06 | [06-llm-and-the-agent-loop.md](sharness-brief-pack/docs/06-llm-and-the-agent-loop.md) | how an agent message flows (observed), `sharness.llm`, `sharness.bash`, the dual-LLM split | [Agents and LLMs](../../design/agents/index.md) |
| 07 | [07-enforcing-the-process-tree.md](sharness-brief-pack/docs/07-enforcing-the-process-tree.md) | every process through `sharness.bash`; side doors; safe testing; proof of concept not yet run | [Enforcing the process tree](../../design/process-tree/index.md) |

## How this pack relates to sgit's

The design began as cli.sgit.ai's [sealed vault keys design pack](https://cli.sgit.ai/dev/sealed-vault-keys/index.html). Compared against the sgit pack's documents 00–04 as Dinis Cruz shared them, as of 24 Oct 2026: 01, 02 and 03 here are **identical**; 00 here adds documents 05–07 to the reading list and the note on names; 04 here adds §7, the observation of the agent loop. Nothing in the sgit pack's 00–04 is missing from this one. The sgit pack also has a 05, *compatibility and rollout* (with nothing switched on, sgit behaves exactly as 0.24.0 does; sealed and plain clones side by side; staged rollout), which is sgit-specific and is linked, not republished.

## Memos

| Date | Memo | Written up as |
|---|---|---|
| 24 Oct 2026 | [Voice memo 01: guidance notes for SHarness](memos/2026-10-24-memo-01-secure-harness.md), as transcribed | [A secure harness for agents](../../articles/secure-harness-for-agents.md) |

## The evolution, on cli.sgit.ai

SHarness began as a fix for sgit, and that history is published where it happened:

1. [A vault key that never lands](https://cli.sgit.ai/articles/a-vault-key-that-never-lands.html): the analysis that started it, the morning of 24 October 2026.
2. [Sealed vault keys in sgit: requirements](https://cli.sgit.ai/research/sealed-vault-keys-requirements.html), from an agent that moves vault keys for a living, the same day.
3. [The requirements and the design, side by side](https://cli.sgit.ai/research/sealed-vault-keys-side-by-side.html): the two read against each other and against the code.
4. [Sealed vault keys for sgit: a design pack](https://cli.sgit.ai/dev/sealed-vault-keys/index.html): the sgit-specific design, with its compatibility and rollout document.
5. The SHarness design pack, above: the same design, generalised.

## Known issues in the pack

Published as received, so these remain in the raw files:

- `00-README.md` links `05-the-sharness.md`; the file is `05-sharness.md`.
- Documents 01–04 use the sgit-specific component names (sgit-cli, sgit-fs, sgit-net, sgit-kms); document 05's diagram uses `harness.<role>` where the rest of the pack uses `sharness.<role>`. The site's pages use `sharness.<role>` throughout.
- The pack lists the command name as open; it was settled as `sharness-ai` the same day (see [Roadmap](../../design/roadmap/index.md)).

All content CC BY 4.0.
