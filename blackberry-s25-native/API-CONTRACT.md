# Native S25 service API contract — NOT DEPLOYED

Base: `https://s25.fantest.win/api/native/v1/`

- `GET status` → JSON `{"online":true,"name":"Galaxy S25"}`
- `GET battery` → JSON `{"level":85,"charging":true}`
- `GET device` → JSON `{"model":"SM-S938B","platform":"Android"}`

This is a proposed response contract only. Live `GET /api/native/v1/status` currently returns HTTP **404**, not a device state. Do not expose device-control endpoints anonymously. Pair once using an on-device approved, revocable session before implementing any state-changing actions. BlackBerry OS 7 TLS support must be verified on the actual handset.

Current Java client displays raw JSON for read-only diagnostics. A native presentation parser and controls should be added only after the backend response contract is implemented and verified.
