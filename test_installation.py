#!/usr/bin/env python3
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
        print("✓ pdfplumber installed")
    except ImportError:
        print("✗ pdfplumber NOT installed")
        return False
    
    try:
        import pandas
        print("✓ pandas installed")
    except ImportError:
        print("✗ pandas NOT installed")
        return False
    
    try:
        import openpyxl
        print("✓ openpyxl installed")
    except ImportError:
        print("✗ openpyxl NOT installed")
        return False
    
    print("\n✓ All required packages are installed!\n")
    return True


def test_processor():
    """Test if the processor module can be imported."""
    print("Testing processor module...")
    
    try:
        from setup_report_processor import SetupReportProcessor
        print("✓ setup_report_processor module can be imported")
        return True
    except ImportError as e:
        print(f"✗ Cannot import setup_report_processor: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Setup Report Processor - Installation Test")
    print("="*60)
    print()
    
    # Test 1: Package installation
    if not test_installation():
        print("\n⚠ Please install required packages:")
        print("   pip install -r requirements.txt")
        return 1
    
    # Test 2: Processor module
    if not test_processor():
        print("\n⚠ Please ensure setup_report_processor.py is in the current directory")
        return 1
    
    # All tests passed
    print("="*60)
    print("✓ All tests passed! You're ready to process PDFs.")
    print("="*60)
    print("\nQuick start:")
    print("  python setup_report_processor.py your_report.pdf")
    print()
    return 0


if __name__ == "__main__":
    exit(main())
