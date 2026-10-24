# sharness.ai — the SHarness-AI project

> The home of the **SHarness-AI** project and its command line tool, `sharness`. This is
> the first version of the site: it states what exists today, and it marks what does not
> exist yet rather than describing it.

*Source: <https://sharness.ai/index.html> · site v0.1.1 · markdown twin of the front page.*

---

## Install

```bash
pip install sharness-ai
sharness --version        # sharness-ai v0.1.0 (the first release, as of 24 Oct 2026)
```

Two commands are installed: `sharness-ai` and the shorthand `sharness`. Python 3.11 or later.
Published on PyPI as [`sharness-ai`](https://pypi.org/project/sharness-ai/), released from
`main` by CI through Trusted Publishing, with no API token stored anywhere.

## What is here today

| Thing | What it is |
|---|---|
| [The CLI](cli/index.html) | The package skeleton: entry points, version file, and the release pipeline. It does nothing else yet. |
| [The PyPI package](https://pypi.org/project/sharness-ai/) | Published by GitHub Actions through Trusted Publishing (OIDC). |
| [This site](admin/index.html) | Static HTML, a pre-release gate, validate → tag → deploy to GitHub Pages. |

## What this site does not say yet

What SHarness *does* has not been written down here yet. The gap is published as
[R1 on the comms board](admin/comms.html#r1) rather than filled with a guess.
