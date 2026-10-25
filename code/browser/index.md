# Linux in the browser: the harness under a second kernel

> **Status: built and measured, 25 Oct 2026.** Dinis Cruz's question of 25 October 2026: can Linux run in a browser and verify this, how much of the harness runs there, and can the same Linux run in the agent's own environment, so there are two kinds of test? Yes to all three, as of 25 Oct 2026: one guest (Alpine 3.23 for 32-bit x86 with Alpine's `linux-virt` kernel, which ships Landlock, Python 3.12 and the `sharness-ai` package) boots under [v86](https://github.com/copy/v86) in **Node** and in a **browser tab**, and the same binaries run on the **host kernel** through chroot. `sharness-ai hello` held 6 of 6 in all three. This is experiment E09 on the [ladder](../experiments/index.md); the code is [`experiments/browser/`](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/experiments/browser) in the CLI repository, and the page itself is [here](demo/index.html).

## 0. What was built and what it showed

| Form | Kernel | CPU | What it is for |
|---|---|---|---|
| **Node** (`npm run node`) | the guest's, Linux 6.18.58 i686 | emulated by v86, x86 in WebAssembly | the second kernel in any agent session or CI job, no browser, no root |
| **browser** (`npm run browser`, or [open the page](demo/index.html)) | the guest's | emulated by v86, in the tab | the same, for anyone with a browser and nothing installed |
| **chroot** (`sudo npm run native`) | the **host's**, through the i386 syscall table | the real one | the guest's 32-bit binaries driving the host's Landlock: same code, no emulator |

Measured 25 Oct 2026 in one Claude Code cloud session (Ubuntu 24.04, Linux 6.18.44 x86_64, uid 0; Node 22.22; Chromium 153 headless through Playwright; v86 0.5.472; guest `linux-virt` 6.18.58-0-virt, Python 3.12.15), each form run once, alone, <span class="asof">as of 25 Oct 2026</span>:

| Form | The guest reports | `hello` (E04) | `run` (E03) | Wall clock to `hello`'s exit / to power-off |
|---|---|---|---|---|
| Node | `landlock: Up and running.`; `probe`: Landlock ABI 7, `memfd_secret` yes, cgroups v2 | 6 of 6 held | under P1 (port 443 only): 443 `ENETUNREACH`, allowed by the policy and failing for want of a network backend; 80 `EACCES`. Under P2 (read-only): write refused, read allowed. Under P0: a 200 MiB allocation refused by the 64 MiB cap | 58.0 s / 74.6 s |
| browser | the same | 6 of 6 held | the same | 75.9 s / 95.9 s; `crossOriginIsolated false`, no `SharedArrayBuffer`, no page errors |
| chroot | host kernel 6.18.44, Landlock ABI 7; the binaries' ELF `e_machine` is `0x0003`, i386 | 6 of 6 held | not run in this form | under 2 s |

The seven [example policies](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/policies/README.md) check and hash in the guest to the same values as on the host: the second kernel agrees with the first on the one value the person supplies.

What this is and is not. The same syscalls (444 to 446 for Landlock, `unshare`, the rlimits, the cgroup files) on a second kernel, on an emulated CPU, applied by a process to its child: a Boundary for the child, a Setting for the page's guest. The timings are of a single emulated core and say nothing about the harness's cost on real hardware; they are here so a reader knows what the page will do. Nothing in a tab says anything about the host. And the guest has no network backend, so the port-443 probe shows *the policy allowed it* (the error is the network's, `ENETUNREACH`, not Landlock's `EACCES`) rather than a connection.

Three things learned building it:

- **The ELF interpreter must be executable.** Under `allow-https-example` (exec `/usr` and `/bin`) the guest could not start `python3` at all: `execve` failed with `Permission denied` because Alpine's loader is `/lib/ld-musl-i386.so.1`. On the host a merged `/usr` hides this (`/lib64` is a link into `/usr`). The profiles P0 to P4 list `/lib` and `/lib64` as executable; `translate` will have to carry the same rule to every target.
- **No special headers.** v86 ran from a plain static server with no COOP or COEP headers, with `crossOriginIsolated false` and no `SharedArrayBuffer`; the earlier research note's inference that it might need them was wrong. The page is seven static files, 25 MB, and fits GitHub Pages.
- **The console is bytes.** The serial line hands over one byte at a time; `hello`'s `✔` is three of them. The runners decode with a streaming UTF-8 decoder, one byte per call.

The build ([`build_guest.py`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/browser/build_guest.py), standard library only) fetches the pinned Alpine packages, unpacks them with `tarfile`, adds the package and the policies, writes the initramfs with its own cpio writer and assembles the page; a rebuild from the cache takes seconds. v86 is the one dependency, pinned by version, and lives only under `experiments/browser/`. Not yet: a network backend (v86 can proxy over `fetch` or a WebSocket), so the 443 probe can connect without a policy and fail with `EACCES` under one; a booted-state snapshot so the page opens in seconds; a non-root user in the guest; a kernel without Landlock as the negative control.

The rest of this page is the research of the same morning that chose this build, kept as written (as of 25 Oct 2026), with what it got right and the one inference it got wrong.

## 1. What the guest has to offer

`hello` and `run` call Landlock through syscalls 444, 445 and 446, probe `memfd_secret` as 447, and use `unshare` for the empty network namespace. So the guest needs a real Linux kernel of 6.7 or later (TCP rules, ABI 4), ideally 6.15 or later (ABI 7, the same as the measured environment), built with `CONFIG_SECURITY_LANDLOCK=y` and `landlock` in its LSM list, user and network namespaces, cgroups, and Python 3.11 or later with `ctypes`.

Three kernel facts decide the rest, all from the kernel's own sources:

- **Landlock is architecture-independent.** `security/landlock/Kconfig` depends only on `SECURITY`; the three syscalls are in every syscall table, including the 32-bit x86 one (`444 i386 landlock_create_ruleset`). The numbers the CLI uses are the same on i386 and x86_64.
- **The ABI follows the kernel version:** 1 = 5.13, 2 = 5.19, 3 = 6.2, 4 = 6.7, 5 = 6.10, 6 = 6.12, 7 = 6.15, 8 = 7.0, 9 = 7.1 (`landlock(7)`).
- **`memfd_secret` is available on i386 in principle** (`SECRETMEM` depends on `ARCH_HAS_SET_DIRECT_MAP`, selected by x86, arm64, riscv, s390 and loongarch), with one caveat: a July 2026 kernel thread reports a crash with highmem folios on 32-bit x86, and Alpine's x86 kernel uses PAE. Not verified whether the fix is merged.

## 2. The options

| Option | Real kernel? | Arch | Kernel shipped | Landlock | seccomp, namespaces, cgroups | Python | Licence | Cost to embed on this site |
|---|---|---|---|---|---|---|---|---|
| **v86 + Alpine 3.23 x86** (own image) | yes | i386 only | Alpine `linux-virt` 6.18.58 | **yes**: `CONFIG_SECURITY_LANDLOCK=y`, `landlock` first in `CONFIG_LSM`; ABI 7 expected | yes (`USER_NS`, memcg, pids, freezer) | 3.12.15 (an 8.3 MB apk) | BSD-2 (v86), distro licences | 2.4 MB runtime, no special headers, 30 to 60 MB of kernel and rootfs fetched lazily over 9p; fits GitHub Pages |
| v86 with the copy.sh Buildroot image | yes | i386 | 6.8.12 | **no** (no Landlock string in the kernel) | partly | no | BSD-2 | same; a useful negative control |
| v86 + Debian bookworm i386 | yes | i386 | 6.1.190 | ABI 2 only: no TCP rules | yes | 3.11.2 | BSD-2 | larger image |
| JSLinux (TinyEMU) x86_64 | yes | x86_64 | 6.19.3, Bellard's build | **no** (`CONFIG_SECURITY` appears off) | seccomp yes | not shown | TinyEMU MIT; the web build's terms unstated | not redistributable with confidence |
| WebVM / CheerpX 1.2.8 | **no**: syscall emulation, no kernel | 32-bit user mode | none | no | no | 3.7 (Debian buster) | engine free only for individuals and FOSS; no self-hosting | COOP/COEP headers, 600 MB streamed disk |
| container2wasm 0.8.4 (default) | yes (Bochs or TinyEMU) | x86_64, riscv64 | 6.1 | **no** (`CONFIG_SECURITY` unset in its config) | yes | any OCI image | Apache-2.0 plus LGPL Bochs | 150 to 200 MB per visitor; needs a service worker for the headers on GitHub Pages |
| container2wasm with a forked kernel ≥ 6.15 | yes | x86_64 | custom | yes (expected) | yes | any | as above | same, plus a kernel rebuild |
| qemu-wasm (QEMU 8.2) | yes | x86_64, aarch64, riscv64 | yours | depends on your kernel | yes | yours | GPL/LGPL | pthreads, SharedArrayBuffer, experimental |
| Pyodide 314 | no | Wasm | none | no | no | 3.14.2 | MPL-2.0 | one script tag; no `ctypes` syscalls at all |
| Wasmer SDK 0.19 (WASIX) | no | Wasm | none | no | no | 3.13.20 | modified MIT | COOP/COEP |
| browser_wasi_shim, jco | no | Wasm | none | capabilities instead | no | a CPython-wasi build | MIT/Apache | tiny |

The split is clean. Anything without a kernel (WebVM, Pyodide, Wasmer, WASI) cannot run Landlock, seccomp, namespaces or cgroups: there is no process in the Linux sense to confine. Anything with a kernel can, if the kernel was built with them, and of those only v86 with Alpine's kernel has Landlock on by default, runs without special response headers, and has a licence that allows self-hosting on a static site.

## 3. The recommended build: `hello` in a tab on sharness.ai (as researched; §0 is what was built)

1. **Build the guest** with v86's own `tools/docker/alpine`, moving the base image from `i386/alpine:3.21.0` to `i386/alpine:3.23` (kernel 6.18.58, Landlock ABI 7, the same as the measured workspace) and adding `python3` and the `sharness_ai` package (no dependencies) to the rootfs. Keep the 9p initramfs. Snapshot the booted state with `build-state.js` so the page opens in seconds, not after a full boot.
2. **Check inside the guest:** `dmesg | grep landlock` must say "Up and running"; `sharness-ai probe` must report Landlock ABI 7, user namespaces, cgroups. Add a non-root user so the network probe exercises Landlock's TCP rule (as root, `hello` takes the network-namespace path instead).
3. **Make the network probe honest.** With no network backend in v86, a connect fails anyway. Either turn on the `fetch` or `wisp` backend and show the probe succeed without a policy and fail with `EACCES` under one, or print the errno so the refusal is attributable to Landlock. Run the same page against the copy.sh Buildroot kernel as a negative control: no Landlock, `landlock_restrict_self` returns `ENOSYS`.
4. **The page:** `libv86.mjs` and `v86.wasm` from the `v86` npm package, pinned (0.5.472 as of 25 Oct 2026, 2.4 MB, self-hosted), the BIOS files, Alpine's kernel and initramfs, the 9p filesystem index and files, and the state snapshot; an xterm.js console; `sharness-ai hello` run on the serial line at boot. Static files only; the large ones can sit on a CORS-enabled CDN, as copy.sh's do.
5. **Label the result** on Evidence as measured in "v86 0.5.472, Alpine 3.23 x86, Linux 6.18.58, browser and date", and say what it is: the same kernel code paths, on an emulated 32-bit CPU, applied by a process to its child. A Boundary for the child, a Setting for the page's guest.

A 64-bit route for later: fork container2wasm, raise its kernel to 6.15 or later with `CONFIG_SECURITY=y` and `CONFIG_SECURITY_LANDLOCK=y`, convert `python:3.12-alpine` plus `sharness-ai`, host with a service worker for the headers. It costs 150 to 200 MB per visitor and runs slower, but it is x86_64 and keeps `memfd_secret` clear of the 32-bit caveat.

## 4. How much of the harness can run there

| Part | In the v86 guest | Honest label |
|---|---|---|
| E01 `probe`, E02 `policy hash` | yes | the same code |
| E03 `run`, E04 `hello`: Landlock files and ports, `no_new_privs`, the caps, the network namespace | yes, on the guest kernel | the same syscalls, emulated CPU |
| separate uids per component, cgroups, the freezer | yes, inside the guest | real inside the guest; says nothing about the host |
| mutual TLS over loopback between components (E05), the KMS protocol (E08), the process-tree proof of concept (E06) | yes: all of it is processes and loopback sockets | a full harness in a tab is possible |
| `memfd_secret` | kernel logic runs; the physical property it provides is meaningless against a real host | demonstrate, do not claim |
| timing figures (3.2 ms handshakes, 0.6 s `hello`) | no: single emulated core | never quote browser timings as measurements |
| real egress, hardware keys, TPM, x86_64-only behaviour, anything about the host | no | out of scope |

## 5. The WASI variant, for what it can show

Pyodide or a WASI build can show the policy pipeline without the kernel: hashing (the [mockup](../../explain/mockups/policy-hash.html) does this already), validation, and a simulator of "what this policy would allow". With a WASI runtime, `files.read` maps to read-only preopened directories, `files.write` to writable ones, `network: "none"` to no sockets at all; `exec`, `no_new_privs` and scoping have no equivalent. It demonstrates deny-by-default at the host layer and the shape of the policy, with the JavaScript host as the enforcer: a Boundary for the guest, a Setting for the page. It is a different thing from the kernel demo and must be labelled as one.

## 6. Not verified when the research was written, and since

- ~~That Alpine 3.23's i386 kernel reports ABI 7 under v86~~: **verified 25 Oct 2026**, ABI 7, `landlock: Up and running.` in the guest's `dmesg` (§0).
- ~~Boot time and speed of v86 with Alpine and Python~~: **measured 25 Oct 2026** (§0).
- `memfd_secret` on 32-bit with PAE: the status of the July 2026 fix.
- ~~Whether v86 needs SharedArrayBuffer~~: **it does not** (25 Oct 2026): the page ran with `crossOriginIsolated false` and no `SharedArrayBuffer`.
- How CheerpX answers an unknown syscall.
- The licence of the current JSLinux x86_64 web build; the JSLinux kernel inspection relies on the absence of strings in the image, not on a config file.

Sources (all read 25 Oct 2026): the kernel's [Landlock documentation](https://docs.kernel.org/userspace-api/landlock.html), [`landlock(7)`](https://man7.org/linux/man-pages/man7/landlock.7.html), [`memfd_secret(2)`](https://man7.org/linux/man-pages/man2/memfd_secret.2.html), `security/landlock/Kconfig`, the x86 and generic syscall tables and `mm/Kconfig` in [torvalds/linux](https://github.com/torvalds/linux); [v86](https://github.com/copy/v86) (README, `docs/linux-9p-image.md`, `docs/networking.md`, `tools/docker/alpine`), the `v86` npm package 0.5.472; Alpine aports `main/linux-lts/virt.x86.config` and `main/python3/APKBUILD` for 3.21 to 3.23; Debian's 6.1.190 kernel config; [JSLinux](https://bellard.org/jslinux/) and [TinyEMU](https://bellard.org/tinyemu/); [CheerpX](https://cheerpx.io/docs/licensing) and [WebVM](https://github.com/leaningtech/webvm); [container2wasm](https://github.com/ktock/container2wasm) and its kernel configs; [qemu-wasm](https://github.com/ktock/qemu-wasm); [Pyodide](https://pyodide.org/en/stable/usage/wasm-constraints.html); the [Wasmer JS SDK](https://docs.wasmer.io/sdk/wasmer-js); [browser_wasi_shim](https://github.com/bjorn3/browser_wasi_shim); [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
