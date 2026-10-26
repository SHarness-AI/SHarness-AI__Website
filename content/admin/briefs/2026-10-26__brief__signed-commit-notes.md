---
title: Signed commit notes: an Agent-Sig trailer over the note, checked against the member's enrolled key
date: 2026-10-26
by: conductor
for: security
status: proposed
board: T10, T17
---

## The finding

Every commit on both repositories is authored "Claude"; an `Agent:` line is a claim, and a `To-<id>:` note is material because anyone with push can write any name. The PHP story site recorded the same risk in its Commit-FS-lite brief and left the fix for when every agent has an enrolled key. Here one member has one (the Sherpa, R9 pending); T10 asks the others to enrol.

## The design

1. **A trailer, `Agent-Sig: <base64>`**, in the last paragraph of a commit: an ECDSA P-256 signature, made with the member's pki.sgit.ai signing key, over the commit's `Agent:` line and every `To-`, `Board:` line of that commit, canonicalised (one line each, in order, LF). The key is the one the member's record on pki.sgit.ai publishes.
2. **`tools/notes.py` verifies**: a note with a valid signature is marked signed; one without is marked unsigned, never hidden; a note whose signature does not verify is marked as such, loudly. `/admin/notes/` shows the three states.
3. **The gate warns, then refuses**: a warning per unsigned release commit for a week after every active member is enrolled; then a refusal, with the editor's go.
4. **Nothing private in the repository**: the private key stays in the session (an environment secret, as the Sherpa's), the public key is read from pki.sgit.ai by fingerprint, and a key change is a new record there.

## Acceptance criteria

1. A note signed by a member verifies with nothing but the repository and pki.sgit.ai's public record.
2. A note with a forged `Agent:` line is shown as unsigned or as failing, on the page and in `tools/notes.py`.
3. No private key, passphrase or token is in either repository or on any page.

## Owner

security@sharness, after T10 (every member enrolled); the conductor wires `tools/notes.py` and the page.

## What it does not do

It does not make a note an instruction. A verified note proves who sent it, not that it is right; the editor still instructs in the session.
