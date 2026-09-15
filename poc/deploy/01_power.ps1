# Make the work PC stay awake with the monitors dark. Elevated PowerShell.
# Backs the current values up first, so 99_uninstall.ps1 can put them back.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\01_power.ps1 [-MonitorMinutes 5] [-KeepHibernate]

param(
    [int]$MonitorMinutes = 5,
    [switch]$KeepHibernate
)

. "$PSScriptRoot\_common.ps1"
Assert-Admin

$UNATTENDED = "7bc4a2f9-d8fc-4469-b07b-33eb785aaca0"   # System unattended sleep timeout

function Get-IndexAc {
    param([string]$Sub, [string]$Setting)
    $raw = powercfg /query SCHEME_CURRENT $Sub $Setting 2>$null
    $hex = @($raw | Select-String -Pattern "0x[0-9a-fA-F]+" -AllMatches |
             ForEach-Object { $_.Matches } | ForEach-Object { $_.Value })
    if ($hex.Count -lt 2) { return $null }
    return [Convert]::ToInt64($hex[$hex.Count - 2], 16)
}

powercfg /attributes SUB_SLEEP $UNATTENDED -ATTRIB_HIDE | Out-Null   # readable before we back it up

$backupPath = Join-Path $env:USERPROFILE ".claude\ask_power_backup.json"
if (-not (Test-Path $backupPath)) {
    $backup = [ordered]@{
        saved_utc        = (Get-Date).ToUniversalTime().ToString("s")
        scheme           = ((powercfg /getactivescheme) -join " ")
        monitor_ac_s     = Get-IndexAc "SUB_VIDEO" "VIDEOIDLE"
        standby_ac_s     = Get-IndexAc "SUB_SLEEP" "STANDBYIDLE"
        hibernate_ac_s   = Get-IndexAc "SUB_SLEEP" "HIBERNATEIDLE"
        disk_ac_s        = Get-IndexAc "SUB_DISK"  "DISKIDLE"
        unattended_ac_s  = Get-IndexAc "SUB_SLEEP" $UNATTENDED
        hibernate_file   = (Test-Path "$env:SystemDrive\hiberfil.sys")
    }
    $backup | ConvertTo-Json | Set-Content -Path $backupPath -Encoding UTF8
    Write-Host "saved current power settings to $backupPath"
} else {
    Write-Host "backup already exists, keeping it: $backupPath"
}

# 1. Monitors go dark on their own after N minutes of no input.
powercfg /change monitor-timeout-ac $MonitorMinutes
# 2. The machine itself never sleeps, never hibernates, disks stay spun up.
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change disk-timeout-ac 0
# 3. The trap that catches people: "unattended sleep" fires after a remote wake even when
#    the normal sleep timeout is Never. Set it to Never too.
powercfg /attributes SUB_SLEEP $UNATTENDED -ATTRIB_HIDE   # hidden by default, unhide so it is auditable
powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP $UNATTENDED 0
powercfg /setactive SCHEME_CURRENT
# 4. No hibernate file at all -> no hybrid sleep, no fast startup surprises after a power cut.
if (-not $KeepHibernate) { powercfg /hibernate off }

# 5. Network card is not allowed to power itself down (it would drop Tailscale silently).
$nics = Get-NetAdapter -Physical | Where-Object { $_.Status -eq "Up" }
foreach ($n in $nics) {
    try {
        $p = Get-NetAdapterPowerManagement -Name $n.Name -ErrorAction Stop
        $p.AllowComputerToTurnOffDevice = "Disabled"
        Set-NetAdapterPowerManagement -InputObject $p -ErrorAction Stop
        Write-Host ("nic power save off: {0}" -f $n.Name)
    } catch {
        Write-Host ("nic power save unchanged ({0}): {1}" -f $n.Name, $_.Exception.Message)
    }
}

# 6. USB selective suspend off - the microphone-less bridge does not need it and it has bitten
#    Tailscale USB ethernet dongles before.
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
powercfg /setactive SCHEME_CURRENT

Write-Host ""
Write-Host "== result (minutes, 0 = never) =="
"{0,-20} {1}" -f "monitor off", ((Get-IndexAc "SUB_VIDEO" "VIDEOIDLE") / 60)
"{0,-20} {1}" -f "sleep", ((Get-IndexAc "SUB_SLEEP" "STANDBYIDLE") / 60)
"{0,-20} {1}" -f "hibernate", ((Get-IndexAc "SUB_SLEEP" "HIBERNATEIDLE") / 60)
"{0,-20} {1}" -f "disk off", ((Get-IndexAc "SUB_DISK" "DISKIDLE") / 60)
"{0,-20} {1}" -f "unattended sleep", ((Get-IndexAc "SUB_SLEEP" $UNATTENDED) / 60)
Write-Host ""
Write-Host "Locking the workstation does NOT sleep the machine with these settings."
Write-Host "Use lock_and_blank.cmd (or its hotkey) when you leave to kill the monitors now."
