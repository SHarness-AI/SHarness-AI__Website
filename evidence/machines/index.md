# hello on your machine: every reported run

> **The ask, as of 25 Oct 2026.** A claim that the kernel enforces a policy is only as good as the kernels it was checked on. This page lists every run of `sharness-ai hello` that has been reported, including the ones that did not hold. So far every row is ours; yours is next.

## How to report

```
pip install git+https://github.com/SHarness-AI/SHarness-AI__CLI@dev
sharness-ai hello --json
```

Open [a hello report](https://github.com/SHarness-AI/SHarness-AI__CLI/issues/new?template=hello-report.yml) on GitHub and paste the JSON; add anything odd you saw. The JSON carries the kernel version, the Landlock ABI, the effective uid, the Python version, the policy hash and each probe's result. It carries no hostnames, usernames or paths outside the working directory's name, and `probe` prints the names of proxy variables, never their values. Reports are added here by hand, with the issue linked, in the order they arrive.

The most useful report is a refusal that did not happen: a probe that says `allowed` where the policy said `refused`. That is either a kernel without the feature (the result still tells us which), or a bug, and both go on this page.

## Reported runs

| Date | Where | Kernel | Landlock ABI | uid | Python | Result | Notes |
|---|---|---|---|---|---|---|---|
| 24 Oct 2026 | a Claude Code cloud session (Ubuntu 24.04) | 6.18.44 | 7 | 0 | 3.13 | 5 of 5 | before the memory probe existed; [Evidence §9](../index.md#9-the-first-experiments-run-by-the-cli) |
| 25 Oct 2026 | the same kind of session | 6.18.44 | 7 | 0 | 3.13 | 6 of 6 | cgroups v1 with a unified mount; the 400 MiB probe raised `MemoryError` |
| 25 Oct 2026 | Dinis Cruz's Chrome, the [E09 page](../../code/browser/demo/index.html) | 6.18.58 (Alpine, i686, emulated) | 7 | 0 | 3.12 | 6 of 6 | 28.5 s to the result by the page's clock |
| 25 Oct 2026 | headless Chromium 153, the same page | 6.18.58 (emulated) | 7 | 0 | 3.12 | 6 of 6 | 75.9 s; no page errors |
| 25 Oct 2026 | Node 22, v86 without a browser | 6.18.58 (emulated) | 7 | 0 | 3.12 | 6 of 6 | 58.0 s |
| 25 Oct 2026 | chroot into the guest's files on the host kernel | 6.18.44 | 7 | 0 | 3.12 (i386 build) | 6 of 6 | the 32-bit binaries drive the host's Landlock through the i386 syscall table |
| 25 Oct 2026 | Pyodide 314 (Python in WebAssembly) | none | none | n/a | 3.14 | refused, exit 126 | correct: no kernel, no processes, nothing to confine |

Every row above was run by the project. Rows from other people will say so, with the issue linked.

## Not yet reported, and what we expect

| Where | Expected | Why it matters |
|---|---|---|
| a laptop as a normal user, Ubuntu 24.04 | read, writes, hash and memory hold; `net` holds by Landlock's port rule, since an unprivileged user namespace may be refused | the first run with no root at all |
| Debian 12 (kernel 6.1, Landlock ABI 2) | files hold; no TCP rules, so `net` depends on the namespace | the oldest common kernel |
| Fedora, Arch (recent kernels) | 6 of 6 | breadth |
| WSL2 | unknown: Microsoft's kernel config decides whether Landlock is on | many Windows developers run agents here |
| macOS | refuses: no Landlock; `run` says so and runs nothing | the honest answer on the most common developer machine |
| a container without `CAP_SYS_ADMIN` | files hold; the namespace is refused and Landlock's port rule takes over | where agents actually run |

If you have one of these, you have the most valuable report on the list.
