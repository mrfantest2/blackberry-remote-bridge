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
