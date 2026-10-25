# Linux in the browser: how much of the harness can run in a tab?

> **Status: researched, not yet built.** Dinis Cruz's question of 25 October 2026: is there a way to run Linux in a browser and use it to verify and demonstrate this, and how much of the harness could run there? The answer, from the primary sources read that day (as of 25 Oct 2026): a real Linux kernel runs in a tab today, Landlock has no architecture dependency, and Alpine's 32-bit kernel ships with it enabled, so `sharness-ai hello` in a browser is a build, not a research problem. The rest of the harness (uids, cgroups, mutual TLS on loopback) runs in the same guest; what a browser can never show is listed at the end. This is experiment E09 on the [ladder](../experiments/index.md).

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

## 3. The recommended build: `hello` in a tab on sharness.ai

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

## 6. Not verified

- That Alpine 3.23's i386 kernel reports ABI 7 under v86: the config says Landlock is on and 6.18 implies ABI 7, but nothing was booted for this page.
- Boot time and speed of v86 with Alpine and Python; no published figures.
- `memfd_secret` on 32-bit with PAE: the status of the July 2026 fix.
- Whether v86 needs SharedArrayBuffer: inferred from its package and build instructions, not stated by the project.
- How CheerpX answers an unknown syscall.
- The licence of the current JSLinux x86_64 web build; the JSLinux kernel inspection relies on the absence of strings in the image, not on a config file.

Sources (all read 25 Oct 2026): the kernel's [Landlock documentation](https://docs.kernel.org/userspace-api/landlock.html), [`landlock(7)`](https://man7.org/linux/man-pages/man7/landlock.7.html), [`memfd_secret(2)`](https://man7.org/linux/man-pages/man2/memfd_secret.2.html), `security/landlock/Kconfig`, the x86 and generic syscall tables and `mm/Kconfig` in [torvalds/linux](https://github.com/torvalds/linux); [v86](https://github.com/copy/v86) (README, `docs/linux-9p-image.md`, `docs/networking.md`, `tools/docker/alpine`), the `v86` npm package 0.5.472; Alpine aports `main/linux-lts/virt.x86.config` and `main/python3/APKBUILD` for 3.21 to 3.23; Debian's 6.1.190 kernel config; [JSLinux](https://bellard.org/jslinux/) and [TinyEMU](https://bellard.org/tinyemu/); [CheerpX](https://cheerpx.io/docs/licensing) and [WebVM](https://github.com/leaningtech/webvm); [container2wasm](https://github.com/ktock/container2wasm) and its kernel configs; [qemu-wasm](https://github.com/ktock/qemu-wasm); [Pyodide](https://pyodide.org/en/stable/usage/wasm-constraints.html); the [Wasmer JS SDK](https://docs.wasmer.io/sdk/wasmer-js); [browser_wasi_shim](https://github.com/bjorn3/browser_wasi_shim); [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
