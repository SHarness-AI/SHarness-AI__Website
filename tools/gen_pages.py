#!/usr/bin/env python3
"""Generates each design page's index.html from its index.md twin.

Run from anywhere:  python3 tools/gen_pages.py           (write)
                    python3 tools/gen_pages.py --check   (CI: fail if any page is stale)

The markdown is the source of truth and is served as-is at the same path
(/<page>/index.md), so an agent and a person read the same text. The HTML is
generated from it here and never edited by hand. Same idea as cli.sgit.ai's
markdown twins, implemented as a deliberately small converter for the subset
the pages use (headings, paragraphs, lists, tables, fenced code, blockquotes,
inline code / bold / italic / links), so the site keeps no build dependencies.

Two conversions beyond plain markdown:
  · relative links to `.../index.md` become `.../index.html` in the HTML, so
    each format links to its own kind (links to raw /briefs/*.md stay as they are);
  · "as of <date>" becomes <span class="asof">, the visible half of the
    generate-or-date-every-number rule validate.js enforces.

Adding a page: write <section>/<page>/index.md, add it to PAGES, add it to NAV/FOOTER in
chrome.py if it belongs there, then run this and chrome.py. Sections: design, code, evidence,
explain, project; each section's index.md is its hub.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrome                                                    # noqa: E402

ROOT = chrome.ROOT

# (dir, title, description) in reading order. The first heading of each .md is the page's h1.
PAGES = [
    # the design
    ("design",              "The brief",
     "SHarness in one read: what it is, the moving parts and how they work together, one request end to end, what binds a process, the spectrum from a hello world to sgit, where it is now and what to decide."),
    ("design/why",          "Why: the last metre",
     "A vault key sealed while it travels is exposed the moment it arrives: on disk, on the command line and in the agent's transcript. The problem SHarness started from."),
    ("design/architecture", "Architecture",
     "SHarness components, the edges allowed between them, mutual TLS with a session CA whose key is destroyed after issuing, and the deployment topologies."),
    ("design/components",   "Components",
     "One section per sharness.<role>: launcher, kms, net, fs, bash, llm and policy. Each has one job, one uid, one policy and one certificate."),
    ("design/keys",         "Keys and the KMS",
     "The sealed handover end to end, the KMS protocol, sealing to one-time keys, binding a remote caller, and where a private key lives and for how long."),
    ("design/policies",     "Process Behaviour Policies",
     "The Agent Behaviour Policy model applied to a process: schema, intersection-composed layers, hashing and signing, the enforcement map, and learning a policy from traces."),
    ("design/agents",       "Agents and LLMs",
     "How an agent message flows (observed), where SHarness plugs in, sharness.llm, sharness.bash, the dual-LLM split, and Claude API compatibility."),
    ("design/process-tree", "Enforcing the process tree",
     "Making every process an agent starts go through sharness.bash: a Landlock exec allowlist, a server outside the domain, the side doors, and safe testing. Proof of concept not yet run."),
    ("design/surface",      "What a process can do",
     "The whole surface of a process, one row per interface: what bounds it in SHarness, whether that was measured, and what the bound does not cover. What is left is a virtual operating system for one process."),
    ("design/containment",  "Containment",
     "Can every process be constrained, memory included, and how far can hostile code inside be contained: the answer by threat class, with what is measured, what is designed, and where a microVM belongs."),
    ("design/spectrum",     "The spectrum",
     "Five profiles of one harness, from a hello world to sgit: what each runs, its threat, its policy, its components, its mode and its status; and the map of how sgit's next version stays compatible."),
    ("design/roadmap",      "Roadmap and open decisions",
     "The decisions still open, the refactor path in sgit, the end state, and the first tasks for the agents that will build SHarness."),
    # the code
    ("code",                "The code",
     "Where the code is: the sharness-ai package and its modules, the commands, the experiments, the examples, the flows through the code, the languages, and how to run it in a Claude session."),
    ("code/cli",            "The CLI",
     "The sharness-ai package: what exists, the first version as proposed (experiments today, components tomorrow), the v0 policy, naming, versioning and the release pipeline."),
    ("code/experiments",    "Mockups and experiments",
     "The ladder from browser mockups to runnable experiments to components: what each shows, where it runs, what was measured, and what Claude Code's own sandbox already gives."),
    ("code/flows",          "Flows through the code",
     "What happens, module by module, when sharness-ai run confines a command and when hello runs the acceptance test; and the flow the launcher will add."),
    ("code/examples",       "Examples",
     "Every runnable example: the policies, the commands, their output, the skill for a Claude session, and the sgit probe."),
    ("code/browser",        "Linux in the browser",
     "How much of the harness can run in a browser tab: a real kernel in a tab (v86) can run Landlock, seccomp, namespaces and cgroups; syscall-emulation runtimes cannot. The options, the recommended build, and what a browser can never show."),
    ("code/languages",      "Languages",
     "What each part of SHarness is written in and why: Python for the experiments and the launcher, a static binary for the bash client, the case for Rust in the KMS, JavaScript only in the browser."),
    # evidence and status
    ("evidence",            "Evidence",
     "Every measurement behind the SHarness design, with method, date and caveats, and the list of what has not been measured."),
    ("evidence/status",     "What exists today",
     "The honest column: what exists as running code and can be checked, and what is not here yet."),
    ("evidence/machines",   "hello on your machine",
     "every reported run of sharness-ai hello, with the kernel, the Landlock ABI and the result; how to report yours"),
    ("evidence/research",   "Research note",
     "The published design read in full on 24 Oct 2026: what holds up, what to improve, what this release did about it, and what is still open."),
    # the landscape
    ("landscape",           "The landscape",
     "Policies at the centre: SHarness as the reference implementation of Process Behaviour Policies, other products as integration points and translation targets, and the three questions to ask of any environment."),
    ("landscape/enforceability", "Enforceability",
     "Which rows of a policy can run where: the matrix of policy rows against enforcers (SHarness, bubblewrap, Docker, Claude Code's sandbox, Kubernetes, microVMs, ToolHive, OpenShell), with the barrier kind per cell."),
    ("landscape/integrations", "Integration points",
     "Product by product: what it stands in for in SHarness's terms, what a policy translates into on it, what SHarness adds, and what to keep."),
    ("landscape/ruflo",     "Ruflo and ruv.sgit",
     "rUv's stack (Ruflo, agentic-flow, RuVector, MetaHarness, RVM) in SHarness's terms; what ruv.sgit integrated (a mandate per agent compiled into Ruflo's policy engine, memory in sgit vaults); where the two halves meet, point by point; a swarm under the harness; what to do first."),
    ("landscape/market",    "Market and competitive analysis",
     "What exists in the market that does part of what SHarness is designed to do, as of 24 Oct 2026: sandboxes, guardrails, MCP gateways, LLM gateways, secrets and identity, enterprise platforms, standards; where SHarness sits and the threats to its thesis."),
    # explain
    ("explain",             "Explain",
     "The design told other ways: three storyboards drawn from data, and two browser mockups that compute what the design describes."),
    # project
    ("project",             "Project",
     "Who SHarness is by, where its sources are, and how this site is run: about, the source documents, engineering, comms, releases."),
    ("project/about",       "About and naming",
     "Who SHarness is by, the naming rules, the disambiguation from the Sharness shell test library, and the identifiers."),
    ("project/sources",     "The source documents",
     "The SHarness design pack, published verbatim: the brief for this site and the eight design documents it was built from."),
    ("project/adoption",    "Getting users: the review and the plan",
     "what was wrong for a user and what changed, who the users are, where to find them, how to tell whether it is working"),
    ("project/agents",       "The agents and their keys",
     "Who writes here besides Dinis Cruz: each agent's name, role, key on pki.sgit.ai and vaults (ids, never keys); how a secret reaches an agent and how a vault key reaches Dinis; what the agents need from him."),
    ("project/outreach",     "Outreach",
     "Finding the people SHarness is for: what there is to show, who it is for, where they are, what rUv's playbook teaches, a 30-day plan, the rules every post follows, and how the result is measured. A plan by sherpa@sharness, for Dinis Cruz's go."),
    ("project/telemetry",    "Telemetry",
     "Who reads this site: one anonymous event per page per session, encrypted in the browser to a key only the telemetry vault holds and written to a write-only lane; what is sent, what is never sent, what the counts are worth."),
]

ASOF = re.compile(r"\bas of (\d{1,2} [A-Z][a-z]{2} \d{4})")


def slug(text):
    s = re.sub(r"<[^>]+>", "", text).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "section"


def inline(text):
    """Code spans are swapped for placeholders first, so nothing inside them is touched,
    while bold and links can still wrap them (`**a `b` c**`, `[`x`](url)`)."""
    spans = []

    def stash(m):
        spans.append(f"<code>{html.escape(m.group(1), quote=False)}</code>")
        return f"\x00{len(spans) - 1}\x00"
    t = _inline_plain(re.sub(r"`([^`]+)`", stash, text))
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], t)


def _inline_plain(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{_href(m.group(2))}">{m.group(1)}</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])", r"<em>\1</em>", t)
    t = ASOF.sub(r'<span class="asof">as of \1</span>', t)
    return t


def _href(url):
    url = html.unescape(url)
    if not re.match(r"^(https?:|mailto:|#)", url):
        url = re.sub(r"(^|/)index\.md(#|$)", r"\1index.html\2", url)
    return html.escape(url)


def split_row(line):
    """Cells split on |, except an escaped \\| (a literal pipe, e.g. in a grep pattern)."""
    cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
    return [c.strip().replace("\\|", "|") for c in cells]


def md_to_html(md):
    lines, out, i = md.split("\n"), [], 0
    h1 = None
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):                                  # fenced code
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            out.append('<pre class="diagram">' + html.escape("\n".join(body), quote=False) + "</pre>")
            continue
        m = re.match(r"^(#{1,4}) (.+)$", line)
        if m:                                                        # heading
            level, text = len(m.group(1)), m.group(2).strip()
            anchor = re.search(r"\s*\{#([a-z0-9-]+)\}$", text)          # newsroom-style {#id}
            if anchor:
                text = text[:anchor.start()]
            if level == 1 and h1 is None:
                h1 = inline(text)
            else:
                hid = anchor.group(1) if anchor else slug(text)
                out.append(f'<h{level} id="{hid}">{inline(text)}</h{level}>')
            i += 1
            continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = split_row(line)                                  # table
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            trs = "\n".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="tablewrap"><table>\n<thead><tr>{th}</tr></thead>\n<tbody>\n{trs}\n</tbody>\n</table></div>')
            continue
        if line.startswith(">"):                                     # blockquote
            body = []
            while i < len(lines) and lines[i].startswith(">"):
                body.append(lines[i][1:].strip())
                i += 1
            out.append(f'<div class="note">{inline(" ".join(body))}</div>')
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.) ", line)
        if m:                                                        # list (one level)
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            items = []
            while i < len(lines) and lines[i].strip():
                m2 = re.match(r"^\s*(?:[-*]|\d+\.) (.*)$", lines[i])
                if m2:
                    items.append(m2.group(1))
                elif items:
                    items[-1] += " " + lines[i].strip()             # continuation line
                i += 1
            out.append(f"<{tag}>\n" + "\n".join(f"<li>{inline(t)}</li>" for t in items) + f"\n</{tag}>")
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", line)
        if m:                                                        # figure (+ caption line)
            alt, src = m.group(1), _href(m.group(2))
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            cap = ""
            if i < len(lines) and re.match(r"^\*[^*].*\*$", lines[i].strip()):
                cap = f"<figcaption>{inline(lines[i].strip()[1:-1])}</figcaption>"
                i += 1
            out.append(f'<figure class="lead"><img src="{src}" alt="{html.escape(alt)}">{cap}</figure>')
            continue
        if re.match(r"^-{3,}\s*$", line):                           # rule
            out.append("<hr>")
            i += 1
            continue
        body = []                                                    # paragraph
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4} |```|>|!\[|\s*\||\s*(?:[-*]|\d+\.) )", lines[i]):
            body.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(body))}</p>")
    return h1, "\n".join(out)


SECTIONS = {"design": "the design", "code": "the code", "evidence": "evidence", "landscape": "the landscape", "explain": "explain", "project": "project"}


def crumb(dir_, title):
    parts = dir_.split("/")
    if len(parts) == 1:
        return html.escape(title.lower())
    return f'<a href="../index.html">{SECTIONS.get(parts[0], parts[0])}</a> / {html.escape(title.lower())}'


def render(dir_, title, desc):
    rel = f"{dir_}/index.html"
    up = "../" * len(dir_.split("/"))
    md = (ROOT / dir_ / "index.md").read_text()
    h1, body = md_to_html(md)
    url = f"https://{chrome.HOST}/{rel}"
    full_title = f"{title} — SHarness"
    d = html.escape(desc)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="sharness.ai">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{d}">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="text/markdown" href="index.md" title="This page as markdown">
<link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>

{chrome.nav_html(rel, up)}

<main class="doc">
  <div class="crumb"><a href="{up}index.html">sharness.ai</a> / {crumb(dir_, title)} · <a href="index.md">this page as markdown</a></div>
  <h1>{h1 or html.escape(title)}</h1>
{body}
</main>

{chrome.footer_html(rel, up)}

</body>
</html>
'''


def main():
    check = "--check" in sys.argv
    stale = []
    for dir_, title, desc in PAGES:
        out = ROOT / dir_ / "index.html"
        text = render(dir_, title, desc)
        if out.exists() and out.read_text() == text:
            continue
        if check:
            stale.append(out.relative_to(ROOT).as_posix())
        else:
            out.write_text(text)
            print(f"  · {out.relative_to(ROOT).as_posix()}")
    if check and stale:
        print("gen_pages: stale HTML (run python3 tools/gen_pages.py and commit):", file=sys.stderr)
        for s in stale:
            print(f"  ✗ {s}", file=sys.stderr)
        sys.exit(1)
    print(f"gen_pages: {len(PAGES)} page(s) {'up to date' if check else 'generated'}")


if __name__ == "__main__":
    main()
