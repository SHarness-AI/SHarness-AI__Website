# sharness.fs: the only writer

> **Status: designed, not built.** The kernel half, a workspace with no execute right and writes refused outside the policy's paths, is runnable today as `sharness-ai run` and measured; the component that writes under content rules is not. Written as of 25 Oct 2026.

## Its one job

Apply writes to protected folders under rules. For sgit that is the working tree and `.sg_vault/`; for an agent it is the workspace. It holds no keys and talks to nobody: it answers the app, and it owns the folder, so no other uid can write there at all.

## The API (proposed)

| Request | Body | Response |
|---|---|---|
| `PUT /v0/files/<path>` | the bytes; `{"mode": "0644"}` in a header | `201`, or `403` with the rule that refused |
| `POST /v0/files/<path>/rename` | `{"to": "<path>"}` | |
| `DELETE /v0/files/<path>` | | |
| `POST /v0/mkdir` | `{"path": "…"}` | |
| `GET /v0/policy` | | the root it owns, the rules, the hash |

Transparent mode: a bind mount or a FUSE mount served by this component, so an unmodified app writes a folder and the rules apply anyway. Which of the two is an [open decision](../../design/roadmap/index.md).

## Requests, and their verdicts (designed)

| The app asks | Verdict | By |
|---|---|---|
| `PUT /v0/files/src/main.py` under the root | written; exec bit stripped unless policy allows | `.fs` |
| `PUT /v0/files/../../etc/passwd` | `403 outside the root` | `.fs` |
| `PUT` through a symlink that points outside the root | `403 symlink escape` | `.fs` |
| `PUT /v0/files/.sg_vault/local/vault_key` whose bytes parse as a clear vault key | `403 refuses clear keys`: only sealed formats are accepted there | `.fs` |
| `PUT` of a file containing `-----BEGIN PRIVATE KEY-----` or a bearer token | `403 refuses private keys and tokens` | `.fs` |
| `PUT` of a 2 GiB file, or the 10,001st file | `403 size or count limit` | `.fs` |
| the agent's own process calls `open(…, O_WRONLY)` on the workspace, bypassing `.fs` | `EACCES`: the agent's policy lists the workspace as read-only; `.fs`'s uid owns it | the kernel |
| the agent's process runs a file it wrote | `EACCES`: the workspace has no execute right | the kernel |

## On its own

Adopt only this component and an agent can still write its workspace, through a door that refuses to store anything that parses as a key, a private key or a token, and that keeps every write inside the root. For a repository an agent commits to, that is the difference between a leaked key being a file in the history and being a refused request in a log.

## What it does not do

It does not read for the app: the app reads the clone directly, read-only, because it must show diffs. It does not know what a file means, only what it parses as. It is a Boundary for the app's process once the launcher gave that process no write right to the folder; until then, a Setting.

Sources: [Components](../../design/components/index.md#sharnessfs), [Keys and the KMS §2](../../design/keys/index.md#2-on-disk-in-a-clone). The kernel half, measured: [Evidence §9](../../evidence/index.md#9-the-first-experiments-run-by-the-cli).
