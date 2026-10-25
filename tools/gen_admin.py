#!/usr/bin/env python3
"""Generates /admin/: how the project is run, from the files under content/admin/.

Run from anywhere:  python3 tools/gen_admin.py           (write)
                    python3 tools/gen_admin.py --check   (CI: fail if anything is stale or malformed)

The sources, one file per thing, so two agents rarely touch the same lines:

  content/admin/board/<ID>.md         one row of the board (front matter + body); R = needs the editor, T = a task
  content/admin/members/<id>/ROLE.md  a member's role (front matter + body), with status.json and policy.json beside it
  content/admin/updates/<id>.md       one dated update (front matter + body)
  content/admin/status.json           the snapshot of every branch, written by tools/admin_status.py
  AGENTS.md                           the guidance every agent reads, at the root of the repository

From those this writes admin/index, admin/board, admin/members (and one page per member),
admin/updates (and one page per update), admin/guidance and admin/status, each with its
markdown twin, and project/comms.html as the same board at the address it always had. The
build is deterministic: the only date is the snapshot's own, stamped "as of" on every page so
the gate's generate-or-date rule is met by the file that carries the clock, not by the build.
Kept by the conductor (content/admin/members/conductor/ROLE.md).
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrome                                                    # noqa: E402
from gen_pages import md_to_html, inline                         # noqa: E402

ROOT   = chrome.ROOT
SRC    = ROOT / "content/admin"
HOST   = chrome.HOST
GH     = "https://github.com/SHarness-AI/SHarness-AI__Website/blob/dev"

ROW_STATUS = {"open", "in progress", "waiting", "needs review", "needs you", "decision", "decided", "done", "done for one process", "superseded"}
CLOSED     = {"done", "decided", "done for one process", "superseded"}
ROW_FIELDS = ("id", "kind", "title", "owner", "status", "opened")
UPD_FIELDS = ("id", "at", "kind", "title", "summary", "covers_from", "covers_to", "author")
MONTHS     = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

errors = []


def err(msg):
    errors.append(msg)


# ---------------------------------------------------------------- sources
def parse(path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        err(f"{path.relative_to(ROOT)}: no front matter")
        return {}, text
    meta = {}
    for line in m.group(1).split("\n"):
        k, _, v = line.partition(":")
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        meta[k.strip()] = v
    return meta, m.group(2).strip("\n")


def rows():
    out = []
    for p in sorted(SRC.glob("board/*.md"), key=lambda p: (p.stem[0], int(re.sub(r"\D", "", p.stem) or 0))):
        meta, body = parse(p)
        rel = p.relative_to(ROOT)
        for f in ROW_FIELDS:
            if not meta.get(f):
                err(f"{rel}: front matter has no {f}")
        if meta.get("id") != p.stem:
            err(f"{rel}: id {meta.get('id')} does not match the file name")
        if meta.get("kind") not in ("request", "task"):
            err(f"{rel}: kind must be request or task")
        if meta.get("kind") == "request" and not p.stem.startswith("R") or meta.get("kind") == "task" and not p.stem.startswith("T"):
            err(f"{rel}: a request is R<n>, a task T<n>")
        if meta.get("status") not in ROW_STATUS:
            err(f"{rel}: status '{meta.get('status')}' is not one of {sorted(ROW_STATUS)}")
        for d in ("opened", "closed"):
            if meta.get(d) and not re.match(r"^\d{4}-\d{2}-\d{2}$", meta[d]):
                err(f"{rel}: {d} is not YYYY-MM-DD")
        out.append((meta, body))
    return out


def members():
    out = []
    for d in sorted(p for p in SRC.glob("members/*") if p.is_dir()):
        role = d / "ROLE.md"
        if not role.exists():
            err(f"{d.relative_to(ROOT)}: no ROLE.md")
            continue
        meta, body = parse(role)
        if meta.get("id") != d.name:
            err(f"{role.relative_to(ROOT)}: id {meta.get('id')} does not match the folder")
        for f in ("name", "kind", "role", "status", "joined"):
            if not meta.get(f):
                err(f"{role.relative_to(ROOT)}: front matter has no {f}")
        status = json.loads((d / "status.json").read_text()) if (d / "status.json").exists() else {}
        policy = json.loads((d / "policy.json").read_text()) if (d / "policy.json").exists() else {}
        if status and status.get("member") != d.name:
            err(f"{d.relative_to(ROOT)}/status.json: member {status.get('member')} does not match the folder")
        out.append((meta, body, status, policy))
    return out


def updates():
    out = []
    for p in sorted(SRC.glob("updates/*.md"), reverse=True):
        meta, body = parse(p)
        rel = p.relative_to(ROOT)
        for f in UPD_FIELDS:
            if not meta.get(f):
                err(f"{rel}: front matter has no {f}")
        if meta.get("id") != p.stem:
            err(f"{rel}: id {meta.get('id')} does not match the file name")
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{4}Z$", p.stem):
            err(f"{rel}: the file name is YYYY-MM-DDTHHMMZ")
        if meta.get("kind") not in ("hourly", "daily", "flash"):
            err(f"{rel}: kind is hourly, daily or flash")
        out.append((meta, body))
    return out


def snapshot():
    p = SRC / "status.json"
    if not p.exists():
        err("content/admin/status.json is missing: run python3 tools/admin_status.py")
        return {"as_of": "2026-10-25T00:00Z", "repositories": []}
    return json.loads(p.read_text())


def asof(iso):
    y, mo, d = iso[:10].split("-")
    return f"as of {int(d)} {MONTHS[int(mo) - 1]} {y}"


def when(iso):
    """2026-10-25T23:30Z -> 25 Oct 2026, 23:30 UTC"""
    y, mo, d = iso[:10].split("-")
    t = iso[11:16] if len(iso) > 11 else ""
    return f"{int(d)} {MONTHS[int(mo) - 1]} {y}" + (f", {t} UTC" if t else "")


# ---------------------------------------------------------------- page shell
def shell(rel, title, desc, h1, body, crumb_tail, md_href="index.md"):
    up = "../" * (len(rel.split("/")) - 1)
    url = f"https://{HOST}/{rel}"
    full = f"{title} — SHarness"
    d = html.escape(desc)
    alt = f'<link rel="alternate" type="text/markdown" href="{md_href}" title="This page as markdown">\n' if md_href else ""
    twin = f' · <a href="{md_href}">this page as markdown</a>' if md_href else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(full)}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="sharness.ai">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{html.escape(full)}">
<meta property="og:description" content="{d}">
<meta name="twitter:card" content="summary">
{alt}<link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>

{chrome.nav_html(rel, up)}

<main class="doc">
  <div class="crumb"><a href="{up}index.html">sharness.ai</a> / {crumb_tail}{twin}</div>
  <h1>{h1}</h1>
{body}
</main>

{chrome.footer_html(rel, up)}

</body>
</html>
'''


def twin_header(title, desc, rel):
    return (f"# {title}\n\n> {desc}\n\n*Source: <https://{HOST}/{rel}> · generated by tools/gen_admin.py from "
            f"content/admin/, so the page and this file cannot drift. Every page on this site has a .md twin.*\n\n---\n\n")


def chip(status):
    cls = "t-done" if status in CLOSED else ("t-need" if status in ("needs review", "needs you", "decision") else "t-open")
    return f'<span class="tstat {cls}">{html.escape(status)}</span>'


def owner_link(owner, up_members):
    return f'<a href="{up_members}{owner}/index.html">{html.escape(owner)}</a>' if (SRC / "members" / owner).is_dir() else html.escape(owner)


# ---------------------------------------------------------------- the board
def board_table(items, up_members, rebase=lambda s: s):
    trs = []
    for meta, body in items:
        text = inline(rebase(" ".join(l.strip() for l in body.split("\n") if l.strip())))
        extra = (f" · shipped in {html.escape(meta['shipped'])}" if meta.get("shipped") else "")
        dates = f'<span class="dim small">opened {meta["opened"]}' + (f', closed {meta["closed"]}' if meta.get("closed") else "") + f"{extra}</span>"
        trs.append(f'      <tr id="{meta["id"].lower()}"><td><b>{meta["id"]}</b></td>'
                   f'<td><b>{inline(rebase(meta["title"]))}.</b> {text}<br>{dates}</td>'
                   f'<td>{owner_link(meta["owner"], up_members)}</td><td>{chip(meta["status"])}</td></tr>')
    return ('  <div class="tablewrap"><table>\n    <thead><tr><th>#</th><th>Item</th><th>Owner</th><th>Status</th></tr></thead>\n    <tbody>\n'
            + "\n".join(trs) + "\n    </tbody>\n  </table></div>\n")


def board_md_table(items):
    out = ["| # | Item | Owner | Status |", "|---|---|---|---|"]
    for meta, body in items:
        text = " ".join(l.strip() for l in body.split("\n") if l.strip()).replace("|", "\\|")
        out.append(f"| {meta['id']} | **{meta['title']}.** {text} (opened {meta['opened']}"
                   + (f", closed {meta['closed']}" if meta.get("closed") else "") + (f", shipped in {meta['shipped']}" if meta.get("shipped") else "")
                   + f") | {meta['owner']} | {meta['status']} |")
    return "\n".join(out)


def split_rows(all_rows):
    needs = [r for r in all_rows if r[0]["kind"] == "request" and r[0]["status"] not in CLOSED]
    tasks = [r for r in all_rows if r[0]["kind"] == "task" and r[0]["status"] not in CLOSED]
    done  = [r for r in all_rows if r[0]["status"] in CLOSED]
    return needs, tasks, done


BOARD_INTRO = ("Every piece of work on SHarness as one row, numbered so it can be referred to from any page, commit or "
               "conversation, and never renumbered. **R** is a request: it needs the editor (a decision, a key, a setting) and "
               "says what it blocks. **T** is a task: work a member has or anyone can pick up. One file per row under "
               "`content/admin/board/`; the [Sherpa](../members/sherpa/index.md) keeps the rows honest and scopes them into "
               "releases, the [conductor](../members/conductor/index.md) builds this page from them, and anyone opens a row "
               "by adding a file ([how](../guidance/index.md)).")


def gen_board(all_rows, snap, out):
    needs, tasks, done = split_rows(all_rows)
    date = asof(snap["as_of"])
    intro = BOARD_INTRO + f" {len(needs)} request(s) wait on the editor and {len(tasks)} task(s) are open, {date}."
    body = (f"<p class=\"lead\">{inline(intro)}</p>\n"
            f'<h2 id="needs-the-editor">Needs the editor</h2>\n' + board_table(needs, "../members/")
            + f'<h2 id="open-tasks">Open tasks</h2>\n' + board_table(tasks, "../members/")
            + f'<h2 id="done-and-decided">Done and decided</h2>\n' + board_table(done, "../members/"))
    title, desc = "The board", "Every request to the editor and every task on SHarness, numbered, with its owner and its status; one file per row."
    out["admin/board/index.html"] = shell("admin/board/index.html", title, desc, "The board: tasks and requests", body,
                                          '<a href="../index.html">admin</a> / the board')
    out["admin/board/index.md"] = (twin_header(title, desc, "admin/board/index.html") + intro + "\n\n## Needs the editor\n\n"
                                   + board_md_table(needs) + "\n\n## Open tasks\n\n" + board_md_table(tasks)
                                   + "\n\n## Done and decided\n\n" + board_md_table(done) + "\n")
    # The same board at the address it had since v0.1.0, so every link to project/comms.html#r7 still lands.
    rebase = lambda s: s.replace("](../../", "](../").replace("](../members/", "](../admin/members/")
    cbody = ('<p class="lead">The board, at the address it has had since the first release. Generated from the same rows as '
             '<a href="../admin/board/index.html">the board</a>; to change a row, edit its file under <code>content/admin/board/</code> '
             'and run <code>python3 tools/gen_admin.py</code>. <span class="asof">' + date + '</span></p>\n'
             + '<h2 id="needs-the-editor">Needs the editor</h2>\n' + board_table(needs, "../admin/members/", rebase)
             + '<h2 id="open-tasks">Open tasks</h2>\n' + board_table(tasks, "../admin/members/", rebase)
             + '<h2 id="done-and-decided">Done and decided</h2>\n' + board_table(done, "../admin/members/", rebase)
             + '<div class="pagenav"><a href="engineering.html">← Engineering</a><a href="releases.html">Release history →</a></div>')
    out["project/comms.html"] = shell("project/comms.html", "Comms: tasks & requests",
                                      "The open requests and tasks for sharness.ai, numbered so they can be referred to.",
                                      "Comms: tasks &amp; requests", cbody, '<a href="engineering.html">admin</a> / comms', md_href=None)


# ---------------------------------------------------------------- the members
def state_chip(state):
    cls = {"done": "t-done", "working": "t-open", "waiting": "t-need", "blocked": "t-need", "review": "t-open", "deciding": "t-open"}.get(state, "t-open")
    return f'<span class="tstat {cls}">{html.escape(state or "unknown")}</span>'


def member_rows_md(ms, up):
    out = ["| Member | Role | State | Last did | Waiting for |", "|---|---|---|---|---|"]
    for meta, _, st, _ in ms:
        out.append(f"| [{meta['name']}]({up}{meta['id']}/index.md) | {meta['role']} | {st.get('state', '')} | "
                   f"{st.get('last_did', '').replace('|', '/')} | {st.get('waiting_for', '').replace('|', '/')} |")
    return "\n".join(out)


def member_rows_html(ms, up):
    trs = "\n".join(
        f'      <tr><td><a href="{up}{m["id"]}/index.html"><b>{html.escape(m["name"])}</b></a><br><span class="dim small">{html.escape(m["kind"])}, joined {m["joined"]}</span></td>'
        f'<td>{inline(m["role"])}</td><td>{state_chip(st.get("state", ""))}</td><td>{inline(st.get("last_did", ""))}</td><td>{inline(st.get("waiting_for", ""))}</td></tr>'
        for m, _, st, _ in ms)
    return ('  <div class="tablewrap"><table>\n    <thead><tr><th>Member</th><th>Role</th><th>State</th><th>Last did</th><th>Waiting for</th></tr></thead>\n'
            f'    <tbody>\n{trs}\n    </tbody>\n  </table></div>\n')


MEMBERS_INTRO = ("One person and the agents, each with a folder under `content/admin/members/<id>/`: a `ROLE.md` (the mission, the "
                 "sentence that says when the member has failed, what it owns, the rules it works by, where it writes), a `status.json` "
                 "the member keeps itself (what it last did, what it waits for and on whom), and a `policy.json`, its behaviour policy in "
                 "the shape [riskmandate.ai](https://riskmandate.ai/abp.html) gives, agreed by the editor or marked a draft. Keys and vaults "
                 "are on [the agents and their keys](../../project/agents/index.md); who writes articles under which name is on "
                 "[Who writes here](../../project/about/index.md#who-writes-here). A new member joins by adding its folder "
                 "([how](../guidance/index.md)).")


def gen_members(ms, snap, out):
    date = asof(snap["as_of"])
    intro = MEMBERS_INTRO + f" {len(ms)} member(s), {date}."
    title, desc = "The members", "Who works on SHarness, person and agents: each one's role, what it owns, the rules it works by, where it is and what it waits for."
    out["admin/members/index.html"] = shell("admin/members/index.html", title, desc, "The members: who does what", f"<p class=\"lead\">{inline(intro)}</p>\n" + member_rows_html(ms, ""),
                                            '<a href="../index.html">admin</a> / the members')
    out["admin/members/index.md"] = twin_header(title, desc, "admin/members/index.html") + intro + "\n\n" + member_rows_md(ms, "") + "\n"
    for meta, body, st, pol in ms:
        h1, body_html = md_to_html(body)
        facts = (f'<p class="byline">{html.escape(meta["kind"])} · {inline(meta["role"])} · {html.escape(meta["status"])} · joined {meta["joined"]}'
                 + (f' · alias <code>{html.escape(meta["alias"])}</code>' if meta.get("alias") else "")
                 + (f' · session <code>{html.escape(meta["session"])}</code>' if meta.get("session") else "")
                 + f' · <a href="{GH}/content/admin/members/{meta["id"]}/ROLE.md">ROLE.md</a>, <a href="{GH}/content/admin/members/{meta["id"]}/policy.json">policy.json</a>, '
                 f'<a href="{GH}/content/admin/members/{meta["id"]}/status.json">status.json</a></p>\n')
        status_html = ""
        status_md = ""
        if st:
            status_html = (f'<h2 id="where-it-is">Where it is</h2>\n<div class="tablewrap"><table><tbody>'
                           f'<tr><th>State</th><td>{state_chip(st.get("state", ""))} <span class="asof">{asof(st.get("as_of", snap["as_of"]))}</span></td></tr>'
                           f'<tr><th>Last did</th><td>{inline(st.get("last_did", ""))}</td></tr>'
                           f'<tr><th>Waiting for</th><td>{inline(st.get("waiting_for", ""))}</td></tr>'
                           + (f'<tr><th>Branch</th><td><code>{html.escape(st["branch"])}</code></td></tr>' if st.get("branch") else "")
                           + f'<tr><th>Next</th><td>{inline(st.get("next", ""))}</td></tr></tbody></table></div>\n')
            status_md = ("\n\n## Where it is\n\n| | |\n|---|---|\n" + f"| State | {st.get('state', '')} ({asof(st.get('as_of', snap['as_of']))}) |\n"
                         f"| Last did | {st.get('last_did', '')} |\n| Waiting for | {st.get('waiting_for', '')} |\n"
                         + (f"| Branch | `{st['branch']}` |\n" if st.get("branch") else "") + f"| Next | {st.get('next', '')} |")
        pol_html, pol_md = "", ""
        if pol:
            if pol.get("mandate"):
                items = "".join(f"<li>{inline(x)}</li>" for x in pol["mandate"])
                bars = "".join(f"<li>{inline(b['rule'])} <span class=\"dim small\">({html.escape(b['kind'])})</span></li>" for b in pol.get("barriers", []))
                pol_html = (f'<h2 id="the-policy">The policy</h2>\n<p>{inline(pol.get("status", ""))}. {inline(pol.get("note", ""))}</p>'
                            f'<h3>Mandate</h3><ul>{items}</ul><h3>Reach</h3><p>{inline(json.dumps(pol["reach"].get("repositories", {})))}; writes {html.escape(", ".join(pol["reach"].get("writes", [])))}.</p>'
                            f'<h3>The delta</h3><p>{inline(pol.get("delta", ""))}</p><h3>Barriers</h3><ul>{bars}</ul>\n')
                pol_md = ("\n\n## The policy\n\n" + f"{pol.get('status', '')}. {pol.get('note', '')}\n\n**Mandate**\n\n" + "\n".join(f"- {x}" for x in pol["mandate"])
                          + f"\n\n**Reach**: {json.dumps(pol['reach'].get('repositories', {}))}; writes {', '.join(pol['reach'].get('writes', []))}.\n\n**The delta**: {pol.get('delta', '')}\n\n**Barriers**\n\n"
                          + "\n".join(f"- {b['rule']} ({b['kind']})" for b in pol.get("barriers", [])))
            else:
                pol_html = f'<h2 id="the-policy">The policy</h2>\n<p>{inline(pol.get("status", ""))}</p>\n'
                pol_md = f"\n\n## The policy\n\n{pol.get('status', '')}"
        rel = f"admin/members/{meta['id']}/index.html"
        page_title = f"{meta['name']}: {meta['role']}"
        out[rel] = shell(rel, meta["name"], f"{meta['name']} on the SHarness team: {meta['role']}.", h1 or html.escape(page_title),
                         facts + body_html + "\n" + status_html + pol_html, f'<a href="../../index.html">admin</a> / <a href="../index.html">members</a> / {html.escape(meta["id"])}')
        out[f"admin/members/{meta['id']}/index.md"] = (twin_header(page_title, f"{meta['name']} on the SHarness team: {meta['role']}.", rel)
                                                       + f"{meta['kind']} · {meta['status']} · joined {meta['joined']}\n\n" + body + status_md + pol_md + "\n")


# ---------------------------------------------------------------- the updates
UPDATES_INTRO = ("What changed on the site, in the CLI and across the team, dated, newest first: hourly while things move, daily at the "
                 "end of a day, and at once when something changes what a reader should do. Written for the editor first, who works with "
                 "several agents at once and needs to know in a few minutes what moved and what needs him; for anyone following the work "
                 "second. Every update is drafted from the repositories' own record (commits, tags, branches, the board), never from "
                 "memory, and is kept as written: the next one corrects it. Held by the [conductor](../members/conductor/index.md); the "
                 "shape follows the PHP story site's [how an update is written](https://php.oct.2026.newsroom.sgit.ai/updates/readme/index.html).")


def gen_updates(ups, snap, out):
    date = asof(snap["as_of"])
    title, desc = "Updates", "What is happening on SHarness: dated briefings on what moved on the site, in the CLI and across the team, and what waits on the editor."
    cards = "\n".join(
        f'<h3 id="{m["id"].lower()}"><span class="tstat t-open">{html.escape(m["kind"])}</span> {when(m["at"])} · <a href="{m["id"]}/index.html">{html.escape(m["title"])}</a></h3>\n<p>{inline(m["summary"])}</p>'
        for m, _ in ups)
    intro = UPDATES_INTRO + f" {len(ups)} update(s), {date}."
    out["admin/updates/index.html"] = shell("admin/updates/index.html", title, desc, "Updates: what is happening", f"<p class=\"lead\">{inline(intro)}</p>\n{cards}\n",
                                            '<a href="../index.html">admin</a> / updates')
    out["admin/updates/index.md"] = (twin_header(title, desc, "admin/updates/index.html") + intro + "\n\n"
                                     + "\n".join(f"- **{m['kind']} · {when(m['at'])}** · [{m['title']}]({m['id']}/index.md): {m['summary']}" for m, _ in ups) + "\n")
    for m, body in ups:
        _, body_html = md_to_html(body)
        by = (f'<p class="byline">{html.escape(m["kind"])} update · <time datetime="{m["at"][:10]}">{when(m["at"])}</time> · covers {m["covers_from"]} to {m["covers_to"]} · '
              f'by <a href="../../members/{html.escape(m["author"])}/index.html">{html.escape(m["author"])}</a></p>\n<p class="summary">{inline(m["summary"])}</p>\n')
        rel = f"admin/updates/{m['id']}/index.html"
        out[rel] = shell(rel, m["title"], m["summary"], html.escape(m["title"]), by + body_html, f'<a href="../../index.html">admin</a> / <a href="../index.html">updates</a> / {m["id"]}')
        out[f"admin/updates/{m['id']}/index.md"] = (twin_header(m["title"], m["summary"], rel)
                                                    + f"{m['kind']} update · {when(m['at'])} · covers {m['covers_from']} to {m['covers_to']} · by {m['author']}\n\n{body}\n")


# ---------------------------------------------------------------- guidance and status
def gen_guidance(snap, out):
    text = (ROOT / "AGENTS.md").read_text()
    h1, body_html = md_to_html(text)
    title, desc = "Guidance for agents", "AGENTS.md: how to work on SHarness, for every agent and every person, on both repositories; the status words, the branches and releases, the rules, how to join."
    note = f'<p class="byline">The source is <a href="{GH}/AGENTS.md"><code>AGENTS.md</code></a> at the root of the website repository; the CLI repository carries a pointer to it. <span class="asof">{asof(snap["as_of"])}</span></p>\n'
    out["admin/guidance/index.html"] = shell("admin/guidance/index.html", title, desc, h1 or title, note + body_html, '<a href="../index.html">admin</a> / guidance')
    out["admin/guidance/index.md"] = twin_header(title, desc, "admin/guidance/index.html") + text.split("\n", 1)[1].lstrip("\n") + "\n"


def gen_status(ms, snap, out):
    title, desc = "Status", "Where every branch of both repositories is and where every member is: a snapshot by the conductor, from git, never from a session."
    parts_html, parts_md = [], []
    for r in snap.get("repositories", []):
        if not r.get("present"):
            parts_html.append(f'<h2>{html.escape(r["name"])}</h2><p>{html.escape(r.get("note", ""))}</p>')
            parts_md.append(f"## {r['name']}\n\n{r.get('note', '')}")
            continue
        trs = "\n".join(
            f'      <tr><td><code>{html.escape(b["branch"])}</code></td><td><code>{b["head"]}</code> · {html.escape(b["date"][:16].replace("T", " "))}</td>'
            f'<td>{html.escape(b["subject"])}' + (f' <span class="dim small">(Agent: {html.escape(b["agent"])})</span>' if b.get("agent") else "")
            + f'</td><td>{b["ahead_of_dev"]} ahead, {b["behind_dev"]} behind</td></tr>' for b in r["branches"])
        waiting = [b for b in r["branches"] if b["ahead_of_dev"] > 0 and b["branch"] != "main"]
        parts_html.append(f'<h2 id="{html.escape(r["name"].lower())}"><a href="{r["url"]}">{html.escape(r["name"])}</a></h2>'
                          f'<p>Latest tag <code>{html.escape(str(r.get("latest_tag")))}</code>; {len(waiting)} branch(es) carry commits not yet on <code>dev</code>.</p>'
                          '<div class="tablewrap"><table>\n    <thead><tr><th>Branch</th><th>Head</th><th>Last commit</th><th>Against dev</th></tr></thead>\n'
                          f'    <tbody>\n{trs}\n    </tbody></table></div>')
        parts_md.append(f"## {r['name']}\n\nLatest tag `{r.get('latest_tag')}`; {len(waiting)} branch(es) carry commits not yet on `dev`.\n\n| Branch | Head | Last commit | Against dev |\n|---|---|---|---|\n"
                        + "\n".join(f"| `{b['branch']}` | `{b['head']}` · {b['date'][:16].replace('T', ' ')} | {b['subject'].replace('|', '/')}" + (f" (Agent: {b['agent']})" if b.get("agent") else "")
                                    + f" | {b['ahead_of_dev']} ahead, {b['behind_dev']} behind |" for b in r["branches"]))
    intro = (f"A snapshot taken by the conductor with `python3 tools/admin_status.py`, {asof(snap['as_of'])} ({html.escape(snap['as_of'])}): every branch of both "
             "repositories, its head, its last commit and how far it is from `dev`, read from git, never from a session; then every member's own "
             "`status.json`. A branch ahead of `dev` is work nobody has released yet; a session is only visible here once it has pushed.")
    body = f"<p class=\"lead\">{inline(intro)}</p>\n" + "\n".join(parts_html) + '\n<h2 id="the-members">The members</h2>\n' + member_rows_html(ms, "../members/")
    out["admin/status/index.html"] = shell("admin/status/index.html", title, desc, "Status: where every branch and member is", body, '<a href="../index.html">admin</a> / status')
    out["admin/status/index.md"] = twin_header(title, desc, "admin/status/index.html") + intro + "\n\n" + "\n\n".join(parts_md) + "\n\n## The members\n\n" + member_rows_md(ms, "../members/") + "\n"


# ---------------------------------------------------------------- the hub
HUB = """SHarness is built in the open by one person and a few agents, and this section is where that is run: who does what, what is open and whose it is, what moved, and what only the editor can decide. Everything here is public and CC BY 4.0, including the mistakes; the journey is part of the story, and anyone can read how the work is run and join it ([how](guidance/index.md)). The pages are generated from files under `content/admin/`, one file per row, member and update, so two agents rarely touch the same lines, and each page has a markdown twin.

## How work moves

1. **A request from the editor**, in an agent's session, or a brief published in full under [the source documents](../project/sources/index.md).
2. **A row on [the board](board/index.md)**: `R<n>` when it needs the editor, `T<n>` when a member can do it; one owner, one status, never renumbered.
3. **A branch**, pushed early and often; then **a release to `dev`** by the member that did the work, with the version in the commit subject and a sentence in [the release history](../project/releases.html). CI validates, tags and deploys.
4. **An update** on [Updates](updates/index.md) when something moved: what changed, what waits on whom, by number.
5. **A debrief** at the end of every session in the member's own `status.json`, read on [Status](status/index.md).

## The pages

- [The board](board/index.md): every request and task, with owner and status.
- [The members](members/index.md): one person and the agents, each with a role, a policy and a status of its own.
- [Updates](updates/index.md): what is happening, dated, newest first.
- [Status](status/index.md): where every branch of both repositories is, and every member.
- [Guidance for agents](guidance/index.md): `AGENTS.md`, the rules every agent works by.
- Kept elsewhere in the project section: [engineering](../project/engineering.html) (how the site is built and released), [the agents and their keys](../project/agents/index.md) (keys on pki.sgit.ai, the vault register), [telemetry](../project/telemetry/index.md), [outreach](../project/outreach/index.md) and [getting users](../project/adoption/index.md), [the release history](../project/releases.html).

## Where this comes from

The way the sgit.ai network runs its sites, read on 25 October 2026 and taken as far as a project this size needs: the newsroom's [six roles and their behaviour policies](https://newsroom.sgit.ai/newsroom/index.html), the PHP story site's [team](https://php.oct.2026.newsroom.sgit.ai/team/index.html), [guidance for agents](https://php.oct.2026.newsroom.sgit.ai/admin/agents/index.html) and [updates](https://php.oct.2026.newsroom.sgit.ai/updates/index.html), sgit.ai's [team section](https://sgit.ai/team/index.html) and its page on [every repository](https://sgit.ai/docs/guidance/repositories.html), [coding.sgit.ai](https://coding.sgit.ai/) for the code and [nfrs.sgit.ai](https://nfrs.sgit.ai/) for the requirements that are not features. What is not here yet: a comms vault and a contact file for the conductor (R12), a reality file and a corrections file as such (T12), the `review/` folder.
"""


def gen_hub(all_rows, ms, ups, snap, out):
    needs, tasks, _ = split_rows(all_rows)
    date = asof(snap["as_of"])
    head = (f"**{date}:** {len(ms)} members, {len(needs)} request(s) waiting on the editor, {len(tasks)} open task(s), "
            f"{len(ups)} update(s); the latest update is [{ups[0][0]['title']}](updates/{ups[0][0]['id']}/index.md)." if ups else f"**{date}.**")
    md = head + "\n\n" + HUB
    _, body_html = md_to_html(md)
    title, desc = "Admin: how the project is run", "How SHarness is run in the open: the board, the members and their roles, the updates, the status of every branch, and the guidance every agent works by."
    out["admin/index.html"] = shell("admin/index.html", title, desc, "Admin: how the project is run", body_html + "\n" + member_rows_html(ms, "members/"), "admin")
    out["admin/index.md"] = twin_header(title, desc, "admin/index.html") + md + "\n" + member_rows_md(ms, "members/") + "\n"


# ---------------------------------------------------------------- main
def build():
    out = {}
    all_rows, ms, ups, snap = rows(), members(), updates(), snapshot()
    owners = {m[0]["id"] for m in ms} | {"anyone"}
    for meta, _ in all_rows:
        if meta.get("owner") not in owners:
            err(f"content/admin/board/{meta.get('id')}.md: owner '{meta.get('owner')}' has no folder under content/admin/members/")
    for meta, _ in ups:
        if meta.get("author") not in owners:
            err(f"content/admin/updates/{meta.get('id')}.md: author '{meta.get('author')}' has no folder under content/admin/members/")
    gen_board(all_rows, snap, out)
    gen_members(ms, snap, out)
    gen_updates(ups, snap, out)
    gen_guidance(snap, out)
    gen_status(ms, snap, out)
    gen_hub(all_rows, ms, ups, snap, out)
    return out


def main():
    check = "--check" in sys.argv
    out = build()
    if errors:
        print("gen_admin: the sources are malformed:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)
    stale = []
    for rel, text in out.items():
        p = ROOT / rel
        if p.exists() and p.read_text() == text:
            continue
        if check:
            stale.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
            print(f"  · {rel}")
    if check and stale:
        print("gen_admin: stale output (run python3 tools/gen_admin.py and commit):", file=sys.stderr)
        for s in stale:
            print(f"  ✗ {s}", file=sys.stderr)
        sys.exit(1)
    print(f"gen_admin: {len(out)} file(s) {'up to date' if check else 'generated'}")


if __name__ == "__main__":
    main()
