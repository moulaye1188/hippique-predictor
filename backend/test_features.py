#!/usr/bin/env python3
"""Test feature engineering"""
import sys
sys.path.insert(0, '/app/backend')

from pdf_parser_smart import parse_pdf_smart
from feature_engineering import RaceFeatureEngineer

print("Testing Feature Engineering...\n")

# Parse PDF
race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart('/app/backend/test_full.pdf')

# Engineer features
engineer = RaceFeatureEngineer()
features_df = engineer.engineer_race_features(race_info, horses_df, classements, pronostics, best_week)

print("=" * 80)
print("FEATURES ENGINEERED")
print("=" * 80)
print(f"\nColumns: {list(features_df.columns)}\n")

# Show features for first 5 horses
display_cols = ['horse_number', 'horse_name', 'perf_score', 'odds_consensus', 
                'classement_score', 'pronostic_score', 'expert_score']
available = [c for c in display_cols if c in features_df.columns]

print("First 5 horses with engineered features:")
print(features_df[available].head().to_string())

print("\n" + "=" * 80)
print("Feature Statistics:")
print("=" * 80)

feature_cols = engineer.get_feature_columns()
for col in feature_cols:
    if col in features_df.columns:
        mean_val = features_df[col].mean()
        std_val = features_df[col].std()
        print(f"{col:25s}: mean={mean_val:.3f}, std={std_val:.3f}")

print("\n✅ Feature Engineering Test Complete!\n")
