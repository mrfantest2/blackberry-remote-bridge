# TorchOS CP006.7 — QEMU GICv2 SGI service and return to console

**Scope:** QEMU `virt-8.2` (GICv2, Cortex-A15) only. Not BlackBerry firmware.
**Parent:** CP006.6 accepted code `0db2be3c1843b078cb1bd23c468a625eb6433382`.
**Issue:** #17.

## What changed

- `torchos-emulator/src/gic_irq.S` (new):
  - `cp067_probe_gicv2_resume` — test-only probe. It is entered only by a hosted GDB PC redirect after verified boot, with the interrupted console PC pushed on the SVC stack. It checks SVC mode, IRQ+FIQ masked, not already armed, no prior service and SGI ID ≤ 15. It then programs GICD/GICC, arms, writes `GICD_SGIR` (self) and returns with one atomic `ldm sp!, {pc}^` (CPSR←SPSR_svc with I cleared). The pending SGI is therefore taken by the **console code**, not by the probe.
  - `cp067_irq_entry` — IRQ vector target:
    - **Unarmed:** restores registers and branches to the unchanged CP006.6 `cp066_trap_irq` recorder (LR/SPSR intact).
    - **Armed:** reads `GICC_IAR`, accepts only ID 0, writes `GICC_EOIR` with the full IAR value and increments `cp067_irq_count`. It then disarms, quiesces GICD/GICC (enables and pending cleared, CTLR = 0), sets SPSR.I so the console resumes **masked**, and returns with `subs pc, lr, #4`.
    - **Spurious (1023):** no EOI, counted and returned.
    - **Other IDs:** EOI'd (if < 1020), recorded, GIC quiesced, fail-closed halt `0x067bad01`.
    - **Re-entry guard:** fail-closed `0x067bad02`.
    - **Probe precondition failure:** `0x067bad03`, with no GIC access.
- `startup.S`: the IRQ vector now branches to `cp067_irq_entry`. Everything else is unchanged.
- Normal boot never executes either path. IRQ/FIQ stay masked and the GIC is never written.

## Evidence (local QEMU 8.2.2, Ubuntu 24.04, arm-none-eabi-gcc 13.2.1)

`make -C torchos-emulator test`: **62/62 passed** (57 CP006.6 + 5 CP006.7), three consecutive runs.
ELF SHA-256: `a06ea36fbbfc6e08317bb62d101fc341bde5facf3d18b4902fee9fbb847b7724` (local build).

| Test | Observed |
|---|---|
| Normal boot | PSR mode svc, I+F set; GICD_CTLR/GICC_CTLR = 0; GICD_TYPER ≠ 0, which proves the MMIO is observable; all cp067 telemetry 0 |
| SGI0 service | count = 1 exactly (after 300 ms settle); IAR ID 0; `resume_pc` == the exact PC paused in the console loop (e.g. `0x40100e9c`); resume SPSR `0x200001d3` (svc, I+F masked); GIC disabled afterwards; no CP006.6 trap; `help`, `notes set/show`, `files` work afterwards; dispatch count +4 |
| SGI3 (unsupported) | phase `0x067bad01`, rejected_id 3, count 0, GIC disabled, halted at `cp064_halt` with IRQ masked |
| Nested guard | phase `0x067bad02`, IAR never read |
| SGI 16 request | phase `0x067bad03`, GIC untouched |

The host only pauses the guest, pushes the PC and redirects it (GDB), and reads RAM/MMIO (QMP). All GIC MMIO, the IRQ exception, acknowledgement, EOI and exception return are done by guest code on the virtual CPU.

## Still unsupported

FIQ, prefetch/data-abort recovery, SPIs/PPIs/timer, general re-armable interrupt service, scheduler, MMU, storage, network, touchscreen, QWERTY, trackpad, power management, and any real BlackBerry Torch 9810 boot or rollback. **Physical replacement OS remains NO-GO.**
