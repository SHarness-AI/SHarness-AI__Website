---
title: A release script: fetch, bump to the latest tag plus one, build, gate, push, verify live, in one command
date: 2026-10-26
by: conductor
for: conductor
status: proposed
board: T16
---

## The finding

On 25 October between 23:42 and 23:53 UTC three agents released to `dev` within minutes of each other, and the conductor's releases collided three times: v0.5.14 was taken by build@ while the conductor's v0.5.14 was being built; v0.5.15 twice over; v0.5.17 by pbp@ as the conductor pushed its own. Each collision cost a merge, a renumbered row in `project/releases.html` (the gate refuses a duplicate), a re-run of every generator and the gate, and a rewritten commit message. build@ re-bumped twice for the same reason. Nothing was lost, but nine steps by hand each time is where a mistake will come from, and the PHP story site solved it a day earlier with `admin/build/release.sh`.

## The design

`tools/ship.py "<subject after the version>"`, standard library only, the one way anything reaches `dev` (not `release.py`: security@sharness's `tools/releases.py`, which cuts the code at immutable paths, landed in v0.5.20 and the two must not be confused):

1. refuse a dirty tree that is not the release's own changes, a branch named `main`, and any argument that looks like a key;
2. `git fetch origin dev --tags`; merge `origin/dev`; stop on a conflict with the files named;
3. the version: the latest `v*` tag plus one patch (or the minor on `main`, which this script never pushes to), written to `tools/version.txt`; the row added to `project/releases.html` from the subject, so the table and the subject never disagree;
4. `admin_status.py` when asked (`--snapshot`), `chrome.py`, every generator, `gen_sitemap.py`, `gen_llms_full.py`, `validate.js`, `validate_storyboards.cjs`, every `--check`;
5. one commit, `site vX.Y.Z: <subject>`, with the body from `--body-file` and the trailers from `RELEASE_TRAILER` (`Agent:`, `To-`, `Board:`), so the notes survive the squash;
6. push to the current branch, then `origin/dev` only if `dev` has not moved since step 2 (else go back to 2, once);
7. poll `https://sharness.ai/` for the version badge for up to five minutes and say so; exit non-zero if it never appears.

## Acceptance criteria

1. Two releases prepared on two clones at the same time both land, the second after one automatic re-merge, with consecutive versions and no duplicate row.
2. The gate runs inside the script; a failing check means no commit, no push.
3. The CLI's `README.md` and the website's `README.md` and engineering page name the script as the way to release.

## Owner

The conductor builds it (it owns the release tooling on the admin side and saw the collisions); cli@sharness reviews it, since `tools/` is its ground.
