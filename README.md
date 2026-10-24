# sharness.ai — the SHarness-AI website

The home of the SHarness-AI project and its command line tool, `sharness-ai`
([PyPI: `sharness-ai`](https://pypi.org/project/sharness-ai/),
[source](https://github.com/SHarness-AI/SHarness-AI__CLI)).

Live site: https://sharness.ai (GitHub Pages, deployed from `dev`).

Built the same way as the *.sgit.ai sites (modelled on
[SGit-AI__Website__NFRs](https://github.com/SGit-AI/SGit-AI__Website__NFRs)): hand-written
static HTML, no framework, no build step, a pre-release gate, and validate → tag → deploy.

## Structure

- `index.html` / `index.md` — the front page and its markdown twin
- `<page>/index.md` — the design pages, the CLI page, the experiments map and the research note: markdown is the source, `gen_pages.py` writes the HTML
- `experiments/` — the ladder of mockups and experiments; `mockups/` — the browser mockups (hand-written HTML)
- `storyboards/` — generated from `admin/content/storyboards/` by `gen_storyboards.py`; previews rendered by the kit (see the script's docstring)
- `shipped/` — what exists today, and what is not here yet
- `admin/` — engineering, comms (tasks & requests), release history
- `admin/build/version.txt` — owns the site version
- `admin/build/chrome.py` — the single definition of nav, footer and the version badge
- `admin/build/validate.js` — the pre-release gate
- `admin/build/gen_sitemap.py` — generates `sitemap.xml` from the tree and git dates
- `admin/build/gen_llms_full.py` — generates `llms-full.txt`
- `assets/site.css`, `assets/nav.js` — the sgit.ai design language and nav component
- `llms.txt`, `llms-full.txt`, `sitemap.xml`, `robots.txt`, `CNAME`

## Release process

1. Bump `admin/build/version.txt` (vX.Y.Z, exactly once per release) and add a row to
   `admin/versions.html`; update `admin/comms.html` if the state of play changed.
2. `python3 admin/build/chrome.py` — propagates the version badge and any nav/footer change
   to every page, and stamps the version into `llms.txt` and `index.md`.
3. `python3 admin/build/gen_pages.py && python3 admin/build/gen_articles.py && python3 admin/build/gen_storyboards.py`
4. `python3 admin/build/gen_sitemap.py && python3 admin/build/gen_llms_full.py`
5. `node admin/build/validate.js && node admin/build/validate_storyboards.cjs`
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
