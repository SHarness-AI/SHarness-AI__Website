# What is in this folder, and under which licences

The E09 page: a real Linux kernel in a browser tab running `sharness-ai`. Built by
[`experiments/browser/build_guest.py`](https://github.com/SHarness-AI/SHarness-AI__CLI/blob/dev/experiments/browser/build_guest.py)
in the CLI repository on 25 Oct 2026; rebuilt only deliberately, with the date.

| File | What | From | Licence |
|---|---|---|---|
| `libv86.mjs`, `v86.wasm` | v86, an x86 emulator in WebAssembly, 0.5.472 | the `v86` npm package | BSD-2-Clause ([LICENSE-v86.txt](LICENSE-v86.txt)) |
| `seabios.bin`, `vgabios.bin` | SeaBIOS and its VGA BIOS, as shipped by v86 | [copy/v86](https://github.com/copy/v86/tree/master/bios) | LGPL-3.0 (SeaBIOS) |
| `vmlinuz-virt` | Alpine Linux 3.23 x86 `linux-virt` 6.18.58-r0 | [dl-cdn.alpinelinux.org](https://dl-cdn.alpinelinux.org/alpine/v3.23/main/x86/) | GPL-2.0; source in [aports](https://gitlab.alpinelinux.org/alpine/aports/-/tree/3.23-stable/main/linux-lts) |
| `initramfs.cpio.gz` | the guest: Alpine 3.23 x86 packages (busybox, musl, python3 and their libraries; the list with versions is `PACKAGES` in `build_guest.py`), the `sharness_ai` package and the example policies, `/init` | Alpine packages from the same CDN; `sharness_ai` from the CLI repository | each package its own (GPL-2.0 busybox, MIT musl, PSF Python, Apache-2.0 OpenSSL, …); `sharness_ai` as the CLI repository |
| `index.html` | this site's page | the CLI repository's `page.html`, with this site's head | as this site |

Sources for every GPL binary here are the Alpine aports at the versions named; nothing was modified.
