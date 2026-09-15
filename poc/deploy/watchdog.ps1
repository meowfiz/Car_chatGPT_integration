# Runs every 5 minutes from the scheduled task AskBridge\watchdog.
#  shallow check: GET /health - catches a dead or crashed server
#  deep check   : POST /ask - catches the failure /health cannot see, a claude session that
#                 expired, so the bridge answers HTTP 200 with an error text
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\watchdog.ps1 [-Force]

param(
    [string]$EnvFile = (Join-Path $env:USERPROFILE ".claude\ask_bridge.env"),
    [switch]$Force
)

. "$PSScriptRoot\_common.ps1"

$cfg = Import-EnvFile -Path $EnvFile
$bind = Resolve-Bind $cfg
if (-not $bind) {
    Write-Log "watchdog.log" "no tailscale address - cannot check"
    exit 1
}
$port = 8787
if ($cfg.ContainsKey("ASK_PORT") -and $cfg["ASK_PORT"] -ne "") { $port = [int]$cfg["ASK_PORT"] }
$base = "http://${bind}:${port}"

function Test-Health {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "$base/health" -TimeoutSec 8
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

$ok = Test-Health
if (-not $ok) {
    Start-Sleep -Seconds 5
    $ok = Test-Health
}

if (-not $ok) {
    Write-Log "watchdog.log" "health FAILED at $base - restarting task"
    try {
        Stop-ScheduledTask -TaskPath $TaskPath -TaskName "bridge" -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        Start-ScheduledTask -TaskPath $TaskPath -TaskName "bridge"
        Send-Notify $cfg "Most pytan nie odpowiadal - zadanie zrestartowane"
    } catch {
        Write-Log "watchdog.log" "restart failed: $($_.Exception.Message)"
        Send-Notify $cfg "Most pytan lezy i restart sie nie udal"
    }
    exit 1
}

# --- deep check -------------------------------------------------------------------------
$deepMin = 60
if ($cfg.ContainsKey("ASK_DEEP_MIN") -and $cfg["ASK_DEEP_MIN"] -ne "") { $deepMin = [int]$cfg["ASK_DEEP_MIN"] }
if ($deepMin -le 0 -and -not $Force) { exit 0 }

$stamp = Join-Path $RunFiles "watchdog_deep.stamp"
$due = $Force
if (-not $due) {
    if (-not (Test-Path $stamp)) {
        $due = $true
    } elseif ((Get-Date) -gt (Get-Item $stamp).LastWriteTime.AddMinutes($deepMin)) {
        $due = $true
    }
}
if (-not $due) { exit 0 }

$secret = $cfg["ASK_SECRET"]
$body = @{ q = "Odpowiedz jednym zdaniem: nad czym teraz pracuje projekt Car?" } | ConvertTo-Json -Compress
try {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $r = Invoke-RestMethod -Method Post -Uri "$base/ask/$secret`?format=json" `
                           -ContentType "application/json" -Body $body -TimeoutSec 150
    $sw.Stop()
    $answer = ""
    if ($r.a) { $answer = [string]$r.a }
    if ($answer.Trim().Length -lt 10) {
        Write-Log "watchdog.log" "deep check EMPTY answer after $($sw.ElapsedMilliseconds) ms"
        Send-Notify $cfg "Most odpowiada pusto - sprawdz, czy claude jest zalogowany"
    } else {
        Write-Log "watchdog.log" ("deep check ok in {0} ms: {1}" -f $sw.ElapsedMilliseconds,
                                  $answer.Substring(0, [Math]::Min(80, $answer.Length)))
    }
} catch {
    Write-Log "watchdog.log" "deep check FAILED: $($_.Exception.Message)"
    Send-Notify $cfg "Most nie odpowiedzial na pytanie kontrolne"
}
Set-Content -Path $stamp -Value (Get-Date).ToString("s") -Encoding ASCII
