@ECHO OFF

for /d %%d in ("c:\program files\JetBrains\IntelliJ*") do set IDEA="%%d\bin\idea64.exe"

if exist %CD%\*.iml (
    echo Found project
    start "" %IDEA% "%CD%"
    goto :eof
)

if exist %CD%\pom.xml (
    echo Found maven pom
    call :getabsolute %CD%\pom.xml
    start "" %IDEA% "%absolute%"
    goto :eof
)
goto :eof

:getabsolute
set absolute=%~f1
goto :eof
