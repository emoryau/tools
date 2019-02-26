@ECHO OFF

IF NOT [%1] == [] (
	SET BRANCHNAME=%~1
)
REM check for BRANCHNAME being set
IF ["%BRANCHNAME%"] == [""] (
	ECHO BRANCHNAME is not defined
	GOTO end
)
ECHO Branching to %BRANCHNAME% and commiting

hg branch "%BRANCHNAME%" && hg commit -m "Created branch %BRANCHNAME%"

:end