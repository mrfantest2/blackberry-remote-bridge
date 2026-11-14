# TorchOS Codex + RDC QA checkpoint — 2026-11-14

## Scope and provenance
- Steam Deck reached through authorized Remote Desktop Commander device `bazzite`.
- Connected USB: RIM device `0fca:8004`.
- Codex CLI 0.166.0 reported logged in via ChatGPT; ran in dedicated clean Git worktree, created native source, tests and 480×640 preview. One Codex run stalled after source/testing work and was terminated before remote packaging refinements. No production or handset operations requested.
- Original private BlackBerry repo checkout had 17 modified/untracked entries and was not reset, cleaned, rebased or overwritten.

## Real build
Build via RDC process outside the Codex tool sandbox after packaging correction:
`cd /home/SD/Projects/torchos-native-shell && bash torchos-native/build.sh`
RAPC authentic JDE 7.0; JDK8 Temurin 8u512; WTK 2.5.2 with extracted compatibility libs.
Result: **exit 0; RAPC No errors; TorchOS.cod present**. Non-blocking compiler warnings for old Java source/target and deprecated API.
SHA-256 COD: `cc9f5abfc940b4251b6a3c84b29f690d3e69097e9d82b0be9ee111ca3fccf1d3`.
Artifact: `torchos-native/build/TorchOS.cod`, about 8.5 KB; unsigned/uninstalled. JAR and JAD also produced.
Codex sandbox preverify failed under sandbox with `Bad system call`; direct RDC run established preverification works on authorized host. An earlier RAPC attempt revealed missing MIDlet attributes; fixed by adding MicroEdition-Profile and MicroEdition-Configuration to .rapc. ALX follows nested file entry structure.

## QA
Host tests: `bash torchos-native/test.sh` — 13 tests, including 65,536 shortcut assertions using host UI doubles, layout/touch/trackpad tests. This is *not* on-device UI verification.
Existing `python3 -B -m unittest discover -s tests -q` — 9 protocol tests.
Existing `python3 -B -m unittest discover -s blackberry-s25-native/tests -q` — 7 native contract tests.
Final RDC re-run: TorchOS **13/13 PASS** (65,557 host-double assertions); existing protocol **9/9 PASS**; existing S25Hub **7/7 PASS**; total **29/29 tests PASS**. Both shell scripts pass `bash -n`; valid ALX XML and MIDlet manifest tested. The initial ALX test mismatch was corrected to assert the nested `<files><file>` structure used by the known working native project, and optional module-name expectation was replaced with required MIDP/CLDC manifest assertions.
Additional checks: `git diff --check` before staging; no physical device writes.
- Physical TorchOS module installation: NOT ATTEMPTED.
- Phone launch, screen rendering, focus, navigation: UNVERIFIED ON DEVICE.
- Legacy native TLS, authenticated S25 pairing, camera, VPN, archive, actual network status: NOT IMPLEMENTED.
- Firmware replacement: NOT ATTEMPTED; no validated alternative boot chain.
- User data backup: historical USB volume copy exists; not a full flash/OS recovery image.

## Rollback
No handset changes to roll back. Remove standalone development worktree only after ensuring any feature branch commit is preserved; retain original checkout and backups.
