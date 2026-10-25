#!/usr/bin/env python3
"""The single definition of this site's nav and footer, and the tool that applies it.

Run from anywhere: python3 tools/chrome.py

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

ROOT    = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "tools/version.txt").read_text().strip()
GH      = "https://github.com/SHarness-AI/SHarness-AI__CLI"      # the header link: the code
HOST    = (ROOT / "CNAME").read_text().strip()

# The nav, two levels. Each entry is (label, own page, [(sub-label, href), ...], prefixes).
#   · A group label is always a link to a real page, never a menu-only stub.
#   · `prefixes` decides the "here" state, so a page not itself in the nav still
#     lights up the group it belongs to.
NAV = [
    ("Try it", "code/playground/index.html", [
        ("&#9679; The playground: type sharness-ai in your browser", "code/playground/index.html"),
        ("A Linux kernel in a tab, running hello", "code/browser/demo/index.html"),
        ("Start in 60 seconds", "index.html#start"),
        ("Help us measure it: report your machine", "evidence/machines/index.html"),
        ("Mockup: the policy hash", "explain/mockups/policy-hash.html"),
        ("Mockup: the edge matrix", "explain/mockups/edges.html"),
    ], ("code/playground/", "code/browser/demo/", "evidence/machines/")),
    ("The design", "design/index.html", [
        ("&#9679; The brief: in one read", "design/index.html"),
        ("Why: the last metre", "design/why/index.html"),
        ("Architecture", "design/architecture/index.html"),
        ("Components", "design/components/index.html"),
        ("Keys and the KMS", "design/keys/index.html"),
        ("Process Behaviour Policies", "design/policies/index.html"),
        ("Agents and LLMs", "design/agents/index.html"),
        ("Enforcing the process tree", "design/process-tree/index.html"),
        ("What a process can do", "design/surface/index.html"),
        ("Containment", "design/containment/index.html"),
        ("The spectrum: hello world to sgit", "design/spectrum/index.html"),
        ("Roadmap &amp; open decisions", "design/roadmap/index.html"),
    ], ("design/",)),
    ("The code", "code/index.html", [
        ("&#9679; Where the code is", "code/index.html"),
        ("The CLI: sharness-ai", "code/cli/index.html"),
        ("Mockups &amp; experiments", "code/experiments/index.html"),
        ("Flows through the code", "code/flows/index.html"),
        ("Examples", "code/examples/index.html"),
        ("Linux in the browser", "code/browser/index.html"),
        ("Playground: run it in your browser", "code/playground/index.html"),
        ("Languages", "code/languages/index.html"),
    ], ("code/",)),
    ("Evidence", "evidence/index.html", [
        ("&#9679; Measurements", "evidence/index.html"),
        ("What exists today", "evidence/status/index.html"),
        ("Research note", "evidence/research/index.html"),
        ("hello on your machine: reported runs", "evidence/machines/index.html"),
    ], ("evidence/",)),
    ("Landscape", "landscape/index.html", [
        ("&#9679; Policies at the centre", "landscape/index.html"),
        ("Enforceability matrix", "landscape/enforceability/index.html"),
        ("Integration points", "landscape/integrations/index.html"),
        ("Ruflo and ruv.sgit", "landscape/ruflo/index.html"),
        ("Market &amp; competitors", "landscape/market/index.html"),
    ], ("landscape/",)),
    ("Explain", "explain/index.html", [
        ("&#9679; Storyboards &amp; mockups", "explain/index.html"),
        ("Storyboards", "explain/storyboards/index.html"),
        ("Mockup: policy hash", "explain/mockups/policy-hash.html"),
        ("Mockup: edge matrix", "explain/mockups/edges.html"),
        ("Articles", "articles/index.html"),
    ], ("explain/", "articles/")),
    ("Project", "project/index.html", [
        ("&#9679; Project", "project/index.html"),
        ("About &amp; naming", "project/about/index.html"),
        ("The source documents", "project/sources/index.html"),
        ("Engineering: how the site is built", "project/engineering.html"),
        ("Comms: tasks &amp; requests", "project/comms.html"),
        ("Release history", "project/releases.html"),
        ("Getting users: the review and the plan", "project/adoption/index.html"),
        ("Admin: how the project is run", "admin/index.html"),
        ("The board: tasks &amp; requests", "admin/board/index.html"),
        ("Updates: what is happening", "admin/updates/index.html"),
        ("Outreach: finding the people it is for", "project/outreach/index.html"),
        ("The agents and their keys", "project/agents/index.html"),
        ("Telemetry: who reads this site", "project/telemetry/index.html"),
    ], ("project/", "admin/")),
]

FOOTER = [
    ("The design", [
        ("The brief: in one read", "design/index.html"),
        ("Why: the last metre", "design/why/index.html"),
        ("Architecture", "design/architecture/index.html"),
        ("Components", "design/components/index.html"),
        ("Keys and the KMS", "design/keys/index.html"),
        ("Process Behaviour Policies", "design/policies/index.html"),
        ("Agents and LLMs", "design/agents/index.html"),
        ("Enforcing the process tree", "design/process-tree/index.html"),
        ("What a process can do", "design/surface/index.html"),
        ("Containment", "design/containment/index.html"),
        ("The spectrum", "design/spectrum/index.html"),
        ("Roadmap &amp; open decisions", "design/roadmap/index.html"),
    ]),
    ("The code", [
        ("Where the code is", "code/index.html"),
        ("The CLI: sharness-ai", "code/cli/index.html"),
        ("Mockups &amp; experiments", "code/experiments/index.html"),
        ("Flows through the code", "code/flows/index.html"),
        ("Examples", "code/examples/index.html"),
        ("Linux in the browser", "code/browser/index.html"),
        ("Languages", "code/languages/index.html"),
        ("PyPI: sharness-ai", "https://pypi.org/project/sharness-ai/"),
        ("GitHub: SHarness-AI__CLI", "https://github.com/SHarness-AI/SHarness-AI__CLI"),
    ]),
    ("Evidence, landscape, explain", [
        ("Measurements", "evidence/index.html"),
        ("What exists today", "evidence/status/index.html"),
        ("Research note", "evidence/research/index.html"),
        ("hello on your machine", "evidence/machines/index.html"),
        ("Landscape: policies at the centre", "landscape/index.html"),
        ("Enforceability matrix", "landscape/enforceability/index.html"),
        ("Ruflo and ruv.sgit", "landscape/ruflo/index.html"),
        ("Market &amp; competitors", "landscape/market/index.html"),
        ("Storyboards", "explain/storyboards/index.html"),
        ("Mockups", "explain/index.html"),
        ("Articles", "articles/index.html"),
    ]),
    ("Project &amp; agents", [
        ("About &amp; naming", "project/about/index.html"),
        ("The source documents", "project/sources/index.html"),
        ("Engineering", "project/engineering.html"),
        ("Comms &amp; release history", "project/comms.html"),
        ("Admin: how the project is run", "admin/index.html"),
        ("The board", "admin/board/index.html"),
        ("Updates", "admin/updates/index.html"),
        ("Commit notes", "admin/notes/index.html"),
        ("Guidance for agents (AGENTS.md)", "admin/guidance/index.html"),
        ("Getting users", "project/adoption/index.html"),
        ("Outreach", "project/outreach/index.html"),
        ("The agents and their keys", "project/agents/index.html"),
        ("Telemetry", "project/telemetry/index.html"),
        ("llms.txt", "llms.txt"),
        ("llms-full.txt", "llms-full.txt"),
        ("index.md", "index.md"),
        ("sitemap.xml", "sitemap.xml"),
    ]),
]

BLURB = ("SHarness runs agents and their tools as small, single-purpose processes, each locked "
         "down by the kernel and talking only over allowed, mutually authenticated connections. "
         "By Dinis Cruz. All content CC BY 4.0.")
PARTNOTE = ('⚠ Status: design, with the first experiments runnable. No component is built; measured figures '
            'carry their date. <a href="{up}evidence/index.html" style="display:inline;padding:0">What is measured, '
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
            f'  <span class="stage-pill" title="No SHarness component is built; the experiments are runnable and measured">status: experiments</span>\n'
            f'  <a class="ver" href="{up}project/releases.html" title="Site release history">{VERSION}</a>\n'
            f'  <button class="nav-toggle" type="button" aria-expanded="false" aria-label="Menu">Menu</button>\n'
            f'  <div class="nav-items">\n{rows}\n  </div>\n'
            f'  <a class="gh" href="{GH}">★ GitHub</a>\n'
            f'  <script src="{up}assets/nav.js" defer></script>\n'
            f'  <script src="{up}assets/telemetry.js" data-root="{up}" defer></script>\n'
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
            f'    <p class="verline">site <a href="{up}project/releases.html">{VERSION}</a> · '
            f'<a href="{up}project/engineering.html">engineering</a>{md_twin}</p>\n'
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
        if rel == "404.html":
            up = "/"                     # served at any missing address, so its links must be absolute
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
