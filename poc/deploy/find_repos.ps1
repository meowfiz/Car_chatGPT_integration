# Find the git checkouts on THIS machine and print the ASK_REPOS line to paste into
# %USERPROFILE%\.claude\ask_bridge.env. Repositories do not have to share a parent directory
# and they sit in different places on the home and the work PC - this is how you pin them down.
#
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\find_repos.ps1
#        .\find_repos.ps1 -SearchRoots "D:\","C:\Users\me\src" -Depth 4
#        .\find_repos.ps1 -Apply           writes the line into the env file

param(
    [string[]]$SearchRoots,
    [int]$Depth = 3,
    [string[]]$Names = @("Car_chatGPT_integration", "project_integration", "HA", "nihongo_no_sensei"),
    [switch]$All,
    [switch]$Apply,
    [string]$EnvFile = (Join-Path $env:USERPROFILE ".claude\ask_bridge.env")
)

. "$PSScriptRoot\_common.ps1"

if (-not $SearchRoots) {
    $SearchRoots = @(Get-PSDrive -PSProvider FileSystem |
        Where-Object { $_.Used -ne $null -and $_.Name.Length -eq 1 } |
        ForEach-Object { "$($_.Name):\" })
}

Write-Host ("scanning (depth {0}): {1}" -f $Depth, ($SearchRoots -join ", "))
$found = @()
foreach ($root in $SearchRoots) {
    if (-not (Test-Path $root)) { continue }
    try {
        $hits = Get-ChildItem -Path $root -Directory -Filter ".git" -Recurse -Depth $Depth `
                    -Force -ErrorAction SilentlyContinue
    } catch {
        continue
    }
    foreach ($h in $hits) {
        $repo = Split-Path $h.FullName -Parent
        $name = Split-Path $repo -Leaf
        if (-not $All -and ($Names -notcontains $name)) { continue }
        if ($repo -like "*\node_modules\*") { continue }
        $found += $repo
    }
}
$found = @($found | Sort-Object -Unique)

if ($found.Count -eq 0) {
    Write-Host "nothing found - widen the search with -SearchRoots / -Depth, or -All"
    exit 1
}

Write-Host ""
foreach ($f in $found) {
    $head = (git -C $f log -1 --format="%h %cd %s" --date=short 2>$null)
    $remote = (git -C $f remote get-url origin 2>$null)
    "{0,-28} {1}" -f (Split-Path $f -Leaf), $f
    "{0,-28} {1}" -f "" , "$head"
    if ($remote) { "{0,-28} {1}" -f "", $remote }
}

$line = "ASK_REPOS=" + ($found -join ";")
Write-Host ""
Write-Host $line

if (-not $Apply) {
    Write-Host ""
    Write-Host "paste that line into $EnvFile (or rerun with -Apply)"
    exit 0
}

if (-not (Test-Path $EnvFile)) { throw "env file not found: $EnvFile" }
$lines = [IO.File]::ReadAllLines($EnvFile, [Text.Encoding]::UTF8)
$done = $false
$out = foreach ($l in $lines) {
    if ($l -match "^\s*ASK_REPOS\s*=") { $done = $true; $line } else { $l }
}
if (-not $done) { $out = $out + $line }
[IO.File]::WriteAllLines($EnvFile, $out, (New-Object Text.UTF8Encoding($false)))
Write-Host "written to $EnvFile"
