# The landscape: policies at the centre

> **Status: a position, as of 25 Oct 2026.** This section is where SHarness meets everything else: the products and projects that do part of the same job, the ones it should plug into, and the ones it should translate its policies into. It starts from the point Dinis Cruz made on 25 October 2026: at the heart of all of this are the behaviour policies. SHarness is a **reference implementation** of Process Behaviour Policies; the other products are less competitors than integration points.

## 1. The thesis, in four steps

1. **A policy says what a process may do.** An [Agent Behaviour Policy](https://riskmandate.ai/abp.html) (riskmandate.ai) describes an agent's mandate, its grant, the delta between them, and the barrier on each capability. A [Process Behaviour Policy](../design/policies/index.md) is the same model applied to a process: files, network, processes, IPC, memory, time, identity, syscalls, the model, secrets ([the whole surface](../design/surface/index.md)), hashed, supplied from outside the agent.
2. **SHarness is one way to enforce it, built to be read.** Every component on the design pages is a policy enforced by something the subject does not include: the kernel, or a separate process. That is the reference implementation: small enough to read in one sitting, every rule traceable to a line of a policy, every claim labelled measured or designed.
3. **Any environment that can enforce the same rules is a valid enforcer.** The design is distributed by construction: the components talk over mutual TLS and the same protocol works on one laptop, in containers, on Kubernetes, with a remote KMS, or with the platform providing the components ([topologies A to E](../design/architecture/index.md#deployment-topologies)). So the parts can be mixed and matched: a microVM vendor's boundary around the outside, a cloud provider's KMS, a sandbox product's bash, SHarness's own `net` and `fs`, all under one policy hash.
4. **Therefore the question to ask of every product is not "is it a competitor" but "which rows of a policy can it enforce, natively, and how do I translate the policy into its form?"** That question has an answer per product and per policy row, and the answer is a matrix: [Enforceability](enforceability/index.md). The translation is a command: `sharness-ai policy translate` ([E10](../code/experiments/index.md)).

## 2. What that changes about the competitive analysis

The [market and competitive analysis](market/index.md) surveyed sandboxes, guardrails, MCP and tool security, LLM gateways, secrets and identity, enterprise platforms and standards, and placed SHarness among them as a process architecture rather than a product. Read through the thesis above, the same survey sorts differently:

| Kind | Examples | In SHarness terms | What to do with it |
|---|---|---|---|
| **outer boundaries** | Firecracker, Docker Sandboxes, E2B, Fly Sprites, Cloudflare Sandboxes, gVisor, Kata, Agent Sandbox | topology B or C: the ring around the whole harness; the answer to a kernel escape | run inside them; translate the policy's resource and network rows into their configuration |
| **shell sandboxes** | Claude Code's sandbox, Codex's, Antigravity's, Cursor's, bubblewrap, nsjail, landrun, OpenShell | `sharness.bash` for one agent | generate their settings from the policy; keep them as the transparent stand-in until `sharness.bash` exists |
| **tool and MCP gateways** | ToolHive, Docker MCP Gateway, Wassette | a harnessed app per tool, with `fs` and `net` | run their servers as harnessed apps; translate the policy into their permission profiles (ToolHive's JSON, Wassette's capabilities) |
| **LLM gateways and key holders** | LiteLLM, Portkey, Cloudflare AI Gateway, OpenRouter | `sharness.llm` without the lock | put them behind `sharness.llm`, or treat `sharness.llm` as a policy-aware front for them |
| **secrets and identity** | 1Password's broker, Infisical, Vault, AgentCore Identity, SPIFFE/SPIRE, Okta, Entra Agent ID | the upstream of `sharness.kms`; the identity format of the session CA | `sharness.kms` fetches from them and never hands the clear key on; SPIFFE IDs are already the certificate format |
| **guardrails and authorisation engines** | NeMo Guardrails, Lakera, Invariant, Cedar, OPA, OpenFGA, Permit, Oso | decisions about intent on an allowed channel: the one thing a kernel bound cannot do | consume their decisions at `sharness.llm` and at the tool components; express the policy's business rules in Cedar where a product already speaks it |
| **enterprise platforms** | Zenity, Obsidian, HiddenLayer, Prisma AIRS, Cisco AI Defense | monitoring and API-hook enforcement with nothing kernel-level to point at | emit the policy hash, the audit lines and the barrier kinds as OpenTelemetry or OCSF traces (OWASP's Agent Control Standard), so they can show a *boundary* instead of an *expectation* |
| **standards** | OWASP ASI Top 10 and Agent Control Standard, NIST CAISI, CSA MAESTRO, Five Eyes guidance, ABP | the vocabulary the policy should be expressible in | map each policy row to the ASI mitigation it implements; keep ABP as the model |

Direct competitors remain, for the one thing none of them does: per-component, kernel-enforced least privilege with the secret in a process the agent can never reach. But even there the right posture is to be their enforcement layer, not their replacement.

## 3. The three questions for any policy and any environment

For a policy P and an environment or tool E, the landscape work reduces to three questions, and the answers are what the enforceability matrix records:

1. **Can P be expressed in E's terms?** (a translation exists, lossless or lossy, and the loss is listed)
2. **Can E enforce it, and as what barrier kind?** (a Boundary enforced above the subject, a Setting the subject can flip, an Expectation in prose, or nothing)
3. **Can the enforcement be verified from outside?** (a hash, an attestation, an audit line, a test like `hello`)

Where all three are yes, the policy runs natively in E. Where the second is "Setting", a launcher above E is needed to make it a Boundary. Where the first is no, that row is SHarness's own component to supply. The matrix is a map of exactly those gaps.

## 4. What is in this section

- [Enforceability](enforceability/index.md): the matrix of policy rows against enforcers, with the barrier kind for each cell, and the command that produces each translation.
- [Integration points](integrations/index.md): product by product, what it stands in for, what to translate, what to keep.
- [Market and competitive analysis](market/index.md): the survey of 24 Oct 2026, every row sourced.
- [Ruflo and ruv.sgit](ruflo/index.md): rUv's stack in SHarness's terms, what ruv.sgit integrated (a mandate per agent compiled into Ruflo's policy engine; memory in sgit vaults), where the two halves meet, a swarm under the harness, what to do first.

## 5. What this does not claim

- No translation on these pages has been run against its target in this project; `policy translate` writes the target's form and lists the gap, and the enforcement by the target is as documented by that target, as of the date read.
- "Integration point" describes a possible relationship, not an existing one; no vendor has agreed to anything.
- The policy is v0: six keys. The matrix will grow with the schema.

Sources: [Agent Behaviour Policies](https://riskmandate.ai/abp.html); [Process Behaviour Policies](../design/policies/index.md); [Architecture: deployment topologies](../design/architecture/index.md#deployment-topologies); the [market analysis](market/index.md) and its sources; Dinis Cruz's message of 25 Oct 2026.
