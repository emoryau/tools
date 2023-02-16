$User32 = Add-Type -Debug:$False -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X,int Y, int cx, int cy, uint uFlags);' -Name "User32Functions" -namespace User32Functions -PassThru

# Set streamer view window always on top
$vmsHandle = (Get-Process -Name VMStreamerView).MainWindowHandle
[Void]$User32::SetWindowPos($vmsHandle, -1, 708, -936, 457, 127, 0)

# Move slack window, Get-Process returns several matches, but only 1 is the "real" handle, the rest are null
$slackHandles = (Get-Process -Name Slack).MainWindowHandle
ForEach ($h in $slackHandles) {
    if (0 -ne $h) {
        [Void]$User32::SetWindowPos($h, 0, -760, -1040, 960, 1040, 0)
    }
}

# Move teams window, Get-Process returns several matches, but only 1 is the "real" handle, the rest are null
$teamsHandles = (Get-Process -Name Teams).MainWindowHandle
ForEach ($h in $teamsHandles) {
    if (0 -ne $h) {
        [Void]$User32::SetWindowPos($h, 0, 200, -1040, 960, 1040, 0)
    }
}

# Try to rest winlirc