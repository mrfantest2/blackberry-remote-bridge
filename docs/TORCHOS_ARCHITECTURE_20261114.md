# TorchOS — architecture and feasibility (2026-11-14)

## Decision
**Build a native BlackBerry OS 7 shell, not a firmware replacement.** This is the original private `mrfantest2/blackberry-remote-bridge` project, with a separate implementation worktree and feature branch. No stock phone OS has been erased or modified by this checkpoint.

Physical target: BlackBerry Torch 9810, verified USB 0fca:8004 on Bazzite Deck. Prior physical OS evidence: 7.0.0.296. Screen 480×640, touch + trackpad + slide-out QWERTY, 1.2GHz CPU and 768MB RAM. This is a low-power front end, not an Android/modern Linux target.

A full replacement OS is **not a validated feasible deployment path**. It would require verified alternate boot-chain/firmware loading, board support, touchscreen/keyboard/display drivers, storage, power, radio, and recovery images. No reproducible alternative boot image or restore path was established. Do not flash/wipe/repartition/erase or claim a bootloader unlock. The prior USB volume backup is not a recovery-capable firmware image.

## TorchOS native v0.1
- Genuine BlackBerry JDE 7.0 Java UiApplication program, entrypoint `TorchOS`.
- 480×640 native home rows: Devices; Camera; Archives; Network; Notes & Tasks; Settings/About menu.
- Trackpad/touch navigation and 1–5 or D/C/A/W/N, S for settings; local clock. Client-side preview shares this language but is HTML mock, not phone code.
- Devices: S25, Steam Deck, MASTER-PC; camera: CamDoor/C301; archives: EchoVault/Tahani; network: Abu Jamal Wi-Fi/VPN. **Every external data panel says Not connected**.
- Notes/tasks remain in RAM for session only; draft not persisted; 512 character bound. No live camera, external controls, device telemetry, backend authentication, or archives playback in v0.1.
- Build: `cd torchos-native && ./build.sh`; tests: `./test.sh`. The build uses an authentic local JDE and JDK8 plus WTK/i686 compatibility libs. COD output is ignored by Git.

## Next modules by usefulness
P0: Persist user notes locally with safe BlackBerry RMS and explicit delete/export flows; add battery/local storage readings when verified against physical OS7 API.
P0: Read-only network/device health from a modern Steam Deck bridge, with separate short-lived authorization and secure handset-to-gateway transport validated on hardware.
P1: CamDoor motion event list and low-resolution JPEG snapshots served by the Deck (no unsupported modern streaming on Torch).
P1: Wi-Fi/router and GitHub/QA status, jobs watch summaries through an allowlisted backend adapter; only server-side GitHub integration.
P2: Offline cache of selected EchoVault transcript snippets, memorial audio metadata, and opt-in small media files; never publish or automatically download private content.
P2: Explicitly approved actions (e.g. ring S25) only after device-specific auth, on-device confirmations, scoped permissions, anti-replay, auditing.

## Security and platform limits
- BlackBerry's proprietary legacy infrastructure ended in 2022; never rely on this handset for emergency calling or time-critical communications.
- BlackBerry OS7 TLS to current Cloudflare is not confirmed; earlier installed S25Hub/probes demonstrated TLS errors. Do not disable certificate validation or lower public TLS security; a dedicated constrained local bridge needs design and physical validation.
- Do not embed private data, PINs, account tokens, screenshots or backup contents in the source or GitHub.
- No background root/admin shell or arbitrary device command execution.
- Phase gates: authentic COD builds; static+host tests; private physical USB install only after reviewed approval; launch/keyboard/touch QA; stable secure transport; backend pairing; real read-only data; actions only after security review.
- Always maintain a full recoverable *user data* backup and recovery procedure before any destructive handset operation. None is authorized in this checkpoint.

## Workspace
Source GitHub repo: `mrfantest2/blackberry-remote-bridge`.
Original dirty checkout preserved: `/home/SD/BlackBerryBridge/project`.
Isolated development worktree: `/home/SD/Projects/torchos-native-shell` on `feat/torchos-native-shell-20261114`.
Preview: `torchos-native/preview/index.html`; not hosted or installed.
