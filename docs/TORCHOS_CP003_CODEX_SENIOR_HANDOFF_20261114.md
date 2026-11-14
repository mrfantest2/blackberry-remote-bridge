# TorchOS CP003 — Codex Senior Engineering Handoff
Date: 2026-11-14
Intent: Codex directs and independently reviews; OpenCode performs all implementation using the **explicit pinned DeepSeek free model** on the authorized Steam Deck.

## Roles and operating agreement
**Codex: Senior BlackBerry OS 7 / Java ME architect, security reviewer, QA lead, release manager.**
- Read the authoritative checkpoint before work, write a concise defect/priority plan, assign narrow implementation tickets to OpenCode, review the resulting diff for security and correctness.
- Own definition of done, threat model, architecture, testing matrix, independent authentic JDE build, evidence and final checkpoint.
- **Do not implement application source yourself.** When code fails, write a precise reproduction/repair ticket and hand it to OpenCode. Codex may update handoff/QA/review documentation.
- Never silently switch OpenCode to another model, a paid model, or a different provider. No second autonomous agent or concurrency across the same worktree.

**OpenCode: Implementation agent and test author** running on Bazzite, not MASTER-PC.
- Mandatory invocation model: `opencode/deepseek-v4.1-flash-free`. It is advertised by local `opencode models`.
- Execute the scoped CP003 task brief in `docs/TORCHOS_CP003_OPENCODE_TASKS_20261114.md`, edit only `torchos-native/**` and CP003 notes in `docs/**`, preserve existing features, author regression tests and explain failures.
- Do not mutate the OpenCode global config or other projects. The Deck's global OpenCode default is `lmstudio/google/gemma-4-e4b`; pin the DeepSeek free model **per invocation**.

## Live verification and current blocker (read before launching)
1. On the Steam Deck, `opencode --version` returned **1.19.5**; `codex --version` returned **0.166.0**.
2. `opencode models` lists **`opencode/deepseek-v4.1-flash-free`**.
3. `opencode auth list` shows **0 stored credentials**. Do not print, read or modify auth files.
4. A harmless no-tools invocation on the free model from /tmp returned **exit code 124 (70-second timeout)** with **no streamed JSON output**. So free-model inference is **NOT VERIFIED**. Catalog discovery alone is not an availability guarantee.
5. OpenCode's earlier log contains completed provider-selection entries for this exact DeepSeek free model around 2026-11-14 01:25–01:32 UTC, but those historical sessions do not prove the current CLI probe is healthy. The latest controlled probe timed out with zero output; it might be a provider, service, CLI or connection problem, not necessarily missing credentials.
6. Stop if the model probe cannot return an actual response. **Do not fall back** to paid, Google, local Gemma or another DeepSeek model without explicit separate authorization. Do not claim implementation occurred while blocked.
7. Do not launch a persistent Codex/OpenCode session until the model is confirmed responding; avoid hanging supervisors and duplicate agents. A successful model health check is a prerequisite for coding.

## Authoritative identity and preservation
- Repo (private): `mrfantest2/blackberry-remote-bridge`
- **Only** branch: `feat/torchos-native-shell-20261114`
- CP002 verified clean feature HEAD/remote: `60aef4b39e7218cfc326437ea325d1796325e495`
- Isolated worktree: `/home/SD/Projects/torchos-native-shell`
- Original checkout (not yours to modify): `/home/SD/BlackBerryBridge/project` (17 pre-existing dirty entries)
- Existing S25Hub native code and data: `blackberry-s25-native/`, untouched.
- Preserve all BlackBerry personal backups, stock BlackBerry OS 7, existing CamDoor/Xiaomi/BlackBerry dashboard services, original GitHub history, the S25 and other phones.
- Hardware: Torch 9810 USB `0fca:8004` seen. USB enumeration does not grant installation or read-write access to the phone.

## CP002 verified baseline — do not repeat as if unverified, but independently regress
- Native TorchOS **0.2.0** Java OS 7 shell is not Linux or full Parrot OS.
- Six primary modules: Terminal, Network Center, Security Center, Device Manager, File Manager, System Monitor.
- Secondary: Notes & Tasks, CamDoor, EchoVault/Tahani, Project Monitor, Settings.
- Offline local allowlisted terminal with editable `local>` line, output/history bounds; commands `help date about clear status history notes files`; never shell execution or root claims. Terminal history session only.
- Versioned RMS persistence for bounded notes/checklists/owner labels; separate RMS for one local diagnostic report; failures visible and fail closed. These were **host-double tested**, not phone-tested.
- Read-only JSR-75 folder listing max 64 entries / depth 8, no file contents or writes, with unknown physical permissions.
- Device battery OS API; Java *application* runtime memory, not total system RAM; all remote services explicitly disconnected.
- Detached Python `torchos-native/gateway/contract.py` with per-device HMAC-SHA256, only `status network services inventory`, nonce replay/clock rollback/expiry limits. Contract only: **no transport, pairing, listener, provider implementation or remote commands**.
- Authentic JDE 7.0 build on authorized Deck **PASS**, RAPC "No errors", 3 legacy warnings; `TorchOS.cod` **23,012 bytes**, `TorchOS.jar` **55,945 bytes**, `TorchOS.jad` **480 bytes**.
- COD SHA-256: `1046f042da3bf0b1e106d25c98c0d9fc3c45d5ce5228bf006fa117a641fd7d2c`.
- Automated tests **52/52 PASS**: TorchOS 36, original companion 9, S25Hub 7.
- Self-contained offline 480×640 HTML design preview and Chrome image committed under `docs/TORCHOS_CP002_PREVIEW_480x640.png`.
- Physical TorchOS install/launch/permission/TLS/secure pairing/signing: **NOT VERIFIED**.
- The prior legacy BrowserField signed API required RRT and usable signing credentials were not found; do not bypass protected API signing or weaken TLS.

## Detailed CP003 coding scope — safe, offline only
Delegate to OpenCode in small serial batches using the companion task document:
A. CP002 regression and source review: six-module navigation, no screen truncation, keyboard focus, terminal command/history strictness, Java ME compatibility, stale UI event risks, RMS atomic/fail-closed logic, read-only file path guarantees.
B. Correct confirmed defects **only**; add tests for each correction; avoid cosmetic changes that increase native startup time or break 480×640 usability.
C. Prepare installability analysis in docs: check COD dependencies, supported vs protected API calls, JAD/ALX integrity, needed signing keys/permissions; **no physical installation or signing-key modifications**.
D. If robust local improvements are safely possible, improve offline terminal keyboard/back handling, report-RMS recoverability and status refresh UX. Do not implement a network endpoint, browser TLS bypass, arbitrary remote command execution, scanning or privileged APIs.
E. Keep the gateway as a contract until a proven secure transport and explicit separate approval exist. No exposing existing local dashboard or new daemon.
F. Return code diffs, exact tests, compiled artifact checksums, blockers and recommended next steps. Codex independently validates.

## Codex workflow (execute only after the DeepSeek model has passed a real probe)
1. `cd /home/SD/Projects/torchos-native-shell`; verify clean branch, expected HEAD/remote, no other agents editing this worktree, and original checkout still untouched.
2. Read all three CP002 docs in `docs/`, `TORCHOS_CP002_BRIEF.md`, `torchos-native/CP002_PLAN.md`, the new OpenCode CP003 task document, and `torchos-native/src/TorchOS.java`.
3. Verify a simple `opencode run --pure -m opencode/deepseek-v4.1-flash-free` **responds** under a bounded timeout. It is currently NOT responsive; fail closed if still blocked.
4. Invoke OpenCode **once** for a bounded implementation batch, explicitly pin `-m opencode/deepseek-v4.1-flash-free`, with `--pure --agent build` and the CP003 scoped task; **never** use `--auto` or change global config. Run from the authoritative worktree and log locally without secrets.
5. Codex reviews `git diff`, checks no edits outside authorized paths and no secrets, no external sockets or privilege escalation, and asks OpenCode for specific corrections if needed.
6. Independent tests:
   - `bash torchos-native/test.sh`
   - `python3 -B -m unittest discover -s tests -q`
   - `python3 -B -m unittest discover -s blackberry-s25-native/tests -q`
   - `bash torchos-native/build.sh` (authentic JDE 7.0 on authorized host)
   - `git diff --check`, `bash -n torchos-native/build.sh torchos-native/test.sh`.
   Legacy 32-bit `preverify` may be blocked with SIGSYS inside Codex sandbox even when direct Desktop Commander build succeeds. Distinguish these environments, do not bypass security.
7. If all tests pass, preserve a CP003 QA artifact, compare against CP002 baseline, commit/push **only the existing feature branch** if explicitly tasked to publish. Never merge to main, modify production or install handset.
8. Handoff report must classify each feature **verified on host / simulated / unverified on physical device / blocked** with exact test counts and SHA.
9. No future work promise or asynchronous assertions: either perform the approved batch and show evidence, or report the exact blocker.

## Deployment guardrails — absolute
No `bjavaloader -u`, `javaloader`, ADB to S25/OP7, firmware flashing, reboot, wipe, reset, repartition, signing bypass, automatic installation, private archive reads, camera/network scan, Cloudflare publish, persistent daemon, token exposure, unbounded shell, or application replacement. A **separate physical-device deployment authorization** is required for any change to the Torch.

## Next action when free-model provider is unavailable
Do NOT start paid fallback or take over coding with Codex. Run narrowly scoped read-only connectivity/model authentication diagnostics and report:
- selected model, catalog vs real inference outcome;
- zero or existing auth account state *without exposing credentials*;
- network reachability errors (without printing tokens);
- whether OpenCode requires the user's explicit login.
Preserve the feature branch and resume only after the free model responds.
