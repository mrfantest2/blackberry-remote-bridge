# TorchOS roadmap after CP003 offline repairs

Date: 2026-11-14. CP003 is an offline engineering checkpoint; the older CP002
roadmap's physical-install milestone remains a separate authorization gate.

## Current accepted foundation

Terminal control-input rejection and preview parity, defensive Notes saves,
and report decode consistency are repaired. Terminal history now preserves typed
drafts, including empty-history navigation and rejected-submission reset.
Sixty-one host automated tests,
authentic JDE compilation, packaging checks and 25 desktop 480 x 640 preview checks
pass. Native application version is still 0.2.0. No handset installation,
secure transport, live remote module or Linux environment is claimed.

## Next offline engineering batch

1. Terminal draft preservation is complete and independently accepted; see
   `TORCHOS_CP003_HISTORY_QA_20261114.md`. Next evaluate physical Menu/QWERTY
   history access and long-output focus on real OS7 before choosing new bindings. Keep eight local commands,
   input/output/history limits and complete offline operation. Add targeted
   behavior regressions for any change and retain native/preview parity.
2. Notes/reports: avoid redundant writes after Save then Back; design explicit,
   user-authorized corrupt-store recovery/export without silently replacing
   records. Keep failed-write outcomes unconfirmed and block unsafe retries.
3. Local status: add an explicit snapshot refresh only if supported and tested.
   Keep battery permission failures visible and memory labeled app runtime.
4. File Manager: expand behavioral permission/depth/listing failure coverage
   under host doubles; retain direct-child validation, READ-only opens, bounds
   and no file-content access until a separately reviewed feature needs it.

## Physical readiness milestone — separate permission required

The current compiler emitted only optional signing metadata and no mandatory
signature list. Review the exact candidate and conditional loader-reboot scope
in `TORCHOS_CP003_INSTALL_DECISION_20261114.md`, then obtain explicit scoped
preflight/installation/testing permission, including a possible required reboot.
Stop if the handset reports a required missing signature. Verify native launch, UI/focus/scrolling, slide QWERTY,
touch/trackpad, local battery, JSR-75 permission denial and RMS persistence after
process restart. Do not infer reboot permission. See
[installation gates](TORCHOS_CP003_DEPLOYMENT_READINESS_20261114.md).

## Security Center future checksumming architecture

Current checksum control stays disabled. A future offline checksum feature
needs an explicit user-selected single file, a verified supported hash API,
read-only streaming in bounded chunks, an agreed file-size/time budget,
cancellation and guaranteed connection closure. Report algorithm, bytes read
and failure status honestly; never auto-enumerate private files or silently
save filenames/content. Review protected API/signing and native permission
requirements before implementation. This is architecture only: no checksum
code or file-content reader was added in CP003.

## Secure read-only gateway milestone

First prove a transport with verified peer identity and encryption acceptable
to the legacy handset; never weaken TLS. Design enrollment, per-device keys,
revocation, startup key rotation, durable replay/clock policy, rate/size limits
and redacted auditing. Keep `status`, `network`, `services`, `inventory` as the
only operations; each must map to a narrow read-only provider without shell
text. Independently review and test before any service exposure or production
configuration. Current contract remains detached and cannot serve live data.

## Secondary integrations

Only after secure pairing and explicit data scope: approved CamDoor events,
EchoVault/Tahani metadata and Project Monitor summaries through read-only
operations. Preserve Notes and disconnected placeholders. No private-media
auto-sync, credential collection, network scanning or unrestricted command
execution. Remote actions require a later independently reviewed scope and
new explicit authorization.
