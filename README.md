# sharness.ai — the SHarness-AI website

The home of the SHarness-AI project and its command line tool, `sharness-ai`
([PyPI: `sharness-ai`](https://pypi.org/project/sharness-ai/),
[source](https://github.com/SHarness-AI/SHarness-AI__CLI)).

Live site: https://sharness.ai (GitHub Pages, deployed from `dev`).

Built the same way as the *.sgit.ai sites (modelled on
[SGit-AI__Website__NFRs](https://github.com/SGit-AI/SGit-AI__Website__NFRs)): hand-written
static HTML, no framework, no build step, a pre-release gate, and validate → tag → deploy.

## Structure

Five sections, each with an `index.md` hub, plus the articles and the files agents read. Markdown
is the source of every page that has a twin; the HTML beside it is generated and never edited.

| Folder | What | Source of truth |
|---|---|---|
| `design/` | the brief (the section's index) and the design pages: why, architecture, components, keys, policies, agents, process-tree, surface, containment, spectrum, roadmap | `index.md` in each, rendered by `tools/gen_pages.py` |
| `code/` | where the code is, the CLI, experiments, flows, examples, languages | same |
| `evidence/` | measurements (the index), status, the research note, the market analysis | same |
| `explain/` | the hub, `storyboards/` (generated from `content/storyboards/`), `mockups/` (hand-written HTML) | `content/storyboards/` and the mockups' HTML |
| `articles/` | the articles in the newsroom's format, generated from `content/articles/`, and their lead figures | `content/articles/` |
| `project/` | about, `sources/` (the design pack and memos, verbatim), `agents/`, `outreach/`, `telemetry/`, `engineering.html`, `comms.html`, `releases.html` | markdown pages rendered by `tools/gen_pages.py`; the three HTML pages hand-written; the pack is never edited |
| `data/` | `telemetry.json`: the telemetry lane's write-only credential and public key (publishable by design); `telemetry-report.json` once the first drain runs | written by `tools/telemetry_postmaster.py` and `tools/telemetry_drain.py` |
| `assets/` | `site.css`, `nav.js`, `telemetry.js` (one anonymous event per page, see `/project/telemetry/`), `images/` | |
| `content/` | the sources the generators read: `articles/`, `storyboards/` | |
| `tools/` | `version.txt` (owns the version), `chrome.py` (nav, footer, badge), the generators, `validate.js` and `validate_storyboards.cjs` (the gate) | |
| root | `index.html` and `index.md`, `404.html` (maps the pre-v0.5.2 addresses to the new ones), `llms.txt`, `llms-full.txt`, `sitemap.xml`, `robots.txt`, `CNAME` | |

## Release process

1. Bump `tools/version.txt` (vX.Y.Z, exactly once per release) and add a row to
   `project/releases.html`; update `project/comms.html` if the state of play changed.
2. `python3 tools/chrome.py` — propagates the version badge and any nav/footer change
   to every page, and stamps the version into `llms.txt` and `index.md`.
3. `python3 tools/gen_pages.py && python3 tools/gen_articles.py && python3 tools/gen_storyboards.py`
4. `python3 tools/gen_sitemap.py && python3 tools/gen_llms_full.py`
5. `node tools/validate.js && node tools/validate_storyboards.cjs`
6. `git commit -am "site vX.Y.Z: ..." && git push origin dev`

Every push to `dev` runs `.github/workflows/deploy-pages.yml`: validate → auto-tag → deploy to
GitHub Pages. The versioning rule: **every push to `dev` is a patch release** (`vX.Y.Z+1`);
**a merge to `main` is a minor release** (`vX.Y+1.0`), tagged on `main`. CI verifies the version
in `version.txt` against the commit subject and against the latest tag, and refuses the wrong
bump for the branch. Pull requests run validation only.

To cut a minor: on `main`, merge `dev`, add a release commit that bumps `version.txt` to
`vX.Y+1.0` (subject `site vX.Y+1.0: ...`), push; then fast-forward `dev` to `main` (CI sees the
tag already on that commit and does nothing). The next push to `dev` is `vX.Y+1.1`.

All content CC BY 4.0 unless noted. Code under the repository licence.
