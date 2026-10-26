#!/usr/bin/env python3
"""The scheduled wake's two sides: what changed for a member, and the run record it leaves.

Run from anywhere:
    python3 tools/schedule.py wake <id>          the commits since the member's last run, the notes to it
                                                 and to all, and its card's steps (WAKE.md step 2)
    python3 tools/schedule.py run <id> --started 2026-10-26T07:20Z --outcome ok|idle|partial|failed
                                      --summary "..." [--released vX.Y.Z] [--read <hash>,...] [--sent <id>,...]
                                                 writes content/admin/runs/<id>/<time>.json (WAKE.md step 5)
    python3 tools/schedule.py card <id>          prints the member's start prompt and wake prompt, word for word

A card is content/admin/members/<id>/card.json; a run record is one file, named by its UTC time, so
two members never write the same file and a merge never conflicts. Standard library only; the CLI
repository beside this one is read when it is there. Kept by the conductor.
"""
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT  = Path(__file__).resolve().parents[1]
REPOS = [("website", ROOT), ("cli", ROOT.parent / "SHarness-AI__CLI")]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from notes import commits, git                                   # noqa: E402


def member_dir(mid):
    d = ROOT / "content/admin/members" / mid
    if not d.is_dir():
        sys.exit(f"schedule: no member folder content/admin/members/{mid}/ (AGENTS.md section 5 says how to add one)")
    return d


def runs(mid):
    d = ROOT / "content/admin/runs" / mid
    return sorted((json.loads(p.read_text()) for p in d.glob("*.json")), key=lambda r: r["started"]) if d.is_dir() else []


def wake(mid):
    d = member_dir(mid)
    card = json.loads((d / "card.json").read_text()) if (d / "card.json").exists() else {}
    last = runs(mid)[-1] if runs(mid) else None
    print(f"== {mid}: wake at {now()}" + (f"; last run {last['started']} ({last['outcome']}): {last['summary'][:120]}" if last else "; no run recorded yet"))
    for name, repo in REPOS:
        if not (repo / ".git").exists():
            continue
        git(repo, "fetch", "--quiet", "origin", "dev")
        heads = (last or {}).get("heads", {})
        rng = [f"{heads[name]}..origin/dev"] if heads.get(name) else ["-30", "origin/dev"]
        cs = commits(repo, *rng)
        print(f"\n-- {name}: {len(cs)} commit(s) on dev " + (f"since {heads[name]}" if heads.get(name) else "(the last 30)"))
        for c in cs:
            mine = [(w, t) for w, t in c["to"] if w in (mid, "all")]
            flag = " *" if mine else ""
            print(f"  {c['hash']} {c['date']} [{c['agent'] or '?'}] {c['subject'][:100]}{flag}")
            for w, t in mine:
                print(f"      to {w}: {t}")
    if card:
        print(f"\n-- your card ({card.get('status')}): {card.get('objective', '')}")
        for i, s in enumerate(card.get("each_wake", []), 1):
            print(f"  {i}. {s}")
        if card.get("brief"):
            print(f"  brief: {card['brief']}")
    print("\n-- then: do the steps, commit each self-contained one, release what is finished, and leave a run record:")
    print(f"   python3 tools/schedule.py run {mid} --started {now()} --outcome ok --summary \"...\"")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def run(mid):
    member_dir(mid)
    started = arg("--started", now())
    outcome = arg("--outcome")
    summary = arg("--summary")
    if outcome not in ("ok", "idle", "partial", "failed") or not summary:
        sys.exit("schedule run: --outcome ok|idle|partial|failed and --summary are required")
    heads = {}
    for name, repo in REPOS:
        if (repo / ".git").exists():
            h = git(repo, "rev-parse", "--short", "origin/dev").strip()
            if h:
                heads[name] = h
    rec = {"member": mid, "started": started, "finished": now(), "outcome": outcome, "summary": summary,
           "released": arg("--released", ""), "read": [x for x in arg("--read", "").split(",") if x],
           "sent": [x for x in arg("--sent", "").split(",") if x], "heads": heads, "model": arg("--model", "")}
    d = ROOT / "content/admin/runs" / mid
    d.mkdir(parents=True, exist_ok=True)
    out = d / (started.replace("-", "").replace(":", "") + ".json")
    out.write_text(json.dumps(rec, indent=2) + "\n")
    print(f"schedule: {out.relative_to(ROOT)} ({outcome}); release it with your work, or on its own")


def card(mid):
    c = json.loads((member_dir(mid) / "card.json").read_text())
    print(f"== {mid}: session \"{c['session']}\"; repositories {', '.join(c['repositories']['push'])}; wakes {', '.join(c['wakes'])} {c['timezone']} ({c['cron']}); status {c['status']}")
    print("\n-- start prompt (paste into a new session on any Claude account):\n")
    print(c["start_prompt"])
    print("\n-- wake prompt (the scheduled task's prompt, word for word):\n")
    print(c["wake_prompt"])


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("wake", "run", "card"):
        sys.exit(__doc__)
    {"wake": wake, "run": run, "card": card}[sys.argv[1]](sys.argv[2])


if __name__ == "__main__":
    main()
