# Policy v0: the canonical form and the hash

> **Status: written, as of 26 Oct 2026, from code that runs.** This is the first SHarness standard: the version 0 Process Behaviour Policy as a file, the canonical bytes it is reduced to, the hash that names it, and what an implementation must refuse so that the same policy hashes the same in every language. Three implementations (Python, JavaScript, Go) pass every vector below; the Python CLI is the oracle that generated them. What a policy *means*, its four objects and what makes it binding, is [the PBP on one page](../../../design/pbp/index.md); this page fixes bytes, not meaning. Kept by dev@sharness; the shape is pbp@sharness's.

## 1. The shape

A v0 policy is one JSON object with these keys and no others:

| Key | Must be | Notes |
|---|---|---|
| `pbp` | the integer `1` | the version of the shape |
| `id` | a non-empty string, at most 200 characters, no control characters | the policy's name for people; the hash is its name for machines |
| `layer` | a string, optional | a label in v0 (`invocation`, `session`, `component`, ...); composition by intersection is a later version |
| `notes` | a string, optional | free text for the reader; part of the hash like everything else |
| `files` | an object with `read`, `write`, `exec`, each a list of paths, each optional | a path is absolute, normalised (no `..`, `.`, `//`, no trailing `/`, so it reads as it binds), without control characters; `/` alone is allowed |
| `network` | the string `"none"`, or `{"connect_tcp_ports": [...]}` with integers 1 to 65535 and no other key | v0 says ports, not hosts |
| `process` | an object: `no_new_privs` must be `true` if present; `max_memory_mb` and `max_pids` non-negative integers, optional; no other key | |

Booleans are not integers: `true` where a port or a cap is expected is refused.

## 2. The canonical bytes

The hash is taken over **canonical JSON**, which an implementation produces from the parsed object, never from the file's text:

1. Object keys sorted. Every key v0 allows is ASCII, so the order is the same whether a language sorts by code point (Python, Go) or by UTF-16 code unit (JavaScript); a later version with free keys adopts RFC 8785's rule, UTF-16 order.
2. No whitespace: `,` and `:` as the only separators.
3. UTF-8, with non-ASCII characters written as they are, not as `\uXXXX`. Only `"`, `\` and the control characters below U+0020 are escaped: `\b`, `\f`, `\n`, `\r`, `\t` by name, the rest as `\u00XX` in lower case. U+007F, U+2028, U+2029, `<`, `>` and `&` are written raw. No Unicode normalisation of any kind.
4. Numbers are integers written in decimal with no sign on zero, no leading zeros, no fraction, no exponent.
5. `true`, `false`, `null` as those words.

The hash is `sha256:` followed by the lower-case hexadecimal SHA-256 of those bytes, 71 characters in all.

## 3. What must be refused, so that every language hashes the same

RFC 8785 (JCS) is the target; v0 refuses the inputs where languages would differ instead of canonicalising them:

| Refused | Why |
|---|---|
| any number with a fraction or an exponent in the **text** (`1.5`, `64.0`, `1e2`), not only after parsing | a JavaScript or Go parser reads `64.0` as the integer 64 and would hash what Python refuses; the text is scanned before it is parsed |
| an integer beyond ±9007199254740991 (2^53 - 1) | JavaScript rounds it |
| a string containing a lone surrogate (`"\ud800"`) | it has no UTF-8 form; Go's decoder would silently replace it with U+FFFD, so the raw text is scanned |
| a duplicate key in any object | two values on the page, one in the hash; `JSON.parse` and `json.loads` keep the last silently, so the text is scanned |
| a file larger than 1 MiB; a top-level value that is not an object | a policy is a small object |
| anything §1 does not allow: an unknown key, a relative or unnormalised path, a port out of range, a boolean for an integer, `no_new_privs: false`, `pbp` other than 1 | the shape is closed; what the reader sees is what the kernel binds |

A refusal is a list of problems (`policy check`) or an error (`policy hash`), never a different hash.

## 4. The contract with the process

An enforcer that applies a v0 policy to a process sets `SHARNESS_AI_POLICY_HASH` to the hash and `SHARNESS_AI_POLICY_ID` to the `id` in the process's environment, so a harness-aware program can say what it runs under and refuse, for instance, a clear key on its command line. An enforcer given `--expect-hash sha256:...` refuses to run anything when the file does not hash to it, and exits 125 (runnable in `sharness-ai run`; the launcher's first check, designed). Which rows of the policy an enforcer holds, and as which barrier kind, is the conformance statement on [the PBP on one page §8](../../../design/pbp/index.md#8-what-a-spec-means-here), not this page.

## 5. The test vectors

[`vectors.json`](vectors.json) lists every case with its kind, and for an accept case its hash and its canonical bytes as a string; the cases themselves are under [`vectors/`](vectors/), byte for byte as the oracle read them. An implementation passes when it produces the hash of every accept case and refuses every refuse case. The accept cases are the CLI's eight example policies (P0 to P5 and the two minimal ones), a minimal policy, the same policy with its keys in another order (same hash), a policy whose `notes` carry non-ASCII text, U+2028, `<&>`, every named escape, a control character and DEL, the largest safe integer and a zero cap, and `/` as a path. The refuse cases are one per row of §3.

```
$ curl -sS https://sharness.ai/code/standards/policy-v0/vectors.json | python3 -c "import json,sys; m=json.load(sys.stdin); print(m['counts'], m['oracle'])"
{'accept': 13, 'refuse': 15} {'implementation': 'sharness-ai (Python)', 'repository': 'https://github.com/SHarness-AI/SHarness-AI__CLI', 'commit': '7dcbe05'}
```

Three hashes a reader can check in [the playground](../../playground/index.html) or with any of the implementations:

```
p0-hello-world      sha256:a6244d346ea9d7955c04defba5e67f71ae9867af618fa21d11589c7ef8449032
a01-minimal         sha256:90ec82be5c13db084b1fd40777b79b0ff6822b73efdec394cd88c6dfe661a5da
a03-unicode-notes   sha256:0994ad5f4c128bddb60ecf76e6086770511ce124b015902457aad70594d7bb7f
```

Vectors are generated by `tools/gen_vectors.py` on this site from the CLI checkout beside it, and the tool refuses to publish a case the oracle disagrees with; the manifest names the oracle's commit. Every implementation's CI fetches `vectors.json` and the files it lists ([the registry](../index.md#3-the-implementations)).

## 6. Implementations that pass

| Implementation | Where | Run | Result |
|---|---|---|---|
| Python, the oracle | `sharness_ai/policy.py` in the CLI | `python -m pytest tests/unit/test_policy.py tests/unit/test_security.py` | by construction; the vectors are its output |
| JavaScript, Node 20+ and the browser | `src/policy.js` ([R21](../../../admin/board/index.md#r21) for the repository) | `npm test` | 28 of 28, Node 22, 26 Oct 2026 |
| Go 1.22+ | `policy/policy.go` (R21) | `go test ./...` | 28 of 28, Go 1.24, 26 Oct 2026 |

Two things the second and third implementations taught, now rows of §3: a parser that keeps numbers as doubles cannot tell `64.0` from `64`, and a decoder that repairs lone surrogates hides them; both have to be caught in the text.

## 7. What this standard does not fix

- What a policy means, which rows an enforcer must hold and how it reports barrier kinds: [the PBP on one page](../../../design/pbp/index.md).
- Hosts, UDP, uids, seccomp, signing, layers composed by intersection, behaviour rows and keepers: later versions, each with its own page and vectors; a new optional key leaves every existing v0 hash unchanged, and a v0 implementation refuses the unknown key, which is the right failure.
- Enforcement. Three languages hash a policy the same; one of them, Python, enforces it for a child process today, as a Setting for the process that applies it.

Sources: `sharness_ai/policy.py` at the CLI's `dev` head `7dcbe05` (its docstring is the first draft of §2 and §3); [Policies §10](../../../design/policies/index.md#10-a-v0-that-two-implementations-hash-the-same-runnable); [the PBP on one page](../../../design/pbp/index.md); security@sharness's review 1, which added the integer, surrogate, duplicate-key and path rules; RFC 8785.
