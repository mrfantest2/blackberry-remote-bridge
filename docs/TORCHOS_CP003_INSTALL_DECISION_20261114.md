# TorchOS — controlled test installation decision

2026-11-14. **Local engineering complete; awaiting separate physical
authorization and device preflight. No installation or handset testing done.**

## Exact candidate

Application: TorchOS, version 0.2.0, stock BlackBerry OS7 Java application.
Target: the authorized Torch 9810 only.
File: `/home/SD/Projects/torchos-native-shell/torchos-native/build/TorchOS.cod`.
Size: 23416 bytes. SHA-256:
`c51215db3d4367805859c90e5eb98a24e8fa427c541df1493ff0be6c0edf825e`.
The COD is unsigned. It passed authentic JDE compilation and host packaging;
61 automated tests and 25 desktop browser checks passed.

## Signing evidence

Fresh build has no `TorchOS.csl`; `TorchOS.cso` lists RIMAPPSA2, RBB, RCI and RCR.
Codex inspected only local vendor tool bytecode with `javap`; SignatureTool was
not executed, no signing registration/key files were opened and no request was
sent. In `net.rim.device.codesigning.signaturetool.ap`, the caller passes `.csl`
to the four-string method whose table entries say `Required`; `.cso` goes to
the method with the boolean argument whose entries say `Optional` or
`Not Required`. The inspection outputs remain in
`/tmp/torchos-cp003-signaturetool-ap.txt` and `...-q.txt`.

Thus optional signer entries alone are not evidence of missing mandatory
signatures. This build has **no compiler-reported mandatory signing list**.
That does not prove the handset will load it or accept all runtime APIs. If
preflight/loading identifies a required missing signature, stop. Never spoof,
skip or disable code-signing enforcement. Do not assume the earlier unrelated
BrowserField/RRT requirement applies to this offline application.

## Why reboot authorization is material

The local Barry source explicitly documents and implements automatic reset
when the handset replies `RESET_REQUIRED` to session cleanup:

- `src/barry-master/tools/bjavaloader.cc` calls `StartStream()` and eventually
  `StopStream()` for loader sessions, including queries.
- `src/barry-master/src/m_javaloader.cc`, `JavaLoader::StopStream()`, sends
  Goodbye and sets `ResetOnClose(true)` on a reset-required reply.
- `src/barry-master/src/socket.cc` sends the reset packet when that flag is set.

Those paths are under `/home/SD/BlackBerryBridge/`. No loader/source was changed
or executed. The local tool exists under
`src/barry-master/tools/bjavaloader` but is not on PATH. The inspected source
does not establish that any given handset session will require a reset.
It does establish that a no-reboot promise would be unjustified for this path.
No attempt will be made to suppress reset protocol or bypass platform behavior.

## Proposed authorized scope, not executed

1. Obtain explicit permission for device preflight, installing only this TorchOS
   module and initial TorchOS testing. The scope must include any reboot
   required by the chosen loader; otherwise establish another supported method
   that meets the user's no-reboot restriction before touching the device.
2. After authorization, identify only the intended Torch/model/OS and confirm
   backup/recovery readiness, adequate power/free space and current module
   inventory. Do not read private archives or alter other devices. A USB-volume
   backup is not automatically a complete firmware/user-data recovery image.
3. Revalidate the exact candidate hash and metadata. If an existing TorchOS
   module would be replaced without explicit update scope, or another gate is
   uncertain, stop before load. Never erase a module to make installation work.
4. Load only the accepted TorchOS COD using the supported module loader. No
   wipe, reset-to-factory, force erase, firmware update, repartition, signing
   bypass, production-service change or S25Hub action is in scope. No unrelated
   manual reboot is implied by conditional loader-reset permission.
5. If allowed installation succeeds, test icon/launch, all modules, 480 x 640
   native layout, touch/trackpad/QWERTY, terminal bounds/history/draft behavior,
   local battery, permission denial, read-only files and RMS persistence after
   process restart. Keep real-device evidence separate from simulated QA.
   Do not enable a gateway, network diagnostics or remote commands.
6. If installation or testing fails, record the nonsecret error and stop. Any
   uninstall, recovery, data export or additional handset change needs its
   authorized scope; no automatic destructive rollback.

The user's original safety requirements explicitly require separate permission
for all physical installation/testing. The question about when installation can
happen did not grant it. Current status is **ready for an authorization
decision and controlled preflight**, not proof of physical installability.
