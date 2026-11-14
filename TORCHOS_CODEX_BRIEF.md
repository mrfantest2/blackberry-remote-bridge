# TorchOS native-shell v0.1 — Codex implementation brief

Project: same existing private repository `mrfantest2/blackberry-remote-bridge`; dedicated clean Git worktree `/home/SD/Projects/torchos-native-shell` on `feat/torchos-native-shell-20261114`. This is NOT a new repo. Original dirty checkout at `/home/SD/BlackBerryBridge/project` must not be touched.

## Verified facts
- Physical BlackBerry Torch 9810 on USB 0fca:8004; OS 7.0.0.296, 480x640 portrait, touch/optical trackpad/physical sliding QWERTY.
- Real BlackBerry JDE 7.0: `/home/SD/BlackBerryBridge/toolchains/blackberry-jde-7.0.0`, JDK8: `/home/SD/BlackBerryBridge/toolchains/jdk8`, WTK: `/home/SD/BlackBerryBridge/toolchains/wtk252`; see original native `blackberry-s25-native/README.md` for build prerequisites.
- Existing S25Hub native app is separate and must not be replaced/broken. Existing project has real COD build and USB installation evidence; secure native HTTPS to Cloudflare fails on Torch, so DO NOT claim live remote control works.
- Codex CLI is installed and authorized.

## Mission
Implement in this isolated worktree a first **real native BlackBerry Java OS7 TorchOS Shell preview**, not a webpage or OS firmware. Make compact, usable navigation with key/trackpad and touch. Build a genuine `TorchOS.cod` locally with JDE 7.0 if possible. Do not install or run on the BlackBerry; do not reboot/erase/flash anything. This app is a prototype launcher experience *running on top of stock OS7*, not a real replacement OS.

## Features for v0.1
1. Native Home with custom title, local clock / date if straightforward, status bar, compact five-entry menu, deterministic focus and numeric/QWERTY navigation where viable.
2. Sections: Devices (S25 / Steam Deck / MASTER-PC), Camera (CamDoor / Xiaomi C301), Archives (EchoVault / Tahani family memories), Network (Abu Jamal Wi-Fi / VPN health), Notes & Tasks, Settings / About.
3. Every external device metric/action is explicitly `Not connected` / `Preview` until a real authenticated integration exists. Never fake battery percentages or camera feed. No production credentials. No HTTP/TLS bypass.
4. Offline-first, portrait 480x640, legible on small screen. Space and font optimized. Dedicated native Java API `UiApplication` / `MainScreen`; only OS 7.0 APIs (not BB10 Android).
5. Tests and a simple readme indicating actual status, limitation, safe integration roadmap, and rollback.
6. Prefer a single Java source in `torchos-native/src/TorchOS.java`, companion `.rapc`, `.alx`, `build.sh`; follow authentic `blackberry-s25-native` build approach. All build artifacts stay in `torchos-native/build` and are untracked via .gitignore where appropriate.
7. Provide an optional 480x640 HTML **design preview** under `torchos-native/preview/` to illustrate visual language, with no network request, no real hardware claims, no dependency. Note preview is not on-device code.

## Hard constraints
- READ current checkout before modifying it. Work ONLY within `/home/SD/Projects/torchos-native-shell`; read-only access to toolchain allowed.
- Do not change `blackberry-s25-native/`, `dashboard/`, `scripts/`, production systems, other worktrees, nor unrelated projects.
- Do not perform USB writes, firmware flashing, wipe, reboot, physical install, or any alteration to handset.
- Do not change permissions/credential stores/network settings, do not bypass TLS/security, do not launch additional agents.
- Do not run git reset/clean/force-push, do not push or merge, do not commit automatically. Keep output verifiable.
- Do not copy private backups, identifiers, screenshots, SMS, contacts, or secrets into repo.
- If compiler fails, retain build-ready source and accurately report error. Tests should exercise source/layout/config checks where possible.
- A true replacement OS requires board-support, boot chain, radio drivers, signed firmware considerations and is not assumed feasible. Do not make an unlocking claim.

## Deliverables
- `torchos-native/` usable native source and build/test scripts
- `docs/TORCHOS_ARCHITECTURE_20261114.md`: feasibility, actual vs unsupported capabilities, milestones for the user's known projects
- `docs/TORCHOS_CODEX_QA_20261114.md`: exact evidence, commands, failures, test counts, artifacts
- At end, print concise changed files, compilation status, test status, blockers; stop.