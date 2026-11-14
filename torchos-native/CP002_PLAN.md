# CP002 implementation ledger
Specification: ../TORCHOS_CP002_BRIEF.md (fully read).
User explicitly requests immediate implementation in this isolated worktree, no approval pauses, commits, deployments, device interaction or services. Those instructions override skill approval/commit workflows. No external requests.

Design: preserve native MainScreen/Field navigation; six compact primary rows, secondary menu/navigation screen. Native editable terminal over a bounded pure local model; versioned bounded RMS snapshot for notes, tasks and three optional owner labels. Corrupt persistence blocks overwrites and exposes errors. Read-only JSR75 folder browser with bounded depth/listing and safe child names. Local battery API and Java app runtime metrics; unavailable remote/network/checksum functions explicitly labeled. Standalone gateway authenticates only four read-only operation names; no transport or provider execution. HTML mirrors these capabilities, with browser-only session notes and no hardware claims.

Sequence:
1. Extend failing host/contract tests, preserve keyboard/touch/trackpad/layout protections and run baseline suites.
2. Implement native terminal, RMS codec/store and six-module UI. Compile with existing authentic toolchain; diagnose a bounded failure without OS changes.
3. Implement and test strict bounded per-device gateway authentication and replay handling; no listener.
4. Implement self-contained accessible interactive preview and verify offline/navigation/terminal contract.
5. Run complete regression suites and authentic build; review diff and document exact results, limitations and deployment blockers in CP002 architecture, QA and readiness docs.

Review focus: malformed/truncated/oversized RMS must not overwrite; terminal never executes input; file paths cannot escape roots and connections use READ; gateway validates device, MAC, time and nonce before acceptance, bounded replay state fails closed; six rows fit conservative 480x640 budget; preview cannot imply hardware data or native persistence.
