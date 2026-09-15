# Measure the bridge end to end. On the work PC run it with no arguments (reads the env file);
# from another machine in the tailnet pass the address and the secret.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\check_bridge.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\check_bridge.ps1 `
#              -Address 100.x.y.z -Secret <secret> -Question "Ile zadan zostalo?"

param(
    [string]$Address,
    [string]$Secret,
    [int]$Port = 0,
    [string]$Question = "Nad czym teraz pracuje projekt Car?",
    [string]$EnvFile = (Join-Path $env:USERPROFILE ".claude\ask_bridge.env")
)

. "$PSScriptRoot\_common.ps1"

if (-not $Address -or -not $Secret) {
    $cfg = Import-EnvFile -Path $EnvFile
    if (-not $Address) { $Address = Resolve-Bind $cfg }
    if (-not $Secret) { $Secret = $cfg["ASK_SECRET"] }
    if ($Port -eq 0 -and $cfg.ContainsKey("ASK_PORT") -and $cfg["ASK_PORT"] -ne "") { $Port = [int]$cfg["ASK_PORT"] }
}
if ($Port -eq 0) { $Port = 8787 }
$base = "http://${Address}:${Port}"

Write-Host "target $base"
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
    $h = Invoke-WebRequest -UseBasicParsing -Uri "$base/health" -TimeoutSec 8
    Write-Host ("health   {0} in {1} ms" -f $h.StatusCode, $sw.ElapsedMilliseconds)
} catch {
    Write-Host "health   FAILED: $($_.Exception.Message)"
    exit 1
}

$body = @{ q = $Question } | ConvertTo-Json -Compress
$sw.Restart()
try {
    $r = Invoke-RestMethod -Method Post -Uri "$base/ask/$Secret`?format=json" `
                           -ContentType "application/json" -Body $body -TimeoutSec 180
    $sw.Stop()
    Write-Host ("ask      {0} ms wall, {1} ms server" -f $sw.ElapsedMilliseconds, $r.ms)
    Write-Host ""
    Write-Host "Q: $Question"
    Write-Host "A: $($r.a)"
} catch {
    Write-Host "ask      FAILED: $($_.Exception.Message)"
    exit 2
}
