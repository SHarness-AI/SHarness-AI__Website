#!/usr/bin/env python3
"""Generates /articles/: each article's page and markdown twin, and the index.

Run from anywhere:  python3 admin/build/gen_articles.py           (write)
                    python3 admin/build/gen_articles.py --check   (CI: fail if anything is stale)

Sources are admin/content/articles/<slug>.md, in the newsroom's format exactly as
send.sgit.ai's "Every site its own articles" sets it out (front matter, a lead
figure, In short {#in-short}, the argument, What this does not claim {#limits},
Where this comes from {#sources}), so a source file imports into newsroom.sgit.ai
unchanged. From each this writes:

  articles/<slug>.html   the page (the converter in gen_pages.py, plus byline and summary)
  articles/<slug>.md     the markdown twin: a header, then the body, no front matter

and articles/index.html + index.md, newest first, from the front matter alone.
The slug is the address and never changes once published. validate.js holds every
source to the format; this file only renders it.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrome                                                    # noqa: E402
from gen_pages import md_to_html                                 # noqa: E402

ROOT    = chrome.ROOT
SRC     = ROOT / "admin/content/articles"
OUT     = ROOT / "articles"
HOST    = chrome.HOST
FIELDS  = ("title", "date", "author", "author_url", "summary", "version", "license", "tags", "status")


def parse(path):
    """Front matter is flat `key: value` lines (tags as [a, b]); the rest is the body."""
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"{path}: no front matter")
    meta = {}
    for line in m.group(1).split("\n"):
        k, _, v = line.partition(":")
        v = re.sub(r"\s+#.*$", "", v).strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        meta[k.strip()] = v
    meta["slug"] = path.stem
    return meta, m.group(2).lstrip("\n")


def articles():
    out = [parse(p) for p in sorted(SRC.glob("*.md"))]
    return sorted(out, key=lambda a: (a[0]["date"], a[0]["slug"]), reverse=True)


def byline(meta, link_md=False):
    return f'By [{meta["author"]}]({meta["author_url"]}) · {meta["date"]} · {meta["status"]}'


def twin(meta, body):
    return (f'# {meta["title"]}\n\n> {meta["summary"]}\n\n'
            f'*Source: <https://{HOST}/articles/{meta["slug"]}.html> · generated from the same source '
            f'as the page, so the two cannot drift.*\n\n---\n\n'
            f'{byline(meta)}\n\n**Summary:** {meta["summary"]}\n\n{body.rstrip()}\n\n---\n\n'
            f'*[Site index for agents](../llms.txt) · [All articles](index.md)*\n')


def page(rel, title, desc, main, og_type="article", md_href=None):
    up = "../"
    url = f"https://{HOST}/{rel}"
    alt = (f'<link rel="alternate" type="text/markdown" href="{md_href}" title="This page as markdown">\n'
           if md_href else "")
    d = html.escape(desc)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="sharness.ai">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{d}">
<meta name="twitter:card" content="summary">
{alt}<link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>

{chrome.nav_html(rel, up)}

<main class="doc article">
{main}
</main>

{chrome.footer_html(rel, up)}

</body>
</html>
'''


def article_html(meta, body):
    _, body_html = md_to_html(body)
    by = (f'By <a href="{html.escape(meta["author_url"])}">{html.escape(meta["author"])}</a> · '
          f'<time datetime="{meta["date"]}">{meta["date"]}</time> · {html.escape(meta["status"])} · '
          f'<a href="{meta["slug"]}.md">this article as markdown</a>')
    main = (f'  <div class="crumb"><a href="../index.html">sharness.ai</a> / <a href="index.html">articles</a></div>\n'
            f'  <h1>{html.escape(meta["title"])}</h1>\n'
            f'  <p class="byline">{by}</p>\n'
            f'  <p class="summary"><b>Summary:</b> {html.escape(meta["summary"])}</p>\n'
            f'{body_html}\n')
    short = meta["title"].split(":")[0]
    return page(f'articles/{meta["slug"]}.html', f"{short} — SHarness", meta["summary"][:300],
                main, md_href=f'{meta["slug"]}.md')


INTRO = """Each article makes **one argument** about SHarness, in the format the [newsroom](https://newsroom.sgit.ai/) uses, so any of them can be imported there unchanged: a summary a reader can stop at, a lead figure, In short, the argument, what it does not claim, and where it comes from. The format is the one send.sgit.ai's [Every site its own articles](https://send.sgit.ai/articles/every-site-its-own-articles.html) sets out for every site in the network.

There are two kinds of author, and the byline says which:

- **Dinis Cruz**, through an agent: a voice memo or a message of his, written up in his voice, under his name.
- **An agent in its own voice**: sharness.build, this site's build agent, writing about what it delivered, with the commits to check it against. [Who writes here](../about/index.md#who-writes-here) says who each is.

The design itself is on the [design pages](../architecture/index.md); an article is an argument about it, or the record of a piece of work."""


def index_md(items):
    rows = "\n".join(f'- [{m["title"]}]({m["slug"]}.md): {byline(m)}' for m, _ in items)
    return (f'# Articles\n\n> Articles on sharness.ai, newest first, in the newsroom\'s format: each one argument '
            f'about SHarness, written up from Dinis Cruz\'s memos or by an agent about what it delivered.\n\n'
            f'*Source: <https://{HOST}/articles/index.html> · generated from the articles\' front matter.*\n\n'
            f'---\n\n{INTRO}\n\n## Newest first\n\n{rows}\n')


def index_html(items):
    _, intro = md_to_html(INTRO)
    cards = "\n".join(
        f'    <a class="card" href="{m["slug"]}.html"><span class="tag">{html.escape(m["date"])} · '
        f'{html.escape(m["author"])}</span><h3>{html.escape(m["title"])}</h3>'
        f'<p>{html.escape(" ".join(m["summary"].split()[:60]))}…</p><span class="go">Read →</span></a>'
        for m, _ in items)
    main = (f'  <div class="crumb"><a href="../index.html">sharness.ai</a> / articles · '
            f'<a href="index.md">this page as markdown</a></div>\n'
            f'  <h1>Articles</h1>\n{intro}\n  <h2 id="newest">Newest first</h2>\n'
            f'  <div class="cards articles">\n{cards}\n  </div>\n')
    return page("articles/index.html", "Articles — SHarness",
                "Articles on SHarness, newest first: Dinis Cruz's memos written up in his voice, and agents "
                "writing what they delivered.", main, og_type="website", md_href="index.md")


def outputs():
    items = articles()
    out = {OUT / "index.html": index_html(items), OUT / "index.md": index_md(items)}
    for meta, body in items:
        out[OUT / f'{meta["slug"]}.html'] = article_html(meta, body)
        out[OUT / f'{meta["slug"]}.md'] = twin(meta, body)
    return items, out


def main():
    check = "--check" in sys.argv
    items, out = outputs()
    stale = [p for p, t in out.items() if not p.exists() or p.read_text() != t]
    if check:
        if stale:
            print("gen_articles: stale (run python3 admin/build/gen_articles.py and commit):", file=sys.stderr)
            for p in stale:
                print(f"  ✗ {p.relative_to(ROOT).as_posix()}", file=sys.stderr)
            sys.exit(1)
    else:
        OUT.mkdir(exist_ok=True)
        for p in stale:
            p.write_text(out[p])
            print(f"  · {p.relative_to(ROOT).as_posix()}")
    print(f"gen_articles: {len(items)} article(s) {'up to date' if check else 'generated'}")


if __name__ == "__main__":
    main()
