---
title: CI owns the version: one file at the root, written by the one commit that tags the release, in every repository
date: 2026-10-26
by: dev
for: editor
status: proposed
board: R23
---

## The finding

The editor asked, on 26 Oct 2026, for a look at how the send repository tags its releases, because the website's scheme has stuck twice in one evening ([T21](../board/index.md#t21)). Three repositories, three schemes, read on 26 Oct 2026:

| | the send app (`SGraph-AI__App__Send`) | the CLI (`SHarness-AI__CLI`) | the website |
|---|---|---|---|
| who chooses the number | **CI**, after the push: the latest tag plus one, inside a job that runs one release at a time | CI, the same way, but on `main` only; a push to `dev` runs the tests and gets no version | **the committer**, before the push: `tools/ship.py` guesses the latest tag or dev's file plus one, writes `tools/version.txt`, puts the number in the commit subject; CI then checks the guess |
| the one file | `<package>/version`, written by CI, committed as "Update release badge and version file"; that commit is what the tag points at | `sharness_ai/version`, the same (the composite action inlined as shell after the security review); `_version.py` reads it; `pyproject.toml` and the README badge are rewritten in the same commit | `tools/version.txt`, written by the agent; the gate (`validate.js`) checks every page's badge, `llms.txt` and `index.md` agree with it |
| dev and main | `dev` → last number plus one; `main` → middle number plus one, last to zero (the action calls these *minor* and *major*) | `main` → middle number plus one; `dev` → nothing | `dev` → last number plus one; `main` → middle number plus one (the workflow calls these *patch* and *minor*) |
| what collides | nothing: two pushes a second apart are two runs in one queue, each reads the tags after the previous one pushed its tag | nothing on `main` | two pushes within a minute both guess the same number, or a queued run is dropped and its number is never tagged: the live site stuck at v0.5.32 and at v0.5.38 tonight |
| what a reader looks at for the version | one file, one path, in every clone and every checkout | the same | the file, but also the subject line and the badge, which must all agree |

The send scheme is the one to keep, for the reason the editor gave: **the commit that writes the version file is the release**. It is made by one serialised job, so no two releases can claim one number; the file is the single place the version lives; and a tree whose `version` differs from the tag is a tree nobody released. The website's scheme asks the committer to know the number before CI does, which is exactly the thing that cannot be known when several agents release within a minute of each other, and T21's two incidents are that gap and not a bug in anyone's release.

## The design

1. **One file, `version`, at the root of every repository**, written only by CI. The website moves `tools/version.txt` to `/version`; the CLI keeps `sharness_ai/version` as the packaged copy and gains the root file, both written in the same commit (`_version.py` reads the packaged one so an installed wheel still knows its version); the language repositories ([R21](../board/index.md#r21)) carry `/version` from their first release, so the [registry](../../../code/standards/index.md) can read every implementation's version from one path.
2. **CI assigns the number and writes the commit.** On a push to `dev`: the last number plus one; on a push to `main`: the middle number plus one, last to zero. The job reads the tags, writes `/version`, re-stamps whatever carries the version (on the website: `python3 tools/chrome.py` and the generators, so the badge, `llms.txt`, `index.md` and `llms-full.txt` follow; on the CLI: `pyproject.toml`, the packaged copy and the README badge), commits as the actions user with the subject `release vX.Y.Z` and the triggering commit's subject in the body, tags that commit, pushes the branch and the tag, then deploys or publishes from that commit. One job, one concurrency group, `cancel-in-progress: false`, and the queued run is never dropped because the only thing queued is the bump, which always applies on top of whatever is there.
3. **A commit that touches `/version` by hand is refused**: the gate and the workflow both check that the file changed only in a commit by the actions user with a `release` subject. That is the lock the editor described: nothing lands on top of a release that disagrees with its number.
4. **The commit subject carries no number.** `tools/ship.py` stops bumping and stops adding the row; it merges `dev`, runs the generators and the gate, commits with the trailers and pushes. The release history page is generated from the tags and their release commits (`tools/releases.py` or a sibling), so the row for a release is written by the same job that numbers it; the human-written sentence per release comes from the triggering commit's subject, as it does today.
5. **One vocabulary.** The action says *major* and *minor* for the middle and the last number; the website's workflow says *minor* and *patch* for the same two. The editor's words in session were major and minor. Proposed: say what moves, "`main` bumps the middle number, `dev` the last", on the releases page and in `AGENTS.md`, and use *major* and *minor* when a word is needed, as the editor does and the send repository does.
6. **The CLI's `dev` gets a version too**, as the send repository's does: every push to `dev` that passes the tests is tagged `vX.Y.Z+1` and written to `/version`, so the dev snapshot the site publishes and the vectors' oracle commit have a version, not only a hash; publishing to PyPI stays a `main` release.

## Acceptance criteria

1. On both repositories, `/version` exists, is written only by CI, and equals the newest tag on the branch's head after every push to `dev` or `main`.
2. Two pushes to `dev` ten seconds apart both deploy, in order, with consecutive numbers, and the live site serves the second.
3. A commit that edits `/version` by hand is refused by the gate before it is pushed and by CI if it is.
4. `tools/ship.py` has no bump logic; the release history page is generated from the tags.
5. The language repositories' first release writes `/version` the same way.

## Owner

The editor decides (R23). Then website@sharness for `deploy-pages.yml`, `ship.py` and the gate, with security@sharness's review of the workflow (it needs `contents: write` to push the commit and the tag, which the tag job already has); cli@sharness for the CLI's `dev` tagging and the root file; dev@sharness for the language repositories, and for the registry reading `/version`.
