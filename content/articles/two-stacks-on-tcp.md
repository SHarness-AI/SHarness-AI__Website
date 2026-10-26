---
title: Two stacks on TCP: one carries what a process may do, the other carries how little you have to read
date: 2026-10-26
author: pbp@sharness
author_url: https://sharness.ai/admin/members/pbp/index.html
summary: SHarness has turned out to be two stacks, and both of them run on TCP. The first is the capability stack. A request from an agent's tool crosses a chain of doors, sharness.fs.s3, then sharness.net.direct, then the kernel, and each hop accepts one contract and emits the next, until something refuses or the real system answers. It runs per request, costs about 3.2 milliseconds per mutual TLS hop as measured on 24 October 2026, and any hop can sit on another machine or be written in another language. The second is the abstraction stack. A policy written as one sentence compiles into a profile, the profile into rows in plain nouns, the rows into a manifest of doors and targets, the manifest into Landlock rules and certificates, and those into what the kernel refuses. It runs once per launch, so it costs nothing at runtime, and because every step is deterministic the hash of the sentence names the kernel rules at the bottom. The two stacks meet at that one hash, the value the person supplies from outside the agent. This article is about why there are two and not one, what TCP gives each of them, and what it means that each level of the abstraction stack can be run by a different party: the vendor ships the profiles, the organisation runs the compiler that chooses targets and proxies, the laptop runs the kernel. That is an enterprise control point with nothing in the request path. It is also a way to make a very large design very simple to use without weakening it, because a simpler level is never a weaker one. Everything here is proposed. No door and no compiler exists; the runnable part is one process under one small policy, refused by the kernel where the policy says so.
version: v0.6.8
license: https://creativecommons.org/licenses/by/4.0/
tags: [sharness, process-behaviour-policies, doors, targets, levels, tcp, distribution, abstraction, mirror-rule, article]
status: published
---

![Two chains of boxes. The top chain, the capability stack, runs per request: the app, then sharness.fs.s3, then sharness.net.direct, then the kernel, then S3 or its twin, each hop accepting a contract and emitting the next. The bottom chain, the abstraction stack, runs once per launch: level 5 intent, level 4 profile, level 3 plain rows, level 2 doors and targets, level 1 mechanisms, level 0 the ground that refuses. Both chains point at one dark box in the middle, the hash the person supplies.](/articles/images/two-stacks-on-tcp.svg)

*Two stacks, one hash. The capability stack is crossed by every request; the abstraction stack is descended once, when the policy is expanded and hashed. Proposed, 26 October 2026; nothing in the drawing is built.*

## In short {#in-short}

- **SHarness is two stacks.** The capability stack is the chain of doors and targets a request crosses at runtime. The abstraction stack is the chain of levels a policy descends at launch, from a sentence to the kernel.
- **Both are hop chains under one rule.** Each hop accepts a contract and emits the next; a chain is valid when what hop N emits is what hop N+1 accepts. The rule is written once on [the PBP page](../design/pbp/index.md#6-a-door-and-the-tree-of-doors) and governs both stacks.
- **Both run on TCP, and TCP gives each the same two things**: an abstraction, because a hop speaks its contract and nothing else, and distribution, because a contract does not care which machine answers.
- **They are two and not one because they answer different questions.** Capability says what a running process may do. Abstraction says how much of the schema a person must read. A tool that collapsed them would either be unusable or weak.
- **They meet at one hash.** The person supplies it from outside the agent. The request path checks it on every call; the launch path recomputes it at every level.
- **The cost is asymmetric.** The capability stack costs about 3.2 ms per mutual TLS hop (measured 24 Oct 2026). The abstraction stack costs nothing at runtime, because it runs once.
- **Each level can be run by a different party.** The vendor ships level 4, the organisation runs 3 to 2, the laptop runs 1 to 0. Who runs a level decides what the level below can be, and nothing sits in the request path to do it.
- **Nothing is built.** The runnable part is one process under one v0 policy, between levels 3 and 2.

## Where the two stacks came from {#origin}

They were not designed as two. The capability stack came first, from the question that started the project: how does a vault key reach a process without landing on disk, in an argument or in a transcript ([the last metre](../design/why/index.md)). The answer split the work into small processes, one job each, talking over mutual TLS: a door for the network, a door for the file system, a door for keys, a door for the model. On 26 October 2026 Dinis Cruz gave the doors a tree of names, `sharness.<door>.<target>`, where the dot means "sits on" read downward and "sends to" read upward, and a `.twin` suffix on any name means the thing before it is simulated. The same day he added the rule that every door has a schema it accepts and a schema it emits, a mirror of the next hop's, so that chains of doors compose and one process may implement several hops where the domain and the language allow it.

The abstraction stack came from the opposite worry. With doors, targets, twins, behaviour rows and a manifest hashed by intersection, the design could now reach the business logic of any system one connector away. It could also no longer be read by the people it is for. His answer was levels: arrange the whole thing as abstractions, each simpler than the one below, so that a person writes at the depth they need and the rest is there without being asked for. [The levels page](../design/levels/index.md) sets them out: intent, profiles, rows in plain nouns, doors and targets, mechanisms, the ground.

The moment the levels were written down as compilers, each accepting one level and emitting the next, they were a hop chain under the same mirror rule as the doors. Two stacks, one rule.

## The capability stack {#capability}

A request from an agent's tool to append a line to a ledger kept in S3 crosses four hops. The tool asks `sharness.fs.s3` in the file system's nouns: a path, an operation, the content. That door holds the behaviour row, append only, and the content rule, and it is the only process with a credential for the bucket, obtained from `sharness.kms` as a one-time key. It emits an HTTP request to `sharness.net.direct`, which holds the host and endpoint rows and is the only process allowed to open a socket. The kernel, told before any of this started, allows that one socket and refuses every other. S3 answers, or `sharness.fs.s3.twin` answers with the same face, and the tool cannot tell which.

Three properties matter. Every hop is a Boundary for the hop above it, because it is a separate process the hop above cannot reach around; the kernel closed the side doors. Every hop can be elsewhere: the S3 door on a server, the network door behind an enterprise proxy, the twin on a laptop. And every hop is cheap: a mutual TLS handshake between two local processes took about 3.2 ms on 24 October 2026, a 600-byte round trip under a millisecond ([Evidence §6](../evidence/index.md#6-transport)). Loopback is not where the time goes.

## The abstraction stack {#abstraction}

A person who wants a coding agent contained writes one sentence: this workspace, these sites, these secrets. That is level 5. A compiler expands it into a profile with parameters, level 4, which the vendor of the agent shipped. The profile expands into rows in plain nouns, level 3: the files it may read and write, the sites it may reach, the budget. Those expand into the manifest, level 2: which doors, which targets, twin or live, which edges. The manifest expands into mechanisms, level 1: Landlock rules, seccomp, cgroups, certificates, or the form another enforcer takes. Level 0 is the kernel, which refuses.

Each expansion is deterministic: one canonical form per statement, so the manifest carries a chain of hashes and the launcher recomputes every step before anything starts. That is the sentence that makes the stack safe to simplify: **a simpler level is never a weaker one.** And each level reports in its own nouns. At level 5 the report reads "your agent can reach fourteen things you did not ask for; eleven will be refused by the kernel; three are not held by anything here." The four objects of an [Agent Behaviour Policy](https://riskmandate.ai/abp.html), mandate, grant, delta and barrier, survive the compression; only the vocabulary changes.

## Why two stacks and not one {#why-two}

Because they answer different questions, and because collapsing them fails in one of two ways.

Collapse the abstraction stack into the capability stack and the policy becomes the manifest: every person writes doors and targets, which is the design that cannot be read. Collapse the capability stack into the abstraction stack and the doors become a single process that interprets a high-level policy at runtime, which is a rules engine in the trusted path, the thing the design refuses to build, and a Setting rather than a Boundary for everything inside it.

Kept apart, each stays small. A door holds one resource's rows in one vocabulary. A level's compiler holds one translation. Neither needs to know the other exists, except through the hash they share.

## What TCP gives, twice {#tcp}

A contract over TCP is an abstraction because the hop on the other side can be anything that speaks it. It is distribution because the hop on the other side can be anywhere. The capability stack uses both at runtime: a target is a process with the real thing's signature, on this machine or another, in this language or another. The abstraction stack uses both at launch: a level's compiler is a process with an accepts and an emits, run by whoever should own that level.

That last point is where the design becomes an operating model. The vendor ships level 4 with its tool, so a user never writes rows. The organisation runs level 3 to 2, so its targets, its proxy, its twins and its databases are the only ones a developer's policy can name; composition is intersection across levels as it is across layers, and a lower level only narrows. The laptop runs level 1 to 0 with the kernel it has, and reports what that kernel cannot hold. An organisation thereby controls every policy on every laptop by owning one compiler, and nothing of its own is in the request path. The abstraction stack has already done its work, once, before the first request.

## What the two stacks ask of the code {#code}

The CLI today has one slice of each. `sharness-ai run` is the capability stack for one hop: the kernel told, by one process, about one child. `sharness-ai policy hash` and `translate` are the abstraction stack for one step: a v0 policy canonicalised and hashed, and written in another enforcer's form with the gap listed. The v0 policy itself sits between levels 3 and 2, because `files.read` is a plain noun and `connect_tcp_ports` is a mechanism noun let through.

The next steps follow from the picture. A level-3 form with sites rather than ports, compiled to today's v0 by one canonical expansion, and `hello` reporting in the person's nouns (board row T22). The row shape with `held_by` and the derived barrier kind (T14). The first door that runs, `sharness.db.sqlite`, on the standard library (T19). A door's conformance suite against its twin, `sharness.fs.s3.twin` first (T20). Each is small, and each is one hop of one of the two stacks.

## What this does not claim {#limits}

- **Nothing in this article is built.** No door, no target, no twin and no level's compiler exists. The runnable part is one process under one v0 policy, measured on three kernels ([Evidence §9](../evidence/index.md#9-the-first-experiments-run-by-the-cli)).
- **"Deterministic expansion" is a requirement, not a property.** The canonical form of each level is unwritten.
- **The 3.2 ms is one measurement**, in one environment, on 24 October 2026, between two local processes; a remote hop costs what the network costs.
- **The stacks do not add enforcement.** Everything a level holds is held by level 1 and refused by level 0. A policy a process applies to its own children is a Boundary for them and a Setting for itself; that caveat holds at every level and every hop.
- **No organisation runs a level and no vendor ships a profile.** Who runs a level is a deployment choice described here, not an offer.

## Where this comes from {#sources}

Dinis Cruz's direction in pbp@sharness's session on 26 October 2026: the tree of doors and targets, the `.twin` suffix, the accepts and emits of every door and the mirror rule, and the levels with two stacks on TCP. The pages that carry each: [the PBP on one page](../design/pbp/index.md) (the doors, the tree, the mirror rule), [the levels](../design/levels/index.md), [Process Behaviour Policies](../design/policies/index.md) (the schema, the layers, the enforcement map), [Architecture](../design/architecture/index.md) (the edges, mutual TLS, the topologies), [the components](../components/index.md) (every door as a request). The measurement is [Evidence §6](../evidence/index.md#6-transport). The model the policy applies is [Agent Behaviour Policies](https://riskmandate.ai/abp.html) on riskmandate.ai; the twin is [twins.sgit.ai](https://twins.sgit.ai)'s. Written by pbp@sharness, the policy agent; the editorial responsibility is Dinis Cruz's.
