# TorchOS CP003 — independent engineering acceptance

Historical first CP003 acceptance below. The current terminal-history follow-up
is documented in [latest acceptance](TORCHOS_CP003_HISTORY_QA_20261114.md);
[current install decision](TORCHOS_CP003_INSTALL_DECISION_20261114.md) records
the new artifact and conditional loader-reboot requirement.

Date: 2026-11-14. Repository: `mrfantest2/blackberry-remote-bridge`.
Branch: `feat/torchos-native-shell-20261114`.
Parent handoff: `38b8af9999368dd792810f238856695b038ce7e6`.
CP002 baseline: `60aef4b39e7218cfc326437ea325d1796325e495`.

## Decision

**ACCEPTED for a source checkpoint; physical installation remains HOLD.**
Codex independently reviewed every application/test diff and ran the complete
test matrix and authentic host build. All application and committed test changes
were written by OpenCode 1.19.5 using exactly
`opencode/deepseek-v4.1-flash-free`, in three sequential bounded invocations of
one session. Codex authored supervision, independent QA procedures and evidence
documents. No competing coding agent or fallback model was used.

The model prerequisite was genuinely met: a bounded, no-tools probe returned
`TORCHOS_CP003_MODEL_OK`, exit 0, on 2026-11-14 at 02:46:54 UTC. CLI catalog and
version were checked separately. `opencode auth list` reported zero credentials;
no auth file was read and no global configuration changed. The former timeout
does not describe this successful probe.

## Implemented fixes

1. Terminal validates raw input before trimming. U+0000..U+001F and DEL cannot
   be normalized into valid commands, enter history, or be echoed raw. Native
   and preview semantics match, including ordinary surrounding ASCII spaces.
   The eight-command allowlist, no-argument syntax, 96-character input,
   4096-character output and 16-entry session history remain bounded.
2. Notes revalidate the existing RMS record's size and codec immediately before
   replacement. Corrupt, oversized and unexpected-record-count states block
   writes and further saves. Storage/open/write/close uncertainty also blocks
   further saves in that session. Invalid drafts are rejected before storage
   access and remain retryable after correction. Format/version and namespaces
   are unchanged; no user-data migration or deletion occurs.
3. Report decoding accepts the valid seven-byte empty-string record emitted by
   its own encoder. Fresh load and empty/nonempty replacements now roundtrip.
   Magic, version, trailing-data, 384-character and 1024-byte protections remain.
   Save errors describe uncertain persisted state honestly.

The native application version and UI checkpoint text remain `0.2.0` / CP002;
CP003 is this engineering checkpoint, not a rewritten application or Linux OS.
No new physical keyboard binding was added. Enter, native focus traversal,
history controls, Back and scrolling retain their existing implementations.

## Independent test results

| Command / check | Result | Evidence classification |
|---|---|---|
| `bash torchos-native/test.sh` | 41/41 PASS, exit 0; 4.037 seconds | Host JVM/UI/RMS doubles, source contracts, Node DOM doubles, Python gateway |
| `python3 -B -m unittest discover -s tests -q` | 9/9 PASS, exit 0 | Original companion protocol host tests |
| `python3 -B -m unittest discover -s blackberry-s25-native/tests -q` | 7/7 PASS, exit 0 | Original S25Hub host regressions |
| Complete automated suite | **57/57 PASS** | Original 52 retained, five new named regressions |
| New regressions against unchanged handoff source | Five expected failures independently reproduced | Differential QA in temporary harnesses; repository source untouched |
| `bash -n torchos-native/build.sh torchos-native/test.sh` | PASS, exit 0 | Shell syntax |
| `git diff --check` | PASS, exit 0 | Whitespace inspection |
| Explicit Chrome 480 x 640 viewport | 15/15 PASS | Real desktop browser, scripted interactions; not native handset QA |
| Native portrait budget | 632/640 pixels including synthetic chrome | Host font/UI doubles only |

The five new regressions cover raw terminal controls, preview parity, Notes
revalidation after load, Notes failure blocking, and empty report roundtrip.
Detailed terminal/storage assertion counts and all test names are preserved in
[native output](TORCHOS_CP003_NATIVE_TEST_OUTPUT_20261114.txt).
The existing ten gateway tests cover MAC/device/operation rejection, replay,
expiry, clock rollback, strict types, capacity exhaustion and concurrent replay.
[Companion output](TORCHOS_CP003_COMPANION_TEST_OUTPUT_20261114.txt) and
[S25Hub output](TORCHOS_CP003_S25HUB_TEST_OUTPUT_20261114.txt) are independent runs.
OpenCode's own red/green reports are retained separately in
[implementation evidence](TORCHOS_CP003_OPENCODE_IMPLEMENTATION_REPORT.md).

## Authentic compiler and packaging

Codex ran the existing `bash torchos-native/build.sh` on the authorized host
outside the restricted sandbox with approved execution. Exit **0**. JDE 7.0,
Temurin Java 8u512, WTK 2.5.2 and existing local 32-bit libraries were used.
Full unabridged [compiler output](TORCHOS_CP003_BUILD_OUTPUT_20261114.txt) is
committed as evidence. Relevant output:

```text
openjdk version "1.8.0_512"
warning: [options] source value 1.3 is obsolete and will be removed in a future release
warning: [options] target value 1.3 is obsolete and will be removed in a future release
warning: [options] To suppress warnings about obsolete options, use -Xlint:-options.
Note: .../torchos-native/src/TorchOS.java uses or overrides a deprecated API.
Note: Recompile with -Xlint:deprecation for details.
3 warnings
Resolving
Optimizing
Populating
No errors.
```

The first unchanged-baseline build inside the Codex sandbox failed at preverify,
RAPC exit 97. The historical handoff identified SIGSYS there; this run's RAPC
output only says preverifier failed, so no fresh signal number is asserted.
The same baseline and final source both built successfully through approved
host execution. No compiler/preverify bypass, toolchain installation or OS
configuration change was used.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `build/TorchOS.cod` | 23296 | `31a916a3cbec455196d83f9145d1a45bb2bc700bb59a9be255b53beeed7221af` |
| `build/TorchOS.jar` | 56216 | `9b1dbdde7371847e8c7ee8f6207dbb225f1a665f89490e71a22660baceb2a6b0` |
| `build/TorchOS.jad` | 480 | `1f6dd3ede58563c3600a043dceb1f7f4eaa66dc67990723279f8d7083f58076c` |
| `TorchOS.alx` | 409 | `08e95536e5cf5cd8c342c24c2158f96e102cd0f973a5e29e854f6d275ed988b8` |

Paths above are relative to `torchos-native/`. Binaries remain ignored local
outputs. COD grew 284 bytes from the CP002 artifact; JAR grew 271 bytes.
RAPC embeds creation metadata, so rebuilding even unchanged baseline source did
not reproduce the historical COD hash. No reproducible-build claim is made.

Independent packaging checks passed: nonempty outputs; COD magic; JAR CRC,
entry class and Java class major version 47; actual JAR/COD sizes vs JAD; COD
SHA-1 vs JAD; module/entrypoint/version and ALX build fileset. JAD dependency is
`net_rim_cldc`. Full values and source/preview checksums are in
[artifact verification](TORCHOS_CP003_ARTIFACT_VERIFICATION_20261114.json).
These checks do not establish signatures or physical installability.

## Review and preview evidence

Codex reviewed control rejection ordering, mutation boundaries, fail-closed
storage state, bounds before allocation, Java 1.3 compatibility, source scope
and test retention. No new imports, network execution, file writes, transport,
secrets, protected-API bypass or service integration were introduced.

Read-only browsing still uses only OS-supplied roots and sanitized direct child
names, `Connector.READ`, a 64-entry cap and an eight-level cap. Network Center
clearly reports unsupported diagnostics. Battery uses `DeviceInfo`; memory is
explicitly Java application runtime memory. Labels are local owner labels,
not discovery/pairing. Notes and all secondary modules are preserved. Gateway
source is unchanged and remains a detached authenticated contract without
transport, pairing, listener, diagnostic provider or dispatcher.

The [480 x 640 screenshot](TORCHOS_CP003_PREVIEW_480x640.png) is desktop Chrome
rendering of the final offline preview. The entire home and footer fit.
[Browser evidence](TORCHOS_CP003_BROWSER_QA_20261114.json) records actual
viewport, seven home rows, ArrowDown focus, shortcut/input focus, Enter submit,
control rejection, bounded output scrolling, history focus, Escape focus
restoration and all primary module navigation. The first DOM-only browser
attempt used Chrome's minimum window geometry (500 x 553) and failed the
viewport check; a DevTools pipe then explicitly set 480 x 640 and all checks
passed. No debugging listener or persistent Flatpak permission was created.
Temporary QA fixtures/profiles are confined to ignored `build/` and `/tmp`.

## Outstanding defects, limits and preservation

No unresolved release-blocking defect was found in this bounded offline repair
diff. This is not exhaustive OS7 or security certification. Remaining work:

- Physical launch, QWERTY/trackpad/touch, fonts/chrome, permissions, scrolling,
  and RMS durability after process/handset restart remain **NOT TESTED**.
- Signing requirements and valid signatures remain **UNVERIFIED**; generated
  metadata is analyzed in the readiness report. No credential search/signing
  or device operation occurred.
- There is no recovery/export workflow for a corrupt store. Fail-closed state
  can prevent saves until an independently authorized recovery; restarting
  does not repair corrupt data. Save then Back can still repeat an unchanged
  write; deduplication and draft-history UX are future improvements.
- Local status is a snapshot; refresh is by reopening. No system-wide RAM/CPU,
  network diagnostic, file checksum or remote metric is claimed.
- Modern TLS, secure transport/pairing/revocation and durable replay policy
  remain blocked/unimplemented. No production gateway is deployable.

The original checkout still reports the same 17 pre-existing status entries;
its source/data were not edited. S25Hub, personal backups, production services
and BlackBerry firmware were not modified. No device read/write, signing,
installation, reboot, wipe or flash command was run. Publish scope is only the
existing feature branch after this independent source acceptance.

## Publication receipt

Verified source checkpoint: `b162fe7b0adfb50cf9020d882bc959b072389fa6`.
`git push origin HEAD:refs/heads/feat/torchos-native-shell-20261114` succeeded;
`git ls-remote` confirmed that exact SHA on the existing GitHub feature branch.
The feature worktree was clean after publication. This subsequent documentation
receipt does not change the tested application, tests, preview or artifacts.
