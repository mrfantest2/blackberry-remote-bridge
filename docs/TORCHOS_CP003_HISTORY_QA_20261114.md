# CP003 terminal history follow-up — independent acceptance

2026-11-14, resumed from published `eb0198117157cacb4bd0226151edffbc444ad14e`
on `feat/torchos-native-shell-20261114`. **Accepted for source publication.**
Physical installation/testing is not authorized or performed.

## Implementation and review

OpenCode 1.19.5 with exactly `opencode/deepseek-v4.1-flash-free` wrote the
application and committed regression changes. Codex supervised two serial
batches (initial change, review repair), independently reviewed all diffs and
ran acceptance QA. A fresh bounded probe returned `TORCHOS_CP003_RESUME_OK`,
exit 0. No model/provider fallback or global configuration change occurred.

Previous/Next now preserves the exact typed draft when returning from history.
Empty history and repeated Next keep the live input. Native draft-aware
overloads retain legacy no-argument compatibility. Drafts are session-only,
bounded to 96 characters, and navigation does not execute, echo or append them
to history. Existing 16-entry history and 4096-character output limits remain.
Native button actions pass the current EditField text and restore focus.
The HTML preview matches, including Help/Clear clearing input and restoring
focus. No keyboard binding, app version, persistence, module or gateway change.

Independent Chrome QA rejected the initial implementation: a rejected command
could restore a stale draft after input clearing. Codex returned the exact
reproduction to OpenCode. The accepted repair resets browsing state before
null/length/control rejection guards; accepted history additions still place
the cursor at the newest position. Rejected input is neither echoed raw nor
stored. See [OpenCode evidence](TORCHOS_CP003_HISTORY_IMPLEMENTATION_REPORT_20261114.md).

## Independent verification

| Check | Result |
|---|---|
| `bash torchos-native/test.sh` | 45/45 PASS, exit 0; 4.551 seconds |
| Original companion tests | 9/9 PASS, exit 0 |
| Original S25Hub tests | 7/7 PASS, exit 0 |
| Total automated tests | **61/61 PASS**, retaining the prior 57 |
| Four new regressions against older code | All four expected behavioral failures independently reproduced |
| Real Chrome, explicit 480 x 640 viewport | **25/25 PASS** |
| Native portrait budget | Synthetic host result 632/640 pixels |
| Authentic JDE 7.0 build | Exit 0, `No errors.` |
| Packaging and shell syntax / whitespace | PASS |

Draft-preservation regressions fail against published `eb01981`; rejected-input
reset regressions fail against the captured first implementation. Temporary
harnesses were used without modifying repository application source.
The full test output is in [native evidence](TORCHOS_CP003_HISTORY_NATIVE_TEST_OUTPUT_20261114.txt),
[companion evidence](TORCHOS_CP003_HISTORY_COMPANION_TEST_OUTPUT_20261114.txt), and
[S25Hub evidence](TORCHOS_CP003_HISTORY_S25HUB_TEST_OUTPUT_20261114.txt).

The browser checks cover home layout, focus, Enter/Escape, scrolling, history
restoration, empty history, repeated Next, edited-draft recapture, no navigation
execution, reset after accepted/rejected submissions, Clear and all primary
modules. Its executed script was checked against the exact final production
preview script. [Browser results](TORCHOS_CP003_HISTORY_BROWSER_QA_20261114.json)
and [screenshot](TORCHOS_CP003_HISTORY_PREVIEW_480x640.png) are desktop evidence.
Native JVM/UI/RMS doubles and browser rendering are not physical handset tests.

## Compiler, artifacts and warnings

Existing authentic JDE 7.0 / Temurin 8u512 / WTK preverifier were used directly
on the authorized host. No tool installation or preverifier/signing bypass.
[Full compiler output](TORCHOS_CP003_HISTORY_BUILD_OUTPUT_20261114.txt) records
three Java obsolete source/target warnings, a deprecated-API note and two RAPC
warnings that the legacy no-argument `previous()` / `next()` wrappers are not
invoked by the application. The wrappers are retained for compatibility with
the original tests; native controls use the new draft-aware overloads.
RAPC ends with `No errors.` These additional warnings are disclosed, not hidden.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `build/TorchOS.cod` | 23416 | `c51215db3d4367805859c90e5eb98a24e8fa427c541df1493ff0be6c0edf825e` |
| `build/TorchOS.jar` | 56540 | `5654297bb6ab6c26d66573e43963f4d6f510c8bc4ef28a58f0692143f8e2c98d` |
| `build/TorchOS.jad` | 480 | `371d689d984e66140fea5d8a33cc5dbde93411b7c5125dd62cc08c41d428f0ea` |
| `TorchOS.alx` | 409 | `08e95536e5cf5cd8c342c24c2158f96e102cd0f973a5e29e854f6d275ed988b8` |

Artifact paths are relative to `torchos-native/`. COD/JAR/JAD remain ignored
local outputs. Verification covered JAD URLs/actual sizes/COD SHA-1, JAR CRC
and entry class, class major version 47, COD magic, ALX identity/version/fileset
and `net_rim_cldc` dependency. App version remains 0.2.0. Full metadata and
source/preview SHA-256 values are in
[artifact evidence](TORCHOS_CP003_HISTORY_ARTIFACTS_20261114.json).

## Installation decision and remaining work

The fresh build emitted the same optional `.cso` entries and no mandatory
`.csl` list. Static inspection of the supplied vendor signing tool confirms
`.cso` and `.csl` are classified separately as optional and required. This is
evidence of no compiler-reported mandatory signing requirement for this build,
not evidence of signatures, handset loading or handset security policy.

Read-only inspection of local Barry source found conditional automatic reset
on session cleanup. No loader was executed. Before any JavaLoader session or
install/testing, obtain explicit scoped physical authorization covering a
possible loader-required reboot, or independently establish a supported
no-reset method. See the concrete
[install decision](TORCHOS_CP003_INSTALL_DECISION_20261114.md).

No release-blocking defect remains in the reviewed bounded diff. Physical
QWERTY/trackpad/touch, font/chrome, native scrolling, permission handling and RMS
durability remain untested. Drafts do not survive process restart. Notes write
deduplication, corrupt-store recovery and explicit status refresh remain future
offline work. Live transport/pairing and all remote metrics remain unavailable.
Original checkout, S25Hub, backups, services, firmware and other devices were
not modified. Only the existing feature branch is eligible for publication.
