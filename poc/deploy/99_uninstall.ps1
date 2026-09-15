# Undo everything this deployment did: remove the three tasks and restore the power settings
# saved by 01_power.ps1. Elevated PowerShell. Leaves the env file and the logs alone.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\99_uninstall.ps1 [-KeepPower]

param([switch]$KeepPower)

. "$PSScriptRoot\_common.ps1"
Assert-Admin

foreach ($name in @("bridge", "watchdog", "gitpull")) {
    $t = Get-ScheduledTask -TaskPath $TaskPath -TaskName $name -ErrorAction SilentlyContinue
    if ($t) {
        Stop-ScheduledTask -TaskPath $TaskPath -TaskName $name -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskPath $TaskPath -TaskName $name -Confirm:$false
        Write-Host "removed $TaskPath$name"
    } else {
        Write-Host "not present: $TaskPath$name"
    }
}

# Any python still serving from a previous manual start stays untouched on purpose:
# killing python.exe blindly would take down unrelated work.
Write-Host "if a manually started server is still listening, close its window yourself"

if ($KeepPower) { exit 0 }

$backupPath = Join-Path $env:USERPROFILE ".claude\ask_power_backup.json"
if (-not (Test-Path $backupPath)) {
    Write-Host "no power backup at $backupPath - power settings left as they are"
    exit 0
}
$b = Get-Content $backupPath -Raw | ConvertFrom-Json
function Restore { param([string]$Label, [string]$Cmd, $Seconds)
    if ($null -eq $Seconds) { Write-Host "skip $Label (not recorded)"; return }
    $min = [int]($Seconds / 60)
    powercfg /change $Cmd $min
    Write-Host ("restored {0} to {1} min" -f $Label, $min)
}
Restore "monitor timeout" "monitor-timeout-ac" $b.monitor_ac_s
Restore "sleep timeout" "standby-timeout-ac" $b.standby_ac_s
Restore "hibernate timeout" "hibernate-timeout-ac" $b.hibernate_ac_s
Restore "disk timeout" "disk-timeout-ac" $b.disk_ac_s
if ($null -ne $b.unattended_ac_s) {
    powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP 7bc4a2f9-d8fc-4469-b07b-33eb785aaca0 $b.unattended_ac_s
    powercfg /setactive SCHEME_CURRENT
}
if ($b.hibernate_file -eq $true) { powercfg /hibernate on; Write-Host "hibernate turned back on" }
Remove-Item $backupPath -Force
Write-Host "done"
