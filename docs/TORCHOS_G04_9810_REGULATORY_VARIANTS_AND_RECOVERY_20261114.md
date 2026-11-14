# TorchOS G0.4 — Retail BlackBerry Torch 9810 Regulatory Variant and Recovery Evidence

**Checkpoint date:** 2026-11-14  
**Scope:** Read-only public-source investigation; original retail BlackBerry Torch 9810.  
**Issue:** [#3 — independent OS replacement feasibility](https://github.com/mrfantest2/blackberry-remote-bridge/issues/3)  
**Parent report:** [G0.3 silicon, boot and recovery](TORCHOS_G03_9810_SOC_BOOT_RECOVERY_EVIDENCE_20261114.md)  
**Base development commit:** `eed24c58f5491a0b00ba58215fb0e6b31c4f1092`

## Executive result

**A new useful finding:** The manufacturer-authored *Torch 9810 Safety and Product Information* manual expressly identifies **three retail model codes and their FCC IDs**, not merely the two IDs previously highlighted in a US hearing-aid-compatibility summary.

| Manufacturer retail model | FCC ID | Model-specific filing evidence |
|---|---|---|
| `RDM71UW` | `L6ARDM70UW` | FCC describes WCDMA/HSDPA **II/V** |
| `RDN71UW` | `L6ARDN70UW` | FCC describes WCDMA/HSDPA **II** |
| `REN71UW` | `L6AREN70UW` | FCC records **band IV** variant |

**Source (manufacturer-authored document, HTML rendering, page 6):** https://www.manualslib.com/manual/684473/Blackberry-Torch-9810.html?page=6

**Individual regulatory entries:**
- RDM: https://fccid.io/L6ARDM70UW
- RDN: https://fccid.io/L6ARDN70UW
- REN: https://fccid.io/L6AREN70UW

An FCC product code such as `RDM70UW` is **not identical text** to the manufacturer manual's retail hardware model `RDM71UW`; this report preserves both identifiers without claiming they are interchangeable.

The manual explicitly locates the regulatory sticker **behind the removable battery**. A clean reading of *just* the retail model number or FCC ID on this particular handset would advance the radio-variant identity gate; **do not publish the device PIN, IMEI, serial number, barcodes or personal data**. No instruction or permission to disassemble the phone's motherboard is implied.

## What the earlier owner photograph does and does not establish

The owner-supplied OS 7 information screen shows:
- **BlackBerry 9810** smartphone;
- **BlackBerry 7.0 Bundle 1465**, application `7.0.0.296`, platform `5.0.0.496`;
- 3G-band display `1,2,5,6`.

These are visible software-reported capabilities. The screenshot **does not show** `RDM71UW`, `RDN71UW`, `REN71UW`, an FCC ID, a silicon marking, motherboard revision or boot-ROM hash. The presence of bands II/V in the screen could be consistent with more than one product/configuration; it is **not a verified regulatory-model binding**. The photo itself was not copied into this public report.

A past read-only Steam Deck enumeration identified a BlackBerry USB composite device with VID:PID `0fca:8004`, one vendor-specific interface and one mass-storage interface. This is **not** a chip or FCC-ID diagnostic, nor a verified physical-to-photo identity binding.

## SoC dispute and board photos

The existing G0.3 comparison documented **MSM8255T** in two secondary catalogs and **MSM8655/MSM8655T** in others. Neither the manufacturer safety page nor the available FCC filing summaries exposed the Qualcomm processor's readable silicon marking. The [iFixit 9810 motherboard replacement photographs](https://www.ifixit.com/Guide/Blackberry+Torch+9810+Motherboard+Replacement/31633) depict a board covered by metal RF/processor shields: a shielded board photograph cannot certify the part number beneath it. Do **not** infer a Linux kernel target from these photographs, a generic `msm8x55` device tree, or another BlackBerry model.

**Exact SoC and board revision: UNVERIFIED.** Valid evidence would be a trustworthy original BOM, variant-specific manufacturer service documentation explicitly naming the SoC, or independently readable silicon marking from a documented exact-board teardown. This research does **not** authorize disassembly.

## Retail secure boot and independent kernel research

A BlackBerry *Security Technical Overview* describes family-level cryptographic checks of boot ROM and device software, including authenticity/signature checks. It does **not** identify an unlocked or independently reproducible alternate-kernel boot route on the retail 9810: https://blackberry.manymanuals.com/software/enterprise-solution-security-security-for-devices-with-bluetooth-wireless-technology-technical/users-guide-29990/71

No model-specific publicly documented **independent 9810 ARM kernel boot procedure** was verified during this checkpoint. The QEMU `virt-8.2` monitor successfully boots only because QEMU provides a different virtual board and boot mechanism.

**G1 independent retail boot = BLOCKED.** There is no reason to test privileged USB commands, signed-loader bypasses, boot-ROM modes, firmware images, or partitions on the owner's working handset.

## Stock reload is not full bootloader rollback

The original 9810 OS 7 user's guide explains using **BlackBerry Desktop Software** to reinstall stock device software; it also warns that backups might be unavailable in some fault states and that data might be lost. The guide does **not** promise recovery after replacing/corrupting protected boot stages:
https://blackberry.manymanuals.com/smartphones/torch-9810/users-guide-32124/258

BlackBerry officially discontinued its legacy BlackBerry OS 7.1 and earlier services and software distribution (including the Torch 9810) on **2022-01-04**:
https://www.blackberry.com/en/secure-communications/support/end-of-life

The historical USB media copy (~2.9 GB on the Steam Deck) is **not** a complete firmware/bootloader dump, and its data content was not inspected. No verified device-specific, reproducible, complete stock firmware recovery method was found.

**G0 recovery/rollback = BLOCKED**, even if a historical general-purpose stock reload utility or unofficial file is discoverable elsewhere.

## Gate matrix

| Requirement | Status | Evidence needed to progress |
|---|---|---|
| Model and OS family of photographed device | **PASS** | Existing OS 7.0 screen shows BlackBerry 9810 |
| Known retail model/FCC mapping | **PASS (published mapping)** | Three pairs in manufacturer manual |
| Exact retail hardware variant of owner's unit | **UNVERIFIED** | Its own factory label's *model code or FCC ID only*; no serial/IMEI/PIN |
| Exact physical Qualcomm SoC | **UNVERIFIED** | Authentic board-specific component evidence, not frequency-band inference |
| Model-specific alternate OS boot | **BLOCKED** | Independently reproducible retail 9810 boot path with preservation/recovery proof |
| Complete signed-stock restore and recovery | **BLOCKED** | Authentic exact-variant files, documented complete repair scope and verified rollback |
| Physical display/input/storage/USB/power BSP | **BLOCKED** | Exact motherboard/SoC and independent board-level driver evidence |
| Off-device TorchOS ARM QEMU CI | **SEPARATE, PASS per CP006.4** | 52/52 previously accepted, no physical device evidence implied |
| Real-device installation of research ARM ELF | **NO-GO** | G0/G1/G2 and separate physical authorization, not met |

## Recommended next checkpoint

**G0.5: Resolve the connected handset's *retail model code or FCC ID* from its normal factory product label, recording only that single non-sensitive identifier.** This is a narrow identity check; it will **not itself** identify the SoC or unlock the bootloader. The owner need not send the whole label or any serial/IMEI. If label visibility cannot be achieved without risking the unit, leave G0.5 blocked and continue the already proven QEMU-only CP006.5 virtual UART reliability work.

No physical device interactions, battery removal, firmware operations, privileged USB access, personal backup reads or new runner were performed as part of preparing G0.4. Only research documentation is proposed for GitHub.
