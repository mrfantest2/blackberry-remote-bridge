# TorchOS CP006.6 — ARMv7 Exception Vectors and Virtual GIC IRQ QA

**Checkpoint:** 2026-11-15, independent QEMU research only  
**Authoritative repository:** `mrfantest2/blackberry-remote-bridge`  
**Development base:** `feat/torchos-native-shell-20261114`  
**Starting branch HEAD:** `e7fc4ab8aaf29f21e3147f3361d0baf2a078564e`  
**CP006.6 feature:** `feature/torchos-cp0066-arm-exception-vectors-20261115`  
**QEMU:** `virt-8.2`, Cortex-A15, ARMv7-A / AArch32, 128 MiB virtual RAM  
**Hardware policy:** No retail BlackBerry Torch 9810 access, firmware, bootloader, partition, proprietary toolchain or physical runner.

## Goal and architectural constraints

Establish a deliberately small, **fail-closed AArch32 exception foundation**, preserving CP006.5's bounded UART error handling and all original terminal commands.

ARM's AArch32 exception architecture supports a 32-byte aligned vector base register (VBAR) and eight exception vectors. This checkpoint installs and checks the actual CPU VBAR, allocates banked exception-mode stacks, and records the architectural LR/SPSR when a real CPU exception occurs.

**Primary references:** [Arm AArch32 VBAR](https://support.arm.com/documentation/111107/2026-06/AArch32-Registers/VBAR--Vector-Base-Address-Register?lang=en); [Arm Cortex-A Programmer's Guide — exception types](https://support.arm.com/documentation/den0013/0400/Exception-Handling/Types-of-exception); [QEMU v8.2.2 `virt.c`](https://github.com/qemu/qemu/blob/v8.2.2/hw/arm/virt.c).

## Changes

| Source | Responsibility |
|---|---|
| `torchos-emulator/src/startup.S` | 8 A32 vector branch instructions, CP15 VBAR install/readback, separate banked UND/ABT/IRQ/FIQ stacks, no general interrupt enabling |
| `torchos-emulator/linker.ld` | Enforce vector alignment, exception stack separation, bounded ELF and DTB regions |
| `torchos-emulator/src/kernel.c` | Add volatile RAM exception/GIC readback markers; preserve existing hardware/console execution |
| `torchos-emulator/src/boot_state.h` | Document named fail-closed exception phase and exception kinds |
| `torchos-emulator/tests/test_exception_vectors.py` | Actual QEMU guest SVC and undefined-instruction exceptions after normal cold boot, VBAR readback, architecture state, linker memory checks |
| `torchos-emulator/tests/test_irq_delivery.py` | Real GICv2 software-generated IRQ originating from a **test-only ARM probe** executing on the QEMU guest CPU |

**The test-only GIC probe is not a production IRQ driver.** QEMU v8.2.2 `virt` documents its GICv2 distributor at `0x08000000` and CPU interface at `0x08010000`. In the normal kernel, IRQ/FIQ remain disabled and this probe is never invoked. The isolated hosted test redirects the already-booted QEMU guest PC to this probe through GDB; the **ARM guest itself** performs MMIO writes, sends SGI0 to its CPU and unmasks IRQ. This avoids a failed attempt to program the GIC solely through GDB memory writes, which were observed not to enable the distributor or CPU interface.

The probe exists only for QEMU architecture QA; hardcoded GIC addresses are **not** generalized as BlackBerry board addresses.

## Guest-side evidence

An accepted initial hosted run [#43648081565](https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43648081565) completed **56/56** tests, including actual synchronous CPU traps:

- Hardware VBAR readback `0x40100080`, 32-byte alignment confirmed; eight vector words are real A32 branch instructions.
- SVC test: exception kind `2`, architectural LR `0x40100110`, saved SPSR `0x200001d3`.
- Undefined instruction test: kind `1`, LR `0x40100118`, saved SPSR `0x200001d3`.
- Both traps executed **after real guest cold boot**, not in a host C mock. QMP verified the exception phase, CPU PC in the existing WFI halt, and no command dispatch.
- Separate 1024-byte banked UND, ABT, IRQ and FIQ stacks within the linker-validated 128 MiB virtual RAM, preserving 16 KiB SVC stack and 1 MiB DTB reserve.

A subsequent hosted run [#43648589874](https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43648589874) completed **57/57** with **actual GICv2 SGI0 delivery** to the guest's IRQ vector. QMP verified exception kind `5` and saved pre-interrupt SPSR `0x20000153`, with IRQ unmasked **only** by the isolated probe. A host-side MMIO-write approach failed to cause an IRQ and was replaced with guest-generated MMIO, rather than weakening the test to silence or a mocked IRQ.

Strengthened guest GIC distributor/CPU/priority register readback and exception LR assertions passed. Exact PR-head and post-merge GitHub-hosted checks have now passed; the links and accepted SHAs are recorded below.

## Acceptance status

| Gate | Status |
|---|---|
| ARM ELF and normal guest cold boot | **PASS** |
| Eight-vector table, 32-byte VBAR, CP15 readback | **PASS** |
| Separate UND/ABT/IRQ/FIQ stacks and linker bounds | **PASS** |
| Actual CPU SVC and undefined-instruction fault capture | **PASS** |
| Actual QEMU GICv2 SGI0 delivery to guest IRQ vector | **PASS** including strengthened guest GIC state checks |
| Existing commands/history/RAM notes | **PASS** |
| CP006.5 bounded PL011 test-instrumented QEMU fault regression | **PASS**, exact PR head and post-merge |
| FIQ delivery and physical/timer IRQ servicing | **UNVERIFIED** |
| Recoverable exception return, nested interrupts, GIC EOI | **NOT IMPLEMENTED** |
| Retail Torch 9810 independent OS boot or rollback | **BLOCKED / NO-GO** |

## Explicit exclusions and next engineering checkpoint

The currently implemented exception and IRQ vectors are **diagnostic fail-closed handlers**: they do not return to the interrupted task, acknowledge GIC interrupts, schedule processes, set up an MMU, or provide a hardware-compatible BSP. A real virtual GIC software interrupt reaching a vector **does not** mean TorchOS can service an IRQ in production.

**CP006.7 objective:** Implement a **virtual GICv2 interrupt acknowledge/EOI path** for a deliberately authorized virtual timer or SGI and verify that the ARM guest resumes its normal console with bounded and correctly attributed interrupt accounting. Keep the normal no-IRQ path and all existing UART/FDT behavior unchanged. Do not initiate physical BlackBerry testing.

## Final accepted GitHub evidence

**PR [#16](https://github.com/mrfantest2/blackberry-remote-bridge/pull/16) was merged** into the original `feat/torchos-native-shell-20261114` development branch. The production `main` branch was not touched.

| Evidence | Verified GitHub run |
|---|---|
| PR-head ARM/QEMU boot, exception, GIC SGI, memory, FDT and command QA | [57/57 PASS, run 43648826421](https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43648826421) |
| PR-head actual ARM UART against test-instrumented QEMU PL011 | [2/2 PASS, run 43648826463](https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43648826463) |
| Post-merge ARM/QEMU acceptance on accepted code SHA | [57/57 PASS, run 43649179280](https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43649179280) |
| Post-merge isolated UART fault acceptance on accepted code SHA | [2/2 PASS, run 43649179288](https://github.com/mrfantest2/blackberry-remote-bridge/actions/runs/43649179288) |

- **Reviewed PR head SHA:** `1fa2e749f1b8373b111b168228d7730d318501af`.
- **Accepted executable code SHA:** `0db2be3c1843b078cb1bd23c468a625eb6433382`.
- **59 tests passed across two independent suites** on both PR head and accepted post-merge code; **0 failed / 0 skipped**.
- Post-merge real QEMU GICv2 SGI0: exception kind `5`, saved CPSR value `0x20000153`, guest IRQ vector entered successfully after test-only SGI configuration and IRQ unmask.
- Post-merge QEMU PL011 device fault: real guest reports `BOOT_UART_FAILED` with **65,536** MMIO reads, **0 writes**, **0 command dispatches**; normal control console still works.
- QEMU 8.2.2 source archive SHA-256 was verified again in the UART hosted run.
- A separately authorized engineering commit `7b95971fd712cd0f97b49205c5c646e518f96f82` landed on the same development base during this task, but was **preserved**: it touched the separate offline/native QA workflow and did not conflict with the seven CP006.6 emulator/documentation files.
- This final acceptance section is committed **after** the passing code SHA as documentation only. It does not change executable behavior or claim a new code validation on that docs-only SHA.
- **Next issue:** [#17 — CP006.7: acknowledge/EOI actual virtual IRQ and safely resume console](https://github.com/mrfantest2/blackberry-remote-bridge/issues/17).

**Strict NO-GO:** This is virtual QEMU ARMv7 software only. The retail BlackBerry Torch 9810 has no verified independent kernel boot/complete stock rollback/board drivers from these results. No real handset, OS7 app, backup, firmware, protected boot path, production service or physical device was accessed or modified.
