# Releases of the code

> **Status: published, as of 25 Oct 2026.** Every release of the `sharness-ai` code is published on this site at a path that never changes, complete, with a manifest of hashes; a `latest` names the newest. The rule and the tool are on [Supply chain §5](../../security/supply-chain/index.md#5-the-code-on-this-site-immutable-paths). PyPI carries the same releases as wheels; this is the copy a page, an agent or a reader can pin by hash.

## The paths

| Path | What | Changes? |
|---|---|---|
| [`releases.json`](releases.json) | every release, newest first: name, path, manifest, date, source commit | on each new release |
| [`latest.json`](latest.json) | the newest release, by name and path | on each new release |
| `latest/` | a byte-for-byte copy of the newest release, for a page that wants "the latest" | on each new release |
| `vMAJOR/vMAJOR.MINOR/vMAJOR.MINOR.PATCH/` | one release: the package as source, the wheel and its `wheel.json`, the example policies and the browser code the release had, the licence, the README, and `manifest.json` listing every file with its size, sha256 and sha384 integrity string, and the commit it was exported from | **never** |
| `dev/` | a snapshot of the CLI's `dev` branch, rebuilt on each site release; its manifest says `snapshot` | on each site release; no promise |

## Published

| Release | Path | Source | Date |
|---|---|---|---|
| v0.1.0 | [`v0/v0.1/v0.1.0/`](v0/v0.1/v0.1.0/manifest.json) | the CLI's tag `v0.1.0`, commit `68362921e`: the skeleton on PyPI, `--version` and the help | 25 Oct 2026 |
| dev snapshot | [`dev/`](dev/manifest.json) | the CLI's `dev` head at the time of the site release named in the manifest | with the site |

The next CLI release (the merge of `dev` into `main`, [R7](../../project/comms.html#r7)) lands here as `v0/v0.2/v0.2.0/` the day it is tagged.

## How to use one

Pin the versioned path and the integrity string from its manifest when the bytes must never change under you; read `latest.json` when you want the newest and accept that it moves. To check a file: fetch the manifest, fetch the file, compare the sha256. The gate on this site does the same for every release on every push, and refuses to publish if a byte has changed.
