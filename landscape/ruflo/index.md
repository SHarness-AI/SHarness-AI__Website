# Ruflo, rUv's stack, and ruv.sgit: where a swarm meets the harness

> **Status: a map, as of 25 Oct 2026**, from Ruflo's own documentation and npm registry entries and from [ruv.sgit.ai](https://ruv.sgit.ai)'s pages, all read that day. Dinis Cruz asked how what Reuven Cohen (rUv, GitHub ruvnet) publishes, and the integration the sgit.ai network did with it, could be leveraged here. The short answer: ruv.sgit already does the top half of the thesis (a written mandate per agent, compiled into Ruflo's policy engine, with memory in sgit vaults); SHarness is the bottom half (the same mandate enforced below the agent, by the kernel and by separate processes). Nothing here is integrated yet.

## 1. The names

"Ruflow" and "RuFlow" are third-party spellings. The upstream project is **Ruflo**, formerly **Claude Flow**, by Reuven Cohen: npm `ruflo` (also `claude-flow` and `@claude-flow/cli`), 3.62.0 published 24 Oct 2026, MIT. The sgit.ai network's integration is **ruv.sgit.ai**: "a Ruflo hive + sgit vaults + Agent Behaviour Policies", built 14 to 15 October 2026 for *Agentic Engineering Live: rUv in London* and since 21 October also the site of the ruv.sgit service, with two founding providers, Dinis Cruz and Mondweep Chakravorty. It says of itself: "This is not rUv's offer, and it does not speak for him."

## 2. rUv's projects, in SHarness terms

| Project | What it is (as published) | Version, date, licence | What matters here |
|---|---|---|---|
| **Ruflo** | "agent meta-harness for Claude Code and Codex": swarms and a hive-mind (a queen and workers, Raft, Byzantine or gossip consensus), memory, federation, guardrails; 98 agents, 314 MCP tools, 26 CLI commands | 3.62.0, 24 Oct 2026, MIT | the orchestrator the design calls "the harnessed app": it routes, spawns and remembers. Its policy engine (ADR-324) has modes legacy (allow all, the default), observe and enforce, allow/deny/approval rules, budgets and hash-chained receipts; its hooks (`tool:pre-call`, `agent:pre-spawn`, `file:pre-write`, Claude Code `PreToolUse` and `SessionStart`) are the plug-in points; its plugins "run with your account's permissions and are not sandboxed" (its README); its hive bootstrap secret is, per its docs, "a speed bump, not a boundary" |
| **agentic-flow** | a cost-optimal model router, self-learning hooks (`pre-command` assesses a command's risk before Bash), 213 MCP tools | 2.1.4, 9 Oct 2026, MIT | hooks as routing: the same shape as [Agents §2](../../design/agents/index.md#2-where-sharness-plugs-in) |
| **ruv-swarm** | Rust and WASM neural swarm orchestration with an MCP server | 1.0.20, 10 Sep 2025, MIT or Apache-2.0 | the ancestor of Ruflo's swarm commands |
| **RuVector** | Rust vector and graph memory with a hash-linked witness log, WASM build, MCP server | 0.3.3, 23 Sep 2026, MIT | its README says filters "are not a complete authorization boundary" and recommends treating retrieved context as untrusted: exactly the case for `sharness.fs` as the sole writer and for the dual-LLM split |
| **MetaHarness** | mints a harness (CLI, agents, skills, scoped memory, `.claude/settings.json` permissions) from a repository, with a signed witness manifest | 0.4.17, 26 Sep 2026, MIT | a generator of the agent's own settings: a Setting, in ABP's terms, that a PBP could be compiled into and a launcher could make a Boundary |
| **RVM** | a bare-metal Rust microhypervisor for agents: capability tokens with seven rights (READ, WRITE, GRANT, REVOKE, EXECUTE, PROVE, GRANT_ONCE) and monotonic attenuation | no release stated; Apache-2.0 or MIT | the closest thing in rUv's stack to a kernel-enforced boundary; ruv.sgit's POC3 maps ABP rows to its rights and finds them "coarser than ABP primitives" |
| **flow-nexus** | a hosted platform: cloud sandboxes, swarms, credits | 0.1.128, 18 Sep 2025; npm says proprietary | a provider in the [outer-boundary](../integrations/index.md#1-outer-boundaries-microvms-and-isolates) row, not verified further |
| **SPARC**, the ADRs | a method (specification, pseudocode, architecture, refinement, completion) and numbered architecture decision records | | method, not a control; ADR-346, a "multi-layer agent security stack", is proposed, not shipped |

Nothing rUv publishes is a kernel-enforced sandbox for the agent process itself, except RVM (bare metal, not used by Ruflo at runtime) and a WASM runtime for untrusted guest agents. That is the gap SHarness fills, and the reason the two stacks fit rather than compete.

## 3. What ruv.sgit integrated, from its own pages

Two things were added to rUv's stack: **a written mandate per agent** (an Agent Behaviour Policy, six roles, 36 rows, a vocabulary of 23 `verb.object.reach` primitives) compiled into Ruflo's policy engine, and **agent memory with history**, encrypted client-side in sgit vaults, one ephemeral vault per run with a branch per worker, measured at close and then deleted, with a public ledger of runs. Seven proofs of concept:

| POC | What it showed | Result, as published |
|---|---|---|
| 1 | the ABP compiled into Ruflo's engine (36 rules and a budget) and run against 11 traced actions | legacy mode allowed all 11 (`legacy-default-allow`); enforce mode stopped 6: 4 denied (`email.send`, `network.fetch.world`, a tester's `file.write`, a researcher's `credential.read` of `~/.aws/credentials`), 2 sent for approval (`repo.push`, `deploy`); receipts valid, 14 Oct 2026 |
| 2 | Ruflo's memory database per role on a branch per role in a vault, restored on a fresh runner | identical memory list; run locally |
| 3 | the ABP mapped to RVM capability rights | rights coarser than the primitives: "the argument for compiling tokens from a mandate" |
| 4 | a browser app on RuVector's WASM build answering "can the coder send email?" offline | published |
| 5 | MetaHarness's generated `settings.json` rendered as ABP rows and diffed | 8 of 10 coder rows not covered by the harness |
| 6 | a runbook for a real Ruflo MCP session in observe mode | written, not run (needs a terminal) |
| 7 | the studio: a hierarchical-mesh hive with Byzantine consensus, eight specialists, seven tasks | 31 Ruflo calls in 15.3 s; the workers were Claude Code subagents, not `hive-mind work`; Ruflo's tamper check fired when a folder was recreated and was not bypassed |

Its own rule for agents working on it is the same as this site's: "Do not weaken a security control to make a demo work." Its runs "were not policy-gated. Enforcement was shown separately, in POC1." And its planned next steps are Ruflo's claims as the allowed-primitives list, compiling CLAUDE.md guidance into a policy bundle, and RuVector allow and deny lists. It does not mention SHarness or Process Behaviour Policies anywhere.

## 4. Where the two halves meet

Read with ABP's barrier kinds: everything ruv.sgit enforces is enforced by Ruflo, in the agent's own process, under the agent's own uid, with the ledger anchored in the agent's home directory. That is a **Setting** for the agent (POC1's enforce mode is real, and the same uid could edit the state file). SHarness's job is to make the same 36 rows a **Boundary**, enforced below the agent, without changing the mandate.

| Point in Ruflo | Today (its documentation; "inferred" where so) | What SHarness adds | How the mandate maps |
|---|---|---|---|
| the hooks `ruflo init` writes into Claude Code's settings, and `ruflo-mods`' in-process function hooks | routing and learning inside the harness process, unsandboxed | one `PreToolUse` hook rewriting Bash to `sharness-bash-client --profile <p>` and checking the policy hash; the launcher, not the hook, stops bypass | `execute.process.self` with its instances becomes a `sharness.bash` profile; `write.file.project` instances become Landlock paths |
| the policy engine (ADR-324): rules on caller-emitted strings, receipts, legacy/observe/enforce | the ABP compiled into it (POC1); a Setting by ABP's own test | a PBP manifest hashed in canonical JSON, supplied out of band, checked by the launcher and by each component; Ruflo's receipts stay as the application audit, SHarness's audit lines carry the hash | the same rows: the ABP is the mandate; Ruflo's rules are layers L4 and L5; kernel and component locks are L1 to L3; the effective policy is the intersection |
| the MCP registry (314 tools, one server process as the harness user) | every MCP server runs with the account's permissions | each MCP server as a harnessed app with its own uid, Landlock, seccomp and certificate; the built-in Bash denied so `sharness.bash` is the only shell | the pinned tools list, hashed, in the `sharness.llm` policy; per-tool edges in the manifest |
| the spawn path (`Task` subagents; `hive-mind spawn`, `spawn --claude`, `hive-mind work`, which skip permission prompts by default; nesting to depth 5) | children inherit the parent's uid, environment and keys (inferred) | `agent:pre-spawn` becomes a request to the launcher: each worker a harnessed process under its own PBP, uid and certificate | one ABP role (queen, coder, tester, reviewer, researcher, documenter) is one PBP; the queen's PBP may request launches and never grant more than its own layer |
| API keys (`ANTHROPIC_API_KEY` in the environment or settings) | visible to the harness, every hook, every MCP server, every subagent (inferred from inheritance) | `ANTHROPIC_BASE_URL` to `sharness.llm`, the real key sealed in `sharness.kms`, a dummy in the agent, the secret filter on tool results, model allowlist, token budget | the ABP's `read.credential.host: no`, with its barrier "secrets only via the supervisor", becomes a Boundary; `write.budget.tenant` becomes the llm budget |
| memory (`.swarm/memory.db`, RuVector; a vault per run in ruv.sgit) | SQLite files writable by the agent; RuVector's own README on filters not being a boundary | `sharness.fs` as the sole writer of the memory folder; vault keys only in `sharness.kms`, re-sealed to `sharness.net` | `memory:pre-store` becomes data; the memory folder is a `write.file.project` instance; vault ids go in the `net` policy |
| networking between agents (federation: Ed25519 identities, a trust ladder, optional WireGuard; the hive over stdio or WebSocket) | application-level trust; "network connectivity is the integrator's problem" | `sharness.net` as the only client, allowlisted hosts and vault ids, an empty namespace for everything else, mutual TLS between components | `send.endpoint.allowed` instances (npm, PyPI) become the net allowlist; `send.endpoint.world: no` becomes default-deny egress |
| the policy's anchor (Ruflo's ledger under `~/.config`; MetaHarness's signed witness manifest) | anchored where the agent can reach | one manifest hash from the person, out of band, or signed by the root key; the launcher refuses mismatches | the ABP's owner and `valid_until` ride along; the hash covers the session CA |

## 5. A swarm under the harness

A Ruflo hive is already the shape the design assumes: many agents with distinct roles, each a candidate for its own process and policy. Today they share one uid, one key and one filesystem. Under the harness, the launcher sits above the queen: the platform starts the launcher; the launcher starts the queen's harness under the queen's PBP; every `agent:pre-spawn` or `Task` call becomes a request to the launcher for a worker under the worker's PBP. The orchestrator keeps routing, consensus and memory; it loses the ability to widen any worker's grant, because each layer only narrows the one above it.

A worker's policy, taken from ruv.sgit's coder role, would say: read and write `src/` and `tests/` through `sharness.fs`; run `build`-profile commands through `sharness.bash`; reach `registry.npmjs.org` and `pypi.org` only, through `sharness.net`; call the model through `sharness.llm` under a daily budget with the tool list pinned; no credential in its environment; push and deploy need a person, enforced outside the worker. Federation across machines is topology C with mutual TLS between `net` components and Ruflo's trust ladder as the application layer above it. The vault-per-run and branch-per-worker pattern gives the audit record a place the worker cannot alter.

This is the [spectrum's](../../design/spectrum/index.md) profile P3, the newsroom agent, with a concrete mandate already written: ruv.sgit's `abp.json` is the first real policy file for it, and compiling it to a PBP is the first thing to try.

## 6. What to do first

1. **Compile ruv.sgit's ABP (36 rows) to v0 PBPs**, one per role, and run each role's commands under `sharness-ai run` in a child subtree: the rows that are files and network become Boundaries today; the rows that are tools and approvals stay in Ruflo's engine until `sharness.llm` and `sharness.bash` exist.
2. **Translate the same policy to Claude Code's sandbox settings** (`policy translate --to claude-code`) and compare with what POC5 found in MetaHarness's settings: which of the 36 rows each covers.
3. **Propose the `agent:pre-spawn` hook as a launcher call** to Ruflo, as data (a policy per role), not code.
4. **Ask ruv.sgit's providers whether a run under the harness is an offer**: "no internet from the run" is already in their task-run offer; the harness is how that becomes a Boundary.

## 7. Not verified

- Star counts and performance claims (self-reported, varying between pages).
- Whether Ruflo's enforce mode intercepts Claude Code's built-in tools or only MCP calls and `claude-code.*` actions through `ruflo-mods`: inferred from its issue tracker and plugin README, not from the ADR text.
- Whether `hive-mind work` spawns children with the inherited environment and keys: inferred from "skip permission prompts by default".
- RVM's runtime behaviour and whether anything in Ruflo calls it.
- The ruv.sgit repository's tree was read through the site's published data files; the GitHub API was refused from the research session.

Sources (all read 25 Oct 2026): [ruv.sgit.ai/llms.txt](https://ruv.sgit.ai/llms.txt), [the POCs](https://ruv.sgit.ai/pocs.html), [architecture](https://ruv.sgit.ai/architecture.html), [the rUv stack](https://ruv.sgit.ai/ruv-stack.html), [Article No. 9](https://ruv.sgit.ai/articles/next-phase.md), [data/abp.json](https://ruv.sgit.ai/data/abp.json), [data/report.json](https://ruv.sgit.ai/data/report.json), [data/rvm-caps.md](https://ruv.sgit.ai/data/rvm-caps.md), [data/notes.md](https://ruv.sgit.ai/data/notes.md); [ruvnet/ruflo](https://github.com/ruvnet/ruflo) (README 3.62.0, `docs/USERGUIDE.md`, `docs/federation/README.md`, the plugin READMEs for ruflo-mods, ruflo-agent, ruflo-aidefence and ruflo-sparc, `SECURITY.md`, the ADR index, ADR-444, issue 3164); [agentic-flow](https://github.com/ruvnet/agentic-flow), [ruv-FANN](https://github.com/ruvnet/ruv-FANN), [ruvector](https://github.com/ruvnet/ruvector), [flow-nexus](https://github.com/ruvnet/flow-nexus), [rvm](https://github.com/ruvnet/rvm), the `metaharness` README; the npm registry for every version and date; [riskmandate.ai/abp](https://riskmandate.ai/abp.html).
