# TorchOS CP006.5 — Isolated QEMU PL011 transmit-stall QA

**Date:** 2026-11-14  
**Initial hosted lab test:** [Run 43645910038 — 2/2 PASS](https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43645910038)
**Official QEMU source SHA256:** `847346c1b82c1a54b2c38f6edbd85549edeb17430b7d4d3da12620e2962bc4f3` (verified and now pinned in workflow).
**Base development commit:** `b17f572c19bf54ca8df3a7805e272e3279467205`  
**Feature branch:** `feature/torchos-cp0065-qemu-pl011-tx-stall-20261114`  
**Issue:** [#11](https://github.com/mrfantest2/blackberry-remote-bridge/issues/11)  
**Scope:** GitHub-hosted, QEMU-only ARM research; **never** BlackBerry firmware.

## Initial blocker: stock QEMU 8.2.2 cannot naturally assert TXFF

Inspection of the **exact upstream v8.2.2** `hw/char/pl011.c` reveals:

- `UARTFR` reads return `s->flags`.
- The `PL011_FLAG_TXFF` constant appears in its definition and in `pl011_reset_fifo()`, which **clears** that bit.
- No path in that implementation sets `PL011_FLAG_TXFF` through natural transmit FIFO fill.
- Attempts to fill the TX backend or write `UARTFR` therefore do not create an authentic FIFO-full condition in that upstream model.

**Primary source:** https://github.com/qemu/qemu/blob/v8.2.2/hw/char/pl011.c

This means an upstream-QEMU-only test of a persistent transmit-full register condition is **unsupported by that device model**, not evidence of correct firmware behavior.

## Controlled solution: temporarily instrument the real emulated PL011 model

An isolated GitHub-hosted workflow downloads official QEMU 8.2.2 release source, verifies that the expected `UARTFR` implementation matches exactly, then modifies **only the test QEMU source** so a named process environment variable causes the **actual emulated PL011 register read** to return `TXFF=1`. It emits a single QEMU-side evidence marker. The generated emulator is disposed of after the hosted job; no compiled binary is published or uploaded.

- `torchos-emulator/ci/patch_qemu_pl011.py`: guarded test-only device-model patch.
- `.github/workflows/torchos-pl011-stall.yml`: GitHub-hosted QEMU source build; `contents: read`; no self-hosted runner.
- `torchos-emulator/ci/test_pl011_real_qemu.py`: two **actual running ARM guest** integration tests, using QMP to observe state.
- `torchos-emulator/src/commands.c`: a RAM-only dispatch counter, without any UART/host dependencies or CLI changes.

**Critical distinction:** This injects a **device-model fault** into a test-only QEMU, rather than mocking `uart_poll_read()` or modifying the TorchOS guest's UART HAL. It is **not** a stock QEMU TX FIFO overload and says nothing about the BlackBerry's physical UART.

## Acceptance design

| Gate | Expected evidence | Status |
|---|---|---|
| Upstream source analysis | Tagged v8.2.2 `PL011_FLAG_TXFF` cleared, not set | **PASS** |
| No modification to normal guest UART code | `hal_qemu_virt.c`, `uart_poll.c` and kernel untouched | **PASS (source diff)** |
| Existing 52 regressions | Existing hosted ARM QEMU workflow unaffected by the counter | **PASS** |
| Modified QEMU compiles | Dedicated hosted workflow built `qemu-system-arm` from the pinned QEMU 8.2.2 source | **PASS** |
| Normal model control | Guest console-ready; 19,635 MMIO reads, 284 writes, 1 command | **PASS** |
| TXFF forced in QEMU PL011 | PL011 source emits one injector marker; guest observes **65,536 MMIO reads**, **0 writes** | **PASS** |
| Bounded guest failure | `BOOT_UART_FAILED` + named WFI/halt PC, deadline enforced | **PASS** |
| No commands after failure | Guest dispatch telemetry is **0** | **PASS** |
| Independent PR-head and post-merge CI | Lab branch **2/2 PASS**, original regression **52/52 PASS**; PR-head and post-merge pending | **PARTIAL** |
| Physical Torch 9810 boot or recovery | No evidence generated; no physical work authorized | **BLOCKED / NO-GO** |

Normal-case and forced-stall cases are separate named Python unittests. A missing tool, failed QEMU load, absent PL011 trace marker, missing guest symbols, wrong ARM phase, infinite polling or crash **fails** the job. No false skips.

The original CP006.4 **52/52** hosted tests remain mandatory independently. The focused QEMU job has now passed **2/2**, for **54 successful tests** across the two separately executed suites. No skipped tests were reported in these runs; the final PR-head and post-merge checks remain acceptance gates.

## Physical-device limitations

The emulator's Cortex-A15 virtual board, fixed 128 MiB memory, QEMU PL011, synthetic fault flag, GDB/QMP diagnostics and kernel are not a board-support package for the original BlackBerry Torch 9810. Its exact silicon, signed boot interface, full stock firmware rollback and peripherals remain unresolved as documented in [G0.4](TORCHOS_G04_9810_REGULATORY_VARIANTS_AND_RECOVERY_20261114.md).

**No physical device, personal backup, BlackBerry firmware, OS 7 application, MASTER-PC or Steam Deck runner is involved.**
