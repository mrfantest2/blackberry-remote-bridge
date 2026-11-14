# TorchOS CP003 — OpenCode DeepSeek Free Implementation Ticket
2026-11-14 | CODING AGENT ONLY | Steam Deck Bazzite
Senior review/QA owner: Codex.

## Identity
- Repo `mrfantest2/blackberry-remote-bridge` (private), branch `feat/torchos-native-shell-20261114`.
- Worktree `/home/SD/Projects/torchos-native-shell`, base `60aef4b39e7218cfc326437ea325d1796325e495`.
- Model pin: `opencode/deepseek-v4.1-flash-free` (selected at OpenCode CLI, do not edit global config).
- Source limit: only `torchos-native/**` and CP003-local `docs/TORCHOS_CP003_*.` No other paths, no original checkout.
- Do not read backups, media, contact data, credentials or private memorial archive content.
- Do not use unsafe auto-approvals, network listeners, shell root, scanning/exploitation, TLS bypass, privileged API bypass, phone installs, git reset, force push or merge.

## Stage 0: verify before editing
Check clean branch, HEAD, status. Read CP002 architecture, QA, deployment readiness; validate 52-test baseline and output COD. If baseline fails, stop and report. Wait for senior Codex to verify this model actually responds; catalog alone is not enough.

## Stage 1: implementation
Perform a bounded CP003 **offline quality** iteration, not new infrastructure:
1. Code-review local Terminal: command allowlist has no parameters, no shell escape, no executing arbitrary input, history/output bounded, keyboard and Back behavior robust on OS 7; add negative tests for malformed/long control characters.
2. Review RMS NoteStore/ReportStore: versioning, size bounds, corrupt-record handling, close failures, user-visible errors, double-save prevention, no silent overwrites; add tests demonstrating defensive behavior.
3. Review File Manager JSR-75 only: root enumerations, bound number/depth, child path sanitization, Connector.READ only, no file writes, safe denial display; no permission escalation.
4. Verify 480x640 six-item native layout fit and responsive focus for touch, trackpad and slide QWERTY; HTML preview remains matched and self-contained.
5. Add read-only install readiness checks/documentation for protected API dependency/signing inventory; do not attempt real signing or install.
6. Preserve Notes, CamDoor, EchoVault, project-monitoring placeholders and all existing features and tests. Network Center stays transparently unsupported; gateway contracts only.
7. Prefer minimal diffs and evidence-backed fixes. No UI rewrite or duplicate application.

## Test / acceptance
- Existing 52 tests remain PASS; new tests increase total.
- Authentic JDE 7.0 `bash torchos-native/build.sh` must return 0 and produce nonempty COD + JAD, with no preverify bypass.
- All generated binaries remain ignored local build outputs. Document sha256 in QA, not in source constants.
- Document any security issues and physical-dependent behavior rather than asserting false functionality.
- No physical device testing; no running services or touching other devices.
- Produce `docs/TORCHOS_CP003_OPENCODE_IMPLEMENTATION_REPORT.md` with diff summary, tests, build, unverified features, blockers and recommendations.
- Stop and hand control to senior Codex for independent review; **no commit/push/merge** from OpenCode.

## Stop conditions
Wrong branch/dirty unrelated work, missing toolchain, model unavailable/auth required, nonpassing CP002 baseline, any need for user data or handset writes, production configuration request, sensitive tokens, inability to run allowed tests, or changes outside authorized paths. Record blocker; do not invent success.

## Invocation candidate (senior Codex to run only once provider is healthy)
```bash
cd /home/SD/Projects/torchos-native-shell
opencode run --pure --agent build \
  --model opencode/deepseek-v4.1-flash-free \
  --file docs/TORCHOS_CP003_OPENCODE_TASKS_20261114.md \
  "Read the attached CP003 ticket; implement only the safe offline code and tests, no commit or install. Report exact results."
```
Command is a recipe, not proof of a working provider. OpenCode model probe currently timed out (70 seconds, no output); don't run until verified.
