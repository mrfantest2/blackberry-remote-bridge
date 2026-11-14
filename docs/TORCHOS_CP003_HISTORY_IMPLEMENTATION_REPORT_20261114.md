# CP003 terminal history draft preservation — implementation report

Date: 2026-11-14
Author: OpenCode 1.19.5 (`opencode/deepseek-v4.1-flash-free`), sole coding agent
Checkpoint: clean published `eb0198117157cacb4bd0226151edffbc444ad14e`
Branch: `feat/torchos-native-shell-20261114`
Scope: the single accepted CP003 follow-up batch only (terminal draft
preservation during history browsing). No build, commit, push, device, service,
configuration, subagent or network work was performed. Codex retains review,
build, packaging and publication.

## Files changed

- `torchos-native/src/TorchOS.java`
  - `TerminalModel` gains session-only `String draft` (`:188`); the browsing
    cursor and draft are reset before every submission's rejection guards
    (`:190-191`), and the cursor is restored to the newest entry after a valid
    addition (`:199`). `boundedDraft(String)` is at `:220`, with draft-aware
    `previous(String)` / `next(String)` overloads (`:224-236`).
  - Original no-argument `previous()` / `next()` now delegate to the overloads
    with an empty live input, preserving legacy test behavior (`:238-239`).
  - Native Previous/Next buttons pass `input.getText()` and keep restoring
    input focus (`:260-261`).
- `torchos-native/preview/index.html`
  - Session-only `commandDraft` (`:79`); browsing state resets before the
    rejection guards (`:94-95`), bounded helper plus draft-aware `previous` /
    `next` (`:115-116`).
  - Preview Help and Clear now match the native `command(help)` /
    `command(clear)` path by clearing the command field and restoring focus
    (`:122`).
- `torchos-native/tests/CP002Harness.java.in`
  - New `history_draft` behavior mode (24 assertions), new
    `history_rejected_reset` behavior mode (12 assertions), and a test-only
    reflection adapter that exercises legacy no-argument behavior on the
    baseline, then the draft-aware overloads after implementation.
- `torchos-native/tests/test_cp002.py`
  - Named regressions `test_terminal_history_draft_preservation` and
    `test_terminal_rejected_submission_resets_browsing`.
- `torchos-native/tests/PreviewHistoryHarness.js` and
  `torchos-native/tests/PreviewRejectedHistoryHarness.js` (new)
  - History-specific DOM-double regressions for the preview.
- `torchos-native/tests/test_preview.py`
  - Named regressions `test_preview_history_draft_preservation` and
    `test_preview_rejected_submission_resets_browsing`.
- `docs/TORCHOS_CP003_HISTORY_IMPLEMENTATION_REPORT_20261114.md` (this report).

The supervisor-created `docs/TORCHOS_CP003_HISTORY_PLAN_20261114.md` was left
untracked and unmodified. No other module, manifest, version, allowlist,
permission, persistence format or keyboard binding changed.

## Implemented behavior

- With history, typing `sta`, Previous, Next restores exactly `sta`.
- Only the newest position captures the live draft; repeated Previous cannot
  overwrite the saved draft.
- Returning to the newest position restores the saved draft; editing it there
  and navigating again captures the edited value.
- With empty history, Previous and Next leave the typed text intact.
- The draft is capped at `INPUT_LIMIT = 96`; null and oversized direct-model
  inputs are safe. The draft is never added to history, echoed to output or
  executed by navigation.
- Accepted submission and `clear` reset browsing state together with the
  cleared input field, in both native and preview.
- Rejected submissions (null, over-96-character, and control-character input)
  also reset browsing state before the rejection guards, so a later Next cannot
  resurrect a stale draft. Rejected raw input is never stored in history or
  echoed to output, and rejection semantics are unchanged.
- Preview Help matches native `command(help)`: it records the help command,
  clears the input, resets browsing state and restores command focus. Preview
  Clear keeps the same clear/reset/focus behavior.
- Original no-argument model history methods remain available and compatible.
- The eight-command allowlist, rejection rules, `output=4096`, `history=16`,
  Back behavior, existing controls and module boundaries are unchanged.

## Red evidence (before implementation)

Regression tests were added first and run against the unmodified sources. The
tests failed behaviorally, not through missing-method compilation, because the
harness adapter falls back to the legacy no-argument methods.

Native (`test_terminal_history_draft_preservation`):

```
FAIL: test_terminal_history_draft_preservation
java.lang.AssertionError: next restores typed draft
        at CP002Harness.check(CP002Harness.java:5)
        at CP002Harness.main(CP002Harness.java:322)
AssertionError: 1 != 0
FAILED (failures=1)
```

Preview (`test_preview_history_draft_preservation`):

```
AssertionError [ERR_ASSERTION]: next restores typed draft
  actual: ''
  expected: 'sta'
  operator: '=='
FAILED (failures=1)
```

The red failure is the observable defect: Next could not restore a draft typed
before browsing history.

## Green evidence (after implementation)

Commands were run offline from the repository.

Native full suite — `bash test.sh` (in `torchos-native/`):

```
Ran 45 tests in 4.110s
OK
```

The native harness modes include the new modes and all prior modes:

```
files: 12 assertions passed (host only)
store: 27 assertions passed (host only)
store_revalidate: 34 assertions passed (host only)
codec: 51 assertions passed (host only)
store_fail_closed: 32 assertions passed (host only)
terminal: 18 assertions passed (host only)
controls: 405 assertions passed (host only)
bounds: 25 assertions passed (host only)
history_draft: 24 assertions passed (host only)
history_rejected_reset: 12 assertions passed (host only)
```

Preview DOM-double harnesses (included in the same native suite):

```
preview: control-character rejection parity assertions passed (DOM double only)
preview: history draft preservation, empty history, reset and bounds assertions passed (DOM double only)
preview: rejected control, null and overlimit submissions reset browsing; Help parity passed (DOM double only)
preview: terminal, bounds, navigation, keyboard, session notes and honest hardware assertions passed (DOM double only)
```

Preserved baseline suites (offline):

```
python3 -B -m unittest discover -s tests -q
Ran 9 tests ... OK

python3 -B -m unittest discover -s blackberry-s25-native/tests -q
Ran 7 tests ... OK
```

Total: 45 native + 9 companion + 7 S25Hub = **61 tests PASS**. All 59 tests
from the previous history batch (and the original 57) are preserved; the two
repair additions are the named native and preview rejected-submission
regressions. `git diff --check` reported no whitespace errors.

## Supervisor review repair — rejected submissions

Independent browser QA found that a rejected submission while browsing left
the stale draft and cursor intact, so a later Next restored the old draft.
Root cause: `cursor`/`draft` (native) and `cursor`/`commandDraft` (preview)
were reset after the null, length and control-character guards, so rejected
submissions returned before resetting browsing state.

Repair regressions were added first and run against the pre-repair sources.

Native red (`test_terminal_rejected_submission_resets_browsing`):

```
FAIL: test_terminal_rejected_submission_resets_browsing
java.lang.AssertionError: rejected control does not restore stale draft
        at CP002Harness.check(CP002Harness.java:5)
        at CP002Harness.main(CP002Harness.java:395)
AssertionError: 1 != 0
FAILED (failures=1)
```

Preview red (`test_preview_rejected_submission_resets_browsing`):

```
AssertionError [ERR_ASSERTION]: rejected control does not restore stale draft
  actual: 'sta'
  expected: ''
  operator: '=='
FAILED (failures=1)
```

Fix: reset browsing cursor and draft before the rejection guards in both
`execute` implementations, then set the cursor to the newest entry again after
a valid history addition. The rejection rules, allowlist and output text are
unchanged. Preview Help was aligned with native `command(help)` by clearing
the input and restoring focus after recording the help command; Clear keeps
the same clear/reset/focus path.

Repair green:

```
test_terminal_rejected_submission_resets_browsing ... ok
history_rejected_reset: 12 assertions passed (host only)

test_preview_rejected_submission_resets_browsing ... ok
preview: rejected control, null and overlimit submissions reset browsing; Help parity passed (DOM double only)
```

The new tests verify that rejected control, null and over-limit submissions do
not enter history, do not echo raw input, and leave Next returning empty.
Full-suite totals above (45 + 9 + 7 = 61) are the post-repair results.

## Limitations and evidence classification

- Native tests execute the real `TerminalModel` source against host doubles.
  They do not prove on-device EditField, trackpad, touch or keyboard behavior.
- Preview tests execute the real inline preview script against a host DOM
  double. They are not browser rendering QA; no 480 x 640 browser session was
  run under this ticket.
- The native UI wiring (button argument passing and focus restoration) is
  source-reviewed but was not compiled or packaged here. OpenCode was not
  authorized to run the JDE build; Codex owns the authentic build, packaging
  and hash checks.
- No physical BlackBerry handset, signing, installation, production service or
  gateway transport was touched.
- Draft state is intentionally session-only and is not persisted; reloading or
  restarting discards it, matching the accepted scope.
