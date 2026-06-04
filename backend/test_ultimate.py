#!/usr/bin/env python3
"""Test ULTIMATE parser"""
from pdf_parser_ultimate import parse_pdf_ultimate
import json

print("Testing ULTIMATE PDF Parser...\n")

race_info, horses_df, pronostics, classements, best_week = parse_pdf_ultimate('/app/backend/test_full.pdf')

print("=" * 80)
print("RACE INFO:")
print("=" * 80)
for k, v in race_info.items():
    print(f"  {k}: {v}")

print("\n" + "=" * 80)
print(f"HORSES ({len(horses_df)} total):")
print("=" * 80)
if not horses_df.empty:
    display_cols = ['horse_number', 'horse_name', 'jockey', 'trainer', 'sexe_age', 'weight']
    available = [c for c in display_cols if c in horses_df.columns]
    for idx, row in horses_df.iterrows():
        print(f"  {int(row['horse_number']):2d}: {row['horse_name']:20s} | {row.get('jockey', 'N/A'):15s} | {row.get('trainer', 'N/A'):20s}")

print("\n" + "=" * 80)
print("PRONOSTICS:")
print("=" * 80)
for source, nums in pronostics.items():
    print(f"  {source}: {nums}")

print("\n" + "=" * 80)
print("CLASSEMENTS:")
print("=" * 80)
for cat, nums in classements.items():
    print(f"  {cat}: {nums}")

print("\n" + "=" * 80)
print("BEST OF WEEK:")
print("=" * 80)
print(json.dumps(best_week, indent=2, ensure_ascii=False))

print("\n✅ ULTIMATE TEST COMPLETE\n")
