# Flows through the code

> **Status: runnable**, as of 25 Oct 2026, on the CLI's `dev` branch. What happens, module by module and syscall by syscall, when a command is confined and when the acceptance test runs; then the flow the launcher will add, which is designed and not built. Line numbers are from the files on that date and will drift; the function names will not.

## 1. `sharness-ai run --policy p.json --expect-hash sha256:M -- cmd`

```
 cli.main                      parse: --policy, --expect-hash, --verbose, argv after "--"
   │
   ▼
 policy.load(path)             JSON file → dict; refuses non-objects and non-JSON
 policy.check(policy)          the v0 shape: pbp=1, id, files.read/write/exec (absolute paths),
                               network "none" | {connect_tcp_ports}, process.no_new_privs: true
 policy.policy_hash(policy)    canonical bytes (sorted keys, no whitespace, UTF-8, integers only)
                               → "sha256:" + hex                                         ← E02
   │
   ├── expect_hash given and ≠ hash  →  print "refused … Nothing ran.", exit 125
   ├── check found problems          →  exit 125
   ├── landlock.abi() == 0           →  "Landlock is not available", exit 126
   │
   ▼
 run.run: os.fork()
   │
   ├─ parent: waitpid(child) → the child's exit code
   │
   └─ child: run.apply(policy)
        1. network "none"  → run._unshare_net():  unshare(CLONE_NEWNET)
                               EPERM? → unshare(CLONE_NEWUSER | CLONE_NEWNET)
                               still refused? → rely on Landlock TCP rules (UDP uncovered)
        2. landlock.Ruleset(): landlock_create_ruleset(2) with every fs right the ABI knows,
                               + bind/connect TCP (ABI 4+), + signal/abstract-socket scoping (ABI 6+)
        3. for each path:     landlock_add_rule(2) PATH_BENEATH with O_PATH fd and the rights:
                                 read  → READ_FILE | READ_DIR
                                 exec  → EXECUTE | READ_FILE | READ_DIR
                                 write → every right of the ABI
                               a missing path is skipped and reported; a plain file gets file rights only
           for each port:     landlock_add_rule(2) NET_PORT with CONNECT_TCP
        4. ruleset.restrict_self(): prctl(PR_SET_NO_NEW_PRIVS, 1); landlock_restrict_self(2)
                               → final for this process and every descendant, for ever
        5. environ: SHARNESS_AI_POLICY_HASH, SHARNESS_AI_POLICY_ID
        6. os.execvp(cmd)      the command runs under the policy; anything it starts inherits it
           (any failure before exec → stderr, _exit(126))
```

Why fork then apply, and not apply then fork: `restrict_self` is irreversible for the calling process, so it is only ever called in a child. The shell you typed `run` into is never restricted. That is also why the result is a Boundary for the child and a Setting for the caller.

## 2. `sharness-ai hello`

```
 hello.hello()
   │
   ▼
 hello.hello_policy()          a deny-all for *this* interpreter: read and exec the system prefixes,
                               sys.base_prefix and the interpreter's directory; read the workspace;
                               write nothing; network "none"
 policy.policy_hash()          printed, so the person can keep it
   │
   ▼
 write the policy to a temporary file
 for each probe (read, write-tmp, write-cwd, net):
     subprocess: python -m sharness_ai run --policy <tmp> -- python -I -c <probe>     ← the flow above, end to end
     hello._classify(): "allowed" if the probe printed ok; "refused (…)" on PermissionError / OSError
 one more:  run … --expect-hash sha256:000… → must be refused with "Nothing ran" (exit 125)
   │
   ▼
 compare against EXPECT; print the table, "N/5 held", and the caveat
 delete the temporary policy; exit 0 if every expectation held
```

`hello` deliberately goes through the CLI (`python -m sharness_ai run`) rather than calling `run.run` in-process, so the acceptance test exercises the same path a person types.

## 3. `sharness-ai probe`

`probe.probe()` reads `/proc/self/status` (uid, capability sets, `NoNewPrivs`, `Seccomp`), calls `landlock_create_ruleset(2)` with the version flag to get the ABI, tries `memfd_secret(2)` (syscall 447) and closes the fd, lists `/proc/self/ns`, looks at `/sys/fs/cgroup`, reads the relevant keys from `/proc/config.gz`, checks which tools are on the path, and lists the *names* of proxy variables that are set. `probe.render()` prints it as text; `--json` prints the dict. Nothing is written.

## 4. The policy hash, in two implementations

```
 Python (policy.canonical)                       Browser (explain/mockups/policy-hash.html)
   refuse floats                                   refuse non-integers
   json.dumps(obj, sort_keys=True,                 keys sorted by code point, recursively;
     separators=(",", ":"),                        JSON.stringify for strings, integers, booleans, null
     ensure_ascii=False)                           joined with "," and ":"
   .encode("utf-8")                                TextEncoder (UTF-8)
   hashlib.sha256                                  crypto.subtle.digest("SHA-256")
   "sha256:" + hexdigest                           "sha256:" + hex
```

The test suite pins one vector; the deny-all example's hash appears on this site and in the tests, so a change to either implementation fails a build.

## 5. What the launcher adds (designed)

```
 sharness-ai launch --manifest m.json --expect-hash sha256:M -- claude …        (not built)
   1. canonicalise the manifest, hash it, refuse unless it equals M (or carries the root key's signature)
   2. for each component: useradd an ephemeral uid                                            ~49 ms, measured
   3. make a P-256 session CA; issue one certificate per role (SAN URI spiffe://<session>/<role>);
      destroy the CA key; put the CA certificate's hash in the manifest                       24 ms, measured
   4. start sharness.kms under its policy; it makes the session identity, prints k1 only; freeze it
   5. for the orchestrator: apply its Landlock domain (execute allowlist, state folder, two ports),
      drop to its uid, no_new_privs, then exec it                                             E06
   6. per command: start the other components under their policies (new namespaces ~4 ms), run, tear down
   7. at session end: thaw and kill the KMS; delete users, firewall rules, sockets
```

Steps 2, 3, 4 and 6 reuse what `run.apply` already does per process. The new pieces are the session CA (a few dozen lines with `cryptography`) and the orchestrator's domain, which is the process-tree proof of concept, E06.

Sources: the modules `cli.py`, `policy.py`, `landlock.py`, `run.py`, `hello.py` and `probe.py` on the CLI's `dev` branch, 25 Oct 2026; [Components: sharness.launcher](../../design/components/index.md#sharness-launcher); [Enforcing the process tree](../../design/process-tree/index.md).
