#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test Script for Setup Report Processor
============================================
This script tests the basic functionality of the setup report processor.
"""

import sys
from pathlib import Path

def test_installation():
    """Test if all required packages are installed."""
    print("Testing package installation...")

    try:
        import pdfplumber
        print("[OK] pdfplumber installed")
    except ImportError:
        print("[FAIL] pdfplumber NOT installed")
        return False

    try:
        import pandas
        print("[OK] pandas installed")
    except ImportError:
        print("[FAIL] pandas NOT installed")
        return False

    try:
        import openpyxl
        print("[OK] openpyxl installed")
    except ImportError:
        print("[FAIL] openpyxl NOT installed")
        return False

    try:
        import pytest
        print("[OK] pytest installed")
    except ImportError:
        print("[WARN] pytest NOT installed (optional, for testing)")

    print("\n[OK] All required packages are installed!\n")
    return True


def test_processor():
    """Test if the processor module can be imported."""
    print("Testing processor module...")

    try:
        from setup_report_processor import SetupReportProcessor
        print("[OK] setup_report_processor module can be imported")
        return True
    except ImportError as e:
        print(f"[FAIL] Cannot import setup_report_processor: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Setup Report Processor - Installation Test")
    print("="*60)
    print()

    # Test 1: Package installation
    if not test_installation():
        print("\n[WARN] Please install required packages:")
        print("   pip install -r requirements.txt")
        return 1

    # Test 2: Processor module
    if not test_processor():
        print("\n[WARN] Please ensure setup_report_processor.py is in the current directory")
        return 1

    # All tests passed
    print("="*60)
    print("[SUCCESS] All tests passed! You're ready to process PDFs.")
    print("="*60)
    print("\nQuick start:")
    print("  python setup_report_processor.py your_report.pdf")
    print("\nRun unit tests:")
    print("  pytest test_setup_report_processor.py -v")
    print()
    return 0


if __name__ == "__main__":
    exit(main())
