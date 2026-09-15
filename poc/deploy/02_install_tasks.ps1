# Install the three scheduled tasks. Elevated PowerShell.
#   AskBridge\bridge    at system startup, runs the ask server, restarts itself on crash
#   AskBridge\watchdog  every 5 min, health check + hourly deep check, restarts the bridge
#   AskBridge\gitpull   every hour, fast-forward pull of the repositories
#
# The bridge task runs as YOU (not SYSTEM) because claude code reads its login from
# %USERPROFILE%\.claude. With a stored password it also runs while nobody is logged in,
# which is the whole point: a reboot at 3 a.m. must not take the bridge down.
#
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\02_install_tasks.ps1
#        add -NoPassword to register without storing the password (task then starts only
#        after the first logon, and survives a lock but not a reboot to the login screen)

param(
    [string]$EnvFile = (Join-Path $env:USERPROFILE ".claude\ask_bridge.env"),
    [switch]$NoPassword
)

. "$PSScriptRoot\_common.ps1"
Assert-Admin

$cfg = Import-EnvFile -Path $EnvFile
if (-not $cfg.ContainsKey("ASK_SECRET") -or $cfg["ASK_SECRET"].Length -lt 24) {
    $suggested = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
    throw "ASK_SECRET missing or shorter than 24 chars in $EnvFile. Suggested value: $suggested"
}

$me = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

function New-RepeatingTrigger {
    param([int]$Minutes)
    # The reliable Win10/11 pattern: a daily trigger whose repetition block is copied from a
    # one-shot trigger. Setting RepetitionDuration directly throws on some builds.
    $daily = New-ScheduledTaskTrigger -Daily -At "00:00"
    $once = New-ScheduledTaskTrigger -Once -At "00:00" `
              -RepetitionInterval (New-TimeSpan -Minutes $Minutes) `
              -RepetitionDuration (New-TimeSpan -Days 1)
    $daily.Repetition = $once.Repetition
    return $daily
}

function Register-One {
    param([string]$Name, [string]$Script, $Trigger, $Settings, [switch]$WithPassword, [string]$Plain)
    $action = New-ScheduledTaskAction -Execute $ps -Argument (
        "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`" -EnvFile `"$EnvFile`"")
    if ($WithPassword) {
        Register-ScheduledTask -TaskPath $TaskPath -TaskName $Name -Action $action -Trigger $Trigger `
            -Settings $Settings -User $me -Password $Plain -RunLevel Limited -Force | Out-Null
    } else {
        $principal = New-ScheduledTaskPrincipal -UserId $me -LogonType S4U -RunLevel Limited
        Register-ScheduledTask -TaskPath $TaskPath -TaskName $Name -Action $action -Trigger $Trigger `
            -Settings $Settings -Principal $principal -Force | Out-Null
    }
    Write-Host "registered $TaskPath$Name"
}

$plain = $null
if (-not $NoPassword) {
    Write-Host "Windows password for $me (stored by Task Scheduler, needed to run without a logon):"
    $cred = Get-Credential -UserName $me -Message "Password for the bridge task"
    $plain = $cred.GetNetworkCredential().Password
    if (-not $plain) { throw "empty password - rerun with -NoPassword if this account has none" }
}

# --- bridge ------------------------------------------------------------------------------
$bridgeSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
$bridgeTrigger = New-ScheduledTaskTrigger -AtStartup
Register-One -Name "bridge" -Script (Join-Path $PSScriptRoot "run_bridge.ps1") `
    -Trigger $bridgeTrigger -Settings $bridgeSettings -WithPassword:(-not $NoPassword) -Plain $plain

# --- watchdog ----------------------------------------------------------------------------
$shortSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
Register-One -Name "watchdog" -Script (Join-Path $PSScriptRoot "watchdog.ps1") `
    -Trigger (New-RepeatingTrigger -Minutes 5) -Settings $shortSettings `
    -WithPassword:(-not $NoPassword) -Plain $plain

# --- git pull ----------------------------------------------------------------------------
Register-One -Name "gitpull" -Script (Join-Path $PSScriptRoot "git_pull_all.ps1") `
    -Trigger (New-RepeatingTrigger -Minutes 60) -Settings $shortSettings `
    -WithPassword:(-not $NoPassword) -Plain $plain

$plain = $null
[GC]::Collect()

Write-Host ""
Write-Host "starting the bridge now..."
Start-ScheduledTask -TaskPath $TaskPath -TaskName "bridge"
Start-Sleep -Seconds 8
Get-ScheduledTask -TaskPath $TaskPath | ForEach-Object {
    $i = Get-ScheduledTaskInfo $_
    "{0,-10} {1,-8} last result {2}" -f $_.TaskName, $_.State, $i.LastTaskResult
}
Write-Host ""
Write-Host "check it answers:  powershell -NoProfile -File .\check_bridge.ps1"
