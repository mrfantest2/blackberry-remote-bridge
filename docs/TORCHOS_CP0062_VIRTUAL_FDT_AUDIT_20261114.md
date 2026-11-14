# TorchOS CP006.2 — QEMU virtual Device Tree audit

**Scope:** Non-invasive, GitHub-hosted test of an **emulated** ARM `virt` hardware inventory.  
**Target:** QEMU Cortex-A15 / 128 MiB guest RAM, **not** BlackBerry Torch 9810 silicon.  
**Issue:** [#6](https://github.com/mrfantest2/blackberry-remote-bridge/issues/6).  
**Hardware decision:** Retail BlackBerry OS replacement remains **NO-GO**.

## Verified acceptance checks

The existing CP005/CP006.1 freestanding ELF cold-boots under a GitHub-hosted QEMU system-arm virtual machine. CP006.2 adds a bounded host-side Flattened Device Tree parser and validation against a fresh device tree produced by `qemu-system-arm -machine virt,dumpdtb=<path>`. This is a **QEMU-native** export, not a file read from the handset.

| Capability | Current evidence | Limit |
|---|---|---|
| ARMv7 research boot | Actual QEMU cold boot and UART tests | Not a complete operating system; no scheduler/MMU/userland |
| Serial output | QEMU PL011 virtual UART at `0x09000000` | Real BlackBerry UART controller not identified |
| RAM inventory | Generated virtual DTB contains 128 MiB RAM node | No proof of physical RAM layout |
| FDT parser | Bounded big-endian header/token/property decode | Host-only; cannot parse physical firmware |
| Rejection tests | Bad magic, truncation, malformed names/sections, oversized blobs, missing memory and UART | Does not imply a general-purpose driver framework |
| Guest-side discovery | **NOT implemented** | UART backend still uses an emulator-specific constant |
| BlackBerry screen/input/flash/power | **NOT implemented** | Board-level datasheets and drivers still unidentified |
| Boot ROM and recovery | **NOT verified** | Device must not be flashed |

## Boundary conditions

The parser limits incoming DTB data to **1 MiB**, enforces FDT section bounds and 4/8-byte alignment, limits structural nesting, node/property counts and property payloads, and rejects unknown tags, duplicate property names, inconsistent register cells and missing virtual UART/memory nodes. It recognizes **root-level** `arm,pl011` and `memory` properties for the known QEMU `virt` board; it does not implement nested bus address translation, interrupts, interrupts-parent, overlays or phandle resolution.

`make -C torchos-emulator test` runs QEMU boot/interactive tests and synthetic/device-tree rejection tests. `make -C torchos-emulator inspect-fdt` asks QEMU to generate a new **virtual** DTB, then emits a JSON report from the host-side parser. The report must not include user/device data or be mistaken for a physical hardware inventory. No generated artifacts are committed.

## Evidence and next engineering gate

- QEMU ARM virt machine documentation: https://www.qemu.org/docs/master/system/arm/virt
- Flattened Device Tree structure specification: https://devicetree-specification.readthedocs.io/en/stable/chapter5-flattened-format.html
- Existing exact-phone feasibility evidence: [CP004 audit](TORCHOS_CP004_FEASIBILITY_AUDIT_20261114.md)

**Next CP006.3:** In QEMU only, optionally pass guest device-tree metadata into the freestanding startup code, add validated guest-side discovery and choose an emulated UART base from a checked FDT path. Do not treat that as a Torch 9810 driver.

**Physical-device gates G0/G1/G2 remain blocked**: recovery image and restore procedure, independently supported retail 9810 boot chain, exact board identity, and hardware-specific drivers. No BlackBerry device, firmware, installation, reboot, USB probing, backups, Codex or self-hosted runner were used for this research checkpoint.
