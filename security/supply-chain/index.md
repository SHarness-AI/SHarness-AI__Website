# Supply chain

> **Status: as of 25 Oct 2026.** Everything that runs on a reader's machine or in the project's CI, where it comes from, how it is pinned, how a release of the CLI is built and published, how to verify one, what this site loads from elsewhere, and how the code is published here at paths that never change. The principle: **a reader should be able to name every byte the project asks them to run, and check it.**

## 1. The package: no dependencies

`sharness-ai` is standard library only, by rule (the CLI's `CLAUDE.md`). `pip install sharness-ai` installs one wheel and nothing else; Landlock is reached through `ctypes`, hashing through `hashlib`. The security workflow checks the rule on every push (`test_no_runtime_dependencies`) and audits whatever an install brings anyway (`pip-audit`), so the day a dependency appears it is seen.

The development tools are pinned by version in the workflows and in `pyproject.toml`: pytest, ruff, bandit, zizmor, pip-audit, cyclonedx-bom, build. They never run in the job that publishes.

## 2. What runs in CI

Every action is pinned to a commit, and a test fails the build if one is not (`test_every_action_is_pinned_to_a_commit`); Dependabot proposes the bumps weekly so a pin stays current. Every workflow declares `permissions: contents: read` at the top and widens only the job that needs more; `persist-credentials: false` everywhere nothing pushes; no `pull_request_target`; no event text interpolated into a script (tested). zizmor audits all of it on every push.

| Workflow | Runs | May write |
|---|---|---|
| `tests.yml` | the unit tests on Python 3.11, 3.12 and 3.13; the suite uninstalled; the wheel builder | nothing |
| `security.yml` | ruff (bandit's rules), bandit, zizmor, the repository's own security tests; `pip-audit`, `npm audit` on the bench's one dependency, a CycloneDX SBOM; dependency review on pull requests | the SBOM artifact |
| `codeql.yml` | CodeQL, Python and JavaScript, `security-extended` | its own alerts |
| `workflow.yml` | the release: tests, the version bump, the build, the publish | `main` and a tag (the bump job); PyPI (the publish job, by OIDC) |

Actions used, by commit, as of 25 Oct 2026: `actions/checkout` 11d5960a, `actions/setup-python` a26af69b, `actions/setup-node` 949feb24, `actions/upload-artifact` cf430e03, `actions/download-artifact` 9000827c, `actions/dependency-review-action` 2031cfc0, `github/codeql-action` 9b325408, `pypa/gh-action-pypi-publish` 7245906f. The website's deploy workflow: `actions/checkout`, `actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`, each by commit.

## 3. How a release is built and published

```
 push to main
   │
   ▼
 run-tests ──► increment-tag ──► build ──► publish-to-pypi
 (read)        (contents: write)  (read)    (id-token: write; runs no code of ours)
               a few lines of     python -m  pypa/gh-action-pypi-publish, by commit,
               shell in the       build,     Trusted Publishing: GitHub's OIDC token is
               workflow itself:   pinned     exchanged for a short-lived PyPI token;
               bump v0.N.0 →                 PEP 740 attestations uploaded with the files
               v0.N+1.0, write 3
               files, commit, tag
```

What changed on 25 Oct 2026 (SR-05): the bump and the publish used to be composite actions from another repository; the publish one fetched Poetry's installer over the network and installed `twine` and `id` unpinned, in the job that held the token. Now the job that holds the token downloads the artifact the build job made and hands it to pypa's publisher, pinned to a commit. The two jobs cannot share a process. **The rewritten pipeline has not run yet**: it runs on the next merge of `dev` into `main`, and SR-05 reads *fixed, untested* until it has.

How to verify a release once it has:

```
pip download sharness-ai==<version> --no-deps -d /tmp/d
sha256sum /tmp/d/*                     # compare with the hash printed in the build job's log
pip install pypi-attestations          # then: pypi-attestations verify pypi --repository \
                                       #   https://github.com/SHarness-AI/SHarness-AI__CLI /tmp/d/*.whl
```

Or read the file's page on PyPI: a file published through Trusted Publishing with attestations shows the publisher and the attestation there.

## 4. What this site loads from elsewhere

The site is static HTML with one first-party script (`assets/nav.js`). Two pages load more:

| Page | Loads | From | Integrity |
|---|---|---|---|
| the storyboards | `embed.js` of the storyboards.sgit.ai kit, release v0.1.0 | `api.storyboards.sgit.ai/v0/v0.1/v0.1.0/`, an immutable path with a manifest | the manifest's `sha384-` string is on the `<script>` tag with `crossorigin="anonymous"` (SR-20); the gate checks the tag |
| the playground, the E09 page | v86, the kernel, the initramfs, the BIOS, the wheel, the policies | this site, `code/browser/demo/` | first party; the guest is built from downloads pinned by sha256 (SR-07) |
| the playground | Pyodide 314.0.7 | `cdn.jsdelivr.net` | **none** (SR-25, accepted): Pyodide fetches its own files, so one integrity string cannot cover it. A compromised copy could lie in the Pyodide tab of this one page and reach nothing else; the three-way hash is there so a lying runtime shows. Self-hosting at an immutable path is the fix if the risk is ever judged worth it |

GitHub Pages sets no security headers, so a Content-Security-Policy would have to be a `<meta>` tag per page; the playground needs `unsafe-eval` for Pyodide and `wasm-unsafe-eval` for v86, which is most of what a policy would forbid. Not done; recorded here.

## 5. The code on this site: immutable paths

The same rule the storyboards.sgit.ai kit publishes under, adopted for SHarness on 25 Oct 2026, with one addition Dinis Cruz asked for: a `latest` that can be brought in.

```
 code/releases/
   releases.json              every release, newest first (what, path, manifest, date, commit)
   latest.json                the newest release, by name and path
   latest/                    a byte-for-byte copy of the newest release: the one path that moves
   v0/
     v0.1/
       v0.1.0/                IMMUTABLE: nothing at this path will ever change
         manifest.json        every file: path, bytes, sha256, sha384 integrity string; the source commit
         sharness_ai/…        the package, as source
         sharness_ai-0.1.0-py3-none-any.whl, wheel.json
         experiments/policies/…, experiments/browser/playground.js, …   (when the release had them)
         LICENSE, README.md
   dev/                       a SNAPSHOT of the dev branch, rebuilt on every site release; no promise
```

- **A release is complete.** Every file it needs is in its folder, so files in a release only meet files from the same release.
- **A release never changes.** A fix is the next release in its own folder. `tools/releases.py cut` refuses to write into a folder that exists.
- **`latest` moves, and says so.** `latest.json` names the newest release; `latest/` is its copy. A page that wants the newest reads one of them; a page that must never be surprised pins `vMAJOR/vMAJOR.MINOR/vMAJOR.MINOR.PATCH/` and the integrity string from its manifest.
- **`dev/` is not a release.** Its manifest says `snapshot`. It is what the playground's wheel is built from today.
- **The gate enforces it.** `python3 tools/releases.py check` runs in the deploy workflow before anything is tagged or published: it recomputes every hash of every release and fails if one byte differs, if a folder is not at its proper depth, if `latest.json` names a release that is not there, or if `latest/` is not its copy. `tools/releases.py live-check` fetches every published release from the live host and compares, after a deploy.
- **Cutting one**: `python3 tools/releases.py cut --from ../SHarness-AI__CLI --release vX.Y.Z` exports the CLI repository at that tag with `git archive`, copies the package, the policies and the browser code, builds the wheel with the CLI's own standard-library builder, writes the manifest, and refreshes `releases.json`, `latest.json` and `latest/`. The CLI's tags are the source of truth for which releases exist.

Published so far, as of 25 Oct 2026: `v0.1.0` (the skeleton on PyPI: five files in `sharness_ai/`, the wheel, the licence and the README) at [`code/releases/v0/v0.1/v0.1.0/`](../../code/releases/v0/v0.1/v0.1.0/manifest.json), and the `dev` snapshot. The next CLI release lands as `v0/v0.2/v0.2.0/` the day it is tagged. The index is [`code/releases/releases.json`](../../code/releases/releases.json); the page is [Releases of the code](../../code/releases/index.md).

How to verify a file from a release:

```
curl -sO https://sharness.ai/code/releases/v0/v0.1/v0.1.0/manifest.json
curl -sO https://sharness.ai/code/releases/v0/v0.1/v0.1.0/sharness_ai-0.1.0-py3-none-any.whl
python3 -c "import json,hashlib; m=json.load(open('manifest.json')); f=[x for x in m['files'] if x['path'].endswith('.whl')][0]; print(hashlib.sha256(open(f['path'],'rb').read()).hexdigest()==f['sha256'])"
```

## 6. The browser bench's downloads

`experiments/browser/build_guest.py` fetches 23 Alpine 3.23 packages, one kernel package and two BIOS images. Each is named with its exact version and its sha256 in the script; a cached copy is re-verified on every build; a mismatch moves the file aside and stops the build; the BIOS comes from one commit of `copy/v86`, never a branch; only `https://` is accepted. The one npm dependency, `v86`, is pinned to an exact version in `experiments/browser/package.json` and installed with `npm ci --ignore-scripts`. The built guest (`initramfs.cpio.gz`, `vmlinuz-virt`) is committed to this site's repository under `code/browser/demo/`, so what a visitor's browser boots is what the gate saw.

## 7. What is not in place, and known

- The published pipeline has not run since it was rewritten (SR-05).
- Hash-pinning of the scanner tools' own dependencies (a `--require-hashes` requirements file): they run in read-only jobs, so a compromise there cannot publish, only report wrongly. Low; a follow-up.
- A reproducible build check (build the wheel twice, compare): the stdlib builder is deterministic by construction; the Poetry build is not checked. Low.
- Signatures on this site's `releases.json` and manifests: the integrity string protects a file against its own path changing, not against the index being replaced together with the files; a signed index by the project's key is the next step once there is a key to sign with ([Policies §6](../../design/policies/index.md#6-hashing-signing-distribution) names the same root key).
