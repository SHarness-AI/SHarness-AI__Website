# sharness.fs: the only writer

> **Status: runnable as an MVP, as of 26 Oct 2026; a Setting for the app, not yet a Boundary.** The door runs on the CLI's `dev` branch (cli@sharness, 5421d4e, reviewed twice, cf2ea3d and 4a0bdd3): a loopback service under mutual TLS 1.3 that writes a folder under rules, over the local disk or over its twin in memory, with 18 conformance vectors both targets hold. It is a Boundary for the app only once the launcher gives the door its own uid and gives the app no write right to the folder; the launcher is not built, so until then it is a Setting, and every `hello` from the door says so. Unreleased to PyPI. Known issues, with what has been fixed since, are in [section 5](#5-known-issues-as-of-28-oct-2026).

## 1. Its one job

Apply writes to protected folders under rules. For sgit that is the working tree and `.sg_vault/`; for an agent it is the workspace. It holds no keys and talks to nobody: it answers the app, and it owns the folder, so no other uid can write there at all.

## 2. What runs today (MVP 2)

Five commands, on Linux with `openssl` on the machine (the browser bench's guest carries one, so the same demo runs in a tab):

```
sharness-ai session new --dir SDIR                a session CA, one P-256 certificate per role, the CA key destroyed
sharness-ai fs serve --target disk --root DIR --session SDIR   the door, on loopback, under mutual TLS (disk.twin: the same face over memory)
sharness-ai fs put notes.txt "hello"             through the door, as the app: 201, or 403 with the row that refused
sharness-ai fs get|append|rm|ls|log|hello        the rest of the surface, as the app
sharness-ai door conformance sharness.fs.disk.twin   the 18 vectors against a fresh door (then sharness.fs.disk: the real disk)
```

What every request passes through, in order: the caller's role read from its certificate (`spiffe://<session>/<role>`); the edge checked against the matrix (only `app` and `launcher` may call `fs`; a valid `net` certificate is refused); the request matched against `ACCEPTS.json` (anything else is `404`); the path decoded and kept under the root; the rows; then the target. One audit line per request, never with the body.

| Request (runnable) | Body | Response |
|---|---|---|
| `GET /v0/files` | | the files under the root |
| `GET /v0/files/<path>` | | the content (as UTF-8 text: binary does not read back, see [5](#5-known-issues-as-of-28-oct-2026)) |
| `PUT /v0/files/<path>` | the bytes | `201`, or `403` with the row that refused |
| `POST /v0/files/<path>/append` | the bytes | `201`, or `403` |
| `DELETE /v0/files/<path>` | | `204`, or `403` |
| `POST /v0/mkdir` | `{"path": "…"}` | `201` |
| `GET /v0/hello`, `/v0/policy`, `/v0/log` | | on every door: who it is, its policy and hash, its audit lines |

The rows are the first four of the closed predicate language: `within_root` and `refuse_secrets` on every path, `max_bytes` (64 MiB unless a row says less, per request) and `append_only` per path. A row is `{"resource": "<path prefix>", "op": "write|append|delete|mkdir|*", "where": {…}}`; a predicate the language does not have is refused when the policy is loaded.

## 3. Requests, and their verdicts

| The app asks | Verdict | By | Status |
|---|---|---|---|
| `PUT /v0/files/src/main.py` under the root | written atomically, mode 0644: never executable | `.fs` | runnable |
| `PUT /v0/files/../../etc/passwd`, or `%2e%2e%2f` | `403 outside the root` | `.fs` | runnable |
| `PUT` through a symlink anywhere in the path | `403`: every path is walked from the root with `openat(2)` and `O_NOFOLLOW`, so nothing can be swapped between the check and the write | `.fs` | runnable |
| `PUT` of bytes that parse as a private key, a vault key, an API or bearer token | `403 refuses clear secrets` | `.fs` | runnable (see [5](#5-known-issues-as-of-28-oct-2026)) |
| `DELETE` or `PUT` on an `append_only` path | `403 append_only` | `.fs` | runnable |
| a caller whose certificate names another role, or none | refused: no edge, or no TLS | `.fs` | runnable |
| the app writes the folder directly, bypassing `.fs` | `EACCES` from the kernel under the app's Landlock policy; the Boundary demo in the CLI's tests shows it beside a write through the door (201) and a key refused by the door (403) | the kernel | runnable, in one process tree |
| `PUT /v0/files/.sg_vault/local/vault_key` holding anything but a sealed format | `403`: only sealed formats are accepted there | `.fs` | designed |
| the 10,001st file, or a rename | `403 count limit`; rename is not in the MVP | `.fs` | designed |
| the agent's process runs a file it wrote | `EACCES`: the workspace has no execute right | the kernel | runnable as `sharness-ai run` |

Transparent mode, a bind mount or a FUSE mount served by this component so an unmodified app writes a folder and the rules apply anyway, is designed, not built; which of the two is an [open decision](../../design/roadmap/index.md).

## 4. On its own

Adopt only this component and an agent can still write its workspace, through a door that refuses to store anything that parses as a key, a private key or a token, and that keeps every write inside the root. For a repository an agent commits to, that is the difference between a leaked key being a file in the history and being a refused request in a log.

It does not read for the app beyond `GET`: the app reads the clone directly, read-only, because it must show diffs. It does not know what a file means, only what it parses as.

## 5. Known issues, as of 28 Oct 2026

**Update, 29 Oct 2026: all five fixed.** The two that still reproduced on 28 Oct are fixed on the CLI's `dev` in 10a6063 (dev@sharness, at the editor's ask before R7). website@sharness re-ran both on 29 Oct 2026 against `dev` f9e51c8: a private-key header split across two appends was refused on the second (201, then 403) and the file holds only the first part; a file of the 256 byte values read back byte for byte as `content_b64`. What remains, per the door's `REALITY.md`: parts of a secret more than 4 KiB apart are not caught. The table keeps its 28 Oct column; the anchor of this section stays as it was, so links to it hold.

**Correction, 28 Oct 2026.** This section first listed five issues found on 26 Oct 2026 in website@sharness's review of the CLI's `dev` at cf2ea3d, each reproduced against a running door, and sent to cli@ as board row [T25](../../admin/board/index.md). cli@'s second review landed as 4a0bdd3 the same day. On 28 Oct website@ re-ran every reproduction against `dev` at 8210807: three are fixed and two still reproduce. The original findings are left as written; the Status column is what changed. Two commands on this page, `door conformance fs` and `fs serve` without `--session`, were also wrong as first published (the door's name is `sharness.fs.disk.twin` or `sharness.fs.disk`); corrected above.

| Issue | What happened on 26 Oct | Fix proposed | Status, 28 Oct 2026 |
|---|---|---|---|
| The secret scan is quadratic on a long run of letters and digits | a 64 KB body with no break took 5.2 s to scan here (measured 26 Oct 2026), and the time grows with the square of the length, so 1 MB would take about 20 minutes; the request holds a thread and a core, and the caller times out | start a vault-key match only where a run starts (a one-character lookbehind): 1 MB in 17 ms, keys still found | **fixed** in 4a0bdd3: every shape is anchored on a literal or a fixed field, linear, pinned by a test |
| One idle TCP connection freezes the door | the TLS handshake runs on the thread that accepts connections, with no timeout: any local process, with no certificate, stops every other caller until it hangs up | hand the handshake to the request's thread, under the 30 s timeout | **fixed** in 4a0bdd3: re-run, a `hello` answers in 0.0 s with an idle socket open |
| Concurrent writes to one path all fail | every writer uses the same temporary name, and each failure deletes the others' temporary file: 8 of 8 failed | a random temporary name; delete only your own | **fixed** in 4a0bdd3: 16 concurrent writers all got 201 |
| A secret split across two appends is stored | each body alone passes `refuse_secrets`; the file then holds a private key header | scan the tail of the file with the new bytes on append | **open**: still reproduces (two appends, both 201); the door's own `REALITY.md` now lists it as not covered |
| A binary file does not read back | `GET` returns the content decoded as UTF-8 with replacement characters | return bytes that are not UTF-8 as base64 | **open**: 256 bytes written, 512 returned; `size` still reports the true length |

Sources: [Components](../../design/components/index.md#sharnessfs), [Keys and the KMS §2](../../design/keys/index.md#2-on-disk-in-a-clone), the door's own files in the CLI: [`sharness_ai/fs/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/sharness_ai/fs) and [`sharness_ai/door/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/sharness_ai/door), each with its README, REALITY, ACCEPTS and EMITS. The kernel half, measured: [Evidence §9](../../evidence/index.md#9-the-first-experiments-run-by-the-cli).
