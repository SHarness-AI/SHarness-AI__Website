# The levels: one policy, written at the depth you need

> **Status: proposed, as of 26 Oct 2026.** A proposal from Dinis Cruz's direction of 26 Oct 2026, written by pbp@sharness: the whole of SHarness arranged as levels of abstraction, each simpler than the one below, each compiling into it, so that a person writes at the level they need and everything below is there without being asked for. Nothing on this page is built. The v0 policy, its hash and `sharness-ai run` and `hello` are the only runnable parts, and they sit between levels 3 and 2.

## 1. The claim, checked against what exists

The claim is that SHarness is now a shape that absorbs most curveballs: distributed, one connector away from anything, and able to reach the business logic. Checked against the design pages and the code, as of 26 Oct 2026:

| Claim | Where it is true | Status |
|---|---|---|
| **Distributed by construction** | every door is a small service on a TCP port under mutual TLS; the same protocol runs on one laptop, in containers, on Kubernetes, with a remote KMS, or platform-provided ([topologies A to E](../architecture/index.md#deployment-topologies)) | designed; A measured (24 Oct 2026) |
| **One connector away from anything** | every door declares what it accepts and what it emits, and a chain is valid when hop N emits what hop N+1 accepts ([the mirror rule](../pbp/index.md#6-a-door-and-the-tree-of-doors)); a new system is a new target with the real thing's signature | proposed |
| **All the way to the business logic** | behaviour rows (append only, this field in this range, this row of this table) held by a door, and a Boundary only when the capability rows close every other path ([the rule](../pbp/index.md#4-two-kinds-of-rows-one-policy)) | proposed |
| **Enforced from outside the agent** | a hash the person supplies, a kernel told before `execve` | runnable and measured for one child process ([Evidence §9](../../evidence/index.md#9-the-first-experiments-run-by-the-cli)); the launcher above the agent is the design |

So the shape is right and the parts are not built. The cost of the shape is also real: the full schema ([Policies §4](../policies/index.md#4-schema)) is more than most people will ever write, and a tool that needs it to be useful is not useful. The answer is not a smaller schema. It is levels.

## 2. The idea

The same move the risk work makes with "why does it matter?", asked until the top-level register, made downwards: **every level compiles into the one below, deterministically.** A person writes at the level they need, in that level's nouns. What they wrote is hashed. Its expansion down to the kernel is one canonical form, so the hash of a sentence names, through the chain, the Landlock rules that end up in the kernel. The simplest level is as binding as the deepest, because the person supplies the hash and the launcher verifies every step.

Two things follow. A level never hides what it cannot hold: it reports the unheld rows in its own nouns. And a level never locks a person out of the one below: a document at any level may contain a row from any lower level, passed through unchanged. Go only as deep as you need; it is all there.

## 3. The levels

Six, from the sentence a person says to the ground that refuses. Five are written at; the ground is measured.

| Level | You write | Its nouns | What it compresses away | It emits |
|---|---|---|---|---|
| **5 · Intent** | one sentence with blanks: "contain my agent to *this workspace*, *these sites*, *these secrets*" | agent, workspace, sites, secrets, budget | everything: a stance and three blanks | a level-4 profile with its parameters |
| **4 · Profiles** | a profile's name and its parameters: a coding agent, a tool or MCP server, a newsroom agent, a vault CLI, a hello world | roles of processes | which rows a role needs; the example policies [P0 to P4](../../code/experiments/index.md#the-example-policies) are these | a level-3 policy with the holes filled |
| **3 · Rows in plain nouns** | the policy you would show a manager: files to read and write, sites, a database's tables and operations, commands, secrets, a budget; predicates in words (append only, within this range, once per order) | files, sites, databases, commands, secrets, budget | every mechanism: no ports, no Landlock, no certificates | a level-2 manifest |
| **2 · Doors and targets** | the manifest: `sharness.<door>.<target>`, each door's rows, what each accepts and emits, the edges, twins or live ([the tree](../pbp/index.md#6-a-door-and-the-tree-of-doors)) | doors, targets, rows, edges, hashes | how each row is held | a level-1 configuration per door |
| **1 · Mechanisms** | nothing by hand: Landlock rules, seccomp, cgroups, namespaces, the session CA and certificates, a database's row-level security, a bucket policy, or another enforcer's form (`policy translate`: bubblewrap, Docker, Kubernetes, Claude Code's sandbox) ([the enforcement map](../policies/index.md#5-enforcement-map)) | the kernel's and each system's own nouns | nothing; this is the whole truth of what is applied | syscalls and configurations |
| **0 · The ground** | nothing: the kernel and the real systems refuse or allow | syscalls, sockets, engines | | the measured result (`hello`) |

Today's v0 policy sits between 3 and 2: `files.read` and `write` are level-3 nouns, `connect_tcp_ports` is a level-1 noun let through. The first step this page asks for is a true level-3 form, with sites rather than ports, and `hello` reporting at the level the person wrote.

**Level is not layer.** The [Policies page](../policies/index.md#3-fractal-layers) composes one policy from *layers* L0 to L5 (the OS, the runtime, the application, the component, the subcommand, the invocation), by intersection, all at level 2. A *level* is how much of the schema a person has to read. The two are different axes and this page keeps the words apart.

Each level is one person's universe. At level 5 the universe is "my agent, my workspace, the internet"; at level 3 it is the things a business names in a policy document; at level 2 it is the architecture; at level 1 the kernel. A person at level 5 never sees a door. A person at level 2 sees every door and no syscall.

## 4. Three rules that keep the simple levels honest

1. **Deterministic expansion.** Each statement at level N has exactly one canonical form at level N−1, and the manifest carries the chain of hashes, `sha256:L5 → L4 → L3 → L2 → L1`. The person supplies the hash of what they wrote; the launcher recomputes every expansion and refuses on any mismatch. A simpler level is never a weaker one.
2. **Every level reports in its own nouns.** The four objects of the [ABP](https://riskmandate.ai/abp.html) survive the compression: at level 5 the grant is "today your agent can read every file on this machine and reach every site", the mandate is the sentence, the delta is "it can reach 14 things you did not ask for", and the barrier is "11 of those will be refused by the kernel; 3 are not held by anything here". Simplification never hides an unheld row; it only says it in words the level's reader knows.
3. **The escape hatch.** A document at any level may contain a row from any lower level, passed through unchanged. A level-3 policy may say `sites: [github.com]` and, beside it, one level-2 row that names a door and a target, or one level-1 row that names a port. The compiler passes it down; the report says which level each row came from. That is how a person goes one level deeper for one row and stays simple for the rest.

## 5. Each level is a service, and that is where the power is

The compiler of a level is a process with an accepts and an emits, like any door: it accepts level N and emits level N−1. So the levels are a chain of hops under the mirror rule, exactly as the doors are, and the chain can be cut anywhere and run anywhere:

- **the vendor** ships level 4, the profiles, with its tool;
- **the organisation** runs level 3 to 2: its targets, its proxies (`net.proxy`), its twins, its databases. A developer writing at level 3 cannot name a target the organisation's compiler does not offer, because composition is intersection across levels as it is across layers: a lower level can only narrow;
- **the laptop** runs level 1 to 0: the kernel it has, with what that kernel can hold reported honestly (Landlock ABI 7 holds TCP ports; an older kernel does not).

Who runs a level decides what the level below can be. That is the enterprise story without a product in the request path: the organisation owns one compiler and every policy on every laptop passes through it at launch. And it costs nothing at runtime: the abstraction chain runs once per launch, when the policy is expanded and hashed, not per request.

## 6. Two stacks, one hash

| | The capability stack | The abstraction stack |
|---|---|---|
| **Hops** | doors and targets: `app → fs.s3 → net.direct → the kernel` | levels: `5 → 4 → 3 → 2 → 1 → 0` |
| **Runs** | per request, at runtime | once per launch, when the policy is expanded |
| **Contract per hop** | accepts and emits; the mirror rule | accepts level N, emits level N−1; the same rule |
| **Can be distributed** | yes: a target on another machine, in another language | yes: a level run by the vendor, the organisation or the laptop |
| **Composes by** | intersection across layers (OS, runtime, app, component, invocation) | intersection across levels: a lower level only narrows |
| **Cost** | about 3.2 ms per mutual TLS handshake, measured 24 Oct 2026 | nil at runtime |
| **Meets the other at** | the manifest hash the person supplies | the same hash |

Both are TCP. TCP gives each stack the same two things: an abstraction, because every hop speaks a contract and nothing else, and distribution, because a contract does not care which machine answers. Two stacks, not one, because capability and abstraction are different axes: one says what a running process may do, the other says how much of the schema a person has to read.

## 7. What a person meets, by level

| A person who | Writes at | Sees |
|---|---|---|
| runs a coding agent on a laptop and wants it contained | 5 | one command: contain this agent to this folder and these sites |
| ships a tool or an MCP server | 4 | a profile name and the tool's own parameters, in the tool's README |
| writes the policy for an agent in a business | 3 | files, sites, tables, commands, secrets, budget, in the words of the policy document; the unheld rows named |
| builds or integrates a door, or runs a platform | 2 | the manifest: doors, targets, edges, twins |
| reviews what the kernel was told, or audits a run | 1 | the mechanisms, one per row, with what each does not cover |
| measures | 0 | `hello`, with the date and the kernel |

The site's front page offers three starts today (the browser, Linux, a Claude Code session). The same page, read through the levels, should offer the levels instead: level 5 is the start in sixty seconds, level 3 is the policy page, level 2 is the design, level 1 is the enforcement map, level 0 is the evidence. Nothing on the site moves; what changes is which page a reader is sent to first.

## 8. The prompt, after the levels

What happens to the agent's permission prompt once a policy sits underneath is its own page: [the decision at the door](../decision/index.md). In one line: yes to what the policy allows, silence for what it refuses, a question in the person's words only for what it cannot hold.

## 9. What this page does not claim

- No level's compiler exists. The v0 policy and `run` are one runnable slice between levels 3 and 2; `policy translate` writes level-1 forms for four enforcers and does not run them.
- "Deterministic expansion" is a requirement on the compilers, not a property anything has yet; the canonical form of each level is unwritten.
- Who runs a level is a deployment choice, not a product; no organisation runs one.
- Levels do not add enforcement. Everything a level holds is held by level 1 and refused by level 0; the caveat on every `hello` result (a Boundary for the child, a Setting for the process that applied it) holds at every level.

Sources: Dinis Cruz's direction of 26 Oct 2026 in pbp@sharness's session (the levels; two stacks on TCP; the "why" ladder of the risk work); [the PBP on one page](../pbp/index.md); [Process Behaviour Policies](../policies/index.md); [Architecture](../architecture/index.md); [the example policies](../../code/experiments/index.md#the-example-policies); [Agent Behaviour Policies](https://riskmandate.ai/abp.html).
