#!/usr/bin/env python3
"""The code, published on this site at immutable paths.

    python3 tools/releases.py cut  --from ../SHarness-AI__CLI --release v0.1.0 [--ref v0.1.0]
    python3 tools/releases.py snapshot --from ../SHarness-AI__CLI        # code/releases/dev/: the dev head
    python3 tools/releases.py check                                       # the gate: no published byte changed
    python3 tools/releases.py live-check [--host https://sharness.ai]     # after a deploy: the live files match

The rule (Dinis Cruz, 25 Oct 2026; the same one the storyboards.sgit.ai kit follows):

  · a release lives at code/releases/vMAJOR/vMAJOR.MINOR/vMAJOR.MINOR.PATCH/ and never changes.
    A fix is the next release in its own folder. `cut` refuses to write into a folder that exists.
  · every release is COMPLETE: the Python package as source and as a wheel, the policies, the
    browser code, the licence, and a manifest.json naming every file with its size, sha256 and
    sha384 integrity string. Files in a release only meet files from the same release.
  · releases.json lists every release, newest first. latest.json names the newest one, and
    code/releases/latest/ is a byte-for-byte copy of it: the one path that moves, by design, so
    a page can "bring in the latest". Pin the versioned path when a change must never surprise you.
  · code/releases/dev/ is a SNAPSHOT of the CLI's dev branch, rebuilt by `snapshot`, and says so in
    its manifest. It is not a release and has no immutability promise.
  · `check` runs in the gate on every push: it recomputes every hash of every release and fails
    the release if one byte differs, if latest.json names a release that is not there, or if
    latest/ is not that release's copy.

Standard library only, plus git. The wheel is built by the CLI's own experiments/browser/build_wheel.py.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL  = ROOT / "code" / "releases"
HOST = (ROOT / "CNAME").read_text().strip()
VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

# What a release carries, relative to the CLI checkout. Absent paths are skipped (older
# releases had fewer files), present ones are copied whole.
CARRY = ["sharness_ai", "experiments/policies", "experiments/browser/playground.js",
         "experiments/browser/playground.html", "experiments/browser/page.html", "LICENSE", "README.md"]


def release_dir(release: str) -> Path:
    m = VERSION_RE.match(release)
    if not m:
        sys.exit(f"{release}: not vMAJOR.MINOR.PATCH")
    major, minor, _ = m.groups()
    return REL / f"v{major}" / f"v{major}.{minor}" / release


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def integrity_of(data: bytes) -> str:
    return "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()


def manifest_for(folder: Path, release: str, kind: str, source: dict) -> dict:
    files = []
    for f in sorted(p for p in folder.rglob("*") if p.is_file() and p.name != "manifest.json"):
        data = f.read_bytes()
        files.append({"path": f.relative_to(folder).as_posix(), "bytes": len(data),
                      "sha256": sha256_of(data), "integrity": integrity_of(data)})
    base = f"https://{HOST}/{folder.relative_to(ROOT).as_posix()}/"
    what = ("Immutable release of the sharness-ai code: nothing at this path will ever change; a fix is the "
            "next release in its own folder. Every file is listed with its sha256 and a sha384 integrity "
            "string for a <script integrity> attribute." if kind == "release" else
            "SNAPSHOT of the sharness-ai dev branch: rebuilt on every site release, no immutability promise. "
            "Pin a release under code/releases/vN/ when the bytes must not move.")
    return {"what": what, "kind": kind, "release": release, "date": date.today().isoformat(),
            "source": source, "base": base,
            "counts": {"files": len(files), "bytes": sum(f["bytes"] for f in files)}, "files": files}


def export_tree(cli: Path, ref: str, dest: Path):
    """The CLI checkout at `ref`, exported with git archive: no .git, no untracked files."""
    tar = dest / "src.tar"
    with open(tar, "wb") as f:
        subprocess.run(["git", "-C", str(cli), "archive", "--format=tar", ref], stdout=f, check=True)
    subprocess.run(["tar", "-xf", str(tar), "-C", str(dest)], check=True)
    tar.unlink()
    commit = subprocess.run(["git", "-C", str(cli), "rev-parse", ref], capture_output=True, text=True, check=True).stdout.strip()
    return commit


def assemble(cli: Path, ref: str, folder: Path, release: str, kind: str, wheel_version: str):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td)
        commit = export_tree(cli, ref, src)
        folder.mkdir(parents=True)
        for rel in CARRY:
            p = src / rel
            if not p.exists():
                continue
            if p.is_dir():
                shutil.copytree(p, folder / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                (folder / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(p, folder / rel)
        (folder / "sharness_ai" / "version").write_text(release.split("+")[0] + "\n")
        # the wheel, built by the CLI's own stdlib builder, from the exported tree
        bw = cli / "experiments" / "browser" / "build_wheel.py"
        spec = importlib.util.spec_from_file_location("build_wheel", bw)
        build_wheel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_wheel)
        (folder / "sharness_ai" / "version").write_text(f"v{wheel_version}\n")
        whl = build_wheel.build(folder, ver=wheel_version, src=folder / "sharness_ai")
        source = {"repository": "https://github.com/SHarness-AI/SHarness-AI__CLI", "ref": ref, "commit": commit}
        (folder / "manifest.json").write_text(json.dumps(manifest_for(folder, release, kind, source), indent=1) + "\n")
        return whl, commit


def write_index():
    """releases.json (every release, newest first), latest.json and the latest/ copy."""
    releases = sorted((d for d in REL.glob("v*/v*/v*") if (d / "manifest.json").exists()),
                      key=lambda d: tuple(int(x) for x in VERSION_RE.match(d.name).groups()), reverse=True)
    rows = []
    for d in releases:
        m = json.loads((d / "manifest.json").read_text())
        rows.append({"release": d.name, "path": d.relative_to(REL).as_posix() + "/",
                     "manifest": d.relative_to(REL).as_posix() + "/manifest.json", "date": m["date"],
                     "commit": m["source"]["commit"], "files": m["counts"]["files"], "bytes": m["counts"]["bytes"]})
    snap = REL / "dev" / "manifest.json"
    (REL / "releases.json").write_text(json.dumps({
        "what": "Every release of the sharness-ai code on this site, newest first. Each path is immutable; "
                "latest.json names the newest and latest/ is its copy; dev/ is a snapshot with no promise.",
        "host": f"https://{HOST}", "base": f"https://{HOST}/code/releases/",
        "newest": rows[0]["release"] if rows else None, "releases": rows,
        "dev": json.loads(snap.read_text())["release"] if snap.exists() else None}, indent=1) + "\n")
    if rows:
        newest = releases[0]
        (REL / "latest.json").write_text(json.dumps({
            "what": "The newest release. This file and latest/ are the only paths under code/releases/ that move; "
                    "pin the versioned path when the bytes must never change under you.",
            "release": newest.name, "path": rows[0]["path"], "manifest": rows[0]["manifest"],
            "base": f"https://{HOST}/code/releases/{rows[0]['path']}"}, indent=1) + "\n")
        latest = REL / "latest"
        if latest.exists():
            shutil.rmtree(latest)
        shutil.copytree(newest, latest)


def cmd_cut(a):
    folder = release_dir(a.release)
    if folder.exists():
        sys.exit(f"{folder.relative_to(ROOT)} exists: a release never changes. Cut the next one.")
    ref = a.ref or a.release
    whl, commit = assemble(Path(a.src).resolve(), ref, folder, a.release, "release", a.release[1:])
    write_index()
    print(f"cut {a.release} from {ref} ({commit[:9]}) into {folder.relative_to(ROOT)}: {whl.name}")


def cmd_snapshot(a):
    cli = Path(a.src).resolve()
    short = subprocess.run(["git", "-C", str(cli), "rev-parse", "--short=7", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    base = re.search(r'^version\s*=\s*"v?([^"]+)"', (cli / "pyproject.toml").read_text(), re.M).group(1)
    folder = REL / "dev"
    if folder.exists():
        shutil.rmtree(folder)
    ver = f"{base}+dev.{short}"
    whl, commit = assemble(cli, "HEAD", folder, f"v{ver}", "snapshot", ver)
    write_index()
    print(f"snapshot of dev ({commit[:9]}) into {folder.relative_to(ROOT)}: {whl.name}")


def verify(folder: Path, read) -> list:
    """Problems with one published folder against its manifest; [] when every byte matches."""
    problems = []
    try:
        m = json.loads(read(folder / "manifest.json"))
    except Exception as e:                                       # noqa: BLE001
        return [f"{folder.relative_to(ROOT)}: no readable manifest.json ({e})"]
    listed = set()
    for f in m["files"]:
        listed.add(f["path"])
        try:
            data = read(folder / f["path"])
        except Exception as e:                                   # noqa: BLE001
            problems.append(f"{folder.relative_to(ROOT)}/{f['path']}: unreadable ({e})")
            continue
        if sha256_of(data) != f["sha256"] or len(data) != f["bytes"]:
            problems.append(f"{folder.relative_to(ROOT)}/{f['path']}: bytes differ from the manifest")
    if folder.exists():
        extra = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} - listed - {"manifest.json"}
        for x in sorted(extra):
            problems.append(f"{folder.relative_to(ROOT)}/{x}: not in the manifest")
    return problems


def cmd_check(a):
    problems = []
    releases = sorted(d for d in REL.glob("v*/v*/v*") if d.is_dir())
    for d in releases:
        m = VERSION_RE.match(d.name)
        if not m or d.parent.name != f"v{m.group(1)}.{m.group(2)}" or d.parent.parent.name != f"v{m.group(1)}":
            problems.append(f"{d.relative_to(ROOT)}: not at vMAJOR/vMAJOR.MINOR/vMAJOR.MINOR.PATCH")
        problems += verify(d, lambda p: p.read_bytes())
        if (d / "manifest.json").exists() and json.loads((d / "manifest.json").read_text()).get("kind") != "release":
            problems.append(f"{d.relative_to(ROOT)}: manifest kind is not 'release'")
    if (REL / "dev").exists():
        problems += verify(REL / "dev", lambda p: p.read_bytes())
    if (REL / "latest.json").exists():
        latest = json.loads((REL / "latest.json").read_text())
        target = REL / latest["path"]
        if not (target / "manifest.json").exists():
            problems.append(f"latest.json names {latest['release']}, which is not published")
        elif not (REL / "latest").exists():
            problems.append("latest/ is missing")
        else:
            for f in sorted(p for p in target.rglob("*") if p.is_file()):
                twin = REL / "latest" / f.relative_to(target)
                if not twin.exists() or twin.read_bytes() != f.read_bytes():
                    problems.append(f"latest/{f.relative_to(target)} is not a copy of {latest['release']}")
    elif releases:
        problems.append("latest.json is missing")
    if (REL / "releases.json").exists():
        listed = {r["release"] for r in json.loads((REL / "releases.json").read_text())["releases"]}
        if listed != {d.name for d in releases}:
            problems.append(f"releases.json lists {sorted(listed)}, the tree has {sorted(d.name for d in releases)}")
    if problems:
        print(f"releases: {len(problems)} problem(s)", file=sys.stderr)
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        sys.exit(1)
    print(f"releases: OK — {len(releases)} immutable release(s){', a dev snapshot' if (REL / 'dev').exists() else ''}, every byte matches its manifest")


def cmd_live_check(a):
    def read(p: Path):
        url = f"{a.host}/{p.relative_to(ROOT).as_posix()}"
        with urllib.request.urlopen(url, timeout=60) as r:    # noqa: S310 - https host given on the command line
            return r.read()
    problems = []
    for d in sorted(REL.glob("v*/v*/v*")):
        problems += verify(d, read)
    if problems:
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        sys.exit(1)
    print(f"live: every published release on {a.host} matches its manifest")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cut", help="publish one release of the CLI at its immutable path")
    c.add_argument("--from", dest="src", required=True, help="a checkout of SHarness-AI__CLI")
    c.add_argument("--release", required=True, help="vMAJOR.MINOR.PATCH, the CLI's tag")
    c.add_argument("--ref", help="git ref to export (default: the release tag)")
    c.set_defaults(fn=cmd_cut)
    s = sub.add_parser("snapshot", help="rebuild code/releases/dev/ from the CLI's dev head")
    s.add_argument("--from", dest="src", required=True)
    s.set_defaults(fn=cmd_snapshot)
    k = sub.add_parser("check", help="the gate: every published byte matches its manifest")
    k.set_defaults(fn=cmd_check)
    l = sub.add_parser("live-check", help="fetch every release from the live host and compare")
    l.add_argument("--host", default=f"https://{HOST}")
    l.set_defaults(fn=cmd_live_check)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
