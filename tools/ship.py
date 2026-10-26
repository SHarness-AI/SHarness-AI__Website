#!/usr/bin/env python3
"""Ships your work to dev: commit, merge dev, build, gate, push, then wait for CI to number it.

Run from the branch that carries your work, with your changes in the tree (committed or not):

    RELEASE_TRAILER=$'Agent: <id>\\nTo-<id>: ...' python3 tools/ship.py "what changed" [--body-file F] [--snapshot]

The one way anything reaches dev (the brief: content/admin/briefs/2026-10-26__brief__the-release-script.md,
and R23: CI owns the version). In order: refuse main and anything key-shaped in the message; commit
the work in the tree if any, with the subject, the body and the trailers; fetch and merge origin/dev
(a conflict stops here, with the files named); tools/admin_status.py when --snapshot; chrome.py and
every generator, then the gate and every --check (a second commit when taking in dev changed a
generated page); push to dev, and if dev moved meanwhile, once more from the merge; push the
branch; then wait for CI's release commit that contains yours (the tag names the version) and for
the live site to serve it. The version is never written here: /version belongs to CI
(tools/release.py). A failure anywhere means no push. Standard library only.
"""
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


def commit(message):
    sh("git", "add", "-A", quiet=True)
    subprocess.run(["git", "commit", "-q", "-F", "-"], cwd=ROOT, input=message, text=True, check=True)


def attempt(subject, body, trailer, snapshot, n):
    sh("git", "fetch", "--quiet", "--tags", "origin", "dev", quiet=True)
    if sh("git", "status", "--porcelain", quiet=True).stdout.strip():
        commit(f"{subject}\n\n{body.strip()}\n\n{trailer.strip()}\n" if body.strip() else f"{subject}\n\n{trailer.strip()}\n")
    r = sh("git", "merge", "--no-edit", "origin/dev", check=False, quiet=True)
    if r.returncode:
        files = sh("git", "diff", "--name-only", "--diff-filter=U", quiet=True).stdout.strip()
        sys.exit(f"ship: merging origin/dev failed:\n{files or r.stderr.strip()[-800:]}\nResolve by hand (keep both sides), then run again.")
    on_dev = sh("git", "show", "origin/dev:version", check=False, quiet=True)
    if on_dev.returncode == 0 and (ROOT / "version").read_text() != on_dev.stdout:
        sys.exit("ship: /version differs from dev's; it is written by CI only (tools/release.py). Restore it: git checkout origin/dev -- version")
    if snapshot:
        sh("python3", "tools/admin_status.py")
    for step in STEPS:
        sh(*step)
    if sh("git", "status", "--porcelain", quiet=True).stdout.strip():
        # the same subject as the work: CI names the release after the newest commit's subject
        commit(f"{subject}\n\nThe generated pages after taking in dev; the work is the commit before this one.\n\n{trailer.strip()}\n")
    head = sh("git", "rev-parse", "HEAD", quiet=True).stdout.strip()
    push = sh("git", "push", "origin", "HEAD:dev", check=False, quiet=True)
    if push.returncode:
        if "fetch first" in push.stderr or "non-fast-forward" in push.stderr or "rejected" in push.stderr:
            print(f"ship: dev moved while this was built; merging again (attempt {n})")
            return None
        sys.exit(f"ship: push to dev failed\n{push.stderr[-1500:]}")
    print(f"ship: {head[:9]} pushed to dev; CI numbers it")
    return head


def wait_for_release(head):
    """The tag CI cuts on the release commit that contains our push; then the live site."""
    before = set(sh("git", "tag", "--list", "v*", quiet=True).stdout.split())
    for _ in range(24):
        sh("git", "fetch", "--quiet", "--tags", "origin", quiet=True)
        new = [t for t in sh("git", "tag", "--list", "v*", quiet=True).stdout.split() if t not in before]
        for tag in new:
            if sh("git", "merge-base", "--is-ancestor", head, tag, check=False, quiet=True).returncode == 0:
                print(f"ship: CI released {tag} with {head[:9]} in it")
                return tag
        time.sleep(15)
    print(f"ship: no release tag containing {head[:9]} after six minutes: check the deploy workflow")
    return None


def verify_live(version):
    for _ in range(20):
        try:
            with urllib.request.urlopen(f"https://{HOST}/index.html", timeout=20) as r:
                if 'class="ver"' in (page := r.read().decode("utf-8", "replace")) and f">{version}<" in page:
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
    if branch in ("main", "dev", "HEAD"):
        sys.exit("ship: never from main, dev or a detached head; work on a branch of your own")
    if KEY_SHAPE.search(subject + body + trailer):
        sys.exit("ship: the message carries something key-shaped; nothing secret in a commit")
    if "Agent:" not in trailer:
        sys.exit("ship: RELEASE_TRAILER must carry your Agent: <id> line (AGENTS.md section 6)")
    if re.match(r"site v\d", subject):
        sys.exit("ship: the subject carries no version; CI writes \"site vX.Y.Z:\" on its own release commit")
    head = attempt(subject, body, trailer, "--snapshot" in sys.argv, 1) or attempt(subject, body, trailer, "--snapshot" in sys.argv, 2)
    if not head:
        sys.exit("ship: dev moved twice while this was built; run again")
    sh("git", "push", "-u", "origin", branch, quiet=True)
    print(f"ship: pushed to dev and {branch}")
    tag = wait_for_release(head)
    sys.exit(0 if tag and verify_live(tag) else 1)


if __name__ == "__main__":
    main()
