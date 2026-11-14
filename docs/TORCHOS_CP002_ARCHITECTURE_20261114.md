# TorchOS CP002 — Parrot-inspired pocket workstation architecture
Date: 2026-11-14 | Branch: feat/torchos-native-shell-20261114 | Platform: BlackBerry Torch 9810 / stock OS 7.0

## Decision
**TorchOS is a native BlackBerry Java application on stock BlackBerry OS 7, not Parrot Linux or a replacement operating system.** No bootloader modifications, OS flashing, factory reset, partition writes, service changes, or handset installation were performed.

Development checkout: `/home/SD/Projects/torchos-native-shell`.
Original dirty checkout: `/home/SD/BlackBerryBridge/project` (preserved).
One original private GitHub repository: `mrfantest2/blackberry-remote-bridge`. No duplicate application repository.

Visual language: original TorchOS identity, dark charcoal/navy panels, mint/cyan focus states, compact monospaced terminal where available, 480×640 portrait, touch / optical trackpad / QWERTY. Fully self-contained offline HTML preview in `torchos-native/preview/index.html`; generated design screenshot in `docs/TORCHOS_CP002_PREVIEW_480x640.png`. A browser screenshot is **not** a native device screenshot.

## Six primary native modules
1. **Terminal:** editable `local>` line, scrollable bounded output (4096 chars), bounded history (16 commands), previous/next, Run, Help, Clear, Back and virtual keyboard support. Exactly `help`, `date`, `about`, `clear`, `status`, `history`, `notes`, `files` are permitted with no arguments. No shell, root prompt, arbitrary code execution, transport, admin controls or privileged access. History is **session only**, not persistent across process restart.
2. **Network Center:** explicitly unavailable radio/network diagnostics; project labels for Abu Jamal Wi-Fi and VPN are not readings. No DNS, gateway, Wi-Fi probe, scan or router operation in CP002.
3. **Security Center:** read-only local battery/app runtime memory and RMS status. File checksums, system logs, vulnerability scanners and permission details are **not implemented**. Display labels are unambiguous.
4. **Device Manager:** real local battery through `DeviceInfo.getBatteryLevel()` where runtime permissions allow; three owner-editable, persistent device labels. Remote S25/Deck/MASTER-PC readings deliberately show Not connected. Labels are not discovered devices.
5. **File Manager:** JSR-75 `FileSystemRegistry.listRoots()` and read-only `Connector.open(url, Connector.READ)`, max 64 entries per listing and 8 folder levels, safe direct-child names. No file contents opened and no write/delete/rename/create operations. Physical permissions and OS behavior unverified.
6. **System Monitor:** local battery, Java **app-runtime allocated/free bytes** (not total device RAM), app uptime. Buttons save/view a single local diagnostics report; report stores only generated local status, capped at 384 characters / 1024 bytes. Dedicated versioned `TorchOS_CP002_Report` RMS, with corrupted-record preservation and visible read/write/close failures.

Secondary navigation: **Notes & Tasks** (512-char bounded draft, three checklist items, three 40-char owner labels stored in versioned `TorchOS_CP002` RMS); **CamDoor**, **EchoVault/Tahani**, and **Project Monitor** placeholders marked disconnected; **Settings/About**. Neither private archives nor network data are copied into the client or repository.

## Persistent data and failure behavior
The native app uses two namespaced RecordStore records, separate from the preexisting S25Hub store. Notes and local snapshot store format/version are bounded, and a malformed or oversize stored record is not silently overwritten. Failed saves, store reads and close operations surface errors and fail closed. The preview intentionally uses session-only browser memory (not genuine RMS); data disappears on reload.

## Gateway design (not deployed)
Architecture: **TorchOS Java client → future authenticated gateway transport → restricted authorized Deck diagnostics**.
Reuse plan: current `blackberry-hub.service`, read-only dashboard and original `companion/protocol.py` were audited; no production service was changed, no new listener started and no Parrot OS installed.

`torchos-native/gateway/contract.py` is a **contract library only**, with HMAC-SHA256 keyed per device supplied in process memory, strict 1024-byte envelope, allowlisted `status` / `network` / `services` / `inventory` operation names, timestamp+expiry bounds, 32-hex nonce, constant-time MAC comparison, per-device replay cache, clock-rollback defense and redacted audit fields. It has **no network listener, no command dispatcher, no credentials stored on disk, no actual diagnostic execution, no pairing or provisioning**, and therefore cannot yet supply live handset data.

Important limitations: native BlackBerry OS7 TLS to current modern services has failed prior tests; there is no accepted modern TLS trust path, no device-specific enrollment and no persisted anti-replay state. A future server must rotate session keys at startup and use a validated transport and independent authorization, never downgrade production TLS or expose admin endpoints.

## Roadmap
- **CP003, only after separate physical deployment authorization:** verify permissions/signing, install TorchOS alongside OS7, inspect native layout, focus, input, RMS read/write/restart, permissions and local files; validate genuine safety.
- **CP004:** design and physically prove a secure handset-to-Deck transport, enrollment, revocation, session-key rotation and scopes; integrate four read-only gateway operations with existing Deck services, without replacing them.
- **CP005:** approved CamDoor event thumbnails, EchoVault transcript metadata, project QA status and opt-in offline export; no private-media auto-sync.
- **CP006:** optional allowlisted remote device actions after independent security review and additional approval; no general-purpose remote shell.
