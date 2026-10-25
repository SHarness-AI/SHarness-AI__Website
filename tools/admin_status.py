#!/usr/bin/env python3
"""Writes content/admin/status.json: where every branch of both repositories is.

Run from anywhere:  python3 tools/admin_status.py [--cli PATH]

The snapshot the conductor takes before an update. It reads git, never a session: branches,
how far each is ahead of and behind dev, the last commit on each (hash, date, subject, the
Agent: trailer when there is one), the latest tag. The build (gen_admin.py) renders the file
and is deterministic because this tool, not the build, holds the clock: the snapshot carries
its own as-of time and is committed like any other source. Nothing here reaches the network
beyond `git fetch`; nothing secret is read or written.

Also every commit on each dev since the project's first day, with its Agent: line and its To-<member>:
notes (Commit-FS-lite, AGENTS.md section 6), so /admin/notes/ can show what the agents told each other.

The CLI repository is found beside this one (../SHarness-AI__CLI) unless --cli says where;
when it is absent the snapshot says so rather than guessing.
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "content/admin/status.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from notes import commits                                        # noqa: E402  (the one parser of Agent: and To-: lines)
SINCE = "2026-10-24T00:00:00Z"                                   # the project's first day; every commit on dev since then
REPOS = [("SHarness-AI__Website", ROOT), ("SHarness-AI__CLI", ROOT.parent / "SHarness-AI__CLI")]


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def snapshot(name, repo):
    if not (repo / ".git").exists():
        return {"name": name, "present": False, "note": f"not checked out beside this repository ({repo})"}
    git(repo, "fetch", "--quiet", "--prune", "origin", "+refs/heads/*:refs/remotes/origin/*", "+refs/tags/*:refs/tags/*")
    heads = [h.split()[-1].removeprefix("origin/") for h in git(repo, "branch", "-r", "--format=%(refname:short)").split("\n")
             if h and "HEAD" not in h]
    out = []
    for b in sorted(heads, key=lambda x: (x not in ("dev", "main"), x)):
        ref = f"origin/{b}"
        line = git(repo, "log", "-1", "--format=%h%x00%ad%x00%s%x00%(trailers:key=Agent,valueonly)", "--date=iso-strict", ref)
        h, d, s, agent = (line.split("\x00") + ["", "", "", ""])[:4]
        ahead  = git(repo, "rev-list", "--count", f"origin/dev..{ref}") if b != "dev" else "0"
        behind = git(repo, "rev-list", "--count", f"{ref}..origin/dev") if b != "dev" else "0"
        out.append({"branch": b, "head": h, "date": d, "subject": s, "agent": agent.strip(),
                    "ahead_of_dev": int(ahead or 0), "behind_dev": int(behind or 0)})
    tags = [t for t in git(repo, "tag", "--list", "v*").split("\n") if t]
    tags.sort(key=lambda t: [int(x) for x in re.findall(r"\d+", t)])
    log = commits(repo, f"--since={SINCE}", "origin/dev")
    return {"name": name, "present": True, "url": f"https://github.com/SHarness-AI/{name}",
            "latest_tag": tags[-1] if tags else None, "branches": out,
            "commits": [{k: c[k] for k in ("hash", "date", "subject", "agent", "to")} | {"body": c["body"][:1500]} for c in reversed(log)]}


def main():
    cli = ROOT.parent / "SHarness-AI__CLI"
    if "--cli" in sys.argv:
        cli = Path(sys.argv[sys.argv.index("--cli") + 1])
    repos = [("SHarness-AI__Website", ROOT), ("SHarness-AI__CLI", cli)]
    data = {"as_of": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "by": "conductor", "repositories": [snapshot(n, p) for n, p in repos]}
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    for r in data["repositories"]:
        n, c = len(r.get("branches", [])), len(r.get("commits", []))
        notes = sum(len(x["to"]) for x in r.get("commits", []))
        print(f"  · {r['name']}: {'%d branch(es), %d commit(s) on dev since %s, %d note(s), latest tag %s' % (n, c, SINCE[:10], notes, r.get('latest_tag')) if r.get('present') else r['note']}")
    print(f"admin_status: {OUT.relative_to(ROOT)} as of {data['as_of']}")


if __name__ == "__main__":
    main()
