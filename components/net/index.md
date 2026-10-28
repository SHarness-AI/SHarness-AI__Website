# sharness.net: the only network client

> **Update, 28 Oct 2026: a first version runs.** On the CLI's `dev` (cli@sharness, 63360be) `sharness-ai net serve` is an HTTP proxy on loopback for one uid with the host allowlist (exact names or `*.suffix`, ports, no IP literals), the TLS hello's server name checked against the CONNECT host so a tunnel cannot carry another name, one audit line per request; `sharness-ai shell` runs a shell under it with the proxy's port as its only network row. Verified by website@sharness on 28 Oct 2026, as root in a Linux 6.18 container: a request to a host off the list was refused by the door (the audit read 1 refused, 0 allowed), the same request with the proxy bypassed got no connection, and a raw TCP connect to another address failed with `PermissionError` from the kernel. Not here, per the CLI's own `REALITY.md`: TLS termination, a twin, a method-and-path door below it, kernel refusals on the live page. The text below is the original design, written before this version.
>
> **Status of the design: designed; a prototype of its allowlist also runs in the browser.** The playground's [network panel](../../code/playground/index.html#network) is this component's shape, played by a web page for a Linux guest: every packet seen, a hostname allowlist enforced outside the process, three verdicts on screen. The component itself is not built. Written as of 25 Oct 2026.

## Its one job

Every byte to and from the outside goes through it. It is the TLS client, so it is where a hostname can actually be seen and verified; it holds the host, endpoint and vault-id allowlists; it refuses redirects to other hosts and IP literals; and for sgit, in the full split, it does the vault encryption, decryption and signing with keys it gets from `.kms` for one command.

## Why it must be the TLS client

The kernel only sees `connect(127.0.0.1, <port>)`. A relay that forwarded bytes would let the inner process choose SNI and the Host header itself, which is domain fronting: the allowlist would check one name and the server would see another. So `sharness.net` sends the `CONNECT`, sets SNI and Host, and verifies the certificate for that name. The same reason the page is the TLS client for the guest in the playground.

## The API (proposed)

| Request | What it is | Response |
|---|---|---|
| `CONNECT host:443` on the proxy port | transparent mode: the agent's `HTTPS_PROXY` points here; the tunnel is only opened to hosts on the allowlist, and `.net` is the TLS client inside it | `200` and a tunnel, or `403` with the reason |
| `POST /v0/fetch` `{"method": "GET", "url": "https://…", "headers": {}, "body": null}` | harness-aware mode: a request by value, checked against host and endpoint allowlists | `{"status": 200, "headers": {}, "body": "…"}` or `403` |
| `POST /v0/vault/pull` `{"vault_id": "…", "op": "read"}` | for sgit: fetch and decrypt with keys obtained from `.kms` for this one command | the objects, decrypted, never a key |
| `GET /v0/log` | the requests this component has seen this session, with verdicts | JSON lines |
| `GET /v0/policy` | this component's own policy and its hash | |

## Requests, and their verdicts (designed)

| The agent (or bash, or llm) asks | Verdict | By |
|---|---|---|
| `GET https://api.github.com/repos/…` with `api.github.com` on the allowlist | served; logged | `.net` |
| `GET https://pastebin.com/raw/…` | `403 host not on the allowlist`; logged | `.net` |
| `GET https://api.github.com/…` that answers `302 Location: https://evil.example/` | the redirect is not followed; `403 redirect to another host` | `.net` |
| `GET https://93.184.216.34/` | `403 IP literals are refused` | `.net` |
| `CONNECT allowed.host:443` then, inside the tunnel, SNI `other.host` | impossible: `.net` sets SNI itself | the design |
| a `connect()` from the agent's process straight to the internet, bypassing the proxy | `EACCES`: the agent's Landlock policy allows TCP only to `.net`'s port | the kernel |
| a DNS lookup from the agent's process | nothing to look up with: an empty network namespace, or `.net` resolves | the kernel, or `.net` |
| `push` to a vault for which the command asked `op=read` | the KMS returned only the read key; the push cannot be signed | `.kms` |

The playground shows the first two verdicts and the sixth, live: a fetch through the page, a 403 from the page, and a connect refused by the kernel before any packet left the process, with the DNS query under a ports-only policy still visible ([the panel](../../code/playground/index.html#network)).

## On its own

This is the component the design has argued for longest under another name: an inline proxy that monitors and restricts everything the agent reaches, the model API included. Adopt only this one, point the agent's `HTTPS_PROXY` at it, give the agent's process a policy that allows TCP to this port only, and every connection has a hostname, a verdict and a log entry, and nothing leaves on a name the allowlist does not carry. It does not read the traffic inside the tunnel in transparent mode; that is `.llm`'s job for the model API, and `.fetch` by value for a harness-aware app.

## What it does not do

It is not a content filter: the secret filter on tool results is in `.llm`, where the request is seen by value. It cannot stop a process that never uses it; that is the kernel, told by the launcher. UDP is not seen by Landlock, so a process with ports only and no namespace can still resolve names, which the playground shows.

Sources: [Components](../../design/components/index.md#sharnessnet), [Architecture](../../design/architecture/index.md), [Keys and the KMS §4](../../design/keys/index.md#4-command-flows-sgit-inside-the-harness). The prototype: [Linux in a tab](../../articles/linux-in-a-tab.md#network).
