# Desktop shortcut "Wyjscie" with a global hotkey (default Ctrl+Alt+Q) that locks the session
# and turns the monitors off. No elevation needed.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\install_shortcut.ps1 [-Hotkey "CTRL+ALT+Q"]

param([string]$Hotkey = "CTRL+ALT+Q")

$target = Join-Path $PSScriptRoot "lock_and_blank.cmd"
if (-not (Test-Path $target)) { throw "missing $target" }

$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desktop "Wyjscie.lnk"

$sh = New-Object -ComObject WScript.Shell
$s = $sh.CreateShortcut($lnk)
$s.TargetPath = $target
$s.WorkingDirectory = $PSScriptRoot
$s.WindowStyle = 7            # minimized, so no console flashes on screen
$s.Hotkey = $Hotkey
$s.IconLocation = "$env:SystemRoot\System32\imageres.dll,101"
$s.Description = "Lock and blank the monitors, keep the ask bridge running"
$s.Save()

Write-Host "created $lnk"
Write-Host "hotkey $Hotkey (works while the desktop shortcut exists; do not delete it)"
