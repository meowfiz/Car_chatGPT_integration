# Fast path: steps 2 to 5 of README_PRACA.md in one go. Elevated PowerShell.
# Run 00_check.ps1 first and close every TODO it prints - this script refuses to start otherwise.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\install_all.ps1

param(
    [string]$EnvFile = (Join-Path $env:USERPROFILE ".claude\ask_bridge.env"),
    [int]$MonitorMinutes = 5,
    [switch]$NoPassword
)

. "$PSScriptRoot\_common.ps1"
Assert-Admin

# --- preconditions, cheap and explicit ---------------------------------------------------
$fail = @()
if (-not (Test-Path $EnvFile)) { $fail += "env file missing: $EnvFile" }
else {
    $cfg = Import-EnvFile -Path $EnvFile
    if (-not $cfg.ContainsKey("ASK_SECRET") -or $cfg["ASK_SECRET"].Length -lt 24) { $fail += "ASK_SECRET too short" }
    $root = $cfg["ASK_ROOT"]
    if (-not $root -or -not (Test-Path $root)) { $fail += "ASK_ROOT not found: $root" }
}
foreach ($c in @("python", "git", "claude")) {
    if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { $fail += "$c not on PATH" }
}
if (-not (Get-TailscaleIp4)) { $fail += "no tailscale address" }
if ($fail.Count -gt 0) {
    $fail | ForEach-Object { Write-Host "BLOCKED: $_" }
    throw "fix the above (see README_PRACA.md, krok 0) and run again"
}

Write-Host "== step 2: power =="
& "$PSScriptRoot\01_power.ps1" -MonitorMinutes $MonitorMinutes

Write-Host ""
Write-Host "== step 3: scheduled tasks =="
if ($NoPassword) {
    & "$PSScriptRoot\02_install_tasks.ps1" -EnvFile $EnvFile -NoPassword
} else {
    & "$PSScriptRoot\02_install_tasks.ps1" -EnvFile $EnvFile
}

Write-Host ""
Write-Host "== step 4: desktop shortcut =="
& "$PSScriptRoot\install_shortcut.ps1"

Write-Host ""
Write-Host "== step 5: end to end check =="
Start-Sleep -Seconds 5
& "$PSScriptRoot\check_bridge.ps1" -EnvFile $EnvFile
