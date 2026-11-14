# TorchOS Native OS — Hardware Replacement Feasibility and Decision Gates
Date: 2026-11-14 | Target: **BlackBerry Torch 9810** | Status: RESEARCH / NO DEVICE WRITES
Repository: mrfantest2/blackberry-remote-bridge
Branch: feat/torchos-native-shell-20261114
Last verified CP003 branch head: 83cd68d89c02556f38e4962553cb76f74547cf22

## Authoritative user goal
**TorchOS must ultimately replace the stock BlackBerry OS 7 entirely and boot on the original Torch 9810 hardware as its own operating system.** A Java shell, launcher, theme, remote dashboard or Linux-looking application is **not** an end-state substitute. Keep the OS7 application as a separate usable fallback, not as a misleading claim of a real OS.

## Evidence reviewed
- On the connected Steam Deck, lsusb sees RIM VID:PID `0fca:8004`, and the existing TorchOS feature branch is clean at CP003 head `83cd68d`. This alone is not an identified bootloader, unlock route or supported recovery interface.
- A historical USB-volume copy is present at `/home/SD/Backups/BlackBerry_9810/2026-11-06_USB_volume`; it is **not** evidence of a bitwise complete firmware backup or restore method.
- TorchOS CP003 is an OS7 Java app with a genuine COD, 61/61 host tests and 25/25 browser checks, **not** a real OS; it has not been installed on the phone.
- Hardware reference: https://bbref.ca/9810 identifies Snapdragon MSM8655-era 1.2 GHz ARM processor, 768 MB RAM, 8 GB internal storage, 480x640 display, optical trackpad and slide-out keyboard. Some third-party references identify MSM8255T instead: **exact processor revision and board implementation must be confirmed from authoritative device documentation**.
- BlackBerry security architecture describes a manufacturer-signed boot ROM/OS authorization chain (see https://blackberry.manymanuals.com/software/enterprise-solution-security-security-for-devices-with-bluetooth-wireless-technology-technical/users-guide-29990/71 ). General BlackBerry security documentation may not establish every specific 9810 boot-stage detail. Do not infer a software unlock is available.
- Target-specific open-source Linux/kernel/bootloader device tree, supported independent boot path and full recovery workflow: **not identified in research on 2026-11-14**. Absence of evidence is not proof of impossibility.
- Ubuntu BlackBerry community page (https://help.ubuntu.com/community/PortableDevices/Blackberry) describes USB sync/backup tools, not firmware replacement.

## Decision gates: NO-GO until independently demonstrated
**G0: Preserve original.** Capture non-sensitive read-only model/board/firmware/USB identification; inventory separate backups and demonstrate a reproducible, lawful full-firmware restore method *without* initiating destructive actions. Keep original applications, photos, archives, S25Hub and all user content untouched.

**G1: Boot-chain feasibility.** Obtain credible documented evidence for an authorized alternative kernel load or recovery-supported RAM boot **specifically on retail Torch 9810 hardware**. A generic Qualcomm Linux image, a microSD card containing Linux, code-signing an OS7 Java COD, a BlackBerry 10 solution or a boot process from another BlackBerry does not satisfy this gate.

**G2: Board support.** Identify RAM map, storage controller, display/framebuffer, touchscreen, QWERTY, trackpad, USB, charging/power, watchdog, Wi-Fi and suspend drivers. Distinguish upstream architecture support from concrete board-level driver support. The target is a 32-bit lightweight system; Parrot Security Linux is visual/workflow inspiration, not assumed compatible.

**G3: Safe independent OS prototype.** Develop a complete original TorchOS userland and bootable image for emulation/test board on the Steam Deck **without contacting or modifying the Torch flash**. Prove terminal, filesystem, UI, keyboard input, storage integrity, idle/power behavior and a recovery test for that emulator/test hardware. Emulated boot is not evidence of Torch bootability.

**G4: Reversible hardware path.** Before any experimental physical boot, require verified return-to-stock restore assets for the exact handset/board and independent explicit authorization. If no approved alternative boot and recovery workflow exists, the internal-flash replacement stage stays blocked indefinitely. Never erase stock bootloader or flash speculative images.

**G5: Real device acceptance.** Only after G0–G4 are proven and separately approved: demonstrate cold boot directly into TorchOS without BlackBerry OS7, repeated restart, keyboard/trackpad/touch, local storage, power/charging, functional safe networking, and successful return-to-stock recovery. Disabled unsupported peripherals must be explicitly labeled.

## Proposed engineering stack (conditional)
- Keep CP003 Java app and source/QA as the existing OS7 fallback.
- Research a low-footprint 32-bit ARM Linux + minimal root filesystem + original local shell UI **off-device**. This is conditional on CPU ISA/kernel availability; any QEMU target should be described as emulation, **not** device compatibility.
- Use Codex as senior engineer/QA reviewer and OpenCode with the verified free model only if its inference is actually available; no paid-model fallback, no global config changes.
- All early experiments are read-only against the attached phone and scoped to new, non-production folders in this same repository. Avoid duplicate apps/services.

## Alternative if G1 cannot be met
A full independent TorchOS can run on a replacement embedded board in the BlackBerry enclosure, reusing the physical keyboard/display only if electrically feasible, but this would be **hardware replacement**, not software replacement on the original motherboard. It must be separately scoped and approved; do not attempt physical disassembly or wiring now.

## Next approved task scope
**CP004-FEASIBILITY (READ ONLY):** Codex audits published 9810 hardware evidence, existing backup/recovery state, open-source kernel/device-tree support and documented boot pathways; produces a likelihood and evidence matrix. No native OS install, no BlackBerry writes, no privileged bootloader changes, no service modification. Present clear GO / NO-GO conditions.

**Current decision: NO-GO for physical OS replacement; GO for read-only feasibility research and off-device prototypes.**
