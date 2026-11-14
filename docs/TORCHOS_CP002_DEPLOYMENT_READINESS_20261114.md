# TorchOS CP002 — physical installation readiness and rollback
Date: 2026-11-14 | Target BlackBerry Torch 9810 (stock OS 7.0), 480×640

## Decision
**READY FOR REVIEW; NOT APPROVED TO DEPLOY.**
A genuine JDE 7.0 `TorchOS.cod`, JAD and ALX were produced on the Steam Deck. A separately authorized user decision is required before any physical install, uninstall, user-data change or device reboot. No firmware wipe/flash/repartition/replacement is part of this release.

## Gates and evidence
| Gate | State | Evidence |
|---|---|---|
| Authoritative source branch and baseline | PASS | Existing feature worktree began clean at `974be674` |
| BlackBerry USB | PASS enumeration only | Steam Deck `0fca:8004` |
| Authentic Java OS7 binary | PASS host build | RAPC exit 0; COD 23012 B, SHA-256 below |
| ALX/JAD metadata | PASS host inspection | 0.2.0, entrypoint TorchOS |
| Existing 29-test baseline preserved | PASS | 13 native + 9 protocol + 7 S25Hub |
| Expanded QA | PASS host-side | 36 native total + 9 + 7 = 52 tests |
| Visual preview | PASS desktop-only | Offline Chrome 480×640 screenshot; no hardware QA |
| Required BlackBerry code signing | UNVERIFIED | JDE has SignatureTool.jar, no validated legacy signing credentials in audited project/toolchain scopes |
| JSR-75 file permissions | UNVERIFIED | JDE compiles read-only file listing but physical permission behavior unknown |
| Native launch, focus, scrolling, physical keyboard | NOT TESTED | No installation performed |
| RMS notes/report durability after handset restart | NOT TESTED | Host doubles only |
| HTTPS or authenticated Deck backend | BLOCKED / NOT IMPLEMENTED | Earlier legacy native TLS failed; no proven secure transport or enrollment |
| Production deployment | HOLD | No install authorization; original services and OS untouched |

Final generated COD local path: `/home/SD/Projects/torchos-native-shell/torchos-native/build/TorchOS.cod`.
SHA-256: `1046f042da3bf0b1e106d25c98c0d9fc3c45d5ce5228bf006fa117a641fd7d2c`.
Do not assume this binary is signed or installable solely because it compiles.

## Controlled future installation procedure — NOT executed
1. Obtain **explicit physical-device deployment authorization** for installing the isolated TorchOS COD; separately authorize any reboot if needed. Do not infer approval from CP002 development scope.
2. Verify physical BlackBerry model, OS build, power, free space, current app modules and backed-up user data; preserve independent backup and avoid all unrelated modules. Prior USB volume backup is **not** a full flash/firmware recovery image.
3. Audit actual code-signing requirements from COD dependencies / signature metadata and available valid credentials. If a signature is required but unavailable, **STOP**; never spoof the RRT key or bypass native security prompts.
4. Review COD/JAD/ALX checksums and verify USB connection. Use a narrowly scoped, user-approved Barry loader operation to add **only** `TorchOS`; no OS install, mass erase, reset or S25Hub modifications.
5. On physical Torch, verify native icon, launch, portrait 480×640 layout, touch/trackpad/QWERTY, terminal allowlist, Notes RMS persistence after process restart, bounded report save/read, local battery/app runtime readings, permission handling for read-only files, and truthful unavailable remote status.
6. Document dated device evidence. If blocked or errors occur, leave firmware/data intact; capture nonsecret error classification only.

## Rollback strategy — user authorization required if physical changes occur
Only if TorchOS was independently installed and a rollback is approved: record module inventory before/after, close TorchOS, uninstall **only** TorchOS COD through a supported module-specific loader, then check S25Hub and other apps remain. Do not wipe BlackBerry OS, factory reset, or delete unrelated RMS/private data. If removal would jeopardize saved TorchOS notes/reports, back up/export with explicit approval before removal; there is no CP002 export implementation yet.

## Next release checkpoints
CP003: explicit physical install consent and safety QA (native app launch, signing, permissions, keyboard/trackpad, real RMS behavior).
CP004: secure transport feasibility and device enrollment to the preexisting Deck hub, strong per-device revocable scopes and durable replay/nonce policy; tests before enabling read-only live diagnostics.
CP005: authorized CamDoor event snapshots, EchoVault archive metadata and GitHub project status via verified read-only gateway; opt-in local caches only.
No public admin endpoint, no standalone unrestricted SSH shell, no credential capture, no network scanning and no Parrot OS installation.
