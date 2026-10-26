#!/usr/bin/env python3
"""Generates the policy v0 standard's test vectors from the reference implementation.

Run from anywhere:  python3 tools/gen_vectors.py           (write)
                    python3 tools/gen_vectors.py --check   (fail if anything is stale)

The cases are files: the CLI's example policies (../SHarness-AI__CLI/experiments/policies/*.json,
the checkout beside this one, as tools/schedule.py already assumes) and this site's own
content/standards/policy-v0/cases/{a*,r*}.json: a* must be accepted, r* must be refused, with the
reason for each refusal in cases/refusals.json. The CLI's own sharness_ai.policy is the oracle:
every accept case is loaded, checked and hashed by it, every refuse case must make it refuse.
The output is code/standards/policy-v0/vectors/<name>.json (the case, byte for byte) and
code/standards/policy-v0/vectors.json, the manifest an implementation's CI fetches: for each
accept case its hash and its canonical bytes as a string, for each refuse case the reason.
A hash here is not a measurement: it is what the standard says the bytes hash to.
Kept by dev@sharness. Standard library only.
"""
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[1]
CLI    = ROOT.parent / "SHarness-AI__CLI"
CASES  = ROOT / "content/standards/policy-v0/cases"
OUT    = ROOT / "code/standards/policy-v0"
sys.path.insert(0, str(CLI))
from sharness_ai import policy                                   # noqa: E402


def cli_commit():
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=CLI, capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def accept_case(name, path):
    obj = policy.load(path)
    problems = policy.check(obj)
    if problems:
        sys.exit(f"gen_vectors: {path} must be accepted but the CLI refuses it: {problems}")
    return {"name": name, "file": f"vectors/{name}.json", "kind": "accept",
            "hash": policy.policy_hash(obj), "canonical": policy.canonical(obj).decode("utf-8")}


def refuse_case(name, path, reason):
    try:
        obj = policy.load(path)
        problems = policy.check(obj)
    except policy.PolicyError as e:
        problems = [str(e)]
    if not problems:
        sys.exit(f"gen_vectors: {path} must be refused but the CLI accepts it")
    return {"name": name, "file": f"vectors/{name}.json", "kind": "refuse", "reason": reason,
            "cli_says": problems[0].replace(f"{path}: ", "")}


def build():
    reasons = json.loads((CASES / "refusals.json").read_text())
    sources = []
    for p in sorted((CLI / "experiments/policies").glob("*.json")):
        sources.append(("accept", p.stem, p))
    for p in sorted(CASES.glob("a*.json")):
        sources.append(("accept", p.stem, p))
    for p in sorted(CASES.glob("r[0-9]*.json")):
        sources.append(("refuse", p.stem, p))
    cases, files = [], {}
    for kind, name, p in sources:
        cases.append(accept_case(name, p) if kind == "accept" else refuse_case(name, p, reasons[name]))
        files[OUT / "vectors" / f"{name}.json"] = p.read_bytes()
    manifest = {"standard": "policy", "version": "v0", "page": "https://sharness.ai/code/standards/policy-v0/index.html",
                "oracle": {"implementation": "sharness-ai (Python)", "repository": "https://github.com/SHarness-AI/SHarness-AI__CLI",
                           "commit": cli_commit()},
                "hash": "sha256 over canonical JSON: keys sorted, no whitespace, UTF-8, integers only",
                "rule": "an implementation passes when it produces the hash of every accept case and refuses every refuse case",
                "counts": {"accept": sum(c["kind"] == "accept" for c in cases), "refuse": sum(c["kind"] == "refuse" for c in cases)},
                "cases": cases}
    return files, manifest


def main():
    check = "--check" in sys.argv
    files, manifest = build()
    existing = json.loads((OUT / "vectors.json").read_text()) if (OUT / "vectors.json").exists() else {}
    manifest["generated"] = existing.get("generated") if existing.get("cases") == manifest["cases"] else datetime.date.today().isoformat()
    if manifest["generated"] is None:
        manifest["generated"] = datetime.date.today().isoformat()
    text = json.dumps(manifest, indent=1, ensure_ascii=False) + "\n"
    stale = [p for p, b in files.items() if not p.exists() or p.read_bytes() != b]
    if not (OUT / "vectors.json").exists() or (OUT / "vectors.json").read_text() != text:
        stale.append(OUT / "vectors.json")
    if check:
        if stale:
            print("gen_vectors: stale (run python3 tools/gen_vectors.py):", file=sys.stderr)
            for p in stale:
                print(f"  ✗ {p.relative_to(ROOT).as_posix()}", file=sys.stderr)
            sys.exit(1)
    else:
        (OUT / "vectors").mkdir(parents=True, exist_ok=True)
        for p, b in files.items():
            if p in stale:
                p.write_bytes(b)
        (OUT / "vectors.json").write_text(text)
    print(f"gen_vectors: {manifest['counts']['accept']} accept, {manifest['counts']['refuse']} refuse "
          f"({'up to date' if check else 'generated'}; oracle {manifest['oracle']['commit']})")


if __name__ == "__main__":
    main()
