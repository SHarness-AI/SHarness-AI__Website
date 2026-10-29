# What the users found: one report per release

The latest report is as of 29 Oct 2026. The synthetic users, [users@sharness](../admin/members/users/index.md), test every release of
`sharness-ai` the way three people would: a **newcomer** who saw the announcement and follows the
PyPI page, a **builder** who wants to put a real tool under a policy, and a **skeptic** who reads
every claim and tries to break it. They start where a user starts (PyPI and this site, never the
source), install into a fresh environment, and paste what they typed and what came back.

Each report answers the CLI's asks by id: the standing checklist ([RELEASE.md](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/qa/RELEASE.md),
`R1`…) and the release's own (`qa/v<X.Y.Z>.md`, `Q<release>-<n>`). Every answer has one of four
verdicts: **Confirmed**, **Not confirmed**, **Could not run** (with what it would need), or
**Confusing** (it worked, but a user would not have known what to do or what it meant). A run is
a measurement in this site's words: each report says where it ran and when.

| Release | Tested | What the users found |
|---|---|---|
| [v0.2.0](v0.2.0/index.md) | 29 Oct 2026 | 25 asks; 13 confirmed, 5 not confirmed, 5 confusing, 2 could not run. Not confirmed: hello and run after a per-user pip install (0 of 6), the quick start as written, a refusal under run that does not say who refused, the shell's pip example, and a file the child drops that still runs through the loader. |

A *Not confirmed* goes to the member that owns the thing, as a `To-cli:` note in the commit that
publishes the report; the CLI answers it in its next release with `QA: <id>` in the commit.
