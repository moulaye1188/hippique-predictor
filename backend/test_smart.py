#!/usr/bin/env python3
"""Test SMART parser with table extraction"""
import json
import pandas as pd
from pdf_parser_smart import parse_pdf_smart

print("Testing SMART PDF Parser...\n")

race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart('/app/backend/test_full.pdf')

print("=" * 80)
print("RACE INFO:")
print("=" * 80)
for k, v in race_info.items():
    print(f"  {k}: {v}")

print("\n" + "=" * 80)
print(f"HORSES ({len(horses_df)} total):")
print("=" * 80)
if not horses_df.empty:
    print(f"\nAll horses:")
    for idx, row in horses_df.iterrows():
        num = int(row['horse_number']) if pd.notna(row['horse_number']) else 0
        name = row.get('horse_name', 'N/A')
        jockey = row.get('jockey', 'N/A')
        trainer = row.get('trainer', 'N/A')
        weight = row.get('weight', 'N/A')
        print(f"  {num:2d}: {name:20s} | {jockey:15s} | {trainer:25s} | {str(weight):8s}")

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
print("✅ SMART TEST COMPLETE\n")
