# BlackBerry Torch 9810 input feasibility (checkpoint 004)

## Confirmed
- Torch 9810: USB `0fca:8004`; Barry 0.19.0 `bjavaloader deviceinfo` and `screenshot` work.
- `src/m_javaloader.h` exposes `GetScreenshot`, `DeviceInfo`, app load/erase, log and other device-management operations; it does **not** declare keyboard/touch input APIs.
- The BlackBerry Bluetooth SDP listing did not advertise HID input services in earlier pairing tests.
- The browser can display the Deck-hosted local dashboard, but page navigation does not grant control over BlackBerry OS.

## Unverified paths
1. An opt-in BlackBerry OS 7 Java companion app might expose a limited command channel, but OS signing, permissions and cross-app input restrictions must be evaluated. Do not install anything on the device without validating its provenance and safety.
2. Legacy desktop remote-control utilities may implement proprietary protocols. Treat compatibility claims as unverified until tested on this exact Torch 9810.
3. External physical HID hardware would need independent compatibility testing and may not emulate touch input.

## Security boundaries
- Do not expose screenshots via the existing unauthenticated LAN dashboard.
- Store screenshots in `/home/SD/BlackBerryBridge/private-captures` and PNG previews in `private-previews`, both outside Git.
- Do not run Barry firmware/erase/reset operations.
- Do not call screenshots 'remote control' until an authenticated input mechanism is demonstrated end to end.
