# TorchOS CP003 — installation readiness

Date: 2026-11-14. **READY FOR AUTHORIZATION/PREFLIGHT; physical changes remain HOLD.**
This report supersedes the CP002 readiness state for the current source
checkpoint; CP002 remains historical evidence. TorchOS remains a Java
application on stock BlackBerry OS7. Application identity/version is unchanged.

## Gates

| Gate | State | Evidence |
|---|---|---|
| Exact implementation model responds | PASS | Successful pinned-model probe; OpenCode 1.19.5 |
| Independent baseline retained | PASS | 52 original tests plus nine regressions, total 61 |
| Authentic JDE 7.0 host compilation | PASS | RAPC exit 0, No errors; three Java and two unused-method warnings |
| COD/JAD/JAR/ALX consistency | PASS host inspection | Sizes, hashes, entry class, module/version and fileset verified |
| 480 x 640 HTML and interaction | PASS desktop only | Screenshot and 25 browser checks; native budget synthetic |
| Signing requirement metadata | NO COMPILER-REPORTED MANDATORY LIST; handset enforcement untested | Vendor tool classifies emitted CSO entries as optional; no CSL emitted |
| JSR-75 permissions and denial behavior | NOT PHYSICALLY TESTED | Read-only source and host safeguards only |
| Native launch, physical QWERTY, trackpad/touch, fonts/scrolling | NOT TESTED | No handset install |
| Notes/labels/report RMS restart durability | NOT PHYSICALLY TESTED | Host doubles only |
| Secure transport and pairing | BLOCKED / NOT IMPLEMENTED | Detached gateway contract only; no accepted legacy TLS path |
| Physical install or other handset changes | NOT AUTHORIZED | Separate user authorization required |

## Read-only API/signing inventory

Source uses native UI (`UiApplication`, `MainScreen`, fields, fonts, graphics,
menus, touch and virtual keyboard), local date formatting, battery via
`DeviceInfo.getBatteryLevel()`, JVM memory, RMS, and JSR-75 root/folder listings.
No BrowserField, sockets/HTTP/TLS API, permission escalation or signing bypass
is present. APIs and formats compiled with the authentic OS7 SDK.

The local SDK's `DeviceInfo.html#getBatteryLevel()` documents a battery
percentage. Its RRT warning occurs in a different method's documentation; a
class-level text search alone must not be treated as proof that the battery
method requires RRT. Local FileConnection documentation explicitly warns that
access is restricted by platform/permissions. Compilation does not prove access
on the Torch. No permission grants were requested or changed.

Generated JAD lists module dependency `net_rim_cldc`. The generated `.cso`
contains these identifiers, recorded without invoking SignatureTool:

```text
33000000=RIMAPPSA2
52424200=RIM Blackberry Apps API
52434900=RIM Crypto API - Internal
52435200=RIM Crypto API - RIM
```

No `.csl` file was emitted by the audited builds. This inventory is not a
validated signature assessment, proof of installed signatures, or permission
to omit required code signing. No signing tool was run, no credentials read,
and no signing configuration changed. The earlier BrowserField/RRT blocker
must not be transferred to this app without examining its actual dependencies;
equally, absence of an RRT line is not clearance to deploy.

## Accepted local artifacts

COD: `torchos-native/build/TorchOS.cod`, 23416 bytes, SHA-256
`c51215db3d4367805859c90e5eb98a24e8fa427c541df1493ff0be6c0edf825e`.
JAR: 56540 bytes; JAD: 480 bytes; ALX: 409 bytes. All checksums and JAD metadata
are in [artifact verification](TORCHOS_CP003_HISTORY_ARTIFACTS_20261114.json).
Authentic compiler output is in
[build evidence](TORCHOS_CP003_HISTORY_BUILD_OUTPUT_20261114.txt).
Generated COD/JAR/JAD remain local ignored artifacts, not committed releases.

## Current controlled-install proposal, not executed

See [exact candidate and authorization scope](TORCHOS_CP003_INSTALL_DECISION_20261114.md).
Read-only vendor-tool inspection now confirms that the emitted CSO entries are
optional, rather than proof of missing mandatory signatures. No signing tool
or credential access was used. Local Barry source also shows that a loader
session can automatically reset the device when it requests RESET_REQUIRED.
Separate permission must cover that possibility before any such session,
including preflight queries, or another supported no-reset method must be
verified. Nothing has contacted or modified the handset.

## Future installation and rollback, not executed

Require explicit separate physical-device authorization. Before an approved
install, verify exact model/OS, backups and recoverability, power/free space,
existing module inventory, required signatures and per-operation permissions.
Recheck the intended artifact hashes. Install only TorchOS through a supported
method if all gates pass, retaining stock firmware and existing applications.
No USB enumeration or development instruction authorizes a device write.

Physical acceptance must cover launch, all navigation/input paths, supported
local status and honest unavailable states, permission denial, read-only files,
note/label/report persistence across process restart, save/close failures where
safely testable, and the whole 480 x 640 interface. Record real handset evidence
separately from host doubles and browser images. Reboot requires its own
authorization. Stop if signatures, permissions or recoverability are uncertain.

If a future install is separately approved and rollback becomes necessary,
obtain authorization to uninstall only TorchOS, preserve its user data as
authorized, and confirm all unrelated modules remain. Never wipe, reset,
repartition, flash or replace firmware. The source checkpoint requires no
physical rollback because this work made no handset changes.
