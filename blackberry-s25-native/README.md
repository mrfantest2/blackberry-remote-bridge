# S25 Remote Hub — native BlackBerry OS 7 application

This is a **native Java BlackBerry UI**, not a BrowserField/web wrapper. `S25Hub.java` uses `MainScreen`, `LabelField`, `ButtonField`, a background network worker, and BlackBerry-compatible J2ME `HttpConnection`.

Current buttons perform **read-only** GET requests to proposed endpoints `/api/native/v1/status`, `/api/native/v1/battery`, and `/api/native/v1/device`. These endpoints are NOT verified or deployed. The application rejects HTML and does not treat a login page as device status. No remote actions are wired until the S25 API and access control are verified.

No password or token is embedded. The target website currently serves a sign-in page. To avoid daily login prompts without making remote control public, implement a one-time device pairing and revocable remembered session on the backend. The BB OS 7 TLS and modern server compatibility must be verified on real hardware.

Requires authentic BlackBerry JDE 7.x (`rapc`, `net_rim_api.jar`), legacy code-signing availability, and on-device testing. No installable `.cod` has been produced.
