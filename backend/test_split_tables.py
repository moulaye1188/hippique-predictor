#!/usr/bin/env python3
"""
Test script for split table detection and extraction
Run: python backend/test_split_tables.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_parser_smart import parse_pdf_smart

def test_pdf_parsing(pdf_path):
    """Test PDF parsing with split table detection"""
    
    print("\n" + "="*60)
    print("🧪 PDF PARSING TEST - SPLIT TABLE DETECTION")
    print("="*60)
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return False
    
    print(f"\n📄 Testing: {pdf_path}")
    print(f"   File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    # Parse PDF
    print("\n🔄 Parsing PDF...")
    race_info, horses_df, pronostics, classements, best_week, arrivals = parse_pdf_smart(pdf_path)
    
    # Results
    print("\n" + "="*60)
    print("📊 RESULTS")
    print("="*60)
    
    # Race info
    print("\n1. RACE INFO:")
    if race_info:
        print(f"   Date: {race_info.get('race_date', 'N/A')}")
        print(f"   Hippodrome: {race_info.get('hippodrome', 'N/A')}")
        print(f"   Distance: {race_info.get('distance', 'N/A')} m")
        print(f"   Race Type: {race_info.get('race_type_bet', 'N/A')}")
        print(f"   Competitors: {race_info.get('num_competitors', 'N/A')}")
    else:
        print("   ❌ No race info found")
    
    # Horses
    print("\n2. HORSES EXTRACTED:")
    print(f"   Total: {len(horses_df)}")
    if len(horses_df) > 0:
        print(f"   ✅ Horse numbers: {list(horses_df['horse_number'].unique())[:5]}...")
        print(f"\n   First 3 horses:")
        for idx, row in horses_df.head(3).iterrows():
            print(f"   #{row.get('horse_number', '?')} - {row.get('horse_name', '?')}")
        if len(horses_df) > 3:
            print(f"   ...\n   Last 3 horses:")
            for idx, row in horses_df.tail(3).iterrows():
                print(f"   #{row.get('horse_number', '?')} - {row.get('horse_name', '?')}")
    else:
        print("   ❌ No horses found!")
    
    # Pronostics
    print("\n3. PRONOSTICS:")
    if pronostics:
        for source, horses in pronostics.items():
            print(f"   {source}: {horses[:3]}...")
    else:
        print("   ⚠️  No pronostics found")
    
    # Classements
    print("\n4. CLASSEMENTS:")
    if classements:
        for cat, horses in list(classements.items())[:3]:
            print(f"   {cat}: {horses[:3]}...")
    else:
        print("   ⚠️  No classements found")
    
    # Best week
    print("\n5. BEST WEEK:")
    if best_week:
        print(f"   {best_week}")
    else:
        print("   ⚠️  No best week found")
    
    # Arrivals
    print("\n6. RACE ARRIVALS:")
    if arrivals:
        print(f"   Quartet: {arrivals.get('quartet', 'N/A')}")
        print(f"   1st: {arrivals.get('1st', 'N/A')}")
        print(f"   2nd: {arrivals.get('2nd', 'N/A')}")
        print(f"   3rd: {arrivals.get('3rd', 'N/A')}")
        print(f"   4th: {arrivals.get('4th', 'N/A')}")
    else:
        print("   ℹ️  No arrivals found (expected if not in PDF)")
    
    # Summary
    print("\n" + "="*60)
    print("✅ SUMMARY")
    print("="*60)
    print(f"✓ Race extracted: {'Yes' if race_info else 'No'}")
    print(f"✓ Horses extracted: {len(horses_df)} horses")
    print(f"✓ Pronostics found: {len(pronostics)} sources")
    print(f"✓ Classements found: {len(classements)} categories")
    print(f"✓ Arrivals found: {'Yes' if arrivals else 'No'}")
    
    # Check for split table success
    if len(horses_df) >= 15:
        print(f"\n✅ SPLIT TABLE DETECTION: SUCCESS!")
        print(f"   Extracted {len(horses_df)} horses (likely from 2-column table)")
    elif len(horses_df) >= 10:
        print(f"\n🟡 SPLIT TABLE DETECTION: Partial")
        print(f"   Extracted {len(horses_df)} horses")
    else:
        print(f"\n⚠️  SPLIT TABLE DETECTION: May not have detected split")
        print(f"   Extracted only {len(horses_df)} horses")
    
    print("\n" + "="*60 + "\n")
    return True


if __name__ == "__main__":
    # Test with any available PDF
    test_pdfs = [
        "data/test_race.pdf",
        "/app/data/test.pdf",
        "../data/test_race.pdf"
    ]
    
    found_pdf = None
    for pdf in test_pdfs:
        if os.path.exists(pdf):
            found_pdf = pdf
            break
    
    if found_pdf:
        test_pdf_parsing(found_pdf)
    else:
        print("\n⚠️  No test PDF found!")
        print("   Place a PDF file in data/ directory and try again")
        print("\nUsage:")
        print("   python backend/test_split_tables.py")
