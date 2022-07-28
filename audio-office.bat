@echo off
REM Kill a running copy of voicemeeter
taskkill /f /im voicemeeter8.exe
REM Restart voicemeeter with office config
REM FIXME TODO this doesn't ever exit and finish running the batch file
"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8.exe" -l "C:\Users\emory.au\office.xml"
REM set priority and affinity for windows audio thing
wmic process where name="audiodg.exe" CALL setpriority "128"
PowerShell "$Process = Get-Process audiodg; $Process.ProcessorAffinity=2"
