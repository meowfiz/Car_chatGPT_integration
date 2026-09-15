# Read only diagnostics for the work PC. Changes nothing. Run this FIRST and read the output.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\00_check.ps1

. "$PSScriptRoot\_common.ps1"

function Line { param([string]$k, $v) ; "{0,-22} {1}" -f $k, $v }

$problems = @()

Write-Host "== machine =="
$os = Get-CimInstance Win32_OperatingSystem
Write-Host (Line "host" $env:COMPUTERNAME)
Write-Host (Line "os" "$($os.Caption) $($os.Version)")
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host (Line "user" $id.Name)
Write-Host (Line "elevated" $isAdmin)
$domain = (Get-CimInstance Win32_ComputerSystem).PartOfDomain
Write-Host (Line "domain joined" $domain)
if ($domain) { $problems += "machine is domain joined - group policy may override power settings" }

Write-Host ""
Write-Host "== power =="
Write-Host "-- sleep states available (powercfg /a) --"
powercfg /a
Write-Host "-- current AC timeouts (minutes, 0 = never) --"
function Get-PowerIndexAc {
    param([string]$Sub, [string]$Setting)
    $raw = powercfg /query SCHEME_CURRENT $Sub $Setting 2>$null
    $hex = @($raw | Select-String -Pattern "0x[0-9a-fA-F]+" -AllMatches |
             ForEach-Object { $_.Matches } | ForEach-Object { $_.Value })
    if ($hex.Count -lt 2) { return $null }
    # last two hex values are the AC then DC power setting index
    return [Convert]::ToInt64($hex[$hex.Count - 2], 16)
}
$vid = Get-PowerIndexAc "SUB_VIDEO" "VIDEOIDLE"
$slp = Get-PowerIndexAc "SUB_SLEEP" "STANDBYIDLE"
$hib = Get-PowerIndexAc "SUB_SLEEP" "HIBERNATEIDLE"
$dsk = Get-PowerIndexAc "SUB_DISK" "DISKIDLE"
$una = Get-PowerIndexAc "SUB_SLEEP" "7bc4a2f9-d8fc-4469-b07b-33eb785aaca0"
foreach ($p in @(@("monitor off", $vid), @("sleep", $slp), @("hibernate", $hib),
                 @("disk off", $dsk), @("unattended sleep", $una))) {
    $v = $p[1]
    if ($null -eq $v) {
        # "unattended sleep" is hidden in the power UI until 01_power.ps1 unhides it
        Write-Host (Line $p[0] "hidden / not readable")
    } else {
        Write-Host (Line $p[0] ("{0} min" -f ($v / 60)))
    }
}
if ($slp -ne $null -and $slp -ne 0) { $problems += "machine still sleeps after $($slp/60) min - run 01_power.ps1" }
if ($isAdmin) {
    Write-Host "-- what currently keeps the machine awake (powercfg /requests) --"
    powercfg /requests
} else {
    Write-Host "-- powercfg /requests skipped (needs an elevated console) --"
}

Write-Host ""
Write-Host "== tools =="
function Probe { param([string]$name, [string]$cmd, [string[]]$cmdArgs)
    $c = Get-Command $cmd -ErrorAction SilentlyContinue
    if (-not $c) { Write-Host (Line $name "MISSING"); return $false }
    try { $v = (& $cmd @cmdArgs 2>&1 | Select-Object -First 1) } catch { $v = "present" }
    Write-Host (Line $name $v); return $true
}
if (-not (Probe "python" "python" @("--version"))) { $problems += "python missing" }
if (-not (Probe "git" "git" @("--version"))) { $problems += "git missing" }
if (-not (Probe "claude" "claude" @("--version"))) { $problems += "claude code missing or not on PATH" }
if (-not (Probe "node" "node" @("--version"))) { $problems += "node missing (claude code needs it)" }

$ts = Get-TailscaleIp4
Write-Host (Line "tailscale ip4" $(if ($ts) { $ts } else { "MISSING" }))
if (-not $ts) { $problems += "tailscale not logged in / not running" }

Write-Host "-- python packages --"
$py = @'
import importlib, sys
for m in ("faster_whisper", "ctranslate2"):
    try:
        mod = importlib.import_module(m)
        print("%-16s %s" % (m, getattr(mod, "__version__", "?")))
    except Exception as e:
        print("%-16s MISSING (%s)" % (m, type(e).__name__))
'@
$tmp = Join-Path $env:TEMP "ask_probe.py"
[IO.File]::WriteAllText($tmp, $py, [Text.Encoding]::ASCII)
python $tmp
Remove-Item $tmp -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "== claude session =="
$credOk = Test-Path (Join-Path $env:USERPROFILE ".claude")
Write-Host (Line "~/.claude present" $credOk)
if (-not $credOk) { $problems += "claude code never logged in as this user - run 'claude' once interactively" }

Write-Host ""
Write-Host "== repositories =="
$root = $env:ASK_ROOT
if (-not $root) { $root = "D:\claude_projects" }
Write-Host (Line "ASK_ROOT" $root)
if (Test-Path $root) {
    Get-ChildItem $root -Directory | ForEach-Object {
        $g = Join-Path $_.FullName ".git"
        if (Test-Path $g) {
            $head = (git -C $_.FullName log -1 --format="%h %cd" --date=short 2>$null)
            Write-Host (Line $_.Name $head)
        }
    }
} else {
    $problems += "ASK_ROOT $root does not exist - clone the repositories (see repos.txt)"
    Write-Host "MISSING"
}

Write-Host ""
Write-Host "== env file and port =="
Write-Host (Line "env file" $DefaultEnvFile)
if (Test-Path $DefaultEnvFile) {
    $cfg = Import-EnvFile $DefaultEnvFile
    $sec = ""
    if ($cfg.ContainsKey("ASK_SECRET")) { $sec = $cfg["ASK_SECRET"] }
    Write-Host (Line "ASK_SECRET" ("{0} chars" -f $sec.Length))
    if ($sec.Length -lt 24) { $problems += "ASK_SECRET shorter than 24 chars" }
    $port = 8787
    if ($cfg.ContainsKey("ASK_PORT") -and $cfg["ASK_PORT"] -ne "") { $port = [int]$cfg["ASK_PORT"] }
    $busy = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($busy) {
        Write-Host (Line "port $port" "BUSY (pid $($busy[0].OwningProcess))")
        $problems += "port $port already in use"
    } else {
        Write-Host (Line "port $port" "free")
    }
} else {
    Write-Host (Line "ASK_SECRET" "no env file yet")
    $problems += "env file missing - copy bridge.env.example to $DefaultEnvFile"
}

Write-Host ""
Write-Host "== scheduled tasks =="
$tasks = Get-ScheduledTask -TaskPath $TaskPath -ErrorAction SilentlyContinue
if ($tasks) {
    $tasks | ForEach-Object {
        $i = Get-ScheduledTaskInfo $_
        Write-Host (Line $_.TaskName "$($_.State), last $($i.LastTaskResult) at $($i.LastRunTime)")
    }
} else {
    Write-Host "none yet (02_install_tasks.ps1 creates them)"
}

Write-Host ""
Write-Host "== verdict =="
if ($problems.Count -eq 0) {
    Write-Host "no blockers found"
} else {
    $problems | ForEach-Object { Write-Host "TODO: $_" }
}
