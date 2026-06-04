#!/usr/bin/env python3
"""Test the FINAL PDF parser"""
from pdf_parser_final import parse_pdf_final
import json

print("Testing PDF Parser FINAL...\n")

race_info, horses_df, pronostics, classements, best_week = parse_pdf_final('/app/backend/test_full.pdf')

print("=" * 80)
print("RACE INFO:")
print("=" * 80)
print(json.dumps(race_info, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print(f"HORSES ({len(horses_df)} total):")
print("=" * 80)
if not horses_df.empty:
    print(f"Columns: {list(horses_df.columns)}\n")
    display_cols = ['horse_number', 'horse_name', 'jockey', 'trainer', 'sexe_age', 'weight', 'perf', 'odds_paris_turf', 'odds_tierce_magazine']
    available_cols = [c for c in display_cols if c in horses_df.columns]
    print(horses_df[available_cols].head(16).to_string())
else:
    print("❌ No horses extracted!")

print("\n" + "=" * 80)
print("PRONOSTICS (External sources):")
print("=" * 80)
if pronostics:
    for source, numbers in pronostics.items():
        print(f"  {source}: {numbers}")
else:
    print("❌ No pronostics extracted!")

print("\n" + "=" * 80)
print("CLASSEMENTS:")
print("=" * 80)
if classements:
    for category, numbers in classements.items():
        print(f"  {category}: {numbers}")
else:
    print("❌ No classements extracted!")

print("\n" + "=" * 80)
print("BEST OF WEEK:")
print("=" * 80)
if best_week:
    print(json.dumps(best_week, indent=2, ensure_ascii=False))
else:
    print("❌ No best_week data!")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
