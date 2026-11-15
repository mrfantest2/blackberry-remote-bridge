# TorchOS CP008 — 0.3.0 resident shell + TorchLink app-local Deck control

**Status:** source, host QA and authentic JDE build complete. **Not yet installed or tested on the handset.**

## What it is

- **TorchOS 0.3.0** on stock BlackBerry OS 7, unsigned. It is not replacement firmware.
- **Resident shell:** Back on Home sends TorchOS to the background instead of quitting, so it stays running and returns instantly. Menu > Exit TorchOS quits.
- **TorchLink v1:** an owner-started, outbound Wi-Fi TCP session from the phone to the paired Steam Deck.
  - **Remote ops:** `OPEN 0-11`, `BACK`, `HOME`, `RUN <allowlisted terminal command>`, `STATUS`, `BYE`.
  - **Scope:** TorchOS's own UI only. No `EventInjector`, no other apps, no OS-wide input.
  - **Pairing:** the pairing screen is unreachable remotely.

## Why not boot auto-run (signing bisect)

The authentic JDE 7.0 `rapc` writes `TorchOS.csl` when a signature-required API is used. I bisected on the Deck:

| Item | Needs RIM Runtime API signature |
|---|---|
| `RIM-MIDlet-Flags-1: 1` (auto-run at boot) | **yes** |
| `ApplicationManager.inStartup()` | **yes** |
| `Connector.open("socket://…;interface=wifi")` | no |
| `requestForeground()` / `requestBackground()` | no |

No usable signing keys exist (see CP007), so auto-run was removed. `build.sh` now **fails if a `.csl` is produced**, so an unsigned COD that cannot start can never ship. TorchOS 0.2.0 produced no `.csl`.

## Security model

| Property | How |
|---|---|
| Key | 20 random bytes generated on the Deck (`torchlink pair`), stored at 0600. The owner types it into the phone as 32 base32 characters; it is stored in TorchOS RMS and never displayed again. |
| Mutual authentication | The phone sends `HELLO` (HMAC). The Deck must answer with `WELCOME` = HMAC over the phone nonce plus a random Deck nonce. Wrong key → session closed. |
| Integrity and replay | Each `CMD` is HMAC'd over both nonces, the sequence number, the op and the argument. The sequence must be exactly previous+1. Any MAC, sequence, format or op error **closes the session**. |
| Bounds | 512-byte lines, printable ASCII, 10 min session, 90 s idle, 500 commands. |
| Kill switch | Phone Stop button, lock screen, leaving TorchOS (`deactivate`), Exit, any error. |
| Deck listener | Requires an explicit private LAN bind (wildcard and public addresses refused) and accepts one connection. **Nothing received is ever executed on the Deck.** |
| Not provided | Encryption: commands and terminal output are visible on the LAN, though they cannot be forged. |

## Evidence

- Host QA: `scripts/test-all.sh` **120/120** (56 native + 57 companion + 7 S25Hub), up from 99. It includes 20 TorchLink tests: real Java core ↔ Python Deck interop, SHA-256 across block boundaries, RFC 4231 HMAC vectors, pairing-code parity, and replay, skip, tamper, cross-session, wrong-key, disallowed-op, expiry and oversize cases.
- Loopback end-to-end over real TCP: the Java core as the phone with `torchlink serve` on the Deck side. `open`, `run`, `back`, `status` and `bye` were all OK; `tap` was refused locally.
- Authentic JDE build on the Steam Deck (commit `35cafb3`): **no `.csl`**, `TorchOS.cod` 36,920 bytes, SHA-256 `dd038392037d0c1dd20fda03cf9345ad7ee3eb876886b1b6a4e5b01e7054ef42`.
- The JDE build also caught a host-invisible bug: `RemoteLink.save()` overrode `Screen.save()`. Fixed.

## Install gate (pending owner approval)

1. Record the module inventory (898 modules, 1 × TorchOS 0.2.0).
2. Load the 0.3.0 COD with the hash above.
3. Read back: exactly one TorchOS module, version 0.3.0, and no other module removed.
4. Owner launches it, then checks Notes persistence and the Wi-Fi permission prompt.

**Rollback:** reload 0.2.0 (`c51215db…f825e`).

## Still unverified

On-device: Wi-Fi socket behaviour, the permission prompt, `deactivate` on lock, UI dispatch, RMS migration of existing notes, and battery impact.

## On-device results (physical Torch 9810, 15 Nov 2026)

### 0.3.0 install (13:40)
- Load completed with no reboot.
- 898 modules before and after, with an identical name set.
- Exactly one TorchOS, at 0.3.0.

### TorchLink live session
The phone (Wi-Fi 10.188.1.144) connected to the Deck (10.188.1.75:47810). The handshake authenticated, and the banner showed `REMOTE CONTROL ACTIVE - Deck`.

| Command | Reply from the phone | Notes |
|---|---|---|
| `status` | `OK screen RemoteLink; Local battery: 98%` | |
| `open 1` | `OK opened 1` | |
| `back` | `OK back` | |
| `run about` | `OK TorchOS 0.3 / stock OS7 pocket workstation…` | A USB screenshot showed the Terminal screen with this output |
| `home` | `ERR home` | By design, HOME stops at the protected Remote link screen. 0.3.1 now reports this clearly. |
| — | — | Owner pressed End (left TorchOS) |
| `open 2` | refused: phone disconnected | Kill switch confirmed |

**Earlier failure, cause not determined.** In the first session, `run about` was dropped and the phone closed the session. On retry the same command worked, and a USB screenshot taken during a later live session did not end it. The phone records the reason on the Remote link screen, but it was not captured.

### Bugs found on the device, fixed in 0.3.1
- The More > Remote link row reopened More instead of the Remote link screen.
- The HOME reply was ambiguous.

### 0.3.1 install (14:33): incident
- The load completed (hash-pinned COD `a6573e46…acce2e`).
- Because TorchOS 0.3.0 was still resident, the loader **rebooted the handset**.
- After the reboot: **891 modules** and exactly one TorchOS, at 0.3.1. **7 modules were gone**: HomeScreenNotes, `net_rim_bb_facebook_lib`, `net_rim_bb_facebook_resource_high_res`, and 4 `net_rim_bb_twitter*` modules.

**Evidence from the handset's own event log (`bjavaloader eventlog`, read-only):**
- `CMM: delete net_rim_bb_twitter_… scheduled`, logged **2026/11/14 03:19**. The deletion was pending long before this session and was finalized by the reboot.
- `CMM: HomeScreenNotes(12272) no sig from 0x33 / 0x414252`, logged at **every boot**. The module was failing signature verification and was purged by the OS.
- `Error starting net_rim_bb_facebook: null`. The Facebook app module was already absent; only its libraries remained in the 898-module list.

**Conclusion:** the loader issued no delete, and the wrapper has no erase or delete operation. However, **our reboot finalized pending OS-side removals**. The preflight did not detect them.

### Procedure change (mandatory for future loads)
1. **Preflight `eventlog`**: abort if any `CMM: delete … scheduled` or `no sig` entry is pending, and report it to the owner first.
2. **TorchOS must be exited** (Menu > Exit TorchOS) before a load, to avoid a loader-triggered reboot.
3. Readback after any reboot must diff the full module list, and every difference must be explained from the eventlog before declaring success.

### 0.3.1 + Deck keep-alive session (14:46)

**Idle drops explained.** The phone's 90 s idle timer starts at WELCOME, and the operator's first command arrived later than that. `serve` now sends an authenticated STATUS keep-alive every 45 s (commit `078f1d4`). Phone-side limits are unchanged.

| Command | Reply from the phone |
|---|---|
| `open 11` | `OK opened 11` |
| `open 5` | `OK opened 5` |
| `back` | `OK back` |
| `run date` | `OK Local device clock: Sun Nov 15 14:40:15 Asia/Beirut 2026` |
| `home` | `OK stopped at Remote link (protected, owner-only)` (0.3.1 fix confirmed) |
| `status` | `OK screen RemoteLink; Local battery: 97%` |
| ~100 s idle | 2 × `(keep-alive) OK …`; session stayed open past the old 90 s limit |
| `run help` | `OK Local only: help date about clear status history notes files remote…` |
| `bye` | session ended cleanly |

**Pending:** the owner has not yet confirmed that the More > Remote link row works on the handset (fixed in 0.3.1 source).

## TorchOS 0.4.0 + ESP32 Sidecar on hardware (15:41–15:54)

**Unsigned check:** JSR-82 Bluetooth (paired-device lookup, service search, `btspp` client) builds with **no `.csl`** on the authentic JDE.

**ESP32 sidecar firmware v0.1**
- **Board:** ESP32-D0WD-V3 rev 3.1, 4 MB flash (HW-394 dev board).
- **Backup first:** the previous flash was saved as a 4 MB image on the Deck (`esp32-backups/…before-sidecar…bin`, SHA-256 `a738f465…c1b376`).
- **Flash:** `esptool` hash-verified write.

**RC522 wiring:** SDA → GPIO5, SCK → 18, MOSI → 23, MISO → 19, RST → 22, 3V3.
- **Detected:** `rfid=ok`.
- **First read, over USB:** `RFID D6D145BC MIFARE_1KB`.

**0.4.0 install**
- **Preflight:** event log clean.
- **Load:** loader-triggered reboot, even with TorchOS exited. Replacing the module itself reboots the phone.
- **After reboot:** 891 → 891 modules with an identical name set, and exactly one TorchOS at 0.4.0.

**Owner photos on the handset**
- **Launcher:** the 12-tile launcher grid renders, with focus ring and the remote banner.
- **Sidecar app connected over Bluetooth:** `INFO … rfid=ok up=941`, then `RFID ONCE` returned **`RFID D6D145BC MIFARE_1KB`**. That is the same UID as the USB read.

**Observed, to fix**
- **Missing clock line:** the Home status band shows only "Offline / stock OS7"; the clock/battery line is not visible.
- **About version string:** still reads 0.4.0 in 0.4.1.

**0.4.1 (app icon) built** (`a002e8c7…be8fc6`, no `.csl`, icon packaged), but **not installed**:
- **Blocked by preflight:** "no sig" log entries (TorchOS, `net_rim_bbid_common`, SilentCam).
- **Gate refinement:** these entries recur at every boot. Only `CMM: delete … scheduled` blocks; new "no sig" modules are reported to the owner.
