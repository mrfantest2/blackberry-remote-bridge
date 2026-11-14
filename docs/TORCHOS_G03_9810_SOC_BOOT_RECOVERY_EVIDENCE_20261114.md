# TorchOS G0.3 — Retail Torch 9810 Silicon, Boot and Recovery Evidence

**Date:** 2026-11-14  
**Scope:** Source-linked research on the original retail BlackBerry Torch 9810 (Jennings); read-only.  
**Authoritative repo:** `mrfantest2/blackberry-remote-bridge`  
**Base SHA:** `d890154b2e3be4e7c99ec5d64dea232fb2efd88c`  
**Parent issue:** [#3 — original OS-replacement feasibility](https://github.com/mrfantest2/blackberry-remote-bridge/issues/3)

## Decision

**GO:** Continue independent QEMU/ARM off-device software architecture, documentation, static driver feasibility research, and voluntary normal-phone-UI verification.  
**NO-GO:** Booting, flashing, installing, unlocking, repartitioning, wiping, probing privileged device modes, or replacing firmware on the original retail Torch 9810.

The owner-provided photo visibly identifies a **BlackBerry 9810**, **BlackBerry OS 7.0 Bundle 1465 (application v7.0.0.296)** and platform **5.0.0.496**. The public repository stores **only** the model and software version observations; the photo and private identifiers are not uploaded. The ordinary phone screen does **not** show the actual SoC marking or boot ROM version.

The previously inspected authorized Steam Deck showed a BlackBerry/RIM USB composite device **0fca:8004** (vendor-specific + mass-storage interfaces). This proves a legacy BlackBerry USB connection, **not** a verifiable match to the pictured unit, a specific motherboard/SoC, or a privileged boot interface.

## 1. Published hardware facts versus unresolved SoC

| Question | Public evidence | Assessment |
|---|---|---|
| Manufacturer/model | Owner's visible OS7 device info: **BlackBerry 9810**. [iFixit Torch 9810](https://www.ifixit.com/Device/Blackberry_Torch_9810), [T-Mobile 2011 release](https://www.t-mobile.com/news/press/t-mobile-announces-upcoming-availability-of-the-blackberry-torch) | **PASS** for the photographed device's displayed model |
| CPU clock and memory/storage | T-Mobile's original 2011 announcement: **1.2 GHz**, OS7. AT&T upgrade sheet: **1.2 GHz, 768 MB RAM, 8 GB storage**. iFixit concurs. | **PASS** for published product-level specifications, not a silicon ID |
| Exact application SoC | [PhoneDB original 9810](https://phonedb.net/index.php?c=rim_blackberry_torch_9810__rim_jennings&id=2839&m=device): **MSM8255T**; [PhoneMore Global 9810](https://www.phonemore.com/specs/blackberry/torch-9810/global/): **MSM8255T**; [BBRef 9810](https://bbref.ca/9810): **MSM8655**; some derivative listings associate 9810 with **MSM8655T** | **UNVERIFIED/CONFLICTING**: two catalogs agree on MSM8255T but this is not conclusive OEM/physical-silicon evidence |
| Radio variants | [FCC filing L6ARDM70UW](https://fccid.io/L6ARDM70UW) describes a 9810 configuration using GSM and WCDMA; another filing **L6AREN70UW** is also recorded for 9810. | **PARTIAL**: shows 9810 regulatory variants, does **not** identify this handset's FCC ID or processor marking |
| Motherboard photo | [iFixit 9810 logic-board guide](https://www.ifixit.com/Guide/Blackberry+Torch+9810+Motherboard+Replacement/31633) includes a photo of the covered/shielded board; [FCC internal photo exhibit 1502065](https://fccid.io/L6ARDM70UW/Internal-Photos/Internal-Photos-1502065) exists | **PARTIAL**: model-specific physical references located; no exposed readable SoC marking verified |
| Real device processor and board revision | Not available from the normal OS 7 software screenshot or generic USB descriptors | **BLOCKED** until independently verifiable evidence without destructive inspection |

**Important source distinction:** The AT&T and T-Mobile product sheets are stronger for clock/RAM/storage; their accessible material **does not claim an exact Qualcomm part number**. Catalog disagreement cannot be resolved by choosing the most common listing. No assumption that 9800, 9850/9860, Bold 9900, later BlackBerry Android models, or generic MSM8x55 boards are electrically or firmware-compatible with the 9810.

Sources for published specs:
- T-Mobile newsroom, Nov 2011: https://www.t-mobile.com/news/press/t-mobile-announces-upcoming-availability-of-the-blackberry-torch
- AT&T original upgrade sheet: https://www.att.com/Common/about_us/pdf/TorchUpgrades_vFINAL.pdf
- iFixit: https://www.ifixit.com/Device/Blackberry_Torch_9810

## 2. Independent boot feasibility

**No publicly documented, independently reproducible method was verified for a retail Torch 9810 to load a custom standalone ARM kernel instead of BlackBerry OS 7.** This is a research evidence gap, not a mathematical claim that such a method could never exist.

- The legacy BlackBerry security technical overview describes boot-ROM authenticity checks and manufacturer verification of device software: https://blackberry.manymanuals.com/software/enterprise-solution-security-security-for-devices-with-bluetooth-wireless-technology-technical/users-guide-29990/71 . This describes an architectural barrier at the **BlackBerry family** level, not a 9810-specific traced boot process or independently inspected boot ROM.
- **Do not** use later Android BlackBerry verified-boot documentation or BlackBerry 10/QNX boot documents as if they specify the OS7 Torch 9810 boot chain.
- A `TorchOS.cod` native OS7 application uses the installed OS7 runtime; an ARM ELF that boots on QEMU `virt-8.2` does **not** prove compatibility with the real Torch 9810.
- No retail 9810-specific Linux device tree, complete display/keyboard/touch/storage/power BSP, independently authorized RAM boot mechanism or validated original-device rollback path was established by the sources reviewed.

**G1 retail independent boot = BLOCKED**; **G2 hardware driver support = BLOCKED**.

## 3. Recovery feasibility and backup distinction

The [official OS 7.0 Torch 9810 user guide](https://files.customersaas.com/files/Manual/BlackBerry_9810_Torch_User_manual.pdf) describes **reloading stock BlackBerry Device Software via BlackBerry Desktop Software**. It warns that missing a device-data backup may delete data, and that recovery from some faults may prevent making a backup. It does **not** promise restoration from a corrupted/overwritten bootloader or untrusted alternate-kernel image.

BlackBerry's official [legacy service end-of-life FAQ](https://www.blackberry.com/en/secure-communications/support/end-of-life) states that services for OS7.1 and earlier ended **2022-01-04**, includes Torch 9810, and that downloads for BlackBerry OS devices and legacy software are no longer available. Consequently, a historical guide's instruction to **download the latest stock OS** cannot be treated as presently reproducible.

The existing Steam Deck copy of the phone's exposed USB media volume (roughly **2.9 GB** from a prior read-only metadata audit) is **not** evidence of full firmware, boot ROM, signed loader, radio configuration or independently verified disaster recovery. Do not read or publish its contents for this research goal.

Historical [Ubuntu community BlackBerry/Barry documentation](https://help.ubuntu.com/community/PortableDevices/Blackberry) covers synchronization, backups/restores and USB storage for legacy BlackBerry devices. **Barry is not a proven full-bootloader or firmware recovery utility.**

**G0 complete rollback = BLOCKED**, independently of the available USB-media copy and historical reload instructions.

## 4. Evidence gate summary

| Gate | Status | Evidence needed to change status |
|---|---|---|
| Photographed handset identification | **PASS** | Visible BlackBerry 9810/OS7 screen; serial/IMEI intentionally not shared |
| USB device connection on Deck | **PASS** | `0fca:8004`, generic BlackBerry USB interfaces |
| Exact SoC/board identity | **UNVERIFIED** | Authoritative, exact-variant silicon marking, verified OEM BOM/teardown, or documented OS-supported hardware identifier |
| G0 firmware rollback | **BLOCKED** | Device-specific verified **complete** stock restore package, all restore prerequisites, repeatable safe procedure independently tested without touching the owner's device |
| G1 alternate kernel boot | **BLOCKED** | Documented reproducible retail Torch 9810 boot entry for an independent ARM image, no unsupported extrapolation |
| G2 board drivers | **BLOCKED** | Actual 9810-specific display, touch, QWERTY, trackpad, flash/storage, USB, power/charging and radio coverage |
| QEMU-only research | **PASS/ONGOING** | CP006.4 off-device suite previously reported **52/52**; independent of handset hardware |
| Real TorchOS firmware installation | **NO-GO** | All above blockers resolved and separately authorized |

## 5. Next safe engineering decision

**A narrowly scoped, non-invasive variant identification** is the next sensible physical evidence milestone. An owner-observed regulatory model/FCC ID on the factory label (no serial number, PIN, IMEI or personal data) could distinguish the known radio-board variant. The full SoC marking could still remain inaccessible without disassembly; **do not** remove board shields or experiment with privileged USB commands for this checkpoint.

Separately, seek a credible **retail Torch 9810-specific** primary-source boot protocol or genuine factory restore proof. Until both are established, prioritise the existing standalone QEMU project and the original native OS7 app as separate, clearly labelled outputs.

No physical firmware changes, handset reboots, privileged queries, storage mounts or personal backup reads occurred while preparing this report.
