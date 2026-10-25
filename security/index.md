# Security

> **Status: the register is live, as of 25 Oct 2026.** SHarness is a security product at the experiments stage, so this section is where the project says what it knows about its own security: the threat model, every known risk and what was decided about it, every review with its findings and fixes, how to run the code safely, and what the project's own supply chain looks like. The rule for the section: **nobody reviewing SHarness should find something it does not already say about itself.** When they do, it goes here first, then it gets fixed or accepted in writing.

## The pages

| Page | What it holds |
|---|---|
| [Threat model](threat-model/index.md) | the assets, the actors, the two trust boundaries (the person's hash; the kernel), and surface by surface what the code of today holds, what the designed launcher adds, and what nothing covers |
| [Known risks](risks/index.md) | the register: one row per risk, with where it lives, how much it matters, whether it is fixed, accepted, open or waiting on the design, and the reason. Accepted risks are listed with the same weight as fixed ones |
| [Reviews](reviews/index.md) | each security review, dated: scope, method, environment, the findings with the fix and the test that pins each, what was examined and found clean, what was not examined |
| [Hardening](hardening/index.md) | how to run `sharness-ai` so it holds as much as it can today; and the lock-down list for the repositories, the accounts and the release path, split into what is in code and what only a setting can change |
| [Supply chain](supply-chain/index.md) | everything that runs on a reader's machine or in CI, where it comes from and how it is pinned; how a release is built and attested and how to verify one; how the code is published on this site at immutable paths |

## Where the review stands

The first full review was done on 25 Oct 2026 by the project's security agent (security@sharness, an AI agent, as the build agent is) over the CLI repository, the example policies, the browser bench, both repositories' workflows and this site. It recorded 25 findings, listed on [Reviews](reviews/index.md) and carried into the [register](risks/index.md):

| Weight | Found | Fixed in code | Accepted and declared | Open: a setting or a design decision |
|---|---|---|---|---|
| High | 5 | 5 | 0 | 0 |
| Medium | 7 | 4 | 1 | 2 |
| Low | 11 | 11 | 0 | 0 |
| Info | 2 | 2 | 0 | 0 |

Every fix landed with a test in the CLI's `tests/unit/test_security.py` that fails if the hole opens again. Two more rows (SR-26, SR-27) were added on 26 Oct 2026 for what landed on `dev` while the review was being merged: the site's telemetry and the bench's page-side network; both are documented by their owners and recorded here so the register is one list. The two open items need Dinis Cruz, as board rows [R15](../admin/board/index.md) (the repository settings on [Hardening §3](hardening/index.md#3-the-repositories-and-the-accounts-settings-only-a-person-can-change)) and [R16](../admin/board/index.md) (the policy row for environment variables, [SR-11](risks/index.md#the-register)).

## How to report something

Use GitHub's private vulnerability reporting on the repository the finding is in: [the CLI](https://github.com/SHarness-AI/SHarness-AI__CLI/security/advisories/new) or [this site](https://github.com/SHarness-AI/SHarness-AI__Website/security/advisories/new). The `SECURITY.md` in each repository and [`/.well-known/security.txt`](../.well-known/security.txt) say the same. A report that reproduces is answered with a fix or a written acceptance, and either way it is added to the register. There is no bounty.

## What this section does not do

It does not grade the design as safe. The design trusts the kernel and the platform, and says so; nothing here changes that. It does not replace a review by someone outside the project: it is the project's own account, written so that an outside review starts from the register rather than from zero. And it does not cover sgit, the first app designed to run inside SHarness; sgit's own register is on [cli.sgit.ai](https://cli.sgit.ai).
