@echo off
rem Generated by JetBrains Toolbox 1.27.2.13801 at 2023-02-15T14:02:13.021768

set waitarg=
set ideargs=

:next
set "passwait="
if "%~1"=="--wait" set passwait=1
if "%~1"=="-w" set passwait=1
if defined passwait (set waitarg=/wait)
if not "%~1"=="" (
  if defined passwait (set "ideargs=%ideargs%--wait ") else (set "ideargs=%ideargs%%1 ")
  shift
  goto next
)

start "" %waitarg% C:\Users\emory.au\AppData\Local\JetBrains\Toolbox\apps\WebStorm\ch-0\223.8617.44\bin\webstorm64.exe %ideargs%