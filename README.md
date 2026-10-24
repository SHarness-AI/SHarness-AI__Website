# sharness.ai — the SHarness-AI website

The home of the SHarness-AI project and its command line tool, `sharness`
([PyPI: `sharness-ai`](https://pypi.org/project/sharness-ai/),
[source](https://github.com/SHarness-AI/SHarness-AI__CLI)).

Live site: https://sharness.ai (GitHub Pages, deployed from `dev`).

Built the same way as the *.sgit.ai sites (modelled on
[SGit-AI__Website__NFRs](https://github.com/SGit-AI/SGit-AI__Website__NFRs)): hand-written
static HTML, no framework, no build step, a pre-release gate, and validate → tag → deploy.

## Structure

- `index.html` / `index.md` — the front page and its markdown twin
- `cli/` — the `sharness` CLI: install, versioning, release pipeline
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
3. `python3 admin/build/gen_sitemap.py && python3 admin/build/gen_llms_full.py`
4. `node admin/build/validate.js`
5. `git commit -am "site vX.Y.Z: ..." && git push origin dev`

Every push to `dev` runs `.github/workflows/deploy-pages.yml`: validate → auto-tag
(`vX.Y.Z`, verified against `version.txt` and the commit subject, next-minor enforced) →
deploy to GitHub Pages. A push to `main` deploys without tagging. Pull requests run
validation only.

All content CC BY 4.0 unless noted. Code under the repository licence.
