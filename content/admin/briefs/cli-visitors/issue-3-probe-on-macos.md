Rule followed: outreach §3.1; AGENTS.md §1 (the honest answer on the most common developer machine); the machines page ("macOS: refuses: no Landlock").

**Title:** `probe` and `run` on macOS: say exactly what is missing, in one line each · **Labels:** good first issue, docs

Landlock, seccomp and cgroups are Linux. On macOS `sharness-ai run` must refuse and run nothing, and `probe` must still print something useful: that there is no Landlock, no seccomp, no cgroups, no `memfd_secret`, and what that means for the reading line (the grant is everything, and nothing here can narrow it).

**Where to look:** `sharness_ai/probe.py` (the rows and the reading line) and the entry point of `run`; `tests/unit/` for tests that skip where Landlock is absent.

**What done looks like:**

- On macOS, `probe` prints the same rows as on Linux with `n/a (macOS: no Landlock)` and a reading line that says so; `--json` carries `"os": "darwin"` and nulls, not errors.
- `run` exits non-zero with one line: what is missing and that nothing was run.
- A test that runs on any OS, parametrised by a fake platform, so CI on Linux covers the macOS text.
- The experiments README's E01 and E03 rows gain "macOS: prints the gap; refuses" and the date you checked it on a real Mac, if you have one.
