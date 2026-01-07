#!/bin/bash
# Batch Process All PDFs in Current Directory
# ============================================
# This script processes all PDF files in the current directory
# and generates Excel schedules for each one.

echo "============================================================"
echo "Batch Processing All PDFs"
echo "============================================================"
echo ""

count=0

for pdf in *.pdf; do
    if [ -f "$pdf" ]; then
        echo "Processing: $pdf"
        python setup_report_processor.py "$pdf"
        ((count++))
        echo ""
    fi
done

echo "============================================================"
echo "Processed $count PDF files"
echo "============================================================"
