# TorchOS CP006.3 — Guest-side FDT verification and virtual UART initialization

**Date:** 2026-11-14  
**Repository:** `mrfantest2/blackberry-remote-bridge`  
**Target:** QEMU ARM `virt` and Cortex-A15 **only**  
**Physical BlackBerry Torch 9810:** **NO-GO** for independent boot, flashing, installation or hardware probing.

## Purpose and verified design

CP006.2 performed *host-side* inspection of QEMU-generated device trees. CP006.3 goes further: the **booting freestanding ARM guest** parses the FDT and initializes its virtual UART **only after** validating the device information. There is no fallback to a hardcoded PL011 UART address in the driver.

Per QEMU's official ARM virt documentation, for an **ELF bare-metal `-kernel` image**, the guest DTB lives at the start of QEMU virtual RAM, `0x40000000`. This is not the Linux image protocol (where 32-bit ARM uses register `r2`). The linker places the research ELF at `0x40100000`, leaving the first 1 MiB of emulated RAM for the device tree. The QEMU-specific memory location is an explicitly limited laboratory assumption.

**Authoritative source:** https://www.qemu.org/docs/master/system/arm/virt

## Code delivered

| Module | Responsibility |
|---|---|
| `torchos-emulator/src/guest_fdt.h` | Small read-only parser contract, max 1 MiB |
| `torchos-emulator/src/guest_fdt.c` | Freestanding C implementation for bounded FDT header, strings, nodes, properties, root 2/2 cell settings and root-level UART/memory records |
| `torchos-emulator/src/hal_qemu_virt.c` | Initialize PL011 virtual UART from validated DTB; no MMIO if validation fails |
| `torchos-emulator/src/hal.h` | Expose `hal_init()` before console operations |
| `torchos-emulator/src/kernel.c` | Boot fails closed before any console I/O if `hal_init()` fails |
| `torchos-emulator/tests/guest_fdt_harness.c` | Standalone host parser harness for test vectors |
| `torchos-emulator/tests/test_guest_fdt.py` | Good/bad FDT tests and real QEMU-generated DTB compatibility |
| `torchos-emulator/tests/test_qemu_boot.py` | Cold-boot command test explicitly confirms guest FDT validation and UART discovery |

## Validation gates

- ARM ELF compiled and linked without proprietary BlackBerry libraries.
- Actual QEMU virtual ARM cold boot and terminal work.
- Guest status identifies its UART as discovered from the QEMU FDT.
- Host-compiled *same C parser* accepts valid minimal FDT and the actual QEMU `virt,dumpdtb` output.
- Tested ability to read a **different virtual UART base** from synthetic FDT (not a hardcoded address).
- Rejects missing UART, missing RAM, bad magic, truncation, oversized blob and RAM-mapped fake UART.
- Malformed FDT prevents setting UART MMIO base; the guest enters a fail-closed state with no serial output.
- Github Actions hosted runner only; no self-hosted hardware, Codex or physical handset access.
- Existing 14 CP006.2/QEMU tests remain included; 9 additional guest-parser tests bring the suite to **23**.

## Explicit limitations

This is a **minimal research monitor**, **not yet a full OS**. It has no process scheduler, MMU management, isolation, filesystem, framebuffer or touchscreen driver. UART, memory and CPU are QEMU-simulated. The FDT implementation supports only the root 2/2-cell arrangement and direct root children used in this QEMU configuration; it does **not** implement generic bus translations, phandles, interrupt routing, arbitrary devices or secure-boot verification.

### Real BlackBerry Torch 9810 blockers (unchanged)

- No verified alternative independent boot path for **retail** Torch 9810.
- No supported physical Torch 9810 device tree or board-driver matrix.
- No verified complete firmware/bootloader recovery image and rollback for the owner's handset.
- Existing OS7 Java app remains intact and separate.

**Decision:** GO for off-device QA and further virtual software architecture; **NO-GO** for device installation or firmware replacement. Keep Issue #3 and Issue #6 open until their real hardware acceptance evidence is satisfied.
