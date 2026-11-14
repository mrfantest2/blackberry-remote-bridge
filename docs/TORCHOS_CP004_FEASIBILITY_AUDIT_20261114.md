# TorchOS CP004 — Retail Torch 9810 Replacement-OS Feasibility Audit

**Date:** 2026-11-14  
**Target:** Original BlackBerry Torch 9810 (Jennings) motherboard, not BlackBerry 10, Passport, Bold or an Android-based BlackBerry  
**Status:** **NO-GO for physical OS replacement**; **GO for documentation and generic off-device emulation**  
**Issue:** [#3](https://github.com/mrfantest2/blackberry-remote-bridge/issues/3)  
**Base branch:** `feat/torchos-native-shell-20261114`  
**Execution:** GitHub connector and GitHub-hosted Actions only. **No Codex, OpenCode, self-hosted runner or BlackBerry device operation during this checkpoint.**

## Executive conclusion

A genuine replacement operating system must boot its own kernel and userspace on the Torch 9810 without executing stock BlackBerry OS 7. The existing `TorchOS.cod` is a native BlackBerry OS 7 Java application and **does not satisfy this objective**.

This review did **not** identify a verified public mechanism for the **retail Torch 9810** to boot an unsigned, independent kernel; nor did it find a device-specific, maintainable Linux device tree or a complete tested factory-return recovery image for this owner's exact device. Therefore **do not flash, unlock, install, repartition, erase, reboot or probe privileged boot modes**. Absence of a publicly reproducible route is not proof that one could never exist.

**This document is a research checkpoint, not proof of an on-device boot.**

## Evidence matrix

| Area | Evidence found | Confidence | Implication / gap |
|---|---|---|---|
| Exact retail model | Torch 9810, original BlackBerry OS 7 device; hardware listed in iFixit and historical product material | High | Original 9810 only; do not generalize from Passport or Torch 9800 |
| Processor speed, memory, flash | iFixit: **1.2 GHz**, **768 MB RAM**, **8 GB internal storage** | High for published product specifications | This is enough to consider a small off-device emulated environment, but not evidence of bootability |
| Display / inputs | 3.2-inch **480×640** touch panel, QWERTY slider, optical trackpad | High for published specifications | Actual display controller, scan matrix, touch controller and device drivers are unidentified |
| SoC revision | BBRef identifies **Qualcomm MSM8655**; PhoneDB and PhoneMore list **MSM8255T** for some variants | **Conflicting sources** | Do not choose a kernel target or board device tree based only on product web listings; obtain trustworthy exact-board evidence |
| USB interface | Previous authorized Steam Deck audit saw USB VID:PID `0fca:8004`, labeled Research In Motion | High for USB enumeration; low for boot protocol | **Does not establish** unlocked bootloader, recovery image, low-level read permissions or RAM-boot |
| Alternative kernel / retail boot entry | No Torch 9810-specific reproducible published independent-kernel boot procedure identified in sources checked | Unknown feasibility | **G1 blocked**; do not substitute generic Qualcomm instructions or another BlackBerry model's boot |
| Mainline/vendor board drivers | No validated, complete retail Torch 9810 kernel target + display/keyboard/touch/storage/power board-support tree identified | Unknown | **G2 blocked**; shared ARM CPU family is not device-specific hardware support |
| Existing BlackBerry Linux utilities | Ubuntu Community Wiki documents **Barry** for sync, USB, application management, backup/restore | High for historical tool purpose | This is **not Linux running on the BlackBerry** and not evidence of a kernel boot interface |
| Existing owner backup | Historical project inventory: `/home/SD/Backups/BlackBerry_9810/2026-11-06_USB_volume` | Verified as a user-volume copy in preceding project audit; not reread in this research run | Not demonstrated as a bit-for-bit full firmware/bootloader recovery set |
| Stock reload workflow | BlackBerry Torch 9810 user guide describes reloading **BlackBerry's own software** with BlackBerry Desktop Software, potentially affecting device data | High as documented stock procedure, current availability unknown | Not a substitute for verified recovery from a failed custom kernel/bootloader attempt |
| Similar ports | Historical postmarketOS listing includes a **Bold Touch 9900 (Dakota) WIP** entry, not Torch 9810. BlackBerry Android kernel public code concerns later Android devices | Model-dependent; limited applicability | Neither establishes a supported OS replacement on the original Torch 9810 |

### Source links and provenance

- **iFixit, Torch 9810 identification and specifications:** https://www.ifixit.com/Device/Blackberry_Torch_9810
- **BBRef, Torch 9810 listing (reports MSM8655):** https://bbref.ca/9810
- **PhoneDB, 9810/T-Mobile hardware catalog (reports MSM8255T):** https://phonedb.net/index.php?c=t-mobile_blackberry_torch_9810__rim_jennings&d=detailed_specs&id=3199&m=Device
- **PhoneMore, Torch 9810 hardware catalog (reports MSM8255T):** https://www.phonemore.com/specs/blackberry/torch-9810/
- **Ubuntu Community Wiki, BlackBerry/Barry USB functionality (not Linux port):** https://help.ubuntu.com/community/PortableDevices/Blackberry
- **Historic postmarketOS device list snapshot, other model WIP (not proof of current device support):** https://yuvadm.github.io/pmosweb/wiki/Devices/
- **BlackBerry Android kernel source repository (not 9810 OS7 source):** https://github.com/blackberry/android-linux-kernel
- **Torch 9810 BlackBerry Desktop Software reload documentation:** https://blackberry.manymanuals.com/smartphones/torch-9810/users-guide-32124/258
- **BlackBerry's official service end-of-life FAQ (includes Torch 9810):** https://www.blackberry.com/en/secure-communications/support/end-of-life

These sources establish device class and known limitations; **none supplies a validated retail Torch 9810 alternative boot sequence or OEM-independent firmware image**. Third-party catalog identifiers are not a substitute for a board schematic or verified silicon readout.

## CP004 decision gates

| Gate | Acceptance evidence required | Result |
|---|---|---|
| **G0 Device/recovery preservation** | Proven owner-specific original firmware and user-data restore mechanism, independently validated; no personal backup contents published | **BLOCKED** — USB-volume backup alone insufficient |
| **G1 Independent boot** | Reproducible boot of a non-BlackBerry kernel on **retail Torch 9810**, with documented authorization and reversible method | **BLOCKED** — no demonstrated path |
| **G2 Board support** | Accurate SoC/board variant and working display, touchscreen, keyboard/trackpad, storage, USB, charging, power, watchdog drivers | **BLOCKED** — device-specific evidence missing |
| **G3 Off-device demonstration** | Generic emulated 32-bit ARM kernel + minimal userspace with TorchOS UI, tests and accurate limitation labels | **ALLOWED TO DEVELOP** — not a claim of hardware compatibility |
| **G4 Safe real-device trial** | All G0–G3 plus separately authorized physical-device scope and demonstrated rollback | **BLOCKED** |
| **G5 Full replacement** | Real-device cold boot, full restart cycle, hardware validation and documented recovery | **BLOCKED** |

The **G1 and G0 gates are independent**. A working Linux image in an emulator does not open the physical-device gate. An OS 7 Java application running on the phone also does not open it.

## Proposed safe architecture for an off-device-only experiment

```text
GitHub-hosted CI (public, unprivileged, no device access)
  └─ static checks, host tests, documentation policy

Optional future development workspace (isolated, off-device)
  └─ QEMU generic 32-bit ARM machine
       ├─ generic ARM Linux kernel or comparable tiny OS
       ├─ memory-only or virtual-disk root filesystem
       ├─ local terminal (offline command allowlist)
       ├─ 480×640 original TorchOS desktop preview
       └─ simulated QWERTY/trackpad inputs and explicit dummy hardware values

Physical BlackBerry Torch 9810
  └─ BlackBerry OS 7 and private data UNCHANGED
```

**QEMU's generic ARM machine is not a Torch 9810 emulator**. Building a generic 32-bit ARM image does not validate BootROM, RIM boot chain, device-specific registers or peripherals. Do not distribute it as a “Torch 9810 flashable OS”.

### Next off-device milestones (future code, not accomplished here)

1. Choose a licensing-compliant generic ARM kernel/rootfs and record all dependencies, sources, checksums and security assumptions; keep any proprietary Blackberry SDK or ROM out of public Actions.
2. Build a minimal self-contained launcher with offline terminal, notes and settings plus a 480×640 original UI. Simulate unsupported battery, network and touch controllers with visible labels.
3. Add GitHub-hosted static/integration tests for configuration, filesystem, deterministic boot and idle. Do not run public PRs on a personal self-hosted Steam Deck.
4. Separately request reliable public evidence for exact Torch 9810 boot-chain, board revision, verified stock recovery and supported drivers.
5. If G1 or G0 never clears, retain the OS7 app as an honest fallback or consider a separately approved **replacement motherboard** project. That is physically and technically different from replacing software on the original motherboard.

## Public repository and release protections

- Source of truth is GitHub, not Codex. Use a **research PR** targeting `feat/torchos-native-shell-20261114`, not `main`.
- The GitHub-hosted Actions workflow verifies host-side tests only; **no BlackBerry JDE COD build** or physical device install in hosted CI.
- Avoid committing credentials, personally identifiable USB IDs/PINs, backups or firmware binaries.
- Do not automatically close Issue #3: the core boot/recovery proof is still missing.
- All speculative findings must be labelled **unverified** rather than promoted into installation instructions.

## CP004 audit outcome

**Research evidence recorded; physical boot feasibility remains UNVERIFIED.** The next useful action is a generic offline image demonstration and a genuinely model-specific boot/recovery evidence search. The BlackBerry is still off limits for experiments.
