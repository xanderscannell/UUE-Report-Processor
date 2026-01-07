@echo off
REM Batch Process All PDFs in Current Directory
REM ============================================
REM This script processes all PDF files in the current directory
REM and generates Excel schedules for each one.

echo ============================================================
echo Batch Processing All PDFs
echo ============================================================
echo.

set count=0

for %%f in (*.pdf) do (
    echo Processing: %%f
    python setup_report_processor.py "%%f"
    set /a count+=1
    echo.
)

echo ============================================================
echo Processed %count% PDF files
echo ============================================================
pause
