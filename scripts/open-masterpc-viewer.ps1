# Run on MASTER-PC after completing the normal Tailscale SSH authentication check.
# No direct Wi-Fi/Tailscale HTTP exposure: forwards only through SSH.
param([int]$LocalPort = 18765)
$ErrorActionPreference = 'Stop'
if ($LocalPort -lt 1024 -or $LocalPort -gt 65535) { throw 'Choose a local port between 1024 and 65535.' }
$ssh = (Get-Command ssh.exe -ErrorAction Stop).Source
Write-Host "Forwarding http://127.0.0.1:$LocalPort/ to Steam Deck private viewer."
Write-Host 'Complete any Tailscale SSH authentication check when prompted. Ctrl+C stops the tunnel.'
& $ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o StrictHostKeyChecking=accept-new -L "127.0.0.1:$($LocalPort):127.0.0.1:18765" 'SD@100.72.130.8'
if ($LASTEXITCODE -ne 0) { throw "SSH tunnel failed: $LASTEXITCODE" }
