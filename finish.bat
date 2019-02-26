@echo off
SETLOCAL

REM TODO: Check for local changes
FOR /F "tokens=* USEBACKQ" %%F in (`hg stat`) DO (
    SET _STAT=%%F
)
IF NOT ["%_STAT%"] == [""] (
    echo Local changes still need to be commited
    exit /b 1
)

FOR /F "tokens=* USEBACKQ" %%F in (`hg branch`) DO (
    SET BRANCHNAME=%%F
)

IF "%BRANCHNAME%" == "default" (
    echo Cannot finish default branch
    exit /b 1
)

IF "%BRANCHNAME%" == "dev" (
    echo Cannot finish dev branch
    exit /b 1
)

hg up default
if %errorlevel% neq 0 exit /b %errorlevel%

hg merge "%BRANCHNAME%"
if %errorlevel% neq 0 exit /b %errorlevel%

hg commit -m"Merging %BRANCHNAME%"
if %errorlevel% neq 0 exit /b %errorlevel%

hg up dev
if %errorlevel% neq 0 exit /b %errorlevel%

hg merge default
if %errorlevel% neq 0 exit /b %errorlevel%

hg commit -m"Merging %BRANCHNAME% from default"
if %errorlevel% neq 0 exit /b %errorlevel%
