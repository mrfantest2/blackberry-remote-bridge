# TorchOS CP007 — Authenticated Input Control Foundation
Date: 2026-11-15 | BlackBerry Torch 9810, stock OS 7

## Physical handset status

- TorchOS 0.2.0 remains installed, previously verified by the Barry USB
  module inventory and a live 480x640 native screenshot.
- The existing Barry loader can retrieve screenshots, module inventory and
  device information. It cannot inject key, trackpad or touch events.
- No remote-input companion, USB HID service, new COD, certificate, local
  input service, or network listener was installed or started in CP007.
- **Full BlackBerry remote control is NOT working yet.**

## Implemented source (not physically deployed)

- `companion/remote_input.py`: reference HMAC-SHA256 request envelope and a
  **fake-sink** gate for host verification. There is no phone transport.
- `torchos-native/remote-input/TorchOSInputDriver.java`: native signed-API
  adapter that can produce key, navigation, tap and swipe events *only*
  after the caller is authorized and the native gate is armed.
- `tests/test_remote_input.py`: strict schema, HMAC, session, expiry,
  nonces, replay rejection, denial, lock handling and rate-limit tests.
- `tests/test_native_input_driver.py`: compiles and exercises the native
  adapter against synthetic BlackBerry API doubles without a device.

## Trust and control model

1. The handset must explicitly enable input and approve the OS permission.
   On-screen disable is the immediate kill switch; initial state is **OFF**.
2. A future **secure, paired transport** must deliver authenticated bytes
   to a phone-side receiver, and that receiver must implement the same
   checks as the Python reference model. This native receiver does not
   exist yet; passing host tests does not certify a native protocol.
3. The model requires a random >=32-byte secret per device, random session,
   strict HMAC, bounded expiry (<=8 seconds), sequence/nonce replay
   rejection, exact field schema and input validation. No keys are stored
   in the repository or diagnostic logs.
4. The model permits <=10 input events per second, a maximum 5-minute
   session, and refuses commands when the phone is locked. The currently
   drafted native adapter conservatively disarms when TorchOS is not in
   the foreground: **other-app/system-wide control is intentionally
   unavailable until a trustworthy lock-state check is demonstrated.**
5. Supported staged actions: UP/DOWN/LEFT/RIGHT, SELECT, BACK; printable
   ASCII/supported special keys; tap and swipe inside 480x640. No HOME,
   credential bypass, OS reset, installation, arbitrary shell, or
   background/lock-screen input. No control of Android or other devices.
6. Screen viewing remains the existing read-only USB screenshot mechanism,
   separate from the unimplemented input receiver.

## Hard blockers to physical input

- `net.rim.device.api.system.EventInjector` is a **signed** BlackBerry API.
  `PERMISSION_INPUT_SIMULATION` is also signed. Physical execution needs
  legitimate accepted signing and the on-device authorization. Never spoof
  signatures or bypass permission checks.
- No usable legacy signing credentials were found in the scoped toolchain
  audit. BlackBerry OS 7-era code-signing infrastructure is end of life.
  The adapter compiles against local JDE 7.0 API stubs but no valid signed
  handset COD containing the adapter has been produced.
- The companion presently has no authenticated transport, receiver,
  session pairing UI, permission UI, native HMAC parity tests, durable
  replay cache, device-lock verifier or cross-application authorization.
- Browser/screenshot preview does not imply input control.

## Future acceptance gates

1. Verify a lawful BlackBerry 7 signing route and the actual
   `Input Simulation` permission on the handset. If unavailable, HOLD.
2. Implement and validate real phone-side authentication and transport
   using a private encrypted link; block public and anonymous control.
3. Add an explicit enable/disable/expiry UI, reject lock-screen input,
   validate crash/restart disarm behavior and test signed execution.
4. Build and sign the next COD without replacing existing TorchOS/S25Hub
   unnecessarily; preserve backups and require a controlled delta update.
5. With deliberate on-device approval, inject harmless DOWN/SELECT/TAP
   actions and verify before/after USB screenshots.
6. Only after those tests, consider cross-application control with a
   verified lock state and a separate safety acceptance.

References: BlackBerry JDE 7.1 `EventInjector`,
`ApplicationPermissions.PERMISSION_INPUT_SIMULATION`,
existing repository `docs/input-feasibility.md`.

## Tests

From the project root, run:
`bash scripts/test-all.sh`

This is a source and host-test checkpoint only. No runtime control endpoint
is exposed or deployed.
