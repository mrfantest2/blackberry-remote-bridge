# TorchOS CP006.2 — Independent ARM Research Monitor

**Status: off-device QEMU prototype, not a BlackBerry Torch 9810 image.**

This directory contains an original minimal **freestanding ARMv7 boot image**, written in assembly and C. It boots into an interactive UART console on QEMU's generic **ARM virt / Cortex-A15** machine. It does **not** execute BlackBerry OS 7 or require any BlackBerry proprietary components.

The QEMU launcher explicitly disables virtual networking with `-nic none`; this also avoids unnecessary guest NIC firmware dependencies in slim hosted runners.

CP006 moves virtual UART access behind a QEMU-only hardware abstraction. This is a source-code boundary, **not** a retail BlackBerry driver.

It is intentionally much smaller than a complete production OS: there is no kernel scheduler, MMU management, process isolation, filesystem, graphics/touch driver, battery driver, persistent notes, network or Linux userland. The local command interpreter accepts a small allowlist and does not execute host commands. It demonstrates an independently booting research monitor, not a finished OS.

## Prerequisites (off-device only)

Linux host with:
- GNU Make and Python 3
- ARM cross-toolchain: arm-none-eabi-gcc, arm-none-eabi-readelf
- qemu-system-arm with the generic ARM virt machine

GitHub Actions installs the compiler/emulator in a disposable GitHub-hosted runner. No personal self-hosted runner is used.

## Build and run

```sh
make -C torchos-emulator all
make -C torchos-emulator inspect
make -C torchos-emulator inspect-fdt  # QEMU-generated virtual DTB only
make -C torchos-emulator test
make -C torchos-emulator run
```

Boot console: `torch> `. Commands: `help`, `about`, `status`, `clear`, `history`, `notes`, `files`. CP006 adds bounded, **volatile RAM-only** `notes set <text>`, `notes show`, and `notes clear`. Notes vanish when QEMU restarts. `files` reports unsupported storage; diagnostics identify virtual rather than BlackBerry hardware.

## CP006.2: host-side QEMU device-tree inventory

The bounded `tools/fdt_inventory.py` parser validates the standard FDT header, section limits, node nesting, property offsets, enabled `arm,pl011` UART registers and the virtual memory node. The GitHub-hosted test generates a new device tree from **QEMU** using `-machine virt,dumpdtb=...`, checks that its PL011 address matches the current QEMU-only UART backend, and rejects malformed device-tree blobs.

This inspection happens **outside the booting ARM guest**. The guest still uses a QEMU-specific PL011 address. Guest-side DTB discovery and driver selection are a **separate future checkpoint**; no retail Torch 9810 board support has been demonstrated. The generated DTB, virtual RAM, and UART addresses must never be treated as real-phone hardware specifications.

### Safety and hardware limits

- **Never flash or install** the produced ELF, object files, or build outputs on any BlackBerry.
- QEMU **virt** is not a Torch 9810 hardware emulator. The emulator's Cortex-A15 CPU is not evidence for the Torch's exact CPU variant, despite both being 32-bit ARM families.
- ELF location `0x40100000` is deliberately chosen for QEMU virt RAM, away from the guest device tree. PL011 serial address `0x09000000` is an emulator-specific implementation assumption and must not be used for a physical handset.
- Any kernel/loader, recovery method, boot chain, display, touch, QWERTY, trackpad, NAND/eMMC and power support on the **retail Torch 9810** remain **unverified**.
- The original BlackBerry OS7 Java TorchOS app remains separate and unchanged.

Reference: [QEMU ARM virt board](https://www.qemu.org/docs/master/system/arm/virt); [CP004 feasibility gates](../docs/TORCHOS_CP004_FEASIBILITY_AUDIT_20261114.md).

**Gate:** Real hardware OS replacement remains **NO-GO**, regardless of success in QEMU.
