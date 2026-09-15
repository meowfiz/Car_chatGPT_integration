# Shared helpers for the ask bridge deployment scripts (work PC, Windows Pro).
# ASCII only per ZASADY 4.1. Dot-source this file: . "$PSScriptRoot\_common.ps1"

$ErrorActionPreference = "Stop"
$DeployDir = $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RunFiles = Join-Path $RepoRoot "project_files\run_files"
$DefaultEnvFile = Join-Path $env:USERPROFILE ".claude\ask_bridge.env"
$TaskPath = "\AskBridge\"

function Assert-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $pr = New-Object Security.Principal.WindowsPrincipal($id)
    if (-not $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from an elevated PowerShell (Run as administrator)."
    }
}

function Import-EnvFile {
    param([string]$Path = $DefaultEnvFile, [switch]$SetProcessEnv)
    if (-not (Test-Path $Path)) {
        throw "Env file not found: $Path (copy bridge.env.example there and fill ASK_SECRET)"
    }
    $cfg = @{}
    foreach ($line in [IO.File]::ReadAllLines($Path, [Text.Encoding]::UTF8)) {
        $t = $line.Trim()
        if ($t -eq "" -or $t.StartsWith("#")) { continue }
        $i = $t.IndexOf("=")
        if ($i -lt 1) { continue }
        $k = $t.Substring(0, $i).Trim()
        $v = $t.Substring($i + 1).Trim()
        $cfg[$k] = $v
        if ($SetProcessEnv -and $v -ne "") { Set-Item -Path "Env:$k" -Value $v }
    }
    return $cfg
}

function Get-TailscaleIp4 {
    $exe = "C:\Program Files\Tailscale\tailscale.exe"
    if (-not (Test-Path $exe)) {
        $cmd = Get-Command tailscale.exe -ErrorAction SilentlyContinue
        if ($cmd) { $exe = $cmd.Source } else { return $null }
    }
    try {
        $out = & $exe ip -4 2>$null
    } catch {
        return $null
    }
    if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
    return ($out | Select-Object -First 1).Trim()
}

function Resolve-Bind {
    param($Cfg)
    if ($Cfg.ContainsKey("ASK_BIND") -and $Cfg["ASK_BIND"] -ne "") { return $Cfg["ASK_BIND"] }
    return (Get-TailscaleIp4)
}

function Write-Log {
    param([string]$Name, [string]$Message)
    if (-not (Test-Path $RunFiles)) { New-Item -ItemType Directory -Path $RunFiles -Force | Out-Null }
    $path = Join-Path $RunFiles $Name
    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "$stamp  $Message"
    Add-Content -Path $path -Value $line -Encoding UTF8
    Write-Host $line
}

function Send-Notify {
    # Optional: HA webhook so a dead bridge shows up on the phone, not in a log nobody reads.
    param($Cfg, [string]$Message)
    if (-not $Cfg.ContainsKey("HA_NOTIFY_URL")) { return }
    $url = $Cfg["HA_NOTIFY_URL"]
    if ($url -eq "") { return }
    try {
        $body = @{ message = $Message; title = "ask bridge" } | ConvertTo-Json -Compress
        Invoke-RestMethod -Method Post -Uri $url -ContentType "application/json" -Body $body -TimeoutSec 10 | Out-Null
    } catch {
        Write-Log "watchdog.log" "notify failed: $($_.Exception.Message)"
    }
}
