#!/usr/bin/env python3
"""
Cleanup Script - Remove dead code and organize files
Run this AFTER applying optimization changes
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).parent

# Files to delete (dead code)
DEAD_FILES = [
    "app_old.py",
    "app_v2.py",
    "model.py",
    "pdf_routes.py",
    # Debug files
    "debug_horse_extraction.py",
    "debug_lines.py",
    "debug_pdf_structure.py",
    "debug_pdf.py",
    "debug_table_structure.py",
    "debug_table.py",
    # Fix files (patches, not integrated)
    "fix_app_json.py",
    "fix_features.py",
    "fix_import.py",
    "fix_parser_final.py",
    "fix_parser_v3.py",
    # Old PDF parsers (keep only pdf_parser_smart.py)
    "pdf_parser_v2.py",
    "pdf_parser_v3.py",
    "pdf_parser_final.py",
    "pdf_parser_ultimate.py",
    "pdf_parser.py",
    "advanced_pdf_parser.py",
]

# Test files to reorganize (don't delete, just note them)
TEST_FILES = [
    "test_cumulative_system.py",
    "test_features.py",
    "test_flow.py",
    "test_final_parser.py",
    "test_json_fix.py",
    "test_migration.py",
    "test_model_v2.py",
    "test_parse_pdf_file.py",
    "test_parser_docker.py",
    "test_parser_final.py",
    "test_parser_v3.py",
    "test_parser.py",
    "test_pdfplumber_direct.py",
    "test_pdfplumber.py",
    "test_smart.py",
    "test_ultimate.py",
    "test_v2_parser.py",
    "test_conversion.py",
]

# Misc temporary files
TEMP_FILES = [
    "page_0_text.txt",
    "page_1_text.txt",
]

def backup_and_remove(file_path):
    """Backup file and remove it"""
    if not file_path.exists():
        print(f"  ⊘ Not found: {file_path.name}")
        return False
    
    # Create backup
    backup_dir = BACKEND_DIR / "backup_optimization"
    backup_dir.mkdir(exist_ok=True)
    
    backup_path = backup_dir / f"{file_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    
    try:
        shutil.copy2(file_path, backup_path)
        file_path.unlink()
        print(f"  ✓ Removed (backup: {backup_path.name}): {file_path.name}")
        return True
    except Exception as e:
        print(f"  ✗ Error removing {file_path.name}: {e}")
        return False

def main():
    print("=" * 60)
    print("🧹 CLEANUP SCRIPT - Remove Dead Code & Optimize")
    print("=" * 60)
    
    removed_count = 0
    total_size_freed = 0
    
    # 1. Remove dead files
    print("\n[1/3] Removing dead files...")
    for filename in DEAD_FILES:
        file_path = BACKEND_DIR / filename
        if backup_and_remove(file_path):
            removed_count += 1
            try:
                total_size_freed += file_path.stat().st_size
            except:
                pass
    
    # 2. Identify test files
    print("\n[2/3] Test files to reorganize:")
    test_count = 0
    for filename in TEST_FILES:
        file_path = BACKEND_DIR / filename
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"  → {filename} ({size_kb:.1f}KB)")
            test_count += 1
    print(f"\n  Total test files: {test_count}")
    print("  ⚠ TODO: Move these to tests/ folder and use pytest")
    
    # 3. Remove temp files
    print("\n[3/3] Removing temporary files...")
    for filename in TEMP_FILES:
        file_path = BACKEND_DIR / filename
        if backup_and_remove(file_path):
            removed_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✓ Cleanup complete!")
    print(f"  - Files removed: {removed_count}")
    print(f"  - Space freed: ~{total_size_freed / 1024 / 1024:.1f}MB")
    print(f"  - Test files to reorganize: {test_count}")
    print("\n📌 Next steps:")
    print("  1. Create tests/ folder")
    print("  2. Move test files to tests/")
    print("  3. Install pytest and run: pytest tests/")
    print("  4. Rebuild Docker image: docker-compose build")
    print("  5. Restart app: docker-compose restart")
    print("=" * 60)

if __name__ == "__main__":
    print("\n⚠️  This will backup and remove dead code files.")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response in ["yes", "y"]:
        main()
    else:
        print("Cancelled.")
