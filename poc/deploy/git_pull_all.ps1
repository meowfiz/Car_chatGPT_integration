# Hourly fast-forward pull of every repository under ASK_ROOT, so answers are not from a stale
# tree (HANDOFF requirement 4). Never pushes, never rebases, never touches a dirty tree
# (ZASADY 2.3 / 2.7: the work PC must not resolve anything on its own).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\git_pull_all.ps1

param([string]$EnvFile = (Join-Path $env:USERPROFILE ".claude\ask_bridge.env"))

. "$PSScriptRoot\_common.ps1"

$cfg = @{}
if (Test-Path $EnvFile) { $cfg = Import-EnvFile -Path $EnvFile }
$repos = Get-RepoPaths $cfg
if ($repos.Count -eq 0) {
    Write-Log "git_pull.log" "no repositories found (set ASK_REPOS or ASK_ROOT in $EnvFile)"
    exit 1
}

foreach ($repo in $repos) {
    $name = Split-Path $repo -Leaf

    $dirty = git -C $repo status --porcelain 2>$null
    if ($dirty) {
        Write-Log "git_pull.log" "$name skipped - working tree dirty"
        continue
    }
    $remote = git -C $repo remote 2>$null
    if (-not $remote) {
        Write-Log "git_pull.log" "$name skipped - no remote"
        continue
    }
    $before = (git -C $repo rev-parse --short HEAD 2>$null)
    $out = (git -C $repo pull --ff-only 2>&1) -join " "
    if ($LASTEXITCODE -ne 0) {
        Write-Log "git_pull.log" "$name FAILED: $out"
        continue
    }
    $after = (git -C $repo rev-parse --short HEAD 2>$null)
    if ($before -eq $after) {
        Write-Log "git_pull.log" "$name up to date ($after)"
    } else {
        Write-Log "git_pull.log" "$name $before -> $after"
    }
}
