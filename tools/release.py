#!/usr/bin/env python3
"""The release, as CI performs it: the next number from the tags, written to /version by the one
commit that is tagged. Nobody else writes /version (R23, the send repository's scheme).

    python3 tools/release.py next  --branch dev|main            print the next version
    python3 tools/release.py bump  --branch dev|main --before SHA [--dry-run]
          write /version, add the row to project/releases.html, re-stamp every page (chrome.py
          and the generators), run the gate; with --dry-run stop there, otherwise commit as the
          actions user with the subject "site vX.Y.Z: <subject>" and tag that commit.
          The row (the shape of sgit.ai's release history): the newest commit's subject as the
          title, the first paragraph of its body as the description, then the pages the pushed
          range (BEFORE..HEAD) added ("New") and changed ("Updated"), each a link with the page's
          own title, plus any page named in a "Pages:" trailer, and a link to every change in git
    python3 tools/release.py guard BEFORE AFTER                 fail if a commit in the range, not by
          the actions user, modifies /version (adding it the first time is allowed)

A push to dev bumps the last number (vX.Y.Z+1); a push to main bumps the middle one and zeroes the
last (vX.Y+1.0). Standard library only; run from anywhere. Kept by website@sharness.
"""
import html
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIONS_USER = "GitHub Actions"
STEPS = [["python3", "tools/chrome.py"], ["python3", "tools/gen_admin.py"], ["python3", "tools/gen_pages.py"],
         ["python3", "tools/gen_articles.py"], ["python3", "tools/gen_storyboards.py"], ["python3", "tools/gen_sitemap.py"],
         ["python3", "tools/gen_llms_full.py"], ["node", "tools/validate.js"], ["node", "tools/validate_storyboards.cjs"],
         ["python3", "tools/gen_admin.py", "--check"], ["python3", "tools/gen_pages.py", "--check"],
         ["python3", "tools/gen_articles.py", "--check"], ["python3", "tools/gen_storyboards.py", "--check"],
         ["python3", "tools/releases.py", "check"]]


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"release: git {' '.join(args)} failed\n{r.stderr[-1500:]}")
    return r.stdout.strip()


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def latest_tag():
    tags = [t for t in git("tag", "--list", "v*").split() if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    return max(tags, key=vtuple) if tags else "v0.0.0"


def next_version(branch):
    a, b, c = vtuple(latest_tag())
    return f"v{a}.{b + 1}.0" if branch == "main" else f"v{a}.{b}.{c + 1}"


REPO = "https://github.com/SHarness-AI/SHarness-AI__Website"
TRAILER = re.compile(r"^(Agent|To-[A-Za-z-]+|Board|Pages|Co-Authored-By|Claude-Session|Signed-off-by):", re.I)
NOT_A_PAGE = ("admin/", "code/releases/", "404.html", "project/comms.html", "project/releases.html")


def is_page(path):
    return (path.endswith(".html") and not path.startswith(NOT_A_PAGE)
            and (path.endswith("/index.html") or path.startswith(("articles/", "project/", "explain/"))))


def page_title(path):
    f = ROOT / path
    if not f.exists():
        return path
    m = re.search(r"<title>(.*?)</title>", f.read_text(errors="replace"), re.S)
    return html.unescape(re.sub(r"\s+", " ", m.group(1)).replace(" — SHarness", "").strip()) if m else path


def describe(before):
    """The newest commit's subject and the first paragraph of its body; the pages the range touched."""
    subject = git("log", "-1", "--format=%s")
    body = [l for l in git("log", "-1", "--format=%b").splitlines() if not TRAILER.match(l)]
    para = []
    for line in body:
        if not line.strip() and para:
            break
        if line.strip():
            para.append(line.strip())
    description = " ".join(para)
    rng = f"{before}..HEAD" if before and re.fullmatch(r"[0-9a-f]{40}", before) and set(before) != {"0"} else "HEAD~1..HEAD"
    named = []
    for line in git("log", "--format=%B", rng).splitlines():
        if line.lower().startswith("pages:"):
            named += [x.strip().lstrip("/") for x in line.split(":", 1)[1].split(",") if x.strip()]
    new, updated = [], []
    for line in git("diff", "--name-status", "-M", rng).splitlines():
        parts = line.split("\t")
        status, path = parts[0][0], parts[-1]
        if is_page(path) and path not in named:
            (new if status == "A" else updated).append(path)
    return subject, description, named, new, updated


def links(paths, up="../"):
    return ", ".join(f'<a href="{up}{html.escape(p)}">{html.escape(page_title(p))}</a>' for p in paths)


def add_row(version, date, before):
    p = ROOT / "project/releases.html"
    t = p.read_text()
    if f'class="vnum">{version}<' in t:
        sys.exit(f"release: project/releases.html already has a row for {version}")
    m = re.search(r'      <tr(?: id="v[^"]*")?><td class="vnum">v\d+\.\d+\.\d+</td>', t)
    if not m:
        sys.exit("release: no release rows found in project/releases.html")
    subject, description, named, new, updated = describe(before)
    text = html.escape(subject.rstrip(".")) + "."
    if description:
        text += " " + html.escape(description)
    spans = []
    if named:
        spans.append(f"<span><b>Pages:</b> {links(named)}.</span>")
    if new:
        spans.append(f"<span><b>New:</b> {links(new)}.</span>")
    if updated:
        more = f" and {len(updated) - 12} more" if len(updated) > 12 else ""
        spans.append(f"<span><b>Updated:</b> {links(updated[:12])}{more}.</span>")
    prev = latest_tag()
    spans.append(f'<span><a href="{REPO}/compare/{prev}...{version}">Every change in this release, in git</a>.</span>')
    row = (f'      <tr id="{version}"><td class="vnum">{version}</td><td>{date}</td><td>{text}'
           f'<div class="vchg">{" ".join(spans)}</div></td></tr>\n')
    p.write_text(t[:m.start()] + row + t[m.start():])
    return subject


def bump(branch, before, dry_run):
    if branch not in ("dev", "main"):
        sys.exit("release: --branch is dev or main")
    version = next_version(branch)
    head = git("rev-parse", "HEAD")
    if version in git("tag", "--points-at", head).split() or (ROOT / "version").read_text().strip() == version:
        print(f"release: {head[:9]} already carries {version}; nothing to do")
        print(f"version={version}\nsha={head}\nbumped=false")
        return
    (ROOT / "version").write_text(version + "\n")
    subject = add_row(version, time.strftime("%-d %b %Y", time.gmtime()), before)
    for step in STEPS:
        r = subprocess.run(step, cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"release: {' '.join(step)} failed\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
        if r.stdout.strip():
            print(r.stdout.strip().splitlines()[-1])
    if dry_run:
        print(f"release: dry run, {version} written and every page stamped; nothing committed")
        return
    git("add", "-A")
    msg = (f"site {version}: {subject}\n\nThe release commit, made by CI from {head[:9]} on {branch} (R23): /version "
           f"written, the row added, every page re-stamped. The work is the commits before this one.\n\nAgent: ci\n")
    subprocess.run(["git", "-c", f"user.name={ACTIONS_USER}", "-c", "user.email=actions@github.com", "commit", "-q", "-F", "-"],
                   cwd=ROOT, input=msg, text=True, check=True)
    sha = git("rev-parse", "HEAD")
    git("tag", version, sha)
    print(f"release: {version} is {sha[:9]}")
    print(f"version={version}\nsha={sha}\nbumped=true")


def guard(before, after):
    if not re.fullmatch(r"[0-9a-f]{40}", before) or set(before) == {"0"}:
        print("release: no previous commit to compare with; the guard passes")
        return
    log = git("log", "--format=%H %an", "--diff-filter=M", f"{before}..{after}", "--", "version")
    bad = [l for l in log.splitlines() if not l.endswith(" " + ACTIONS_USER)]
    if bad:
        sys.exit("release: /version is written by CI only; these commits modify it by hand:\n  " + "\n  ".join(bad))
    print("release: /version untouched by hand in the pushed range")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == "next":
        print(next_version(opt("--branch", "dev")))
    elif a[0] == "bump":
        bump(opt("--branch", "dev"), opt("--before", ""), "--dry-run" in a)
    elif a[0] == "guard":
        guard(a[1], a[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
