# TorchOS CP006.4 — Engineering QA and guest fault-injection report

**Date:** November 14, 2026  
**Target:** Standalone freestanding ARMv7 **QEMU `virt-8.2` / Cortex-A15** research monitor.  
**Repository:** `mrfantest2/blackberry-remote-bridge`  
**Starting accepted CP006.3 SHA:** `947267a9cc213e615b23db9eab0df244582db927`  
**Development base:** `feat/torchos-native-shell-20261114`  
**CP006.4 branch:** `feature/torchos-cp0064-guest-fault-hal-console-20261114`  
**Verified hosted run:** [52/52 PASS — GitHub Actions run 43641108167](https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43641108167)  
**Runner QEMU:** 8.2.2 (Ubuntu 24.04 GitHub-hosted, Debian package `1:8.2.2+ds-0ubuntu1.18`). Board machine type explicitly pinned to `virt-8.2`.

**Verdict:** CP006.4 functional acceptance **PASS** for the QEMU-only scope, subject to final PR-head and post-merge CI. **Real retail BlackBerry Torch 9810 boot remains NO-GO.**

## A. GitHub — PASS pending PR acceptance

This continues the original repository; all changes are isolated to `torchos-emulator/**` and its existing GitHub Actions workflow. The `main` branch, the original BlackBerry OS7 Java application and S25Hub remain unchanged. No independent replacement app was created.

Code review of the branch diff against the accepted CP006.3 SHA lists **24 text-only source/workflow/test files**, with **zero** additions of `.elf`, `.bin`, `.o`, `.cod`, proprietary files, persistent credentials or generated build artifacts. Regex scans of the diff found zero GitHub access-token patterns, private-key headers and nontrivial quoted credential assignments. This is a pattern review, not a claim that machine scanning can guarantee secret absence.

The PR number, final merged SHA and post-merge CI must be recorded only after GitHub independently confirms them.

## B. Actual ARM guest fault injection — PASS

Previous CP006.3 negative tests exercised the C parser on the host. CP006.4 now checks the **guest's actual failure path**:

1. QEMU boots with the real `torchos.elf` and `-S`, pausing the CPU before the first instruction.
2. A GitHub-hosted `gdb-multiarch` client overwrites the QEMU-generated DTB region at **virtual guest RAM `0x40000000`** with a synthetic test DTB. It reads the bytes back from the virtual machine and checks exact equality **before** allowing execution.
3. QMP `cont` resumes the actual ARM guest, which executes `hal_init()` and the **same freestanding guest C FDT parser** used by the production QEMU image.
4. QMP examines the named `cp064_boot_phase` marker. On rejection, it also checks both `cp064_mmio_reads` and `cp064_mmio_writes` are **zero**, and confirms the ARM `R15` instruction pointer is in the named fail-closed `cp064_halt` loop.
5. Failure to load QEMU, deliver the DTB, read it back, reach a valid boot phase or complete within bounded startup/test time **fails the test**. Silence alone is never counted as success.

**Evidence:** A valid injected DTB boots into the console, enabling UART MMIO; a bad magic header and **20 individually named invalid guest FDT cases** reach a verified fail-closed state before any instrumented UART MMIO access.

The 20 named cases include bad magic, declared-length truncation, oversized length, missing UART/RAM, UART mapped in RAM, an MMIO region that crosses the allowed boundary, duplicate UARTs, disabled UART, invalid root address/size cells, malformed structure/string offsets, invalid property length, excessive node depth, unsupported RAM base/size, unsupported address width, root reserved-memory node and a nonempty reservation map.

This makes no assertion about **physical** BlackBerry MMIO or fault injection.

## C. Guest memory integrity — PASS for validated QEMU configuration

- The FDT parser caps accessible guest bytes to **1 MiB**, bounds reads by the header's total size, validates section offsets, alignment and non-overlap, and rejects malformed tokens, unsupported root 2/2 address/size-cell layouts, duplicate or disabled serial nodes and malformed register records.
- Unsupported/ambiguous **FDT memory reservation entries** and `/reserved-memory` are explicitly rejected (the monitor does **not** implement a full reservation allocator).
- A single virtual memory node must specify exactly **`0x40000000` + 128 MiB**. Other layouts fail before virtual UART access.
- UART base and entire extent must be aligned, lie within the **QEMU-only approved MMIO region**, and not overflow address arithmetic.
- The original linker places the ARM executable at `0x40100000`, above the **1 MiB DTB-only region**. Linker assertions and runtime validation check image, BSS and a **16 KiB stack** lie entirely within the declared virtual RAM. Five tests verify linked symbol order/bounds, separated FDT and ELF regions and fault markers inside BSS.
- 32-bit unsupported upper address/size cells fail closed; the parser has no implicit 64-bit address truncation.

The parser is deliberately narrow. It does not provide general bus translation, overlays, phandle resolution, nested-driver discovery, a memory allocator or MMU isolation.

## D. Bounded UART polling — PASS for host-simulated faults, PARTIAL for actual guest stalls

- Removed the unbounded `while (TXFF)` loop from the actual QEMU HAL.
- `uart_poll_send()` permits a finite polling budget of **65,536** register reads per character. Exhaustion returns an error and disables future UART access; the kernel enters a named fault stop rather than silently spinning in the transmitter.
- Pure C mock tests verify pre-init denial (zero MMIO callbacks), ready-after-three-polls success, permanent TX busy capped at seven reads, RX-empty nonblocking behavior, RX data, and a zero-budget rejection.
- Regular QEMU cold boots and serial commands continue to pass.

**Not verified:** Artificially forcing the **real emulated PL011 device's** TX FIFO to remain full inside a running guest. Only a host-side mock simulates that failure.

## E. Console/command architecture — PASS

The kernel now initializes hardware, binds console callbacks, binds command callbacks and runs the lightweight event loop. `console.c` owns transport, 63-byte bounded input, nonprintable rejection, editing and CR/LF. `commands.c` owns offline command allowlist, eight-entry history and volatile notes. `uart_poll.c` owns testable register-poll policy; `hal_qemu_virt.c` remains the only code which touches virtual PL011 registers.

The command processor **never directly references register addresses**, never invokes a host shell and requires no scheduler, operating-system service, persistent storage or network. Independent host mock tests run the console/command processor without QEMU UART or board access.

## F. Regression — PASS

Existing command strings and behavior are preserved: `help`, `about`, `status`, `clear`, `history`, `notes`, `notes set`, `notes show`, `notes clear` and `files`. The files command continues to state there is **no filesystem mounted**. The note is RAM-only and vanishes on a fresh QEMU boot. Input bounds and nonprintable rejection remain tested.

## G. Independent GitHub Actions — PASS

**Verified** run: https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43641108167

- Executed: **52 tests**.
- Passed: **52**.
- Failed: **0**.
- Skipped: **0**.
- Previously accepted CP006.3 baseline: **23** tests.
- Additional CP006.4 coverage: **29** tests (20 invalid guest images, positive/negative guest boot evidence, isolated UART/console mocks, five linker-memory checks, and other test cases).
- Runner: GitHub-hosted Ubuntu 24.04; `contents: read` only.
- Toolchain: freestanding `arm-none-eabi-gcc`, `qemu-system-arm`, `gdb-multiarch`, Python unittest and standard host GCC.
- No uploaded compiled images (Actions artifact quota is not used). No physical runners, sensitive credentials, firmware flashing or device access.

Both real QEMU cold boot and actual guest failure-state instrumentation are required; the test harness does not silently skip missing tools.

## H. Hardware support / policy — BLOCKED for retail Torch 9810

| Area | QEMU research result | Original retail Torch 9810 |
|---|---|---|
| Independent ARM ELF | Boots on QEMU Cortex-A15 | **UNVERIFIED** |
| DTB parser and virtual UART | PASS for QEMU `virt-8.2` | **UNVERIFIED** |
| Terminal & RAM notes | PASS via QEMU UART | **UNVERIFIED** |
| Firmware bootloader / signature chain | Out of scope | **BLOCKED** |
| Safe restore / rollback | Out of scope | **BLOCKED** |
| Board revision / display / touch | Simulated or absent | **UNVERIFIED** |
| Keyboard / trackpad / USB / storage | Unsupported virtual prototype | **UNVERIFIED** |
| Wi-Fi / modem / charging / battery power | Unsupported | **UNVERIFIED** |

This ELF is **not a flashable BlackBerry OS**, Parrot OS port, compatible kernel or retail boot image. No rights to flash or modify the handset have been granted; do not use QEMU outcomes as such evidence.

## I. Single next objective

**CP006.5: in-guest UART TX-stall verification under QEMU with independently observed bounded failure and zero command processing afterward.** The host fake-register test currently passes, but the actual QEMU PL011 transmit-stall path remains untested. Make this the next isolated, guest-side acceptance gate without physical devices or a production release.

### External documentation

- [QEMU ARM `virt` board](https://www.qemu.org/docs/master/system/arm/virt)
- [QEMU GDB integration](https://www.qemu.org/docs/master/system/gdb.html)
- [Flattened Device Tree binary format](https://devicetree-specification.readthedocs.io/en/stable/chapter5-flattened-format.html)
- [Existing CP006.3 baseline report](TORCHOS_CP0063_GUEST_FDT_QA_20261114.md)
