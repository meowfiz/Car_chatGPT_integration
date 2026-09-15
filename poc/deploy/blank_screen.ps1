# Lock the workstation and switch the monitors off right now. The machine keeps working.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\blank_screen.ps1 [-NoLock]

param([switch]$NoLock)

$sig = @'
[DllImport("user32.dll")]
public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);
[DllImport("user32.dll")]
public static extern bool LockWorkStation();
'@
$api = Add-Type -MemberDefinition $sig -Name "ScreenApi" -Namespace "AskBridge" -PassThru

if (-not $NoLock) { [void]$api::LockWorkStation() }

# Give the lock animation and any pending mouse movement a moment, otherwise the display
# wakes back up immediately and it looks like the script did nothing.
Start-Sleep -Milliseconds 1200

$HWND_BROADCAST = -1
$WM_SYSCOMMAND  = 0x0112
$SC_MONITORPOWER = 0xF170
$POWER_OFF = 2
[void]$api::SendMessage($HWND_BROADCAST, $WM_SYSCOMMAND, $SC_MONITORPOWER, $POWER_OFF)
