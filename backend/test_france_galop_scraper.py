"""Test script - France-Galop Scraper"""
import sys
sys.path.insert(0, '/app/backend') if '/' in __file__ else None

from france_galop_scraper import FranceGalopScraper, ScratchListFilter
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)

print("=" * 70)
print("FRANCE-GALOP SCRAPER TEST")
print("=" * 70)

# Test 1: Scrape today's races
print("\n1️⃣  Test scratch-list for today:")
today = datetime.now().strftime('%Y-%m-%d')
print(f"   Date: {today}")

result = FranceGalopScraper.get_scratch_list(date=today)
print(f"   ✅ Success: {result['success']}")
print(f"   Hippodrome: {result['hippodrome']}")
print(f"   Error: {result['error']}")
print(f"   Races with scratches: {len(result['scratches'])}")

if result['scratches']:
    print(f"   Scratches detail:")
    for race_num, horses in result['scratches'].items():
        print(f"      Race {race_num}: {horses}")

if result['jockey_changes']:
    print(f"   Jockey changes:")
    for race_num, changes in result['jockey_changes'].items():
        print(f"      Race {race_num}: {changes}")

# Test 2: Filter horses
print("\n2️⃣  Test horse filtering:")
test_horses = pd.DataFrame({
    'horse_number': [1, 2, 3, 4, 5, 6],
    'horse_name': ['Cheval A', 'Cheval B', 'Cheval C', 'Cheval D', 'Cheval E', 'Cheval F'],
    'jockey': ['Jockey 1', 'Jockey 2', 'Jockey 3', 'Jockey 4', 'Jockey 5', 'Jockey 6'],
})

print(f"   Before: {len(test_horses)} horses")
print(f"   Test scratch-list (simulated): Race 1: [2, 4]")

# Create simulated scratch-list
test_scratch = {
    'date': today,
    'hippodrome': 'TEST',
    'scratches': {'1': [2, 4]},
    'jockey_changes': {'1': {3: 'New Jockey 3'}},
    'success': True,
    'error': None
}

filtered_horses, excluded = ScratchListFilter.filter_horses(test_horses, test_scratch)
print(f"   After filtering: {len(filtered_horses)} horses")
print(f"   Excluded: {excluded}")

# Test 3: Apply jockey changes
print("\n3️⃣  Test jockey changes:")
print(f"   Before jockey change:")
print(f"      Horse 3: {test_horses[test_horses['horse_number'] == 3]['jockey'].values[0]}")

updated_horses = ScratchListFilter.apply_jockey_changes(filtered_horses, test_scratch['jockey_changes']['1'])
print(f"   After jockey change:")
print(f"      Horse 3: {updated_horses[updated_horses['horse_number'] == 3]['jockey'].values[0]}")

# Test 4: Specific hippodrome
print("\n4️⃣  Test specific hippodrome (VINCENNES):")
result_vincennes = FranceGalopScraper.get_scratch_list(date=today, hippodrome='VINCENNES')
print(f"   Success: {result_vincennes['success']}")
print(f"   Hippodrome: {result_vincennes['hippodrome']}")
if result_vincennes['scratches']:
    print(f"   Scratches: {result_vincennes['scratches']}")

print("\n" + "=" * 70)
print("✅ FRANCE-GALOP SCRAPER TEST COMPLETE")
print("=" * 70)
