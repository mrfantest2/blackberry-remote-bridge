# BlackBerry Torch 9810 input-control feasibility — checkpoint 007

## Verified locally

- USB 0fca:8004 responds to Barry read-only screenshot and device information.
- Barry source inspected: no documented USB key/touch injection API.
- Bluetooth SDP advertises OBEX, audio, desktop, phonebook and message access, but no HID service; the phone is paired and not currently connected over Bluetooth.
- Private screenshot viewer is operational on Steam Deck localhost; MASTER-PC access via authenticated SSH port forward is independently verified.

## Legacy BlackBerry OS 7 native API path

BlackBerry JDE 7.1 documentation documents `net.rim.device.api.system.EventInjector` and its KeyEvent, KeyCodeEvent, NavigationEvent and TouchEvent classes. `ApplicationPermissions.PERMISSION_INPUT_SIMULATION` gates event injection. The API is signed/controlled and requires appropriate device permissions. A phone-side application must receive authenticated commands and call EventInjector locally; the existing Barry screenshot interface alone cannot inject events.

References:
- https://nikita36078.github.io/J2ME_Docs/docs/BlackBerry_API_7_1_0/net/rim/device/api/system/EventInjector.html
- https://nikita36078.github.io/J2ME_Docs/docs/BlackBerry_API_7_1_0/net/rim/device/api/applicationcontrol/ApplicationPermissions.html
- https://www.blackberry.com/en/secure-communications/support/end-of-life

## Engineering gates before any phone changes

1. Obtain an authentic, compatible BlackBerry JDE 7.x toolchain and confirm the actual installed OS and existing applications without modifying the phone.
2. Establish whether valid legacy code signing and `PERMISSION_INPUT_SIMULATION` authorization are still possible; BlackBerry OS 7 services are end-of-life. Do not bypass signature or OS permission checks.
3. If feasible, implement a minimal companion app with local pairing, allowlisted navigation commands, explicit on-device enable/disable, and no unattended input on lock screens.
4. Keep screenshot transport independent and encrypted. Do not expose an unauthenticated HTTP input endpoint.
5. Require a controlled, reversible first on-device test and compare screenshots before/after a harmless navigation event.

**Status:** architecture identified; signing, installation and actual input injection NOT VERIFIED. No phone modifications performed.
