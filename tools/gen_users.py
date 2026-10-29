#!/usr/bin/env python3
"""Generates /users/: the synthetic users' reports, one page per release, from content/users/.

Run from anywhere:  python3 tools/gen_users.py           (write)
                    python3 tools/gen_users.py --check   (CI: fail if anything is stale or malformed)

The sources, one file per release, so a report never shares lines with another:

  content/users/v<X.Y.Z>.md   front matter (version, tested, title, summary) + the report body:
                              one section per ask id (R1…, Q<release>-<n>), the persona in each

From those this writes users/index.md (the list of reports, newest first) and
users/v<X.Y.Z>/index.md, each rendered to index.html by gen_pages' own renderer, so the
section looks and links like every other. The markdown is served as the twin. Nothing here
carries a clock: every date comes from the report's front matter.
Kept by users@sharness (content/admin/members/users/ROLE.md). Standard library only.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrome                                                    # noqa: E402
from gen_pages import render                                     # noqa: E402

ROOT   = chrome.ROOT
SRC    = ROOT / "content/users"
OUT    = ROOT / "users"
FIELDS = ("version", "tested", "title", "summary")
GH     = "https://github.com/SHarness-AI/SHarness-AI__Website/blob/dev"
QA     = "https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/qa"

errors = []


def parse(path):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", path.read_text(), re.S)
    if not m:
        errors.append(f"{path.relative_to(ROOT)}: no front matter")
        return {}, ""
    meta = {}
    for line in m.group(1).split("\n"):
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    for f in FIELDS:
        if not meta.get(f):
            errors.append(f"{path.relative_to(ROOT)}: front matter has no {f}")
    if meta.get("version") and path.stem != f"v{meta['version']}":
        errors.append(f"{path.relative_to(ROOT)}: version {meta['version']} does not match the file name")
    return meta, m.group(2).lstrip("\n")


def vkey(meta):
    return tuple(int(x) for x in re.findall(r"\d+", meta.get("version", "0")))


def report_md(meta, body):
    return (f"{body.rstrip()}\n\n---\n\n*Generated from [content/users/v{meta['version']}.md]"
            f"({GH}/content/users/v{meta['version']}.md) by `tools/gen_users.py`; edit the source, "
            f"never this file. The asks are the CLI's [qa/]({QA}/README.md).*\n")


def hub_md(reports):
    rows = "\n".join(f"| [v{m['version']}](v{m['version']}/index.md) | {m['tested']} | {m['summary']} |"
                     for m, _ in reports)
    latest = f"The latest report is as of {reports[0][0]['tested']}." if reports else "No report yet."
    return f"""# What the users found: one report per release

{latest} The synthetic users, [users@sharness](../admin/members/users/index.md), test every release of
`sharness-ai` the way three people would: a **newcomer** who saw the announcement and follows the
PyPI page, a **builder** who wants to put a real tool under a policy, and a **skeptic** who reads
every claim and tries to break it. They start where a user starts (PyPI and this site, never the
source), install into a fresh environment, and paste what they typed and what came back.

Each report answers the CLI's asks by id: the standing checklist ([RELEASE.md]({QA}/RELEASE.md),
`R1`…) and the release's own (`qa/v<X.Y.Z>.md`, `Q<release>-<n>`). Every answer has one of four
verdicts: **Confirmed**, **Not confirmed**, **Could not run** (with what it would need), or
**Confusing** (it worked, but a user would not have known what to do or what it meant). A run is
a measurement in this site's words: each report says where it ran and when.

| Release | Tested | What the users found |
|---|---|---|
{rows}

A *Not confirmed* goes to the member that owns the thing, as a `To-cli:` note in the commit that
publishes the report; the CLI answers it in its next release with `QA: <id>` in the commit.
"""


def build():
    reports = sorted((parse(p) for p in SRC.glob("v*.md")), key=lambda r: vkey(r[0]), reverse=True)
    pages = {"users/index.md": (hub_md(reports), "users", "What the users found",
                                "The synthetic users' reports: every release of sharness-ai tested from PyPI by a newcomer, a builder and a skeptic, one verdict per ask.")}
    for meta, body in reports:
        d = f"users/v{meta.get('version')}"
        pages[f"{d}/index.md"] = (report_md(meta, body), d, meta.get("title", ""), meta.get("summary", ""))
    return pages


def main():
    check = "--check" in sys.argv
    pages = build()
    if errors:
        sys.exit("gen_users:\n" + "\n".join(f"  ✗ {e}" for e in errors))
    stale = []
    for rel, (md, dir_, title, desc) in pages.items():
        md_path = ROOT / rel
        if check:
            if not md_path.exists() or md_path.read_text() != md:
                stale.append(rel)
            elif (ROOT / dir_ / "index.html").read_text() != render(dir_, title, desc):
                stale.append(f"{dir_}/index.html")
            continue
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md)
        (ROOT / dir_ / "index.html").write_text(render(dir_, title, desc))
    if stale:
        print("gen_users: stale (run python3 tools/gen_users.py and commit):", file=sys.stderr)
        for s in stale:
            print(f"  ✗ {s}", file=sys.stderr)
        sys.exit(1)
    print(f"gen_users: {len(pages)} page(s) {'up to date' if check else 'generated'}")


if __name__ == "__main__":
    main()
