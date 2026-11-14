# TorchOS CP003 — OpenCode implementation report (T1, T2, T2 follow-up)

Date: 2026-11-14
Agent: OpenCode 1.19.5, `opencode/deepseek-v4.1-flash-free` (pinned by supervisor)
Scope: T1 (terminal validation and preview parity), T2 (notes persistence
fail-closed consistency) and the narrow ReportStore empty-record follow-up from
T3 source audit, appended separately below. T3 is not otherwise started.
No native build, no commit, no push, no handset/service/network action was performed.

## Result

T1 is implemented and green on host tests. Original tests were preserved; two
separately named regression tests were added (one native behavior test, one
preview DOM-double test). The native suite now runs 38 tests: 36 original plus
2 new regressions.

## Changes

Authorized paths only:

- `torchos-native/src/TorchOS.java` — `TerminalModel.execute`: after the null /
  96-character guard, reject any raw character U+0000..U+001F or U+007F before
  normalization. The rejection returns a visible message, does not echo the raw
  input and does not add history. Existing `trim()`, allowlist, no-argument
  syntax, 16-entry history and 4096-character output bound are unchanged.
- `torchos-native/preview/index.html` — same validation in `execute`: null and
  >96 rejected, ASCII controls rejected before normalization, and surrounding
  whitespace trimming narrowed to ordinary ASCII spaces for native parity.
- `torchos-native/tests/CP002Harness.java.in` — new `controls` mode and helpers;
  all original modes untouched.
- `torchos-native/tests/test_cp002.py` — new
  `test_terminal_control_characters_rejected_before_trim`.
- `torchos-native/tests/PreviewControlHarness.js` — new preview regression
  harness; original `PreviewHarness.js` untouched.
- `torchos-native/tests/test_preview.py` — shared harness runner plus new
  `test_preview_control_character_rejection_parity`; original assertions kept.

`docs/TORCHOS_CP003_SUPERVISOR_PLAN_20261114.md` (supervisor-created, untracked)
was not modified.

## Failing evidence before implementation (red)

Command: `bash torchos-native/test.sh`

```
Ran 38 tests in 3.426s
FAILED (failures=2)

FAIL: test_terminal_control_characters_rejected_before_trim
AssertionError: 1 != 0 : Exception in thread "main" java.lang.AssertionError:
  leading control 0 rejected

FAIL: test_preview_control_character_rejection_parity
AssertionError [ERR_ASSERTION]: leading control 0 not stored
```

Both failures reproduce the confirmed defect: controls around a valid command
survived `trim()`, were accepted/stored, or rejected input was echoed raw.

## Green evidence after implementation

Command: `bash torchos-native/test.sh`

```
Ran 38 tests in 3.416s
OK
controls: 405 assertions passed (host only)
preview: control-character rejection parity assertions passed (DOM double only)
terminal: 18 assertions passed (host only)
bounds: 25 assertions passed (host only)
```

New regression coverage:

- Native: each control U+0000..U+001F and U+007F is tested leading, trailing and
  embedded; rejected controls are absent from history, are not echoed raw, null
  is rejected, surrounding ASCII spaces still work, and the terminal recovers
  after a rejection.
- Preview: the same controls, null, ASCII-space trimming, rejection non-echo and
  recovery are exercised by the actual inline preview script under a DOM double.

`git diff --check` reported no whitespace errors. The diff touches only the
authorized `torchos-native/**` test/source/preview paths and the new CP003 report.

## Verification limits

- Host compilation and host/double behavior only; no physical Torch 9810 QA.
- No authentic JDE build was run (supervisor owns T3/build verification).
- Companion 9 and S25Hub 7 suites were not rerun under this T1 ticket.
- Preview DOM-double parity is not browser or device QA.
- T2 persistence fail-closed work and T3 audit/release evidence remain for
  supervisor assignment/verification.

## Stop

Stopped for Codex review. No commit, push, merge, install or configuration
change was made.

---

# T2 — Notes persistence fail-closed consistency

Executed only after supervisor accepted T1 and independently ran 38/38 native
tests. T1 paths, this report and the supervisor plan were preserved.

## T2 result

`NoteStore.save` now revalidates the existing single RMS record immediately
before replacement and enters a persistent blocked state after storage or close
failure. Original behavior and tests were preserved; two separately named T2
regression tests were added. The native suite now runs 40 tests: 36 original,
2 T1 regressions and 2 T2 regressions.

## T2 changes

Authorized paths only:

- `torchos-native/src/TorchOS.java` — `NoteStore.save` only:
  - draft encoding still runs before any storage access; an invalid draft is
    reported visibly, preserves existing records and does not permanently block
    a corrected retry;
  - a single existing record is size-checked (`<= 2048`) and decoded/validated
    immediately before `setRecord`; oversize records are not read, corrupt
    records are read once and never overwritten;
  - unexpected record counts are rejected before any read or write;
  - any storage exception sets the persistent blocked state and a visible error;
  - close failure after a write leaves the save unconfirmed, sets the persistent
    blocked state and makes later saves fail closed;
  - RMS name `TorchOS_CP002`, note format/version, 512/40-character field limits
    and 2048-byte record limit are unchanged.
- `torchos-native/tests/CP002Harness.java.in` — new `store_revalidate` and
  `store_fail_closed` modes plus host-double counters for opens/writes/reads and
  simulated write/close failures. All original modes remain.
- `torchos-native/tests/test_cp002.py` — new
  `test_rms_revalidates_record_after_successful_load` and
  `test_rms_storage_and_close_failures_block_later_saves`.

## T2 failing evidence before implementation (red)

Command: `bash torchos-native/test.sh`

```
Ran 40 tests in 3.494s
FAILED (failures=2)

FAIL: test_rms_revalidates_record_after_successful_load
AssertionError: 1 != 0 : Exception in thread "main" java.lang.AssertionError:
  corrupt after load blocks overwrite

FAIL: test_rms_storage_and_close_failures_block_later_saves
AssertionError: 1 != 0 : Exception in thread "main" java.lang.AssertionError:
  open failure blocks later save
```

These reproduce the confirmed defects: save overwrote a corrupt single record
introduced after load, and storage/close failures did not persistently block
later saves.

## T2 green evidence after implementation

Command: `bash torchos-native/test.sh`

```
Ran 40 tests in 3.546s
OK
store: 27 assertions passed (host only)
store_revalidate: 34 assertions passed (host only)
store_fail_closed: 32 assertions passed (host only)
```

New T2 regression coverage:

- Corrupt record introduced after a successful load: save rejected, record
  identity and write count unchanged, one bounded read, visible error, later
  saves stay blocked without reopening.
- Oversize (2049-byte) record introduced after a successful load: save rejected,
  record identity and write count unchanged, zero record reads, visible error,
  later saves stay blocked without reopening.
- Unexpected record count introduced after a successful load: save rejected,
  record identity and write count unchanged, no read, visible error, later saves
  stay blocked without reopening.
- Open failure and simulated write failure block all later saves without reopen
  or write.
- Close failure after a write is unconfirmed, visible, and blocks a second save
  without another write or reopen.
- Invalid draft leaves the existing record byte-identical, performs no storage
  open/write, is visibly reported, and does not block a corrected retry.

`git diff --check` reported no whitespace errors. No files outside the authorized
`torchos-native/**` and CP003 report paths were changed.

## T2 verification limits

- Host compilation and host RMS doubles only; no physical Torch 9810 QA.
- No authentic JDE build was run (supervisor owns build verification).
- Companion 9 and S25Hub 7 suites were not rerun under this T2 ticket.
- T3 audit/release evidence remains for supervisor assignment.

## Stop

Stopped for Codex review. No commit, push, merge, install, service, network or
configuration change was made.

---

# T2 follow-up — empty ReportStore record

Narrow follow-up from the T3 source audit. No app version change and no other
feature work.

## Finding

Confirmed: `ReportStore.save("")` encoded a valid 7-byte record
(magic 4 + version 1 + empty modified-UTF length 2), but `ReportStore.decode`
required at least 8 bytes. The save reported success, while a fresh load of the
same record failed as corrupt. This was a decode-bound defect, not an invalid
empty-report case.

## Follow-up changes

Authorized paths only:

- `torchos-native/src/TorchOS.java` — `ReportStore.decode` lower bound changed
  from 8 to 7 because an empty string is valid UTF-8/modified-UTF data. Magic,
  version, 384-character, 1024-byte and trailing-data checks are unchanged.
  `ReportStore.save` error wording for an uncertain write exception now says the
  existing report state is unconfirmed instead of claiming it was preserved.
  `NoteStore.save` uses the same honest uncertain-write wording. Behavior is
  unchanged by the wording edits.
- `torchos-native/tests/ReportHarness.java.in` — new `empty` mode and `bad`
  decode helper.
- `torchos-native/tests/test_reports.py` — new
  `test_empty_report_roundtrip_and_limits`.

## Failing evidence before the fix (red)

Command: `bash torchos-native/test.sh`

```
Ran 41 tests in 4.042s
FAILED (failures=1)

FAIL: test_empty_report_roundtrip_and_limits
AssertionError: 1 != 0 : Exception in thread "main" java.lang.AssertionError:
  fresh load reads empty report
```

The save succeeded but the fresh `ReportStore.load()` returned the storage error,
reproducing the 7/8-byte mismatch.

## Green evidence after the fix

Command: `bash torchos-native/test.sh`

```
Ran 41 tests in 3.809s
OK
empty: 30 diagnostic RMS assertions passed (host double only)
roundtrip: 14 diagnostic RMS assertions passed (host double only)
corrupt: 7 diagnostic RMS assertions passed (host double only)
failure: 8 diagnostic RMS assertions passed (host double only)
```

New regression coverage:

- empty save writes exactly 7 bytes, and a fresh store loads `""` with no error;
- empty -> non-empty -> empty replacement roundtrips through fresh loads with
  single-record writes;
- 6-byte truncation, trailing data, wrong magic, wrong version and a
  1025-byte record are still rejected;
- a 384-character report still roundtrips, while 384 wide multi-byte characters
  exceeding the 1024-byte limit are still rejected without a write.

## Follow-up verification limits

- Host JVM and RMS doubles only; no physical Torch 9810 QA.
- No authentic JDE build was run (supervisor owns build verification).
- Companion and S25Hub suites were not rerun under this narrow follow-up.
- Remaining T3 audit/release evidence stays with the supervisor.

## Stop

Stopped for independent review. No commit, push, merge, install, service,
network or configuration change was made.
