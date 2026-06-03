#!/usr/bin/env python3
"""
Verification script for Hippique Predictor setup
"""

import os
from pathlib import Path

def check_file(path, file_type="file"):
    """Check if a file exists"""
    if os.path.exists(path):
        size = os.path.getsize(path) if os.path.isfile(path) else "dir"
        return f"✅ {path} ({size} bytes)" if isinstance(size, int) else f"✅ {path} (directory)"
    return f"❌ {path} (MISSING)"

def verify_setup():
    """Verify the complete project setup"""
    base = "."
    
    print("\n" + "="*70)
    print("🐴 HIPPIQUE PREDICTOR - SETUP VERIFICATION")
    print("="*70 + "\n")
    
    # Core files
    print("📄 Core Configuration Files:")
    print("  " + check_file("Dockerfile"))
    print("  " + check_file("docker-compose.yml"))
    print("  " + check_file("requirements.txt"))
    print("  " + check_file(".dockerignore"))
    print("  " + check_file(".gitignore"))
    print("  " + check_file(".env.example"))
    
    # Backend files
    print("\n🔌 Backend Python Files:")
    print("  " + check_file("backend/app.py"))
    print("  " + check_file("backend/wsgi.py"))
    print("  " + check_file("backend/model.py"))
    print("  " + check_file("backend/database.py"))
    print("  " + check_file("backend/data_preparation.py"))
    
    # Frontend files
    print("\n🎨 Frontend Files:")
    print("  " + check_file("frontend/index.html"))
    print("  " + check_file("frontend/style.css"))
    print("  " + check_file("frontend/script.js"))
    
    # Documentation
    print("\n📚 Documentation:")
    print("  " + check_file("README.md"))
    print("  " + check_file("LAUNCH.md"))
    print("  " + check_file("QUICKSTART.txt"))
    
    # Scripts
    print("\n🚀 Launch Scripts:")
    print("  " + check_file("start.bat"))
    print("  " + check_file("start.sh"))
    print("  " + check_file("setup.py"))
    print("  " + check_file("verify.py"))
    print("  " + check_file("Makefile"))
    
    # Data directories
    print("\n📁 Data Directories:")
    print("  " + check_file("data"))
    print("  " + check_file("models"))
    
    # Data files
    print("\n📊 Example Data:")
    print("  " + check_file("data/example_horses.csv"))
    
    print("\n" + "="*70)
    print("✅ SETUP VERIFICATION COMPLETE")
    print("="*70 + "\n")
    
    print("🚀 NEXT STEPS:")
    print("  1. Double-click start.bat")
    print("  2. Wait for Docker to start (30-40 seconds)")
    print("  3. Open: http://localhost:5000")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    verify_setup()
