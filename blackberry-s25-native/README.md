# S25 Hub — BlackBerry Torch 9810 native client

Native BlackBerry Java OS 7 BrowserField2 shell targeting `https://s25.fantest.win/`.

## Current status

Source scaffold only; no `.cod` has been built, signed or installed. Requires authentic BlackBerry JDE 7.x (`net_rim_api.jar`, `rapc`) and compatible signing capability. BrowserField2 is a legacy engine: modern JavaScript, CSS, TLS and certificate-chain compatibility remain unverified on the Torch 9810.

## Authentication

This client intentionally does **not** bypass the website's existing authentication. Current live endpoint presents `Fantest S25 Hub · Sign in`. The desired no-prompt experience must use an authenticated, device-bound session or one-time pairing implemented on the backend; removing authentication from remote control is not safe. No secret or token is embedded in source.

## Build prerequisites

- BlackBerry JDE 7.x and device-appropriate signing support
- Compatible HTTPS/TLS connection on device
- Backend implementation of a remembered, revocable device session (not yet implemented)

This project must not be represented as a working APK or installable COD until built and tested on hardware.
