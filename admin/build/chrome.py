#!/usr/bin/env python3
"""The single definition of this site's nav and footer, and the tool that applies it.

Run from anywhere: python3 admin/build/chrome.py

Every page is hand-written static HTML, so a human can open any file and edit it.
What is NOT hand-maintained is the chrome: the nav row (including the version badge
that validate.js requires to agree everywhere) and the footer columns. Those are
defined once here and rewritten in place across the tree. Same tool, same contract,
as the *.sgit.ai sites this one is modelled on.

Adding a page: add it to NAV or FOOTER if it belongs there, write the file with any
nav/footer block at all, then run this. The block contents are replaced; the `here`
state is set from the page's own path.
"""
import re
import sys
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[2]
VERSION = (ROOT / "admin/build/version.txt").read_text().strip()
GH      = "https://github.com/SHarness-AI/SHarness-AI__Website"
HOST    = (ROOT / "CNAME").read_text().strip()

# The nav, two levels. Each entry is (label, own page, [(sub-label, href), ...], prefixes).
#   · A group label is always a link to a real page, never a menu-only stub.
#   · `prefixes` decides the "here" state, so a page not itself in the nav still
#     lights up the group it belongs to.
NAV = [
    ("The design", "brief/index.html", [
        ("&#9679; The brief: in one read", "brief/index.html"),
        ("Why: the last metre", "why/index.html"),
        ("Architecture", "architecture/index.html"),
        ("Components", "components/index.html"),
        ("Keys and the KMS", "keys/index.html"),
        ("Process Behaviour Policies", "policies/index.html"),
        ("Agents and LLMs", "agents/index.html"),
        ("Enforcing the process tree", "process-tree/index.html"),
        ("What a process can do", "surface/index.html"),
        ("The spectrum: hello world to sgit", "spectrum/index.html"),
    ], ("brief/", "why/", "architecture/", "components/", "keys/", "policies/", "agents/", "process-tree/", "surface/", "spectrum/")),
    ("Evidence &amp; status", "evidence/index.html", [
        ("&#9679; Evidence", "evidence/index.html"),
        ("Roadmap &amp; open decisions", "roadmap/index.html"),
        ("What exists today", "shipped/index.html"),
        ("Research note", "research/index.html"),
        ("Market &amp; competitors", "market/index.html"),
    ], ("evidence/", "roadmap/", "shipped/", "research/", "market/")),
    ("Experiments", "experiments/index.html", [
        ("&#9679; Mockups &amp; experiments", "experiments/index.html"),
        ("Storyboards", "storyboards/index.html"),
        ("Mockup: policy hash", "mockups/policy-hash.html"),
        ("Mockup: edge matrix", "mockups/edges.html"),
    ], ("experiments/", "storyboards/", "mockups/")),
    ("Articles", "articles/index.html", [
        ("&#9679; All articles", "articles/index.html"),
        ("The first experiments", "articles/the-first-experiments.html"),
        ("A secure harness for agents", "articles/secure-harness-for-agents.html"),
        ("What shipped on day one", "articles/what-shipped-on-day-one.html"),
    ], ("articles/",)),
    ("Project", "about/index.html", [
        ("About &amp; naming", "about/index.html"),
        ("The CLI", "cli/index.html"),
        ("The source documents", "documents/index.html"),
    ], ("about/", "cli/", "documents/")),
    ("Site", "admin/index.html", [
        ("Admin &amp; engineering", "admin/index.html"),
        ("Comms: tasks &amp; requests", "admin/comms.html"),
        ("Release history", "admin/versions.html"),
    ], ("admin/",)),
]

FOOTER = [
    ("The design", [
        ("The brief: in one read", "brief/index.html"),
        ("Why: the last metre", "why/index.html"),
        ("Architecture", "architecture/index.html"),
        ("Components", "components/index.html"),
        ("Keys and the KMS", "keys/index.html"),
        ("Process Behaviour Policies", "policies/index.html"),
        ("Agents and LLMs", "agents/index.html"),
        ("Enforcing the process tree", "process-tree/index.html"),
        ("What a process can do", "surface/index.html"),
        ("The spectrum", "spectrum/index.html"),
    ]),
    ("Evidence &amp; status", [
        ("Evidence", "evidence/index.html"),
        ("Roadmap &amp; open decisions", "roadmap/index.html"),
        ("What exists today", "shipped/index.html"),
        ("Research note", "research/index.html"),
        ("Market &amp; competitors", "market/index.html"),
        ("The source documents", "documents/index.html"),
    ]),
    ("Experiments", [
        ("Mockups &amp; experiments", "experiments/index.html"),
        ("Storyboards", "storyboards/index.html"),
        ("Mockup: policy hash", "mockups/policy-hash.html"),
        ("Mockup: edge matrix", "mockups/edges.html"),
    ]),
    ("Project", [
        ("Articles", "articles/index.html"),
        ("About &amp; naming", "about/index.html"),
        ("The CLI", "cli/index.html"),
        ("PyPI: sharness-ai", "https://pypi.org/project/sharness-ai/"),
        ("GitHub: SHarness-AI", "https://github.com/SHarness-AI"),
        ("Comms &amp; release history", "admin/comms.html"),
    ]),
    ("For agents", [
        ("llms.txt", "llms.txt"),
        ("llms-full.txt", "llms-full.txt"),
        ("index.md", "index.md"),
        ("sitemap.xml", "sitemap.xml"),
    ]),
]

BLURB = ("SHarness runs agents and their tools as small, single-purpose processes, each locked "
         "down by the kernel and talking only over allowed, mutually authenticated connections. "
         "By Dinis Cruz. All content CC BY 4.0.")
PARTNOTE = ('⚠ Status: design. Nothing here is built; measured figures carry their date. '
            '<a href="{up}evidence/index.html" style="display:inline;padding:0">What is measured, '
            'what is proposed</a>.')
PARTNOTE_SELF = ('⚠ Status: design. Nothing here is built. You are on the page that says what '
                 'was measured and what is only proposed.')
NETLINE = ('<a href="https://cli.sgit.ai"><b>↗ cli.sgit.ai</b></a> — sgit, the first harnessed app · '
           '<a href="https://pki.sgit.ai">↗ pki.sgit.ai</a> — the handover it builds on · '
           '<a href="https://riskmandate.ai/abp.html">↗ riskmandate.ai</a> — Agent Behaviour Policies')


def nav_html(rel, up):
    groups = []
    for label, own, subs, prefixes in NAV:
        active = rel == own or any(rel.startswith(pre) for pre in prefixes)
        links = "\n".join(
            f'      <a class="sl{" here" if href == rel else ""}" href="{up}{href}">{text}</a>'
            for text, href in subs)
        groups.append(
            f'    <div class="ni ni-has">\n'
            f'      <a class="nl{" here" if active else ""}" href="{up}{own}">{label}'
            f'<span class="caret">&#9662;</span></a>\n'
            f'      <div class="sub">\n{links}\n      </div>\n'
            f'    </div>')
    rows = "\n".join(groups)
    return (f'<nav class="site"><div class="row">\n'
            f'  <a class="brand" href="{up}index.html">sharness<span>.ai</span></a>\n'
            f'  <span class="stage-pill" title="Nothing described on this site is built yet">status: design</span>\n'
            f'  <a class="ver" href="{up}admin/versions.html" title="Site release history">{VERSION}</a>\n'
            f'  <button class="nav-toggle" type="button" aria-expanded="false" aria-label="Menu">Menu</button>\n'
            f'  <div class="nav-items">\n{rows}\n  </div>\n'
            f'  <a class="gh" href="{GH}">★ GitHub</a>\n'
            f'  <script src="{up}assets/nav.js" defer></script>\n'
            f'</div></nav>')


def footer_html(rel, up):
    partnote = PARTNOTE_SELF if rel == "evidence/index.html" else PARTNOTE.format(up=up)
    md_twin = f' · <a href="{up}index.md">this page as markdown</a>' if rel == "index.html" else ""
    cols = "\n".join(
        "  <div>\n"
        f"    <h4>{head}</h4>\n"
        + "\n".join(f'    <a href="{l if l.startswith("http") else up + l}">{t}</a>' for t, l in links)
        + "\n  </div>"
        for head, links in FOOTER)
    return (f'<footer class="site"><div class="cols">\n'
            f'  <div>\n'
            f'    <div class="brandline">sharness<span>.ai</span></div>\n'
            f'    <p>{BLURB}</p>\n'
            f'    <p class="netline">{NETLINE}</p>\n'
            f'    <p class="partnote">{partnote}</p>\n'
            f'    <p class="verline">site <a href="{up}admin/versions.html">{VERSION}</a> · '
            f'<a href="{up}admin/index.html">engineering</a>{md_twin}</p>\n'
            f'  </div>\n{cols}\n</div></footer>')


def stamp_text_twins():
    """The version also appears in llms.txt and index.md (llms-full.txt is generated
    from them), and validate.js enforces that it agrees. Set it here so a release
    never depends on remembering to hand-edit them."""
    out = []
    for name, pattern, repl in (
            ("llms.txt", r"Site version: v\d+\.\d+\.\d+", f"Site version: {VERSION}"),
            ("index.md", r"· site v\d+\.\d+\.\d+ ·", f"· site {VERSION} ·")):
        p = ROOT / name
        if not p.exists():
            continue
        t = p.read_text()
        t2, n = re.subn(pattern, repl, t, count=1)
        if n and t2 != t:
            p.write_text(t2)
            out.append(name)
    return out


def main():
    changed = []
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        up = "../" * (len(path.relative_to(ROOT).parts) - 1)
        text = path.read_text()
        before = text
        text, n_nav = re.subn(r'<nav class="site">.*?</nav>', lambda _: nav_html(rel, up),
                              text, count=1, flags=re.S)
        text, n_foot = re.subn(r'<footer class="site">.*?</footer>', lambda _: footer_html(rel, up),
                               text, count=1, flags=re.S)
        if not n_nav or not n_foot:
            print(f"  ! {rel}: missing nav and/or footer block", file=sys.stderr)
        if text != before:
            path.write_text(text)
            changed.append(rel)
    changed += stamp_text_twins()
    print(f"chrome: {VERSION} applied — {len(changed)} file(s) updated")
    for c in changed:
        print(f"  · {c}")


if __name__ == "__main__":
    main()
