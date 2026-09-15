# Wrapper started by the scheduled task AskBridge\bridge. Loads the env file, waits for
# Tailscale to hand out an address, then runs poc\ask_server.py and keeps its output.
# Known pitfall (HANDOFF): the server must be started from PowerShell, not from Git Bash.

param(
    [string]$EnvFile = (Join-Path $env:USERPROFILE ".claude\ask_bridge.env"),
    [int]$TailscaleWaitSec = 120
)

. "$PSScriptRoot\_common.ps1"

$cfg = Import-EnvFile -Path $EnvFile -SetProcessEnv

if (-not $env:ASK_BIND) {
    $deadline = (Get-Date).AddSeconds($TailscaleWaitSec)
    do {
        $ip = Get-TailscaleIp4
        if ($ip) { break }
        Start-Sleep -Seconds 5
    } while ((Get-Date) -lt $deadline)
    if (-not $ip) {
        Write-Log "bridge.log" "no tailscale address after $TailscaleWaitSec s - giving up"
        exit 2
    }
    $env:ASK_BIND = $ip
}

$server = Join-Path $RepoRoot "poc\ask_server.py"
if (-not (Test-Path $server)) {
    Write-Log "bridge.log" "missing $server"
    exit 3
}

# Keep one previous stdout log, so a crash loop cannot fill the disk.
$out = Join-Path $RunFiles "bridge_stdout.log"
if ((Test-Path $out) -and ((Get-Item $out).Length -gt 5MB)) {
    Move-Item $out (Join-Path $RunFiles "bridge_stdout.1.log") -Force
}

Write-Log "bridge.log" "start: bind $($env:ASK_BIND):$($env:ASK_PORT) model $($env:ASK_MODEL) root $($env:ASK_ROOT)"
$env:PYTHONIOENCODING = "utf-8"          # ZASADY 4.10 - console code page must not decide encoding
$env:PYTHONUNBUFFERED = "1"

& python $server *>> $out
$code = $LASTEXITCODE
Write-Log "bridge.log" "exit code $code"
exit $code
