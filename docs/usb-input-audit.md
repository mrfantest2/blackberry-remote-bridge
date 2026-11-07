# Legacy USB input-control audit — checkpoint 010

## Scope

Read-only inspection of the existing Barry checkout on Steam Deck, current USB presence, private screenshot viewer, and available SDK files. No device-side changes, pairing changes, USB write transactions, firmware operations or installation.

## Findings

- Barry USB screenshot path is operational; no `EventInjector`, `SendKey`, `InjectKey` or `InjectTouch` implementation was found in the existing Barry C++ source headers and implementation files using the read-only source scan. This is evidence about this checkout only, **not** proof that a proprietary protocol is impossible.
- Legacy BlackBerry 7.1 API documents EventInjector navigation/key/touch events, requiring a signed application and Input Simulation permission on a physical phone.
- BlackBerry's current developer downloads notice explicitly says BlackBerry OS and BlackBerry 10 software are no longer supported and the historical software-download system is unavailable.
- Do not use a simulator-only success as evidence of handset control. Do not bypass BlackBerry signature or OS permission checks.

## Next viable gate

Locate an authentic, licensed, compatible JDE and existing valid signing credentials, if any, before investing in a physical-phone companion. If unavailable, maintain the verified read-only viewer and classify full software-only input as blocked, not implemented. Hardware keyboard-interfacing is a separate design requiring explicit electrical review before connection.
