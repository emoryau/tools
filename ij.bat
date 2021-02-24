@ECHO OFF

for %%I in (.) do title %%~nxI

for /d %%d in ("c:\tools") do set IDEA="%%d\idea.cmd"

if exist %CD%\*.iml (
    echo Found project
    %IDEA% "%CD%"
    goto :eof
)

if exist %CD%\pom.xml (
    echo Found maven pom
    call :getabsolute %CD%\pom.xml
    %IDEA% "%absolute%"
    goto :eof
)
goto :eof

:getabsolute
set absolute=%~f1
goto :eof
