@echo off
setlocal

REM Delete the existing main-ui folder
if exist "main-ui" (
    rmdir /s /q "main-ui"
)

REM Copy main-ui from the source directory into the current directory
xcopy "..\spruceOS\App\PyUI\main-ui" "main-ui\" /E /I /H /Y

echo Done.
pause