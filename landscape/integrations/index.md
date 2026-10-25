# Integration points: what each product stands in for, and what to translate

> **Status: a map of possibilities, as of 25 Oct 2026.** No vendor has agreed to anything and nothing here has been run against a product. For each kind of product the [market analysis](../market/index.md) found, this page says what it would stand in for in SHarness's terms, what a policy translates into on it, what SHarness would still add, and what to keep as is. The point is the one on the [landscape](../index.md): a distributed design that can mix and match enforcers under one policy hash.

## 1. Outer boundaries: microVMs and isolates

| Product | Stands in for | A policy translates into | SHarness adds inside | Keep |
|---|---|---|---|---|
| Docker Sandboxes | topology B: a microVM per session with credentials injected outside it | the sandbox's network endpoints and files "defined before the run"; the memory row as the VM size | per-component uids, Landlock, the edge matrix, the KMS so the injected credential is never in the agent's process either | their VMM, their credential injection as the upstream of `sharness.kms` |
| Firecracker, E2B, Fly Sprites, Vercel Sandbox, Cloudflare Sandboxes | the hardware ring around a kernel escape | memory, CPU, disk; `network: none` as the VM's network | everything inside the VM | the VM |
| Cloudflare Dynamic Workers | an isolate, not a kernel: no Landlock or namespaces exist | "outbound blocked by default" and credential injection at egress map to `network` and `secrets` | nothing inside (no processes); the policy hash and audit could be carried as metadata | as a target for the policy's network and secret rows only |
| Kubernetes Agent Sandbox, gVisor, Kata | topology C: a pod per harness, identities from SPIRE | `securityContext`, `resources`, `NetworkPolicy` (`policy translate --to kubernetes`); SPIFFE IDs for the session CA's roles | the components as containers in one pod, the KMS as its own Deployment | RuntimeClass for the outer ring |

## 2. Shell sandboxes

| Product | Stands in for | A policy translates into | SHarness adds | Keep |
|---|---|---|---|---|
| Claude Code's sandbox (`@anthropic-ai/sandbox-runtime`) | `sharness.bash` for one agent, transparently | `settings.json` (`policy translate --to claude-code`): `allowWrite`, `allowedDomains`, `strictAllowlist`, `allowUnsandboxedCommands: false` | the rows it cannot express (read allowlist, exec allowlist, ports, memory, pids), the built-in tools and hooks it does not cover, the launcher that makes its settings a Boundary rather than a Setting, the KMS behind its credential mask | bubblewrap and its proxy as the stand-in until `sharness.bash` exists; managed settings for the organisation |
| Codex, Antigravity, Cursor sandboxes | the same for their agents | their modes (read-only, workspace-write) from `files.write`; "network off" from `network: none` | the same | the same |
| bubblewrap, nsjail, landrun | the primitives `sharness.bash` would use | a command line (`policy translate --to bwrap`); landrun takes Landlock rules directly, including TCP ports | a server outside the orchestrator's domain so the sandbox cannot be skipped (E06) | the primitives |
| NVIDIA OpenShell / NemoClaw | `sharness.bash` plus `sharness.llm` plus credentials outside the sandbox, for one agent | its network, filesystem and process policy; approved destinations | per-component split, the edge matrix, the policy hash | its managed inference as a `sharness.llm` back end |

## 3. Tool and MCP gateways

| Product | Stands in for | A policy translates into | SHarness adds | Keep |
|---|---|---|---|---|
| ToolHive | one harnessed app per MCP server with `fs` and `net` | its JSON permission profile (paths, hosts, ports) and `--isolate-network`; its Cedar authorisation for business rules | the uid, Landlock and seccomp inside the container; the policy hash; the KMS for the servers' secrets | its profiles as the first translation target for P2 |
| Docker MCP Gateway | the same, with secrets injected only into the container process | per-tool container settings, `--block-secrets` | the same | its signature verification of images (the "code hash" line of the manifest) |
| Wassette | a tool as a Wasm component with deny-by-default capabilities | the policy's files and endpoints as Wasm capabilities | nothing for tools that compile to Wasm; the rest of the harness around it | it, for those tools |

## 4. LLM gateways and key holders

| Product | Stands in for | A policy translates into | SHarness adds | Keep |
|---|---|---|---|---|
| LiteLLM, Portkey, Kong, Helicone, Bifrost | `sharness.llm`'s routing, budgets and observability | model allowlist, token budget, virtual keys | the lock (its own uid, no files, one port), the pinned tool list, the secret filter on tool results, the real key from the KMS, the policy hash | them behind `sharness.llm`, or `sharness.llm` as a thin policy front for them |
| Cloudflare AI Gateway, OpenRouter | key custody at a provider | bring-your-own-key as the thing the KMS holds | the same | key custody as the upstream |

## 5. Secrets, identity, confidential computing

| Product | Stands in for | A policy translates into | SHarness adds | Keep |
|---|---|---|---|---|
| 1Password's credential broker, Infisical's agent proxy, hoophq Cloak, OpenClaw secrets | `sharness.kms`'s delivery half: the agent sees a placeholder | the secret rows: which placeholder maps to which host | the KMS that never returns the clear key at all (the broker still holds it in a proxy the agent can reach); sealing to one-time keys | the broker as the upstream |
| HashiCorp Vault, AWS Secrets Manager and KMS, AgentCore Identity | the lasting key store behind a session's KMS | the sealed handover's recipient; `seal_to` targets | the session identity, the nonce record, the binding to the caller | them as topology D |
| SPIFFE/SPIRE, Teleport Machine ID | the issuer of the per-component certificates on Kubernetes | the role URIs in the SAN (already SPIFFE-shaped) | the edge matrix checked on both sides | them as the CA in topology C |
| Okta Cross App Access, Entra Agent ID, Keycard, Oasis | the agent's identity to SaaS | nothing in the policy today; a future `identity` row | nothing; they do not confine | them |
| TEEs (Phala, confidential inference) | protection from the operator, a different question | nothing | nothing | them, orthogonal |

## 6. Guardrails, authorisation engines, enterprise platforms

| Product | Stands in for | A policy translates into | SHarness adds | Keep |
|---|---|---|---|---|
| NeMo Guardrails, Lakera, Invariant, LlamaFirewall, Prompt Shields | judgement about intent on an allowed channel | nothing: they are not policy rows; `sharness.llm` and the tool components can call them | the kernel bounds that hold when the classifier is wrong | them, at `sharness.llm` |
| Cedar, OPA, OpenFGA, Permit, Oso | the business rules of `fs`, `net` and `kms` (ops, vault ids, approvals) | the policy's `business` section as Cedar or Rego, where a product already evaluates it | the enforcement in a separate process | them as the decision point |
| Zenity, Obsidian, HiddenLayer, Prisma AIRS, Cisco AI Defense | monitoring, and blocking at API hooks | the audit lines, the policy hash and the barrier kinds as OpenTelemetry or OCSF traces (OWASP's Agent Control Standard) | a kernel-level *boundary* for their dashboards to point at | them as the consumer of the traces |

## 7. Ruflo and ruv.sgit

rUv's stack and the sgit.ai network's integration with it have their own page: [Ruflo and ruv.sgit](../ruflo/index.md). In one line: ruv.sgit compiles a written mandate per agent into Ruflo's policy engine (a Setting, in the agent's process); SHarness would enforce the same mandate below the agent (a Boundary), with each hive worker a harnessed process under its own policy.

## 8. What this page does not claim

Every row is a reading of a product's public documentation on the date the market analysis read it, and a design intent on SHarness's side. Nothing is integrated. The order to try them in is the one on the [landscape](../index.md): the shell sandboxes first (the translation already exists), then ToolHive's profiles for tools, then the Kubernetes topology.

Sources: the [market analysis](../market/index.md) and its sources; [Components: two ways for an app to be compatible](../../design/components/index.md#two-ways-for-an-app-to-be-compatible); [Architecture: deployment topologies](../../design/architecture/index.md#deployment-topologies); [Enforceability](../enforceability/index.md).
