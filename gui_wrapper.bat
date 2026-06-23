@echo off
REM Setup Report Processor - GUI Launcher (Windows)
REM ================================================
REM This script launches the GUI wrapper for the Setup Report Processor.
REM It automatically sets up a virtual environment and installs dependencies on first run.

cd /d "%~dp0"

echo ========================================
echo Setup Report Processor - GUI
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Setting up virtual environment...
    echo This will only happen once.
    echo.

    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Please ensure Python 3.10+ is installed and in your PATH.
        pause
        exit /b 1
    )

    call venv\Scripts\activate.bat

    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )

    echo.
    echo Setup complete!
    echo.
) else (
    call venv\Scripts\activate.bat
)

REM Launch the GUI
echo Launching GUI...
python gui_wrapper.py

if errorlevel 1 (
    echo.
    echo ERROR: GUI failed to start.
    echo Check the error messages above for details.
    pause
    exit /b 1
)
