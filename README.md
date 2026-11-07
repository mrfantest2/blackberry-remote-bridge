# BlackBerry Torch 9810 Remote Bridge

Experimental gateway for a BlackBerry Torch 9810 (BlackBerry OS 7) connected to a Bazzite Steam Deck.

## Verified checkpoint (2026-11-07)
- BlackBerry USB device `0fca:8004` detected on Steam Deck.
- Bluetooth connection supports status and battery reporting, but no Bluetooth HID service is advertised.
- Read-only local HTML dashboard runs on the Deck, currently on port 8765, bound to Wi-Fi interface `wlo1`'s IPv4 at startup.
- User systemd service `blackberry-hub.service` enabled; network-watch timer checks binding roughly every 30 seconds.
- mDNS `bazzite.local` resolved from Deck. Compatibility with BlackBerry browser hostname resolution is unverified.
- Barry upstream source archive downloaded/extracted separately, not vendored here.

## Not yet verified
- BlackBerry screenshot capture (Barry `bjavaloader` not compiled/tested).
- Remote keyboard, touchscreen, or screen viewing (no demonstrated interface).
- End-to-end Bluetooth OBEX transfer.
- Recovery after full Steam Deck reboot.

## Scope and safety
- Dashboard is intentionally read-only, over plain HTTP on a trusted LAN. Never expose it to the internet or enter secrets.
- Do not push BlackBerry backups, proprietary caches, memory cards, personal information, or USB dumps into GitHub.
- Firmware flashing, wiping, and altering BlackBerry data are out of scope.
- Keep builds isolated from the Bazzite host. Before USB commands, verify safety and read-only behavior.

## Deployment
Review `dashboard/serve.py` and `systemd/` before using. Existing live files are at `/home/SD/BlackBerryLocalDashboard/` and `$HOME/.config/systemd/user/` on the Steam Deck. This repository is a reproducible *source snapshot*, not an automatic installer.

## Next checkpoint
1. Build legacy Barry tools inside a container with pinned dependencies and a preserved build log.
2. Run `bjavaloader` help then read-only `deviceinfo` and screenshot only after confirming command behavior and USB permissions.
3. Document actual device-specific results; investigate remote-input feasibility separately.

## Checkpoint 003 verified (2026-11-07)
- Barry 0.19.0 compiled in Ubuntu 24.04 container after a one-line `#include <ctime>` compatibility patch.
- Rootless Podman requires `--userns keep-id --security-opt label=disable` plus access to the specific USB device node to use existing host ACLs. This is not a privileged container.
- `bjavaloader deviceinfo` succeeded on the Torch 9810.
- `bjavaloader screenshot` produced a 480x640 32-bit BMP, 1,228,854 bytes; screenshot stays private on the Deck under `/home/SD/BlackBerryBridge/private-captures`.
- Screenshot capture is **not** remote keyboard or touch control; those capabilities remain unverified.
- Use `scripts/read-only-usb.sh deviceinfo` or `scripts/read-only-usb.sh screenshot`. The script rejects other commands.
