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
        if (d / "card.json").exists():
            card = json.loads((d / "card.json").read_text())
            if card.get("member") != d.name:
                err(f"{d.relative_to(ROOT)}/card.json: member {card.get('member')} does not match the folder")
            if card.get("status") not in ("proposed", "active", "paused", "ended"):
                err(f"{d.relative_to(ROOT)}/card.json: status is proposed, active, paused or ended")
            for w in card.get("wakes", []):
                if not re.match(r"^\d\d:\d\d$", w):
                    err(f"{d.relative_to(ROOT)}/card.json: wake '{w}' is not HH:MM")
                elif card.get("status") == "active" and (int(w[:2]) >= 22 or int(w[:2]) < 7):
                    err(f"{d.relative_to(ROOT)}/card.json: an active wake at {w} is in the quiet hours")
            for f in ("objective", "cron", "session", "repositories", "each_wake", "start_prompt", "wake_prompt"):
                if not card.get(f):
                    err(f"{d.relative_to(ROOT)}/card.json: no {f}")
            meta["_card"] = card
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


def runs_of():
    out = {}
    for p in sorted(SRC.glob("runs/*/*.json")):
        r = json.loads(p.read_text())
        rel = p.relative_to(ROOT)
        if r.get("member") != p.parent.name:
            err(f"{rel}: member {r.get('member')} does not match the folder")
        if r.get("outcome") not in ("ok", "idle", "partial", "failed"):
            err(f"{rel}: outcome is ok, idle, partial or failed")
        for f in ("started", "finished", "summary"):
            if not r.get(f):
                err(f"{rel}: no {f}")
        out.setdefault(p.parent.name, []).append(r)
    for v in out.values():
        v.sort(key=lambda r: r["started"], reverse=True)
    return out


BRIEF_FIELDS = ("title", "date", "by", "for", "status")


def briefs():
    out = []
    for p in sorted(SRC.glob("briefs/*.md"), reverse=True):
        meta, body = parse(p)
        rel = p.relative_to(ROOT)
        for f in BRIEF_FIELDS:
            if not meta.get(f):
                err(f"{rel}: front matter has no {f}")
        if not re.match(r"^\d{4}-\d{2}-\d{2}__brief__[a-z0-9-]+$", p.stem):
            err(f"{rel}: the file name is YYYY-MM-DD__brief__<slug>")
        if meta.get("status") not in ("proposed", "accepted", "built", "superseded"):
            err(f"{rel}: status is proposed, accepted, built or superseded")
        meta["slug"] = p.stem
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
    # rows are written relative to admin/board/; comms.html is one level up, under project/
    rebase = lambda s: s.replace("](../../", "\x00").replace("](../", "](../admin/").replace("\x00", "](../")
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
        card = meta.get("_card")
        card_html, card_md = "", ""
        if card:
            repos = ", ".join(card["repositories"].get("push", []))
            steps_html = "".join(f"<li>{inline(s)}</li>" for s in card.get("each_wake", []))
            lst = lambda k: "".join(f"<li>{inline(x)}</li>" for x in card.get(k, []))
            card_html = (f'<h2 id="start-here">Start here, on any Claude account</h2>'
                         f'<p>To take this role over in a new session, on this account or another: attach <code>{html.escape(repos)}</code> with push access; name the session <code>{html.escape(card["session"])}</code>; paste the start prompt below. '
                         f'Nothing on this page is a secret; a key, if the role needs one, is handed sealed by the editor (<a href="https://pki.sgit.ai/handover.md">the handover</a>). Then, with the editor\'s go, create the scheduled task from the cron and the wake prompt below, firing into that same session.</p>'
                         f'<h3>The start prompt</h3><pre class="diagram">{html.escape(card["start_prompt"])}</pre>'
                         f'<h2 id="the-schedule">The schedule</h2><p>{chip(card["status"])} {inline(card.get("status_note", ""))}</p>'
                         f'<div class="tablewrap"><table><tbody><tr><th>Objective</th><td>{inline(card["objective"])}</td></tr>'
                         f'<tr><th>Wakes</th><td>{html.escape(", ".join(card["wakes"]))} {html.escape(card["timezone"])}, <code>{html.escape(card["cron"])}</code>; {len(card["wakes"])} a day. Quiet hours: {html.escape(card.get("quiet_hours", ""))}</td></tr>'
                         f'<tr><th>Model</th><td>{inline(card["model"])}</td></tr><tr><th>Brief</th><td><code>{html.escape(card.get("brief", ""))}</code></td></tr>'
                         f'<tr><th>Scheduled task</th><td>name <code>{html.escape(card["scheduled_task"]["name"])}</code>; cron <code>{html.escape(card["scheduled_task"]["cron_expression"])}</code>; session: {html.escape(card["scheduled_task"]["session"])}; prompt: {html.escape(card["scheduled_task"]["prompt"])}</td></tr></tbody></table></div>'
                         f'<h3>Each wake</h3><ol>{steps_html}</ol><h3>Reads</h3><ul>{lst("reads")}</ul><h3>Writes</h3><ul>{lst("writes")}</ul><h3>Never</h3><ul>{lst("never")}</ul>'
                         f'<h3>The wake prompt, word for word</h3><pre class="diagram">{html.escape(card["wake_prompt"])}</pre>'
                         f'<p class="small dim">The card is <a href="{GH}/content/admin/members/{meta["id"]}/card.json">card.json</a>, kept by {html.escape(card.get("kept_by", meta["id"]))}, updated {html.escape(card.get("updated", ""))}; the protocol every wake follows is <a href="../../guidance/index.html">AGENTS.md</a> and <a href="{GH}/WAKE.md">WAKE.md</a>.</p>')
            card_md = ("\n\n## Start here, on any Claude account\n\n" + f"Attach `{repos}` with push access; name the session `{card['session']}`; paste the start prompt; then, with the editor's go, create the scheduled task from the cron and the wake prompt. Nothing here is a secret.\n\n"
                       f"**The start prompt**\n\n```\n{card['start_prompt']}\n```\n\n## The schedule\n\n{card['status']}: {card.get('status_note', '')}\n\n"
                       f"- Objective: {card['objective']}\n- Wakes: {', '.join(card['wakes'])} {card['timezone']}, `{card['cron']}`; quiet hours {card.get('quiet_hours', '')}\n- Model: {card['model']}\n- Brief: `{card.get('brief', '')}`\n- Scheduled task: name `{card['scheduled_task']['name']}`, cron `{card['scheduled_task']['cron_expression']}`, {card['scheduled_task']['session']}, prompt: {card['scheduled_task']['prompt']}\n\n"
                       "**Each wake**\n\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(card.get("each_wake", []), 1))
                       + "\n\n**Reads**: " + "; ".join(card.get("reads", [])) + "\n\n**Writes**: " + "; ".join(card.get("writes", [])) + "\n\n**Never**: " + "; ".join(card.get("never", []))
                       + f"\n\n**The wake prompt, word for word**\n\n```\n{card['wake_prompt']}\n```")
        rr = RUNS.get(meta["id"], [])
        runs_html = ('<h2 id="runs">Runs</h2>' + runs_table(rr, "../../runs/index.html")) if rr else ""
        runs_md = ("\n\n## Runs\n\n" + runs_md_table(rr)) if rr else ""
        rel = f"admin/members/{meta['id']}/index.html"
        page_title = f"{meta['name']}: {meta['role']}"
        out[rel] = shell(rel, meta["name"], f"{meta['name']} on the SHarness team: {meta['role']}.", h1 or html.escape(page_title),
                         facts + body_html + "\n" + status_html + card_html + runs_html + pol_html, f'<a href="../../index.html">admin</a> / <a href="../index.html">members</a> / {html.escape(meta["id"])}')
        out[f"admin/members/{meta['id']}/index.md"] = (twin_header(page_title, f"{meta['name']} on the SHarness team: {meta['role']}.", rel)
                                                       + f"{meta['kind']} · {meta['status']} · joined {meta['joined']}\n\n" + body + status_md + card_md + runs_md + pol_md + "\n")


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


# ---------------------------------------------------------------- runs, schedule, briefs
RUNS = {}


def runs_table(rr, up_runs="index.html"):
    trs = "\n".join(
        f'      <tr><td><span class="dim small">{html.escape(r["started"])}</span></td><td>{chip({"ok": "done", "idle": "open", "partial": "waiting", "failed": "needs you"}[r["outcome"]]).replace(">done<", ">ok<").replace(">open<", ">idle<").replace(">waiting<", ">partial<").replace(">needs you<", ">failed<")}</td>'
        f'<td>{inline(r["summary"])}' + (f' <span class="dim small">released {html.escape(r["released"])}</span>' if r.get("released") else "") + "</td></tr>" for r in rr)
    return ('  <div class="tablewrap"><table>\n    <thead><tr><th>Started (UTC)</th><th>Outcome</th><th>Summary</th></tr></thead>\n'
            f'    <tbody>\n{trs}\n    </tbody>\n  </table></div>\n')


def runs_md_table(rr):
    return "| Started (UTC) | Outcome | Summary |\n|---|---|---|\n" + "\n".join(
        f"| {r['started']} | {r['outcome']} | {r['summary'].replace('|', '/')}" + (f" (released {r['released']})" if r.get("released") else "") + " |" for r in rr)


SCHEDULE_INTRO = ("Every member that runs on its own keeps one card, `content/admin/members/<id>/card.json`: its objective, when it wakes "
                  "(London time), the model, the session, the repositories to attach, the steps of each wake, what it reads, writes and never does, "
                  "and two prompts word for word, the start prompt for a new session on any Claude account and the wake prompt for the scheduled task. "
                  "A card is `proposed` until the editor's go creates the task; every wake leaves a run record, so a missing record is a missed wake. "
                  "The protocol every wake follows is [WAKE.md](" + GH + "/WAKE.md); the brief is [schedules, cards and start pages](../briefs/2026-10-26__brief__schedules-cards-and-start-pages/index.md). "
                  "Nothing here is a secret, and nothing here creates a schedule: the editor does, per card, from the member's page.")


def gen_schedule(ms, snap, out):
    date = asof(snap["as_of"])
    cards = [(m, m[0]["_card"]) for m in ms if m[0].get("_card")]
    active = sum(1 for _, c in cards if c["status"] == "active")
    wakes = sum(len(c["wakes"]) for _, c in cards)
    intro = SCHEDULE_INTRO + f" {len(cards)} card(s), {active} active, {wakes} wake(s) a day, {date}."
    hours = list(range(24))
    head = "".join(f'<th class="{"q" if h >= 22 or h < 7 else ""}">{h:02d}</th>' for h in hours)
    rows = []
    for m, c in cards:
        cells = []
        for h in hours:
            marks = [w for w in c["wakes"] if int(w[:2]) == h]
            mark = ("&#9679;" if c["status"] == "active" else "&#9675;") if marks else ""
            cells.append(f'<td class="{"q" if h >= 22 or h < 7 else ""}" title="{html.escape(", ".join(marks))}">{mark}</td>')
        rows.append(f'<tr><td><a href="../members/{m[0]["id"]}/index.html">{html.escape(m[0]["id"])}</a></td>{"".join(cells)}</tr>')
    day = ('<div class="tablewrap"><table class="day"><thead><tr><th>London</th>' + head + '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
           '<p class="small dim">Filled: active; hollow: proposed or paused. Shaded: the quiet hours, 22:00 to 07:00 London. Hover a mark for its minute.</p>')
    trs = "\n".join(
        f'      <tr><td><a href="../members/{m[0]["id"]}/index.html"><b>{html.escape(m[0]["id"])}</b></a><br><span class="dim small">{html.escape(c["session"])}</span></td>'
        f'<td>{inline(c["objective"])}</td><td>{chip(c["status"])}</td><td>{html.escape(", ".join(c["wakes"]))}<br><code class="small">{html.escape(c["cron"])}</code></td>'
        f'<td>{inline(c["model"])}</td><td>{(html.escape(RUNS[m[0]["id"]][0]["started"]) + " " + html.escape(RUNS[m[0]["id"]][0]["outcome"])) if RUNS.get(m[0]["id"]) else "none yet"}</td></tr>' for m, c in cards)
    table = ('  <div class="tablewrap"><table>\n    <thead><tr><th>Member</th><th>Objective</th><th>Status</th><th>Wakes (London)</th><th>Model</th><th>Last run</th></tr></thead>\n'
             f'    <tbody>\n{trs}\n    </tbody>\n  </table></div>\n')
    setup = ('<h2 id="on-any-account">Setting a member up on any Claude account</h2><ol>'
             '<li>Open the member\'s page and read its card: the repositories, the session name, the start prompt, the cron, the wake prompt.</li>'
             '<li>On the account, start a session with those repositories attached (push access) and name it as the card says.</li>'
             '<li>Paste the start prompt. The session reads the guidance, its page and the board, and replies with its role, what it may and must not do, where it writes, and what waits on it.</li>'
             '<li>With the editor\'s go, create one scheduled task on that account: the card\'s name and cron, firing into that session, with the wake prompt word for word. The session then makes the card <code>active</code> in its next release and records the task\'s id in its status.</li>'
             '<li>A key the role needs is handed sealed to the session\'s key, never pasted: <a href="https://pki.sgit.ai/handover.md">the handover</a>.</li></ol>')
    title, desc = "Schedule", "Every member that runs on its own: its card, its wakes on one day, its prompts; how to set a member up on any Claude account."
    out["admin/schedule/index.html"] = shell("admin/schedule/index.html", title, desc, "Schedule: every member that runs on its own", f"<p class=\"lead\">{inline(intro)}</p>\n<h2 id=\"one-day\">One day, every wake</h2>\n{day}\n<h2 id=\"the-cards\">The cards</h2>\n{table}{setup}",
                                             '<a href="../index.html">admin</a> / schedule')
    out["admin/schedule/index.md"] = (twin_header(title, desc, "admin/schedule/index.html") + intro + "\n\n## The cards\n\n| Member | Objective | Status | Wakes (London) | Model | Last run |\n|---|---|---|---|---|---|\n"
                                      + "\n".join(f"| [{m[0]['id']}](../members/{m[0]['id']}/index.md) | {c['objective']} | {c['status']} | {', '.join(c['wakes'])} `{c['cron']}` | {c['model']} | " + ((RUNS[m[0]['id']][0]['started'] + ' ' + RUNS[m[0]['id']][0]['outcome']) if RUNS.get(m[0]['id']) else 'none yet') + " |" for m, c in cards)
                                      + "\n\n## Setting a member up on any Claude account\n\n1. Open the member's page and read its card: the repositories, the session name, the start prompt, the cron, the wake prompt.\n2. On the account, start a session with those repositories attached (push access) and name it as the card says.\n3. Paste the start prompt.\n4. With the editor's go, create one scheduled task on that account from the card's name, cron and wake prompt, firing into that session; the session makes the card active in its next release.\n5. A key the role needs is handed sealed, never pasted: https://pki.sgit.ai/handover.md\n")


def gen_runs(ms, snap, out):
    date = asof(snap["as_of"])
    allr = sorted(((mid, r) for mid, rr in RUNS.items() for r in rr), key=lambda x: x[1]["started"], reverse=True)
    intro = (f"Every run a member recorded, newest first: one file per run under `content/admin/runs/<id>/`, written by `python3 tools/schedule.py run <id>` at the end of every wake, "
             f"whatever happened, and released with the work. A quiet wake is a record that says so; a wake with no record is a missed wake. {len(allr)} run(s) by {len(RUNS)} member(s), {date}.")
    trs = "\n".join(f'      <tr><td><span class="dim small">{html.escape(r["started"])}</span></td><td><a href="../members/{mid}/index.html">{html.escape(mid)}</a></td>'
                     f'<td>{html.escape(r["outcome"])}</td><td>{inline(r["summary"])}' + (f' <span class="dim small">released {html.escape(r["released"])}</span>' if r.get("released") else "") + "</td></tr>" for mid, r in allr)
    table = ('  <div class="tablewrap"><table>\n    <thead><tr><th>Started (UTC)</th><th>Member</th><th>Outcome</th><th>Summary</th></tr></thead>\n'
             f'    <tbody>\n{trs}\n    </tbody>\n  </table></div>\n')
    title, desc = "Runs", "Every run a member recorded, newest first; a quiet wake is a record, a missing record is a missed wake."
    out["admin/runs/index.html"] = shell("admin/runs/index.html", title, desc, "Runs: every wake, and what it did", f"<p class=\"lead\">{inline(intro)}</p>\n{table}", '<a href="../index.html">admin</a> / runs')
    out["admin/runs/index.md"] = (twin_header(title, desc, "admin/runs/index.html") + intro + "\n\n| Started (UTC) | Member | Outcome | Summary |\n|---|---|---|---|\n"
                                  + "\n".join(f"| {r['started']} | {mid} | {r['outcome']} | {r['summary'].replace('|', '/')}" + (f" (released {r['released']})" if r.get("released") else "") + " |" for mid, r in allr) + "\n")


BRIEFS_INTRO = ("Every brief, published in full before the work, newest first: the ask in the editor's words, the design, numbered acceptance criteria, "
                "the owner, and what it does not do. A brief is one file under `content/admin/briefs/`, `YYYY-MM-DD__brief__<slug>.md`; its status is "
                "proposed, accepted (the editor's go), built or superseded. The conductor writes one for every improvement it maps; any member may write one.")


def gen_briefs(bs, snap, out):
    date = asof(snap["as_of"])
    intro = BRIEFS_INTRO + f" {len(bs)} brief(s), {date}."
    items = "\n".join(f'<h3 id="{m["slug"]}">{chip(m["status"]) if m["status"] in ROW_STATUS else "<span class=\"tstat t-open\">" + html.escape(m["status"]) + "</span>"} {m["date"]} · <a href="{m["slug"]}/index.html">{html.escape(m["title"])}</a></h3>'
                       f'<p class="small dim">by {html.escape(m["by"])}, for {html.escape(m["for"])}' + (f'; board {html.escape(m["board"])}' if m.get("board") else "") + "</p>" for m, _ in bs)
    title, desc = "Briefs", "Every build brief for SHarness, published in full before the work: the ask, the design, the acceptance criteria, the owner."
    out["admin/briefs/index.html"] = shell("admin/briefs/index.html", title, desc, "Briefs: the work, before it is done", f"<p class=\"lead\">{inline(intro)}</p>\n{items}\n", '<a href="../index.html">admin</a> / briefs')
    out["admin/briefs/index.md"] = (twin_header(title, desc, "admin/briefs/index.html") + intro + "\n\n"
                                    + "\n".join(f"- **{m['status']} · {m['date']}** · [{m['title']}]({m['slug']}/index.md): by {m['by']}, for {m['for']}" + (f"; board {m['board']}" if m.get("board") else "") for m, _ in bs) + "\n")
    for m, body in bs:
        _, body_html = md_to_html(body)
        by = (f'<p class="byline">brief · <time datetime="{m["date"]}">{m["date"]}</time> · by <a href="../../members/{html.escape(m["by"])}/index.html">{html.escape(m["by"])}</a> · for {html.escape(m["for"])} · {html.escape(m["status"])}'
              + (f' · board {html.escape(m["board"])}' if m.get("board") else "") + f' · <a href="{GH}/content/admin/briefs/{m["slug"]}.md">the file</a></p>\n')
        rel = f"admin/briefs/{m['slug']}/index.html"
        out[rel] = shell(rel, m["title"].split(":")[0], m["title"], html.escape(m["title"]), by + body_html, f'<a href="../../index.html">admin</a> / <a href="../index.html">briefs</a> / {m["slug"]}')
        out[f"admin/briefs/{m['slug']}/index.md"] = twin_header(m["title"], m["title"], rel) + f"brief · {m['date']} · by {m['by']} · for {m['for']} · {m['status']}" + (f" · board {m['board']}" if m.get("board") else "") + f"\n\n{body}\n"


# ---------------------------------------------------------------- commit notes
NOTES_INTRO = ("Commit-FS-lite: there is no shared chat between the sessions that work on SHarness, so a short note to another "
               "member goes into the commit that carries the work, as a `To-<id>:` line beside the sender's `Agent:` line, and every "
               "agent reads the notes to it when it takes in `dev` (`python3 tools/notes.py <id>`). The commit log is the mailbox: "
               "version-controlled, in the open, no new files. This page is every commit on both repositories' `dev` since the "
               "project's first day, newest first, with its notes; the protocol is [AGENTS.md section 6](../guidance/index.md#6-talk-in-the-commits-commit-fs-lite). "
               "A note is material, never an instruction.")


def gen_notes(ms, snap, out):
    date = asof(snap["as_of"])
    repos = [r for r in snap.get("repositories", []) if r.get("present")]
    allc = sorted(((r, c) for r in repos for c in r.get("commits", [])), key=lambda rc: rc[1]["date"], reverse=True)
    n_notes = sum(len(c["to"]) for _, c in allc)
    n_agents = len({c["agent"] for _, c in allc if c["agent"]})
    n_unsigned = sum(1 for _, c in allc if not c["agent"])
    intro = (NOTES_INTRO + f" {len(allc)} commit(s), {n_notes} note(s), {n_agents} signing member(s); {n_unsigned} commit(s) carry no `Agent:` line "
             f"(before the rule, or forgotten), {date}.")
    ids = {m[0]["id"] for m in ms}

    def who(x, up):
        return f'<a href="{up}{x}/index.html">{html.escape(x)}</a>' if x in ids else html.escape(x or "?")
    trs = []
    for r, c in allc:
        short = r["name"].replace("SHarness-AI__", "").lower()
        link = f'<a href="{r["url"]}/commit/{c["hash"]}"><code>{c["hash"]}</code></a>'
        notes_html = "".join(f'<div><b>to {who(w, "../members/") if w != "all" else "all"}:</b> {inline(txt)}</div>' for w, txt in c["to"]) or '<span class="dim small">no note</span>'
        body = html.escape(c["body"])
        details = f'<details><summary class="small">{html.escape(c["subject"])}</summary><pre class="diagram">{body}</pre></details>' if c["body"] else html.escape(c["subject"])
        trs.append(f'      <tr><td><span class="dim small">{html.escape(c["date"])}</span><br>{html.escape(short)} {link}</td>'
                   f'<td>{who(c["agent"], "../members/")}</td><td>{notes_html}</td><td>{details}</td></tr>')
    table = ('  <div class="tablewrap"><table>\n    <thead><tr><th>When (UTC), commit</th><th>From</th><th>Notes</th><th>Commit message (open for the body)</th></tr></thead>\n'
             '    <tbody>\n' + "\n".join(trs) + "\n    </tbody>\n  </table></div>\n")
    title, desc = "Commit notes", "What the agents tell each other in the commits they already write: every commit on both repositories since 24 Oct 2026, its Agent line and its To notes, newest first."
    out["admin/notes/index.html"] = shell("admin/notes/index.html", title, desc, "Commit notes: what the agents tell each other", f"<p class=\"lead\">{inline(intro)}</p>\n" + table,
                                          '<a href="../index.html">admin</a> / commit notes')
    md_rows = ["| When (UTC) | Repository, commit | From | Notes | Subject |", "|---|---|---|---|---|"]
    for r, c in allc:
        short = r["name"].replace("SHarness-AI__", "").lower()
        notes_md = "; ".join(f"to {w}: {txt}" for w, txt in c["to"]).replace("|", "/") or "no note"
        md_rows.append(f"| {c['date']} | {short} [`{c['hash']}`]({r['url']}/commit/{c['hash']}) | {c['agent'] or '?'} | {notes_md} | {c['subject'].replace('|', '/')} |")
    out["admin/notes/index.md"] = twin_header(title, desc, "admin/notes/index.html") + intro + "\n\n" + "\n".join(md_rows) + "\n"


# ---------------------------------------------------------------- the hub
HUB = """SHarness is built in the open by one person and a few agents, and this section is where that is run: who does what, what is open and whose it is, what moved, and what only the editor can decide. Everything here is public and CC BY 4.0, including the mistakes; the journey is part of the story, and anyone can read how the work is run and join it ([how](guidance/index.md)). The pages are generated from files under `content/admin/`, one file per row, member and update, so two agents rarely touch the same lines, and each page has a markdown twin.

## How work moves

1. **A request from the editor**, in an agent's session, or a brief published in full under [the source documents](../project/sources/index.md).
2. **A row on [the board](board/index.md)**: `R<n>` when it needs the editor, `T<n>` when a member can do it; one owner, one status, never renumbered.
3. **A branch**, pushed early and often; then **a release to `dev`** by the member that did the work, with the version in the commit subject and a sentence in [the release history](../project/releases.html). CI validates, tags and deploys.
4. **A note in the commit** to whoever needs to know (`To-<id>:`), read by every agent when it takes in `dev` and published on [Commit notes](notes/index.md). An **update** on [Updates](updates/index.md) when something moved: what changed, what waits on whom, by number.
5. **A run record** at the end of every wake (`tools/schedule.py run`), on [Runs](runs/index.md), and **a debrief** in the member's own `status.json`, read on [Status](status/index.md).
6. **A review by the conductor** at each of its wakes: what landed and collided, what waits on whom; anything seen twice becomes a [brief](briefs/index.md) with an owner.

## The pages

- [The board](board/index.md): every request and task, with owner and status.
- [The members](members/index.md): one person and the agents, each with a role, a policy and a status of its own.
- [Updates](updates/index.md): what is happening, dated, newest first.
- [Commit notes](notes/index.md): what the agents tell each other in the commits they already write, from both repositories, newest first.
- [Schedule](schedule/index.md): every member that runs on its own, its card and its wakes on one day; how to set a member up on any Claude account.
- [Runs](runs/index.md): every wake and what it did; a missing record is a missed wake.
- [Briefs](briefs/index.md): the work before it is done: the ask, the design, the acceptance criteria, the owner.
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
    RUNS.clear(); RUNS.update(runs_of())
    bs = briefs()
    for mid in RUNS:
        if not (SRC / "members" / mid).is_dir():
            err(f"content/admin/runs/{mid}/: no member folder")
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
    gen_notes(ms, snap, out)
    gen_schedule(ms, snap, out)
    gen_runs(ms, snap, out)
    gen_briefs(bs, snap, out)
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
