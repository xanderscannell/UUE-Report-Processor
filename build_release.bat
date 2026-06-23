@echo off
REM ============================================================
REM  Build the Setup Report Processor release binary (PySide6).
REM  Produces a portable --onedir bundle and zips it for release.
REM
REM  Usage:
REM    build_release.bat            (build only)
REM    build_release.bat /deps      (also (re)install dependencies first)
REM ============================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set APP_NAME=SetupReportProcessor
set DIST_DIR=dist\%APP_NAME%

echo.
echo ============================================================
echo  Building %APP_NAME%
echo ============================================================

REM -- Optional dependency install (pass /deps) ----------------
if /i "%~1"=="/deps" (
    echo [1/5] Installing dependencies...
    python -m pip install -r requirements.txt pyinstaller || goto :error
) else (
    echo [1/5] Skipping dependency install ^(pass /deps to force^).
)

REM -- Clean previous build artifacts --------------------------
echo [2/5] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%APP_NAME%.zip" del /q "%APP_NAME%.zip"

REM -- Build with PyInstaller ----------------------------------
echo [3/5] Running PyInstaller...
python -m PyInstaller --noconfirm --windowed --name %APP_NAME% --icon=UUE.ico gui_wrapper.py || goto :error

REM -- Copy runtime files next to the exe ----------------------
echo [4/5] Copying runtime files...
copy /y location_config.json "%DIST_DIR%\" >nul || goto :error
copy /y UUE.ico "%DIST_DIR%\" >nul || goto :error

REM -- Zip the bundle for distribution -------------------------
echo [5/5] Creating %APP_NAME%.zip...
powershell -NoProfile -Command "Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath '%APP_NAME%.zip' -Force" || goto :error

echo.
echo ============================================================
echo  SUCCESS
echo    Bundle: %DIST_DIR%\%APP_NAME%.exe
echo    Zip:    %CD%\%APP_NAME%.zip
echo ============================================================
echo  Tip: launch the exe and click "View Gantt" to confirm the
echo  bundled build renders correctly before sharing the zip.
goto :end

:error
set RC=!ERRORLEVEL!
echo.
echo ============================================================
echo  BUILD FAILED ^(exit code !RC!^)
echo ============================================================
exit /b !RC!

:end
endlocal
