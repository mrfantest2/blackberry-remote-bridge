# TorchOS CP002 — Parrot-inspired Security Edition
Date 2026-11-14
Repository: existing private mrfantest2/blackberry-remote-bridge
Authoritative BRANCH: feat/torchos-native-shell-20261114
Clean, verified worktree: /home/SD/Projects/torchos-native-shell
HEAD checkpoint: 974be6742abc5a1910777eb50238b53e5ad60523
Original checkout /home/SD/BlackBerryBridge/project is DIRTY (17 entries); do NOT touch it.

## Engineering mission (execute now)
Implement a realistic, elegant **native BlackBerry OS 7** pocket workstation shell inspired by Linux security-desktop utility design (charcoal/navy, cyan/mint, monospace where locally supported, original TorchOS brand, no copied Parrot branding). This is NOT Linux or firmware. Optimize native layout for BlackBerry Torch 9810: portrait 480x640, touch, optical trackpad, QWERTY keyboard.

Deliver functional offline home with SIX PRIMARY modules in order:
1. Terminal (workable offline)
2. Network Center (read-only OS7 local capabilities or explicitly unavailable; no probing)
3. Security Center (local safe diagnostics, checksums only if real or explicitly disabled)
4. Device Manager (local battery if available + saved owners' device labels with explicitly offline remote status)
5. File Manager (read-only JSR75 roots/folders if supported by OS7; permission failure in UI; never modify/erase files)
6. System Monitor (device RAM/battery/runtime if supported; label simulated/unavailable honestly)
Maintain **secondary navigation** to Notes & Tasks, CamDoor, EchoVault/Tahani and Project Monitor, plus Settings/About.

Native terminal MUST have editable line, scrollable output, limited command history, Help/Clear/Back, software keyboard input and physical keyboard interaction. Implement hardcoded local-only allowlist: help, date, about, clear, status, history, notes, files; reject anything else with plain explanatory text. No unrestricted shell, root prompt, remote execution or command interpreter injection. Offline regardless of Deck presence. Bound input/output/history length. Distinguish local outputs from disconnected remote services.

Persistent notes and checklists using OS7 `javax.microedition.rms.RecordStore` with versioned/bounded serialization; safe failure handling and visible persistence errors. Optionally persist terminal history. Start with empty record store; no legacy data migration required. No hardcoded PIN/secrets or production data. Avoid overwriting any S25Hub RMS store. If full native persistence is not completed, label and document exactly.

Local diagnostics: native `net.rim.device.api.system.DeviceInfo` battery if compiling successfully; use local Java memory stats as *app runtime* (not total system RAM). For file manager use `javax.microedition.io.file.FileSystemRegistry.listRoots()` and read-only `FileConnection` if JDE 7.0 compiles. Never allow file writes, path escaping or sensitive filesystem snapshots in public logs. No user-initiated network probes. Network Center is offline placeholder unless OS7 APIs positively verified.

Backend: first READ existing `companion/protocol.py` and `dashboard/serve.py`; blackBerry hub and other services already RUNNING; do NOT create/start another listener nor change existing services. Build `torchos-native/gateway/` contract-only read-only prototype with per-device HMAC-SHA256 authentication, strict allowlisted ops (status/network/services/inventory only), timestamp window+expiry, unique nonce replay cache, input size bounds, fail-closed on errors, redacted audit fields, no production secret on disk. Python stdlib okay, no network listener. Add rigorous tests including bad MAC/replay/expiry/wrong-device/oversized/mutated op. Note native transport NOT implemented and modern TLS to legacy handset UNVERIFIED. Do not change `companion/protocol.py` or any existing server.

HTML preview: self-contained `torchos-native/preview/index.html`; 480x640 exact viewport, interactive page navigation and offline terminal demo, original TorchOS aesthetics charcoal/navy cyan mint, no external images/fonts/assets/requests. Must accurately match native functionality; preview not physical Java and no simulated hardware readings misleadingly labeled real. Include modules and secondary navigation. Accessibility and keyboard arrows/shortcuts.

Testing: Keep ALL 29 preexisting baseline tests worth of coverage (13 TorchOS host + 9 existing protocol + 7 S25Hub) and extend with tests for terminal parsing/history, navigation/layout bounds, RMS persistence safety including malformed/corrupt behavior (host mock allowed), offline without gateway, disabled remote actions, gateway auth/replay/expiry/allowlist, file read-only constraints, preview contract. It is okay to evolve `torchos-native/tests/test_torchos.py` to reflect new design as long as previous keyboard/touch/trackpad tests and protections remain tested. Host java harness must keep working or be expanded. Provide no phantom PASS.

Build source with authentic JDE 7.0:
`/home/SD/BlackBerryBridge/toolchains/blackberry-jde-7.0.0`
JDK8 `/home/SD/BlackBerryBridge/toolchains/jdk8`
WTK `/home/SD/BlackBerryBridge/toolchains/wtk252`
32-bit libs `/home/SD/BlackBerryBridge/toolchains/i686-libs/usr/lib`.
Existing `torchos-native/build.sh` from CP001 is proven working outside Codex sandbox, so edit carefully. Real `.cod`, `.jad`, `.jar` produced through RAPC, `TorchOS.alx` valid. If Codex sandbox yields preverify Bad system call, document it and leave a compile-ready build; an RDC direct build will run separately. Do NOT install/sideload, flash, wipe, reboot, read private device storage, alter mounted phone or USB at all. No user-device writes. Avoid starting services/containers. No network external requests; no new repositories/branches.

Documents:
- `docs/TORCHOS_CP002_ARCHITECTURE_20261114.md`
- `docs/TORCHOS_CP002_QA_20261114.md`
- `docs/TORCHOS_CP002_DEPLOYMENT_READINESS_20261114.md`
Document exact local capabilities vs hardware assumptions; gateway pairing and physical TLS blockers; controlled installation with **separate approval required**, uninstall only own TorchOS module after backup, no touching firmware; next roadmap. No claims of physical QA.

## Hard limits
- Work only in isolated worktree and relevant files `torchos-native/**`, CP002 docs, and this spec. Preserve original branch, dirty checkout, S25Hub source/tests, BlackBerry proprietary backup, live Deck services and firmware.
- No git commit, push, reset, clean, rebase, cherry-pick, or merge; final Git commit/push will be checked independently after QA.
- Avoid public exposure, plaintext remote commands, TLS bypass, credential harvesting, arbitrary network scans or exploitation. Never put secrets, PIN, private screenshots or personal data in source.
- Do not install Parrot OS.
- Implement genuinely, not only a plan. Keep code minimal enough for 480x640 OS7 and constrained Java ME.
- Once source/tests/docs complete, run host tests and report evidence. If compiler/toolchain fails, diagnose without changing Deck OS. Stop after one bounded implementation run.
