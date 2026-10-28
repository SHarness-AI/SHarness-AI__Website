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
VERSION = (ROOT / "version").read_text().strip()          # written by CI only (tools/release.py)
GH      = "https://github.com/SHarness-AI/SHarness-AI__CLI"      # the header link: the code
HOST    = (ROOT / "CNAME").read_text().strip()

# The nav, two levels. Each entry is (label, own page, [(sub-label, href), ...], prefixes).
#   · A group label is always a link to a real page, never a menu-only stub.
#   · `prefixes` decides the "here" state, so a page not itself in the nav still
#     lights up the group it belongs to.
NAV = [
    ("Try it", "code/playground/index.html", [
        ("Start here: the playground, in your browser", "code/playground/index.html"),
        ("A Linux kernel in a tab, running hello", "code/browser/demo/index.html"),
        ("Start in 60 seconds", "index.html#start"),
        ("Help us measure it: report your machine", "evidence/machines/index.html"),
        ("Mockup: the policy hash", "explain/mockups/policy-hash.html"),
        ("Mockup: the edge matrix", "explain/mockups/edges.html"),
    ], ("code/playground/", "code/browser/demo/")),
    ("Components", "components/index.html", [
        ("Start here: the OS a process sees", "components/index.html"),
        ("sharness.bash: the shell, as a service", "components/bash/index.html"),
        ("sharness.net: the only network client", "components/net/index.html"),
        ("sharness.kms: where a secret lives", "components/kms/index.html"),
        ("sharness.fs: the only writer", "components/fs/index.html"),
        ("sharness.llm: the only model client", "components/llm/index.html"),
        ("sharness.launcher: the bootstrap", "components/launcher/index.html"),
        ("sharness.policy: the manifest", "components/policy/index.html"),
    ], ("components/",)),
    ("How it works", "design/index.html", [
        ("Start here: the brief, in one read", "design/index.html"),
        ("Why: the last metre", "design/why/index.html"),
        ("Architecture", "design/architecture/index.html"),
        ("Components in depth", "design/components/index.html"),
        ("Process Behaviour Policies", "design/policies/index.html"),
        ("The PBP on one page", "design/pbp/index.html"),
        ("Keys and the KMS", "design/keys/index.html"),
        ("Agents and LLMs", "design/agents/index.html"),
        ("Enforcing the process tree", "design/process-tree/index.html"),
        ("What a process can do", "design/surface/index.html"),
        ("Containment", "design/containment/index.html"),
        ("The spectrum: hello world to sgit", "design/spectrum/index.html"),
        ("Roadmap &amp; open decisions", "design/roadmap/index.html"),
        ("Storyboards &amp; mockups", "explain/index.html"),
        ("Articles", "articles/index.html"),
    ], ("design/", "explain/", "articles/")),
    ("Evidence", "evidence/index.html", [
        ("Start here: the measurements", "evidence/index.html"),
        ("What exists today", "evidence/status/index.html"),
        ("hello on your machine: reported runs", "evidence/machines/index.html"),
        ("Research note", "evidence/research/index.html"),
        ("How it compares: policies at the centre", "landscape/index.html"),
        ("Enforceability matrix", "landscape/enforceability/index.html"),
        ("Integration points", "landscape/integrations/index.html"),
        ("Ruflo and ruv.sgit", "landscape/ruflo/index.html"),
        ("Market &amp; competitors", "landscape/market/index.html"),
    ], ("evidence/", "landscape/")),
    ("Code", "code/index.html", [
        ("Start here: where the code is", "code/index.html"),
        ("The CLI: sharness-ai", "code/cli/index.html"),
        ("Mockups &amp; experiments", "code/experiments/index.html"),
        ("Flows through the code", "code/flows/index.html"),
        ("Examples", "code/examples/index.html"),
        ("Linux in the browser", "code/browser/index.html"),
        ("Releases of the code: immutable paths", "code/releases/index.html"),
        ("Languages", "code/languages/index.html"),
        ("Standards and test vectors", "code/standards/index.html"),
    ], ("code/",)),
    ("Security", "security/index.html", [
        ("Start here: the register", "security/index.html"),
        ("Threat model", "security/threat-model/index.html"),
        ("Known risks", "security/risks/index.html"),
        ("Reviews", "security/reviews/index.html"),
        ("Hardening", "security/hardening/index.html"),
        ("Supply chain", "security/supply-chain/index.html"),
    ], ("security/",)),
    ("Project", "project/index.html", [
        ("Start here: the project", "project/index.html"),
        ("About &amp; naming", "project/about/index.html"),
        ("Release history", "project/releases.html"),
        ("Getting users: the review and the plan", "project/adoption/index.html"),
        ("The source documents", "project/sources/index.html"),
        ("Engineering: how the site is built", "project/engineering.html"),
        ("How the project is run", "admin/index.html"),
        ("The board: tasks &amp; requests", "admin/board/index.html"),
        ("Updates: what is happening", "admin/updates/index.html"),
        ("Outreach: finding the people it is for", "project/outreach/index.html"),
        ("The agents and their keys", "project/agents/index.html"),
        ("Telemetry: who reads this site", "project/telemetry/index.html"),
    ], ("project/", "admin/")),
]

# The footer: four columns by what a reader wants to do, then the files agents read on one line.
FOOTER = [
    ("Try it", [
        ("The playground", "code/playground/index.html"),
        ("A kernel in a tab", "code/browser/demo/index.html"),
        ("Start in 60 seconds", "index.html#start"),
        ("The CLI: sharness-ai", "code/cli/index.html"),
        ("Report your machine", "evidence/machines/index.html"),
        ("PyPI: sharness-ai ↗", "https://pypi.org/project/sharness-ai/"),
        ("GitHub: SHarness-AI__CLI ↗", "https://github.com/SHarness-AI/SHarness-AI__CLI"),
    ]),
    ("Understand", [
        ("The brief, in one read", "design/index.html"),
        ("The components", "components/index.html"),
        ("Why: the last metre", "design/why/index.html"),
        ("Architecture", "design/architecture/index.html"),
        ("Process Behaviour Policies", "design/policies/index.html"),
        ("Roadmap &amp; open decisions", "design/roadmap/index.html"),
        ("Storyboards", "explain/storyboards/index.html"),
        ("Articles", "articles/index.html"),
    ]),
    ("Check it", [
        ("Measurements", "evidence/index.html"),
        ("What exists today", "evidence/status/index.html"),
        ("hello on your machine", "evidence/machines/index.html"),
        ("Enforceability matrix", "landscape/enforceability/index.html"),
        ("Market &amp; competitors", "landscape/market/index.html"),
        ("Security: the register", "security/index.html"),
        ("Threat model", "security/threat-model/index.html"),
        ("Known risks", "security/risks/index.html"),
    ]),
    ("Follow the work", [
        ("About &amp; naming", "project/about/index.html"),
        ("Release history", "project/releases.html"),
        ("Getting users", "project/adoption/index.html"),
        ("How the project is run", "admin/index.html"),
        ("The board", "admin/board/index.html"),
        ("Updates", "admin/updates/index.html"),
        ("Commit notes", "admin/notes/index.html"),
        ("Guidance for agents", "admin/guidance/index.html"),
    ]),
]
AGENT_FILES = [("llms.txt", "llms.txt"), ("llms-full.txt", "llms-full.txt"), ("index.md", "index.md"),
               ("sitemap.xml", "sitemap.xml"), ("security.txt", ".well-known/security.txt")]

BLURB = ("SHarness runs agents and their tools as small, single-purpose processes, each locked "
         "down by the kernel and talking only over allowed, mutually authenticated connections. "
         "By Dinis Cruz. All content CC BY 4.0.")
PARTNOTE = ('⚠ Status: design, with the first experiments, two doors (sharness.fs, sharness.net) and a first slice of the launcher runnable as MVPs; no other component is built; measured figures '
            'carry their date. <a href="{up}evidence/index.html" style="display:inline;padding:0">What is measured, '
            'what is proposed</a>.')
PARTNOTE_SELF = ('⚠ Status: design, with two doors runnable as MVPs. You are on the page that says what '
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
    return (f'<nav class="site"><a class="skip" href="#content">Skip to content</a><div class="row">\n'
            f'  <a class="brand" href="{up}index.html">sharness<span>.ai</span></a>\n'
            f'  <a class="ver" href="{up}project/releases.html" title="Site release history: what this version changed">{VERSION}</a>\n'
            f'  <button class="nav-toggle" type="button" aria-expanded="false" aria-label="Menu">Menu</button>\n'
            f'  <div class="nav-items">\n{rows}\n  </div>\n'
            f'  <a class="gh" href="{GH}">★ GitHub</a>\n'
            f'  <script src="{up}assets/nav.js" defer></script>\n'
            f'  <script src="{up}assets/telemetry.js" data-root="{up}" defer></script>\n'
            f'</div></nav>')


def pager_html(rel, up):
    """Previous and next for a page that is in a menu, in the menu's order: the menu is the
    reading order, so a reader who finishes a page is told where it goes next. Empty for a
    page in no menu."""
    for label, _own, subs, _prefixes in NAV:
        seq = [(t, h) for t, h in subs if "#" not in h and not h.startswith("http")]
        hrefs = [h for _t, h in seq]
        if rel not in hrefs:
            continue
        i = hrefs.index(rel)
        def card(item, cls, word):
            if not item:
                return '<span></span>'
            text = re.sub(r"^Start here: ", "", item[0])
            return (f'<a class="{cls}" href="{up}{item[1]}"><span class="pg-dir">{word} in {label}</span>'
                    f'<span class="pg-title">{text}</span></a>')
        prev = seq[i - 1] if i > 0 else None
        nxt = seq[i + 1] if i + 1 < len(seq) else None
        if not prev and not nxt:
            return ""
        return (f'<nav class="pager" aria-label="Previous and next in {label}">'
                f'{card(prev, "pg-prev", "← Previous")}{card(nxt, "pg-next", "Next →")}</nav>')
    return ""


def footer_html(rel, up):
    partnote = PARTNOTE_SELF if rel == "evidence/index.html" else PARTNOTE.format(up=up)
    md_twin = f' · <a href="{up}index.md">this page as markdown</a>' if rel == "index.html" else ""
    cols = "\n".join(
        "  <div>\n"
        f"    <h4>{head}</h4>\n"
        + "\n".join(f'    <a href="{l if l.startswith("http") else up + l}">{t}</a>' for t, l in links)
        + "\n  </div>"
        for head, links in FOOTER)
    files = " · ".join(f'<a href="{up}{l}">{t}</a>' for t, l in AGENT_FILES)
    return (f'<footer class="site"><div class="cols">\n'
            f'  <div>\n'
            f'    <div class="brandline">sharness<span>.ai</span></div>\n'
            f'    <p>{BLURB}</p>\n'
            f'    <p class="netline">{NETLINE}</p>\n'
            f'    <p class="partnote">{partnote}</p>\n'
            f'    <p class="verline">site <a class="ver" href="{up}project/releases.html" title="Site release history">{VERSION}</a> · '
            f'<a href="{up}project/engineering.html">engineering</a>{md_twin}</p>\n'
            f'  </div>\n{cols}\n</div>\n'
            f'<div class="agentline">For agents and crawlers: {files}</div></footer>')


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
        if rel.startswith("code/releases/") or rel.startswith("code/browser/demo/"):
            continue                     # published copies of the CLI's files: immutable, never re-chromed
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
