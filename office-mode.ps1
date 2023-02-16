Import-Module Voicemeeter

function Start-Voicemeeter {
    Start-Process -FilePath 'C:\Program Files (x86)\vb\Voicemeeter\voicemeeter8x64.exe' -WorkingDirectory "C:\Program Files (x86)\VB\Voicemeeter" -WindowStyle Hidden -ArgumentList "-l", "C:\Users\emory.au\Office.xml"     
}

function Set-Audio-Priority {
    # audiodg.exe needs high priority and affinity set to run on a single core for real-time performance
    Get-WmiObject Win32_process -filter 'name = "audiodg.exe"' | foreach-object {
        $_.SetPriority(128)
    }
    $audiodg_process = Get-Process audiodg
    $audiodg_process.ProcessorAffinity = 1
}

# Restart WinLIRC
$winlirc = Get-Process -Name winlirc -ErrorAction SilentlyContinue
if ($winlrc) {
    $winlirc | Stop-Process
}
Start-Process -filepath 'C:\Program Files\WinLIRC\winlirc.exe' -Workingdirectory 'C:\Program Files\WinLIRC\'

# Set AVR to laptop input
Start-Process -FilePath 'C:\Program Files\WinLIRC\Transmit.exe' -ArgumentList "yamaha", "scene_bd_dvd", "0"

# Voicemeeter - load office config, restart if necessary, launch if necessary
$vmProcess = Get-Process -Name voicemeeter8x64 -ErrorAction SilentlyContinue
if (!$vmProcess) {
    # if the 64 bit version was not found, try the 32 bit version
    $vmProcess = Get-Process -Name voicemeeter8 -ErrorAction SilentlyContinue
}
if ($vmProcess) {
    # process is running, try to load the office confg
    try {
        $vmb = Get-RemoteBanana
        # Send command to load the office.xml config
        $vmb.button[0].state = $true
    } catch {
        # any errors, stop the voicemeeter process and restart
        $vmProcess | Stop-Process -ErrorAction SilentlyContinue
        Start-Voicemeeter
    } finally {
        $vmb.Logout()
    }
} else {
    # Voicemeeter is not yet running
    Start-Voicemeeter
}

# Sleep for 5 seconds to give voicemeeter time to settle
Start-Sleep 5

Set-Audio-Priority