#!/usr/bin/env python3
"""Ensure pdfplumber is installed before starting the app"""
import subprocess
import sys

try:
    import pdfplumber
    print("✅ pdfplumber already installed")
except ImportError:
    print("⚠️ pdfplumber not found, installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pdfplumber==0.10.3"])
    print("✅ pdfplumber installed")

# Now start Flask
if __name__ == '__main__':
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=True)
