# Authenticated remote viewing (checkpoint 006)

- Viewer service on Steam Deck listens only on `127.0.0.1:18765`, not on Wi-Fi or Tailscale.
- The BlackBerry screenshot is refreshed only by running `scripts/capture-preview.sh` on the Steam Deck.
- MASTER-PC has Windows OpenSSH, and can reach the Steam Deck Tailscale SSH endpoint. The first live probe returned **Tailscale SSH requires an additional check**; do not bypass the normal user authentication process.
- After completing the Tailscale authentication check, run `scripts/open-masterpc-viewer.ps1` on MASTER-PC and visit `http://127.0.0.1:18765/` on MASTER-PC. This uses a localhost-to-localhost SSH port forward.
- Tunnel establishment and the MASTER-PC browser view remain **unverified** until SSH authentication is completed and the endpoint is tested.
- Never expose the private viewer on `0.0.0.0` or publish screenshots on the unauthenticated dashboard.
- This is screen viewing, **not** keyboard or touchscreen control.
