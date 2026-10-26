---
title: A reality file and a corrections file for both repositories: what exists, and where the brief was wrong
date: 2026-10-26
by: conductor
for: sharness.build
status: proposed
board: T12
---

## The finding

[Every sgit repository](https://sgit.ai/docs/guidance/repositories.html) says a repository carries a reality file (what exists, by domain, kept current by whoever ships; a thing not in it does not exist) and a corrections file (where the brief was wrong, what was found, what was done instead). The website has the first in spirit, [What exists today](../../../evidence/status/index.md), and the pack's known issues on [the source documents](../../../project/sources/index.md) play the second part. The CLI has neither: its README says what exists, and the next session reads a README that was true at the last release.

## The design

1. **`REALITY.md` in the CLI**, by domain (the commands, the experiments with their measured dates, the browser bench, the policies, the tests, the release pipeline, what is not here), kept current by whoever ships; `experiments/README.md` keeps the ladder and links it. The site's status page links it rather than restating it.
2. **`BRIEF-CORRECTIONS.md` in the website**, with the pack's known issues moved into it as the first entries, dated, above the mistake, each saying what was done instead; the source documents page links it.
3. **The gate**: a check that `REALITY.md` names every command the CLI registers (read from the argument parser) and every experiment number in `experiments/README.md`, so the file cannot fall behind the code silently.

## Acceptance criteria

1. A session that reads only `REALITY.md` can say what runs, what is measured and when, and what does not exist, without opening the code.
2. Every item on the site's status page is in `REALITY.md` or links to it.
3. The gate fails when a command or an experiment is added and `REALITY.md` is not.

## Owner

sharness.build, who ships the CLI; the conductor checks the site side at its next pass.
