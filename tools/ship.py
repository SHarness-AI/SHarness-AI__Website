#!/usr/bin/env python3
"""Ships a release of the site: fetch, merge dev, bump, build, gate, commit, push, verify live.

Run from the branch that carries your work, with your changes in the tree (committed or not):

    RELEASE_TRAILER=$'Agent: <id>\\nTo-<id>: ...' python3 tools/ship.py "what changed" [--body-file F] [--snapshot]

The one way anything reaches dev (the brief: content/admin/briefs/2026-10-26__brief__the-release-script.md).
In order: refuse main and anything key-shaped in the message; fetch dev and the tags; commit the
work in the tree if any (a local commit, pushed only with the release); merge
origin/dev (a conflict stops here, with the files named); the version is the newest of the latest
tag and dev's tools/version.txt, plus one patch, written to tools/version.txt, and its row added
to project/releases.html from the subject; tools/admin_status.py when --snapshot; chrome.py and
every generator; the gate and every --check; one commit "site vX.Y.Z: <subject>" with the body
and the trailers; push to dev, and if dev moved meanwhile, once more from the merge (a new commit
on top, never an amend); then push the branch, and poll the live site for the version badge for up
to five minutes. A failure anywhere means no commit and no push. Standard library only.
"""
import html
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = (ROOT / "CNAME").read_text().strip()
KEY_SHAPE = re.compile(r"[A-Za-z0-9_-]{20,}:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|sgit_private_vault_|-----BEGIN")
STEPS = [["python3", "tools/chrome.py"], ["python3", "tools/gen_admin.py"], ["python3", "tools/gen_pages.py"],
         ["python3", "tools/gen_articles.py"], ["python3", "tools/gen_storyboards.py"], ["python3", "tools/gen_sitemap.py"],
         ["python3", "tools/gen_llms_full.py"], ["node", "tools/validate.js"], ["node", "tools/validate_storyboards.cjs"],
         ["python3", "tools/gen_admin.py", "--check"], ["python3", "tools/gen_pages.py", "--check"],
         ["python3", "tools/gen_articles.py", "--check"], ["python3", "tools/gen_storyboards.py", "--check"]]


def sh(*args, check=True, quiet=False):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"ship: {' '.join(args)} failed\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
    if not quiet and r.stdout.strip():
        print(r.stdout.strip().splitlines()[-1])
    return r


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def next_version():
    tags = [t for t in sh("git", "tag", "--list", "v*", quiet=True).stdout.split() if re.match(r"^v\d+\.\d+\.\d+$", t)]
    dev = sh("git", "show", "origin/dev:tools/version.txt", quiet=True).stdout.strip()
    base = max(tags + ([dev] if dev else []), key=vtuple)
    a, b, c = vtuple(base)
    return f"v{a}.{b}.{c + 1}", base


def add_row(version, subject, date):
    p = ROOT / "project/releases.html"
    t = p.read_text()
    if f'class="vnum">{version}<' in t:
        sys.exit(f"ship: project/releases.html already has a row for {version}")
    m = re.search(r'      <tr><td class="vnum">v\d+\.\d+\.\d+</td>', t)
    if not m:
        sys.exit("ship: no release rows found in project/releases.html")
    row = f'      <tr><td class="vnum">{version}</td><td>{date}</td><td>{html.escape(subject)}</td></tr>\n'
    p.write_text(t[:m.start()] + row + t[m.start():])


def attempt(subject, body, trailer, snapshot, n):
    sh("git", "fetch", "--quiet", "--tags", "origin", "dev", quiet=True)
    if sh("git", "status", "--porcelain", quiet=True).stdout.strip():
        # the work in the tree becomes a local commit first, so the merge can run; it is pushed only with the release
        sh("git", "add", "-A", quiet=True)
        subprocess.run(["git", "commit", "-q", "-m", f"{subject} (the work, before the release commit)\n\n{trailer.strip()}\n"], cwd=ROOT, text=True, check=True)
    r = sh("git", "merge", "--no-edit", "origin/dev", check=False, quiet=True)
    if r.returncode:
        files = sh("git", "diff", "--name-only", "--diff-filter=U", quiet=True).stdout.strip()
        sys.exit(f"ship: merging origin/dev failed:\n{files or r.stderr.strip()[-800:]}\nResolve by hand (keep both sides), then run again.")
    version, base = next_version()
    print(f"ship: attempt {n}: dev at {base}, this release is {version}")
    (ROOT / "tools/version.txt").write_text(version + "\n")
    add_row(version, subject, time.strftime("%-d %b %Y", time.gmtime()))
    if snapshot:
        sh("python3", "tools/admin_status.py")
    for step in STEPS:
        sh(*step)
    msg = f"site {version}: {subject}\n\n{body.strip()}\n\n{trailer.strip()}\n" if trailer.strip() else f"site {version}: {subject}\n\n{body.strip()}\n"
    sh("git", "add", "-A", quiet=True)
    subprocess.run(["git", "commit", "-q", "-F", "-"], cwd=ROOT, input=msg, text=True, check=True)
    push = sh("git", "push", "origin", "HEAD:dev", check=False, quiet=True)
    if push.returncode:
        if "fetch first" in push.stderr or "non-fast-forward" in push.stderr or "rejected" in push.stderr:
            print("ship: dev moved while this was built; merging again")
            return None
        sys.exit(f"ship: push to dev failed\n{push.stderr[-1500:]}")
    return version


def verify_live(version):
    url = f"https://{HOST}/index.html"
    for _ in range(20):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                if f'class="ver"' in (page := r.read().decode("utf-8", "replace")) and f">{version}<" in page:
                    print(f"ship: {HOST} serves {version}")
                    return True
        except Exception:
            pass
        time.sleep(15)
    print(f"ship: {HOST} does not serve {version} after five minutes: check the deploy workflow")
    return False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    subject = args[0].strip()
    body = Path(sys.argv[sys.argv.index("--body-file") + 1]).read_text() if "--body-file" in sys.argv else ""
    trailer = os.environ.get("RELEASE_TRAILER", "")
    branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD", quiet=True).stdout.strip()
    if branch in ("main", "HEAD"):
        sys.exit("ship: never from main or a detached head; work on a branch of your own")
    if KEY_SHAPE.search(subject + body + trailer):
        sys.exit("ship: the message carries something key-shaped; nothing secret in a commit")
    if "Agent:" not in trailer:
        sys.exit("ship: RELEASE_TRAILER must carry your Agent: <id> line (AGENTS.md section 6)")
    version = attempt(subject, body, trailer, "--snapshot" in sys.argv, 1) or attempt(subject, body, trailer, "--snapshot" in sys.argv, 2)
    if not version:
        sys.exit("ship: dev moved twice while this was built; run again")
    sh("git", "push", "-u", "origin", branch, quiet=True)
    print(f"ship: site {version} pushed to dev and {branch}")
    sys.exit(0 if verify_live(version) else 1)


if __name__ == "__main__":
    main()
