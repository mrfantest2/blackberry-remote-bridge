# CP003 follow-up — terminal draft preservation

Resumed 2026-11-14 from clean published `eb0198117157cacb4bd0226151edffbc444ad14e`
on the existing `feat/torchos-native-shell-20261114` branch. The user's resume
instruction continues autonomous offline supervision, not physical deployment.

Codex supervises/reviews/tests/documents/publishes. Sole coding and regression
author: OpenCode 1.19.5, exact `opencode/deepseek-v4.1-flash-free`; no fallback,
global configuration changes, competing agents or concurrent code batches.
A fresh bounded no-tools probe returned `TORCHOS_CP003_RESUME_OK`, exit 0.
Evidence: `/tmp/torchos-cp003-resume-probe-YhMAUB/`. Independent baseline:
41 native + 9 companion + 7 S25Hub = 57 PASS; remote ref matches local HEAD.
Original checkout still has its 17 pre-existing status entries.

## Design and scope

Implement only the first next-offline-batch item in the accepted CP003 roadmap:
draft preservation during history browsing. Retain the bounded TerminalModel,
existing native Previous/Next buttons and EditField focus. Mirror behavior in
the self-contained preview. No new keyboard binding, persistence, command,
network capability, permission, module redesign or application-version change.

Allowed edits: TerminalModel and Terminal history-control wiring in
`torchos-native/src/TorchOS.java`; `torchos-native/preview/index.html`;
CP002Harness.java.in/test_cp002.py; preview harness/test_preview.py (a new
history-specific harness allowed); and
`docs/TORCHOS_CP003_HISTORY_IMPLEMENTATION_REPORT_20261114.md`.
Codex owns other QA/readiness/roadmap documentation and final builds.

## Exact behavior and acceptance

1. With history, typing `sta`, Previous, then Next must restore exactly `sta`.
   Multiple Previous operations must not overwrite the saved draft. Repeated
   Next at the newest position must preserve the live draft.
2. With empty history, either Previous or Next must leave typed text intact.
3. The draft is separate session-only state, bounded to INPUT_LIMIT=96, never
   inserted into history or output and never executed by navigation. Null or
   oversized direct-model inputs must not cause errors or unbounded retention.
4. Browsing recalled entries must not mutate history. When the user returns
   to the newest position and edits the draft, a subsequent navigation cycle
   captures the new draft. Explicit command submission/clear resets saved
   browsing state consistently with the cleared input field.
5. Keep old no-argument model history methods compatible with original tests.
   Add draft-aware overloads (or a similarly minimal bridge) for native UI.
   Preserve the eight-command allowlist, rejection rules, output=4096 and
   history=16, Back semantics and all original 57 tests. Buttons restore input
   focus. Do not intercept native trackpad movement or add unverified key maps.
6. Preview behavior must match, including empty history, restoration, repeated
   navigation and reset after submit/Clear. No storage or external resources.

## Sequential ticket and review

- [x] OpenCode adds separately named native and preview behavior regressions,
  observes failure on current source, then implements the minimal change.
  Prefer behavioral red evidence rather than only missing-method compilation;
  a test-only compatibility adapter can exercise old no-argument history
  behavior against the baseline and draft-aware methods after implementation.
- [x] OpenCode runs the complete native suite, records exact red/green output,
  checks scope/whitespace and stops. No build, commit or push by OpenCode.
- [x] Codex reviews diff, delegates repairs if necessary, independently runs
  all three suites, authentic JDE build and packaging/hash checks.
- [x] Codex verifies explicit 480 x 640 browser navigation/focus/draft behavior,
  updates QA/readiness/roadmap and publishes only after independent acceptance.

Physical handset operations, signing, production service changes and gateway
transport remain outside authorization. All test evidence must distinguish
host doubles, browser rendering and untested physical handset behavior.

## Acceptance evidence

Initial implementation and one supervisor-requested repair were performed by
the same pinned OpenCode model in serial batches. Four new regressions were
independently verified against older code. Final independent results: 45 native
+ 9 companion + 7 S25Hub = 61 PASS; 25 browser checks at explicit 480 x 640 PASS;
authentic JDE build exit 0; packaging/source hashes checked. Application source
is accepted for the existing feature branch. Publication is the release-manager
step following this recorded acceptance; physical authorization remains pending.
