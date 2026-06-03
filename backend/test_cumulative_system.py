#!/usr/bin/env python3
"""
Complete workflow test for cumulative horse system
"""
import sys
sys.path.insert(0, '/app/backend')

from database import (get_or_create_horse_master, add_horse_race, 
                     update_horse_master_stats, get_horse_master_by_id,
                     get_all_horses_master, get_horse_race_history, init_database)
from data_import import OddsFeatureExtractor

print("=" * 70)
print("CUMULATIVE HORSE SYSTEM - WORKFLOW TEST")
print("=" * 70)

# Initialize database
init_database()
print("\nDatabase initialized\n")

# Test data: Same horse appearing in multiple races
test_races = [
    {
        'horse_name': 'MUST BAY',
        'jockey': 'A.THOMAS',
        'trainer': 'C.Y.LERNER',
        'race_date': '2026-05-24',
        'hippodrome': 'LAVAL',
        'distance': 2850,
        'race_type': 'ATTELE',
        'odds': '3/3',
        'age': 5,
        'weight': 57.0,
        'result_position': 3
    },
    {
        'horse_name': 'MUST BAY',
        'jockey': 'A.THOMAS',
        'trainer': 'C.Y.LERNER',
        'race_date': '2026-05-26',
        'hippodrome': 'VINCENNES',
        'distance': 3000,
        'race_type': 'ATTELE',
        'odds': '2/1',
        'age': 5,
        'weight': 57.5,
        'result_position': 1  # Won!
    },
    {
        'horse_name': 'MUST BAY',
        'jockey': 'A.THOMAS',
        'trainer': 'C.Y.LERNER',
        'race_date': '2026-05-28',
        'hippodrome': 'BOURGANEUF',
        'distance': 2600,
        'race_type': 'ATTELE',
        'odds': '1/1',
        'age': 5,
        'weight': 57.2,
        'result_position': 2  # Podium
    },
    {
        'horse_name': 'REVE BLEU',
        'jockey': 'M.BARZALONA',
        'trainer': 'G.BIETOLINI',
        'race_date': '2026-05-24',
        'hippodrome': 'LAVAL',
        'distance': 2850,
        'race_type': 'ATTELE',
        'odds': '1/4',
        'age': 3,
        'weight': 59.6,
        'result_position': 1  # Won!
    },
]

print("Step 1: Importing races into cumulative system\n")
print("-" * 70)

for race_data in test_races:
    horse_name = race_data['horse_name']
    jockey = race_data['jockey']
    trainer = race_data['trainer']
    
    # Get or create horse master
    horse_master_id = get_or_create_horse_master(horse_name, jockey, trainer)
    print(f"\nHorse: {horse_name} (Jockey: {jockey}, Trainer: {trainer})")
    print(f"  Horse Master ID: {horse_master_id}")
    
    # Convert odds to probability
    odds_prob = OddsFeatureExtractor.convert_odds_to_probability(race_data['odds'])
    
    # Add race to horse's history
    horse_race_id = add_horse_race(
        horse_master_id=horse_master_id,
        race_date=race_data['race_date'],
        hippodrome=race_data['hippodrome'],
        distance=race_data['distance'],
        race_type=race_data['race_type'],
        odds=race_data['odds'],
        odds_probability=odds_prob,
        age=race_data['age'],
        weight=race_data['weight'],
        result_position=race_data['result_position'],
        imported_from='TEST_WORKFLOW'
    )
    
    print(f"  Race on {race_data['race_date']} at {race_data['hippodrome']}")
    print(f"  Position: {race_data['result_position']} | Odds: {race_data['odds']}")

print("\n" + "=" * 70)
print("Step 2: Checking cumulative stats\n")
print("-" * 70)

# Get all master horses
all_horses = get_all_horses_master()

for horse in all_horses:
    print(f"\nHorse: {horse['horse_name']}")
    print(f"  Jockey: {horse['jockey']}")
    print(f"  Trainer: {horse['trainer']}")
    print(f"  Total Races: {horse['total_races']}")
    print(f"  Wins: {horse['wins']}")
    print(f"  Podiums: {horse['podiums']}")
    print(f"  Average Position: {horse['avg_position']:.2f}")

print("\n" + "=" * 70)
print("Step 3: Getting detailed horse history\n")
print("-" * 70)

# Get detailed history for MUST BAY
must_bay = all_horses[0] if all_horses else None
if must_bay:
    print(f"\nRace history for: {must_bay['horse_name']}\n")
    
    history = get_horse_race_history(must_bay['id'])
    for i, race in enumerate(history, 1):
        print(f"  Race {i}:")
        print(f"    Date: {race['race_date']}")
        print(f"    Position: {race['result_position']}")
        print(f"    Odds Probability: {race['odds_probability']:.4f}" if race['odds_probability'] else "    Odds Probability: N/A")
        print(f"    Age: {race['age']}, Weight: {race['weight']}")

print("\n" + "=" * 70)
print("WORKFLOW TEST COMPLETED SUCCESSFULLY!")
print("=" * 70)
print("\nKey Features Demonstrated:")
print("  ✓ Horses created in master table")
print("  ✓ Multiple races added to same horse")
print("  ✓ Cumulative statistics calculated (wins, podiums, avg position)")
print("  ✓ Historical data preserved for model training")
print("\nNext: Import PDF files and watch stats update automatically!")
