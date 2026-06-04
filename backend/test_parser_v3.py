#!/usr/bin/env python3
"""Test the complete PDF parser v3"""
from pdf_parser_v3 import parse_pdf_complete
import json

print("Testing PDF Parser V3...\n")

race_info, horses_df, pronostics, classements = parse_pdf_complete('/app/backend/test_full.pdf')

print("=" * 60)
print("RACE INFO:")
print("=" * 60)
print(json.dumps(race_info, indent=2, ensure_ascii=False))

print("\n" + "=" * 60)
print(f"HORSES ({len(horses_df)} total):")
print("=" * 60)
if not horses_df.empty:
    print(f"Columns: {list(horses_df.columns)}")
    print("\nFirst 3 horses:")
    print(horses_df[['horse_number', 'horse_name', 'jockey', 'trainer', 'weight', 'perf']].head(3).to_string())
else:
    print("❌ No horses extracted!")

print("\n" + "=" * 60)
print("PRONOSTICS (External sources):")
print("=" * 60)
if pronostics:
    for source, numbers in pronostics.items():
        print(f"{source}: {numbers}")
else:
    print("❌ No pronostics extracted!")

print("\n" + "=" * 60)
print("CLASSEMENTS:")
print("=" * 60)
if classements:
    for category, numbers in classements.items():
        print(f"{category}: {numbers}")
else:
    print("❌ No classements extracted!")

print("\n" + "=" * 60)
print("✅ TEST COMPLETE")
print("=" * 60)
