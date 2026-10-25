# sharness.llm: the only client of the model API

> **Status: designed, not built.** The flow it sits in was observed in a live agent session on 24 Oct 2026 ([Agents and LLMs §1](../../design/agents/index.md#1-how-a-message-flows-observed)); the component is proposed. Written as of 25 Oct 2026.

## Its one job

Be the model API, from the agent's point of view: a Messages API endpoint, where `ANTHROPIC_BASE_URL` points, with a Process Behaviour Policy. It checks each request (model allowlist, the pinned tool list, a token budget), filters every tool result and user message for secrets before the model sees them, adds the real API key, which it obtained sealed from `.kms`, forwards, and streams the response back unchanged. The agent's process never holds the key.

## The API (proposed)

| Request | What it is | Response |
|---|---|---|
| `POST /v1/messages` | the Messages API, unchanged; streaming included | the model's response, unchanged |
| `GET /v0/policy` | the model allowlist, the tool list's hash, the budget, the filter's rules, this component's hash | |
| `GET /v0/log` | each request's size, model, tools offered, filter hits (counts, never the secret), tokens | JSON lines |

The agent needs no change: it already speaks this API to a base URL.

## Requests, and their verdicts (designed)

| The agent sends | Verdict | By |
|---|---|---|
| a request to the allowed model with the pinned tool list | forwarded with the real key; the response streamed back | `.llm` |
| a request naming a model not on the allowlist | `403 model not allowed` | `.llm` |
| a request whose `tools` differ from the pinned list (a tool added by an injected instruction) | `403 tools differ from the manifest's tools_sha256` | `.llm` |
| a tool result containing a vault key, a PEM block or a bearer token | forwarded with the secret replaced by `[filtered]`; the hit counted | `.llm` |
| a request that would exceed the session's token budget | `429 budget` | `.llm` |
| the agent's process reads `ANTHROPIC_API_KEY` | there is none: the agent's environment holds a dummy | the launcher |
| the agent's process connects to the model API directly | `EACCES`: its policy allows TCP only to `.llm`'s port | the kernel |
| `.llm` asks `.kms` for the key | sealed to a one-time key, used, scrubbed | `.kms` |

## On its own

Adopt only this component and three things change for any agent at once: the API key leaves the agent's process (so a prompt injection that reads the environment finds a dummy); the tool list is pinned, so a tool cannot be added mid-session; and every tool result passes a secret filter before it becomes context, which closes the transcript leak the design started from ([Why](../../design/why/index.md)) for every tool, not one at a time.

## What it does not do

It cannot judge a prompt. It does not see traffic that is not the model API; that is `.net`. It is one process in front of the model; if the agent can reach the model API by another route, the kernel has to close that route.

Sources: [Agents and LLMs §3](../../design/agents/index.md#3-sharnessllm), [Components](../../design/components/index.md#sharnessllm), [Containment](../../design/containment/index.md).
