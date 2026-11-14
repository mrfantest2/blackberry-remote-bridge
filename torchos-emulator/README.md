# TorchOS CP006.4 — Independent ARM Research Monitor

**Status: off-device QEMU prototype, not a BlackBerry Torch 9810 image.**

This directory contains an original minimal **freestanding ARMv7 boot image**, written in assembly and C. It boots into an interactive UART console on QEMU's version-pinned **ARM virt-8.2 / Cortex-A15** machine. It does **not** execute BlackBerry OS 7 or require any BlackBerry proprietary components.

The QEMU launcher explicitly disables virtual networking with `-nic none`; this also avoids unnecessary guest NIC firmware dependencies in slim hosted runners.

CP006 moves virtual UART access behind a QEMU-only hardware abstraction. This is a source-code boundary, **not** a retail BlackBerry driver.

It is intentionally much smaller than a complete production OS: there is no kernel scheduler, MMU management, process isolation, filesystem, graphics/touch driver, battery driver, persistent notes, network or Linux userland. The local command interpreter accepts a small allowlist and does not execute host commands. It demonstrates an independently booting research monitor, not a finished OS.

## Prerequisites (off-device only)

Linux host with:
- GNU Make and Python 3
- ARM cross-toolchain: arm-none-eabi-gcc, arm-none-eabi-readelf
- qemu-system-arm with the ARM virt-8.2 machine (hosted runner currently reports QEMU 8.2.2)
- gdb-multiarch for paused-guest synthetic-DTB fault injection in hosted CI

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

The bounded `tools/fdt_inventory.py` parser validates the standard FDT header, section limits, node nesting, property offsets, enabled `arm,pl011` UART registers and the virtual memory node. The GitHub-hosted test generates a new device tree from **QEMU** using `-machine virt-8.2,dumpdtb=...`, checks that its PL011 address matches the current QEMU-only UART backend, and rejects malformed device-tree blobs.

This CP006.2 inspection happens **outside the booting ARM guest**. CP006.3 subsequently added independent guest-side DTB parsing. The serial MMIO base is now discovered inside the guest; only the QEMU virtual DTB RAM location and approved virtual MMIO window remain deliberate platform-specific assumptions. No retail Torch 9810 board support has been demonstrated. The generated DTB, virtual RAM, and UART addresses must never be treated as real-phone hardware specifications.

## CP006.3: guest-side virtual hardware discovery

The freestanding ARM guest now validates QEMU's **Flattened Device Tree** itself before accessing UART registers. Per the official [QEMU ARM virt bare-metal boot documentation](https://www.qemu.org/docs/master/system/arm/virt), the ELF boot's DTB resides at the start of virtual RAM (`0x40000000`); the RAM-base assumption is **QEMU-specific**, not a BlackBerry address.

A bounded, no-libc C parser validates header limits, structure/string offsets, node depths, root 2/2 address-size cells, one enabled root-level `arm,pl011` UART node and a virtual RAM node. The PL011 register base is read from the validated DTB, and MMIO is enabled **only after** validation succeeds. Malformed or missing device information fails closed before the monitor prints anything; no fallback to a fixed UART address exists.

The C parser is also compiled and tested on the host with malformed/synthetic DTBs and an actual QEMU-generated virtual DTB. Those host tests complement—not replace—real QEMU ELF cold-boot tests. Current virtual memory, UART, and CPU values must not be treated as evidence of BlackBerry hardware support. This remains an incomplete research monitor, not a production operating system.

## CP006.4: guest fault injection, memory invariants and console isolation

The kernel now initializes the validated virtual platform, then constructs a hardware-agnostic terminal:

- `src/hal_qemu_virt.c` and `src/uart_poll.c`: virtual UART initialization and finite TX polling. An unavailable/busy UART fails after a bounded budget; no scheduler or system timer is assumed.
- `src/console.c`: terminal transport, CR/LF editing, bounded input, safe rejection of non-printable input and prompt output via an injected byte callback.
- `src/commands.c`: offline command allowlist, eight-entry history, RAM-only notes, diagnostics and unsupported-file reporting. **No PL011 register references or host shell execution.**
- `src/kernel.c`: minimal boot state and dispatch loop, with named fail-closed halt on invalid DTB or UART transport failure.
- `src/guest_fdt.c`: strict 1 MiB guest DTB bounds, single enabled QEMU PL011, reserved-memory rejection, exact 128 MiB QEMU RAM layout and supported 2/2 root cell arrangement.
- `linker.ld`: a 1 MiB separation between DTB and ELF, plus linked image/BSS/16 KiB stack bounds within QEMU RAM.

**Actual guest fault evidence:** The hosted test launches paused QEMU `virt-8.2`, writes a synthetic DTB into `0x40000000` through its GDB interface, reads the bytes back, resumes the ARM guest and checks its boot-phase marker, MMIO read/write counters and named WFI halt PC through QMP. Thus the malformed-DTB scenarios execute **inside the guest**, not only in a host parser. The tests use bounded startup and execution checks and never attach to physical hardware.

Source: [QEMU GDB debugging](https://www.qemu.org/docs/master/system/gdb.html), [CP006.4 QA report](../docs/TORCHOS_CP0064_ENGINEERING_QA_20261114.md).

### Safety and hardware limits

- **Never flash or install** the produced ELF, object files, or build outputs on any BlackBerry.
- QEMU **virt** is not a Torch 9810 hardware emulator. The emulator's Cortex-A15 CPU is not evidence for the Torch's exact CPU variant, despite both being 32-bit ARM families.
- ELF location `0x40100000` is deliberately chosen for QEMU virt RAM, away from the guest device tree. The virtual PL011 serial address is discovered from a validated QEMU DTB; the **allowed QEMU-only MMIO range** and initial DTB RAM location remain hardcoded laboratory safeguards. Neither may be used for a physical handset.
- Any kernel/loader, recovery method, boot chain, display, touch, QWERTY, trackpad, NAND/eMMC and power support on the **retail Torch 9810** remain **unverified**.
- The original BlackBerry OS7 Java TorchOS app remains separate and unchanged.

Reference: [QEMU ARM virt board](https://www.qemu.org/docs/master/system/arm/virt); [CP004 feasibility gates](../docs/TORCHOS_CP004_FEASIBILITY_AUDIT_20261114.md).

**Gate:** Real hardware OS replacement remains **NO-GO**, regardless of success in QEMU.
