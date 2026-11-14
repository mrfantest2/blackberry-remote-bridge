# TorchOS CP003 supervisor implementation plan

Date: 2026-11-14. Supervisor: Codex. Sole implementer: OpenCode 1.19.5,
`opencode/deepseek-v4.1-flash-free`, pinned on every invocation.

## Goal and architecture

Strengthen the existing offline OS7 application with small fixes to confirmed
defects, retaining the Java ME application, module layout, RMS namespaces,
eight-command local allowlist, branding and disconnected gateway contract.
Specifications: CP003 senior handoff and OpenCode tasks in this directory.
The user explicitly authorized autonomous sequential delegation and independent
acceptance; no competing agents or alternative model will be used.

## Preconditions verified by Codex

- Clean linked worktree on `feat/torchos-native-shell-20261114`, HEAD and cached
  origin ref `38b8af9999368dd792810f238856695b038ce7e6`; CP002 is an ancestor.
- Original checkout retains its 17 pre-existing status entries; not edited.
- Real model probe returned `TORCHOS_CP003_MODEL_OK`, exit 0, at
  2026-11-14 02:46:54 UTC. Probe evidence:
  `/tmp/torchos-cp003-probe-WnPDsG/`. Zero stored credentials reported by CLI;
  no credential files read. Global configuration unchanged.
- Independent baseline: native 36, companion 9, S25Hub 7 = 52 tests PASS.
- Sandbox build exit 97 at preverify; approved host build exit 0, RAPC
  `No errors.`, three warnings. No preverify bypass. Rebuilt COD SHA-256
  `2b616dedfbd214e24d42bd34541a9cbce8781d00b54f41e0a5052ddc57af731a`.
  This fresh binary differs from the historical CP002 artifact; do not claim
  byte reproducibility (RAPC embeds build metadata).

## Global constraints and review focus

Only `torchos-native/**` and CP003 documentation may change. Keep artifacts
ignored. No commit/push by OpenCode, global configuration changes, network
listeners, transport implementation, handset access, signing, installation,
service changes, shell execution in the application or TLS weakening.
Retain Java 1.3 / CLDC compatibility and 480 x 640 layout. All evidence is
host compilation, source review or host doubles, never physical handset QA.

Review control-character normalization, history pollution, corrupt records
introduced after load, unconfirmed close/write outcomes, and preview parity.
Each fix needs an observed failing regression before implementation.

## Sequential tickets

### T1: Terminal validation and preview parity

Files: `torchos-native/src/TorchOS.java` (TerminalModel only), existing native
CP002 test harness/runner, preview HTML and its DOM harness. CP003 report may
be added. Preserve all original tests; add separately named regression tests.

- [x] Add and run failing regressions: leading/trailing/embedded ASCII controls
  U+0000..U+001F and DEL cannot become accepted commands through trim; rejected
  controls must not enter history or be echoed raw. Include null and >96 chars.
- [x] Reject controls before normalization; allow surrounding ordinary ASCII
  spaces and preserve exact allowlist/no arguments. Keep history 16/output 4096.
  Do not broaden command syntax. Reflect the same validation in preview.
- [x] Run native suite, show red/green evidence, inspect diff; stop for supervisor.

### T2: Notes persistence fail-closed consistency

Files: NoteStore in the same Java source and native persistence harness/runner.
Preserve format/version and names. Follow ReportStore's existing defensive
validation pattern without rewriting the UI or changing user data formats.

- [x] Regressions must show corrupt/oversized/unexpected records introduced
  after a successful load cannot be overwritten by save; assert byte identity
  and no write, bounded reads, visible error and subsequent saves blocked.
- [x] Revalidate existing record size and codec immediately before replacing;
  block saves after storage/close failures with visible errors. Invalid draft
  validation should not mutate existing records. Test close uncertainty.
- [x] Run native suite; review independent results before another batch.

### T3: Remaining source audit and release evidence

- [x] Audit file paths, READ-only opens, depth/entry limits, report persistence,
  keyboard focus/navigation, safe diagnostics and preserved secondary modules.
  Delegate any further confirmed repair as its own narrow ticket.
- [x] Independently rerun all three suites, gateway/terminal/storage cases,
  shell syntax and diff checks, approved authentic host build.
- [x] Verify COD/JAR/JAD/ALX metadata, byte sizes and SHA-256; inspect local
  protected API evidence without signing or reading credentials.
- [x] Check preview at 480 x 640 and label synthetic vs browser vs physical QA.
- [x] Write engineering/QA, roadmap and installation-readiness reports with
  exact results and unresolved physical/transport/signing gates.
- [x] Accept only verified changes, commit explicit source/docs paths and
  publish only the existing feature branch; verify remote checkpoint.

## Independent acceptance status

T1 and T2 were independently reviewed and passed. T3 found the seven-byte
empty-report decode defect; OpenCode reproduced and repaired it in a separate
serial follow-up, adding a fifth regression and honest uncertain-write wording.
Codex independently reproduced all five regressions against the unchanged
handoff source. Final validation: 41 native + 9 companion + 7 S25Hub = 57 PASS;
15 desktop browser checks at explicit 480 x 640 PASS; authentic host build exit
0 with No errors and three warnings; packaging checks PASS. Full reports and
evidence are in the CP003 engineering QA and readiness documents. Source
accepted for publication only on the named feature branch. Physical install
remains HOLD. Source checkpoint `b162fe7b0adfb50cf9020d882bc959b072389fa6`
was committed and pushed; `git ls-remote` independently confirmed the same
feature-branch SHA. This ledger update records the completed publication.
