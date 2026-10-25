#!/usr/bin/env python3
"""Generates /storyboards/ from the data in content/storyboards/.

Run from anywhere:  python3 tools/gen_storyboards.py           (write)
                    python3 tools/gen_storyboards.py --check   (CI: fail if anything is stale)

A storyboard is data: one JSON file per storyboard and one cast.json, drawn in the reader's
browser by the storyboards.sgit.ai kit (api.storyboards.sgit.ai, release pinned in KIT below,
immutable at that path). This site keeps the sources under content/storyboards/ in the
same shape storyboards.sgit.ai imports (NN__<slug>.json + cast.json), and generates:

  explain/storyboards/<slug>/storyboard.json   the source, as is
  explain/storyboards/<slug>/bundle.json       {storyboard, cast, packs}: what <sg-storyboard src> fetches
  explain/storyboards/<slug>/index.html        the page: the deck, the script, the embed snippet
  explain/storyboards/<slug>/index.md          the script as markdown (the twin agents read)
  explain/storyboards/cast.json                the cast, as is
  explain/storyboards/index.html + index.md    the section: every storyboard, the cast, how they are made

Not generated here: thumb.jpg and og.jpg beside each storyboard. They are rendered with the
kit's own renderer and committed, so a link preview is drawn by the same bytes as the page:

  git clone https://github.com/SGit-AI/SGit-AI__Website__Storyboards__API api
  SB_RELEASE=v0/v0.1/v0.1.0 node api/tools/render.mjs jobs.json     # needs Node + Playwright

This script refuses --check if a storyboard has no thumb.jpg or og.jpg, so a new storyboard
cannot ship without its previews. Validation of the data itself (unknown character, pose,
mood or prop) is the kit's StoryboardFormats.validate; tools/validate_storyboards.cjs
runs it in Node when Node is available and is part of the gate.
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrome                                                    # noqa: E402
from gen_pages import md_to_html                                 # noqa: E402

ROOT  = chrome.ROOT
SRC   = ROOT / "content/storyboards"
OUT   = ROOT / "explain/storyboards"
HOST  = chrome.HOST
KIT   = "https://api.storyboards.sgit.ai/v0/v0.1/v0.1.0/"
# embed.js's sha384 from the kit's manifest.json at that release (checked 25 Oct 2026): a release is immutable, so this never moves unless KIT does
KIT_INTEGRITY = "sha384-MJYywdRM1gslaDV4AypUBYskTgX6Tc46P6B5aakMDBi/xb2hytOzWCsT6G09oc2q"
PACKS = ["security"]
ASOF  = "24 Oct 2026"                                             # the date the data was last checked against the design


def load():
    cast = json.loads((SRC / "cast.json").read_text())
    boards = []
    for p in sorted(SRC.glob("*__*.json")):
        boards.append(json.loads(p.read_text()))
    return cast, boards


def names(cast):
    return {c["id"]: c["name"] for c in cast["characters"]}


def script_body(sb, cast):
    """The storyboard as a script: what each panel shows and says, in reading order (markdown)."""
    who = names(cast)
    out = []
    if sb.get("rule"):
        out += [f'**Rule:** {sb["rule"]}', ""]
    for i, s in enumerate(sb["scenes"], 1):
        kind = s.get("kind", "scene")
        head = s.get("caption") or s.get("title") or ("Punchline" if kind == "punchline" else f"Panel {i}")
        out += [f"## {i}. {head}", ""]
        if kind == "cover":
            out.append(f'*Cover.* {s.get("subtitle", "")}')
            if s.get("cast"):
                out.append(f'On the cover: {", ".join(who.get(c["who"], c["who"]) for c in s["cast"])}.')
            out.append("")
        if kind == "punchline":
            out += [f'**{s["punchline"]}**', ""]
        said = []
        for c in s.get("cast", []):
            if c.get("says"):
                said.append(f'- **{who.get(c["who"], c["who"])}:** {c["says"]}')
            if c.get("thinks"):
                said.append(f'- **{who.get(c["who"], c["who"])}** (thinks): {c["thinks"]}')
        for p in s.get("props", []):
            if not p.get("lines") and (p.get("label") or p.get("text")):
                said.append(f'- *{p["kind"]}:* {p.get("label") or p.get("text")}')
        if said:
            out += said + [""]
        for p in s.get("props", []):
            if p.get("lines"):
                out += ["```"] + p["lines"] + ["```", ""]
        ev = s.get("evidence")
        if ev and ev.get("quote"):
            out += [f'> "{ev["quote"]}" ({ev.get("source", "")})', ""]
        if s.get("note"):
            out += [f'*Note:* {s["note"]}', ""]
        if s.get("source"):
            out += [f'*Source:* {s["source"]}', ""]
    return "\n".join(out)


def script_md(sb, cast):
    head = [f'# {sb["title"]}', "", f'> {sb["subtitle"]}', "",
            f'*Source: <https://{HOST}/explain/storyboards/{sb["slug"]}/index.html> · status: {sb.get("status", "draft")} · '
            f'by {sb.get("by", "")} · drawn from [storyboard.json](storyboard.json) with [cast.json](../cast.json) '
            f'by the storyboards.sgit.ai kit v0.1.0.*', "", "---", ""]
    foot = ["---", "", "*[All storyboards](../index.md) · [Site index for agents](../../../llms.txt)*", ""]
    return "\n".join(head + [script_body(sb, cast)] + foot)


def page(rel, title, desc, main, md_href, up):
    url = f"https://{HOST}/{rel}"
    d = html.escape(desc)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="sharness.ai">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="https://{HOST}/{rel.rsplit('/', 1)[0]}/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="text/markdown" href="{md_href}" title="This page as markdown">
<link rel="stylesheet" href="{up}assets/site.css">
<script src="{KIT}embed.js" integrity="{KIT_INTEGRITY}" crossorigin="anonymous" defer></script>
</head>
<body>

{chrome.nav_html(rel, up)}

<main class="doc">
{main}
</main>

{chrome.footer_html(rel, up)}

</body>
</html>
'''


def board_html(sb, cast):
    slug = sb["slug"]
    rel = f"explain/storyboards/{slug}/index.html"
    status = sb.get("status", "draft")
    embed = (f'&lt;script src="{KIT}embed.js" defer&gt;&lt;/script&gt;\n'
             f'&lt;sg-storyboard src="https://{HOST}/explain/storyboards/{slug}/bundle.json" view="deck"&gt;&lt;/sg-storyboard&gt;')
    _, script_html = md_to_html(script_body(sb, cast))
    main = (f'  <div class="crumb"><a href="../../../index.html">sharness.ai</a> / <a href="../../index.html">explain</a> / <a href="../index.html">storyboards</a> / {html.escape(slug)} · '
            f'<a href="index.md">this page as markdown</a></div>\n'
            f'  <h1>{html.escape(sb["title"])}</h1>\n'
            f'  <p class="byline">{html.escape(sb["subtitle"])}</p>\n'
            f'  <p class="small dim">Status: <b>{html.escape(status)}</b> · by {html.escape(sb.get("by", ""))} · '
            f'{len(sb["scenes"])} panels, drawn from data in your browser by the storyboards.sgit.ai kit (release v0.1.0, pinned) · '
            f'checked against the design <span class="asof">as of {ASOF}</span>.</p>\n'
            f'  <div class="note">What the strip shows is the <b>design</b>: nothing drawn here is built, except where a panel says it was '
            f'measured, and then the date and the method are on <a href="../../../evidence/index.html">Evidence</a>. '
            f'Every line a character says is the storyboard\'s own words, not a quote; evidence panels quote this site word for word.</div>\n'
            f'  <sg-storyboard src="bundle.json" view="deck"></sg-storyboard>\n'
            f'  <p class="small dim">Flick through as a deck. Every panel at once: '
            f'<a href="index.html#script">the script below</a>, or the data itself: <a href="storyboard.json">storyboard.json</a> · '
            f'<a href="../cast.json">cast.json</a> · <a href="bundle.json">bundle.json</a>.</p>\n'
            f'  <h2 id="script">The script</h2>\n'
            f'{script_html}\n'
            f'  <h2 id="embed">Embed it</h2>\n'
            f'  <p>One script tag and one element; the kit draws it from the data at this address. The release is pinned, so the drawing never changes under you.</p>\n'
            f'  <pre class="diagram">{embed}</pre>\n'
            f'  <div class="pagenav"><a href="../index.html">← All storyboards</a><a href="../../../code/experiments/index.html">Mockups and experiments →</a></div>\n')
    return page(rel, f'{sb["title"]} — a SHarness storyboard', sb["subtitle"], main, "index.md", "../../../")


INTRO = """A storyboard is a short strip of panels: who is there, what they say, the evidence, the punchline. Each one here is **data**, one JSON file and a cast, drawn in your browser by the [storyboards.sgit.ai](https://storyboards.sgit.ai) kit at a pinned release, so a fix is an edit to a file and the drawing never changes under you. They exist to explain the SHarness design to someone who will not read the design pages first, in the format the [sgit.ai network](https://storyboards.sgit.ai) uses for its own.

Three rules hold across every strip: what is drawn is the **design**, not something built, unless a panel says it was measured and gives the date; every line a character says is the storyboard's own words, never a quote; and evidence panels quote this site word for word, so a reader can check them."""


def index_md(boards, cast):
    rows = "\n".join(f'- [{b["title"]}]({b["slug"]}/index.md): {b["subtitle"]} *Status: {b.get("status", "draft")}.*' for b in boards)
    people = "\n".join(f'- **{c["name"]}** ({c["pronouns"]}, {c["kind"]}): {c["role"]}. Stands for {c["stands_for"]}. Line: "{c["line"]}"'
                       for c in cast["characters"])
    return (f'# Storyboards\n\n> The SHarness design as short comic strips, drawn from data by the storyboards.sgit.ai kit: '
            f'the last metre, a tricked process doing its one job, and the hello world inside.\n\n'
            f'*Source: <https://{HOST}/storyboards/index.html> · generated from content/storyboards/.*\n\n---\n\n'
            f'{INTRO}\n\n## The storyboards\n\n{rows}\n\n## The cast\n\n{people}\n\n'
            f'The cast is proposed by sharness.build for Dinis Cruz to accept, change or replace; the data is [cast.json](cast.json).\n\n'
            f'## How they are made\n\n'
            f'- Sources: `content/storyboards/NN__<slug>.json` and `cast.json`, in the shape storyboards.sgit.ai imports.\n'
            f'- Generated by `tools/gen_storyboards.py`: each storyboard\'s page, its markdown script, its `bundle.json`, and this index. CI fails if they drift.\n'
            f'- Drawn by the kit at `{KIT}` (release v0.1.0, immutable, with a hash for every file in its manifest). Nothing is an image except the committed `thumb.jpg` and `og.jpg`, rendered by the kit\'s own renderer for link previews.\n'
            f'- Validated by the kit\'s `StoryboardFormats.validate`: an unknown character, pose, mood or prop stops the build.\n')


def index_html(boards, cast):
    _, intro = md_to_html(INTRO)
    cards = "\n".join(
        f'    <a class="card" href="{b["slug"]}/index.html"><img src="{b["slug"]}/thumb.jpg" alt="" style="width:100%;height:auto;border-radius:8px;border:1px solid var(--line);margin-bottom:.5rem">'
        f'<span class="tag">{html.escape(b.get("status", "draft"))} · {len(b["scenes"])} panels</span><h3>{html.escape(b["title"])}</h3>'
        f'<p>{html.escape(b["subtitle"])}</p><span class="go">Open →</span></a>'
        for b in boards)
    people = "\n".join(
        f'<tr><td><b>{html.escape(c["name"])}</b><br><span class="small dim">{html.escape(c["pronouns"])} · {html.escape(c["kind"])}</span></td>'
        f'<td>{html.escape(c["role"])}</td><td>{html.escape(c["stands_for"])}</td><td><em>{html.escape(c["line"])}</em></td></tr>'
        for c in cast["characters"])
    main = (f'  <div class="crumb"><a href="../../index.html">sharness.ai</a> / <a href="../index.html">explain</a> / storyboards · <a href="index.md">this page as markdown</a></div>\n'
            f'  <h1>Storyboards</h1>\n{intro}\n'
            f'  <p class="small dim">{len(boards)} storyboards · {sum(len(b["scenes"]) for b in boards)} panels · {len(cast["characters"])} characters · '
            f'checked against the design <span class="asof">as of {ASOF}</span>.</p>\n'
            f'  <div class="cards">\n{cards}\n  </div>\n'
            f'  <h2 id="cast">The cast</h2>\n'
            f'  <p>Proposed by sharness.build for Dinis Cruz to accept, change or replace. Fictional; each stands for a part in the design. The data is <a href="cast.json">cast.json</a>.</p>\n'
            f'  <div class="tablewrap"><table><thead><tr><th>Who</th><th>Role</th><th>Stands for</th><th>Line</th></tr></thead><tbody>\n{people}\n</tbody></table></div>\n'
            f'  <h2 id="made">How they are made</h2>\n'
            f'  <ul>\n'
            f'    <li><b>Sources:</b> <code>content/storyboards/NN__&lt;slug&gt;.json</code> and <code>cast.json</code>, in the shape <a href="https://storyboards.sgit.ai">storyboards.sgit.ai</a> imports, so they can be listed there as a series.</li>\n'
            f'    <li><b>Generated</b> by <code>tools/gen_storyboards.py</code>: each page, its markdown script, its <code>bundle.json</code>, and this index. CI fails if they drift.</li>\n'
            f'    <li><b>Drawn</b> by the kit at <code>{KIT}</code> (release v0.1.0, immutable, a hash for every file in its <a href="{KIT}manifest.json">manifest</a>). Nothing is an image except the committed <code>thumb.jpg</code> and <code>og.jpg</code>, rendered by the kit\'s own renderer for link previews.</li>\n'
            f'    <li><b>Validated</b> by the kit\'s <code>StoryboardFormats.validate</code> in the gate: an unknown character, pose, mood or prop stops the release.</li>\n'
            f'  </ul>\n'
            f'  <div class="pagenav"><a href="../index.html">← Explain</a><a href="../../articles/index.html">Articles →</a></div>\n')
    return page("explain/storyboards/index.html", "Storyboards — SHarness",
                "The SHarness design as short comic strips drawn from data: the last metre, a tricked process doing its one job, and the hello world inside.",
                main, "index.md", "../../")


def outputs():
    cast, boards = load()
    out = {OUT / "cast.json": json.dumps(cast, indent=1, ensure_ascii=False) + "\n",
           OUT / "index.html": index_html(boards, cast), OUT / "index.md": index_md(boards, cast)}
    for b in boards:
        d = OUT / b["slug"]
        out[d / "storyboard.json"] = json.dumps(b, indent=1, ensure_ascii=False) + "\n"
        out[d / "bundle.json"] = json.dumps({"storyboard": b, "cast": cast, "packs": PACKS}, ensure_ascii=False) + "\n"
        out[d / "index.html"] = board_html(b, cast)
        out[d / "index.md"] = script_md(b, cast)
    return boards, out


def main():
    check = "--check" in sys.argv
    boards, out = outputs()
    stale = [p for p, t in out.items() if not p.exists() or p.read_text() != t]
    missing = [f'{b["slug"]}/{img}' for b in boards for img in ("thumb.jpg", "og.jpg") if not (OUT / b["slug"] / img).exists()]
    if check:
        if stale or missing:
            print("gen_storyboards: stale (run python3 tools/gen_storyboards.py and commit):", file=sys.stderr)
            for p in stale:
                print(f"  ✗ {p.relative_to(ROOT).as_posix()}", file=sys.stderr)
            for m in missing:
                print(f"  ✗ storyboards/{m} missing: render it (see the docstring)", file=sys.stderr)
            sys.exit(1)
    else:
        for p in stale:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(out[p])
            print(f"  · {p.relative_to(ROOT).as_posix()}")
        for m in missing:
            print(f"  ! storyboards/{m} missing: render it (see the docstring)")
    print(f"gen_storyboards: {len(boards)} storyboard(s) {'up to date' if check else 'generated'}")


if __name__ == "__main__":
    main()
