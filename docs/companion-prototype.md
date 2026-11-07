# Companion command protocol prototype (checkpoint 008)

This is an **offline Python reference model**, not an installed BlackBerry application and not a network control service. It provides a deliberately limited six-command navigation allowlist, HMAC-SHA256 envelope authentication, 128-bit nonce validation, and replay rejection in process memory. No text entry, touch coordinates, destructive actions, or lock-screen actions are supported.

Run: `cd /home/SD/BlackBerryBridge/project && python3 -m unittest discover -s tests -v`

Production gaps: BlackBerry OS 7 Java implementation, reliable per-session pairing and key storage, bounded persistent nonce/session state, signed application deployment, input simulation permission, on-device consent and kill switch, secure transport and actual event injection. Python reference implementation must not be treated as BlackBerry-compatible code. No device modification is authorized by this prototype.
