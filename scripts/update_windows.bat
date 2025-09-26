@echo off
setlocal

set "ROOT=%~dp0.."
cd /d "%ROOT%"

set "REPO_URL=%~1"
if "%REPO_URL%"=="" (
  for /f "delims=" %%i in ('git config --get remote.origin.url 2^>nul') do set "REPO_URL=%%i"
)
if "%REPO_URL%"=="" (
  echo Could not determine repository URL. Pass it as the first argument.
  exit /b 1
)

set "BRANCH=%~2"
if "%BRANCH%"=="" (
  for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%i"
  if "%BRANCH%"=="" (
    for /f "tokens=3" %%i in ('git remote show origin ^| findstr /c:"HEAD branch"') do set "BRANCH=%%i"
  )
  if "%BRANCH%"=="" set "BRANCH=main"
)

set "TMP_DIR=%TEMP%\pyarcade_update_%RANDOM%_%RANDOM%"
md "%TMP_DIR%" >nul 2>&1 || (
  echo Failed to create temporary directory.
  exit /b 1
)

set "EXIT_CODE=0"

echo Downloading latest files from %REPO_URL% (%BRANCH%)...
git clone --depth 1 --branch %BRANCH% "%REPO_URL%" "%TMP_DIR%\repo" >nul
if errorlevel 1 (
  set "EXIT_CODE=%ERRORLEVEL%"
  goto cleanup
)

echo Copying files into place...
robocopy "%TMP_DIR%\repo" "%ROOT%" /MIR /XD .git /XF update_windows.bat /XF update_linux.sh >nul
set "ROBOCODE=%ERRORLEVEL%"
if %ROBOCODE% GEQ 8 (
  set "EXIT_CODE=%ROBOCODE%"
  goto cleanup
)

echo Update complete.
goto cleanup

:cleanup
if exist "%TMP_DIR%" rmdir /s /q "%TMP_DIR%" >nul 2>&1
exit /b %EXIT_CODE%
