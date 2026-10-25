# sharness.policy: the manifest

> **Status: designed; the v0 shape is runnable.** `sharness-ai policy hash|check|translate` and seven example policies exist; the manifest that binds a session's components under one hash is designed. Written as of 25 Oct 2026.

## Not a process

The one component that is not a process: a JSON document with one Process Behaviour Policy per component and per app, the session CA certificate's hash, the code hash of every component, and the edge list. It is composed by intersection, so a layer can only narrow, and hashed; the hash is what the person supplies.

```json
{
  "pbp_manifest": 1,
  "harness": "sharness/0.1",
  "session_ca_cert_sha256": "…",
  "components": {
    "kms":  {"policy": "sha256:…", "code": "sha256:…"},
    "net":  {"policy": "sha256:…", "code": "sha256:…"},
    "fs":   {"policy": "sha256:…", "code": "sha256:…"},
    "bash": {"policy": "sha256:…", "code": "sha256:…", "profiles": ["analyse", "build", "admin"]},
    "llm":  {"policy": "sha256:…", "code": "sha256:…", "tools_sha256": "…"}
  },
  "apps": {
    "sgit":        {"policy": "sha256:…", "mode": "harness-aware"},
    "claude-code": {"policy": "sha256:…", "mode": "transparent", "exec_allow": ["node", "rg", "sharness-bash-client"]}
  },
  "edges": [["app","fs"],["app","net"],["app","bash"],["app","llm"],["net","kms"],["llm","kms"],["bash","net"]]
}
```

## What exists today: v0

A v0 policy is the per-process entry: `files` (read, write, exec), `network` (`"none"` or TCP ports), `process` (`no_new_privs`, memory, pids). It hashes identically in Python, in the browser and in the Linux guest ([one hash, three places](../../code/playground/index.html)), and `translate` writes it for bubblewrap, Docker, Kubernetes and Claude Code's sandbox with the gap listed. Seven examples, from a hello world to sgit, are in [the policies folder](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/policies/README.md).

## Every component answers the same question

Each door's `GET /v0/policy` returns its own policy and hash, so a caller, a log, or a person can ask any running component what it is bound by and compare the answer with the manifest. A component whose answer does not match the manifest's hash for it is not the component the person approved.

## What v0 cannot say yet

Hosts (ports only; hosts are `.net`'s allowlist), UDP, uids and seccomp, signing, and layers composed by intersection: the [roadmap](../../design/roadmap/index.md), in that order.

Sources: [Process Behaviour Policies](../../design/policies/index.md), [Components](../../design/components/index.md#sharnesspolicy), [the enforceability matrix](../../landscape/enforceability/index.md).
