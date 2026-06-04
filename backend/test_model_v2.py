#!/usr/bin/env python3
"""Test upgraded model training and prediction"""
import sys
sys.path.insert(0, '/app/backend')

from pdf_parser_smart import parse_pdf_smart
from model_v2 import UpgradedHippiqueModel

print("Testing Upgraded Model V2...\n")

# Parse PDF
race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart('/app/backend/test_full.pdf')

# Prepare race data (we have only 1 race, so use it multiple times for demo)
races_data = []
for i in range(3):  # Use same race 3 times
    races_data.append({
        'race_info': race_info,
        'horses': horses_df.copy(),
        'classements': classements,
        'pronostics': pronostics,
        'best_week': best_week
    })

# Train model
model = UpgradedHippiqueModel()
model.train(races_data, model_type='random_forest')

# Save model
model.save()

# Make predictions on test race
print("=" * 80)
print("PREDICTIONS ON TEST RACE")
print("=" * 80 + "\n")

predictions = model.predict_on_race(race_info, horses_df, classements, pronostics, best_week)

# Display top predictions
display_cols = ['predicted_rank', 'horse_number', 'horse_name', 'predicted_probability', 'expert_score']
print(predictions[display_cols].head(10).to_string())

print("\n✅ Model Test Complete!\n")
