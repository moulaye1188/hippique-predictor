#!/usr/bin/env python3
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Chercher chevaux avec même nom (duplicates par nom)
cursor.execute("""
SELECT horse_name, COUNT(*) as count, GROUP_CONCAT(race_id) as races
FROM horses
GROUP BY horse_name
HAVING COUNT(*) > 1
ORDER BY count DESC
""")

homonymes = cursor.fetchall()
if homonymes:
    print(f"⚠️ {len(homonymes)} noms de chevaux qui reviennent plusieurs fois:\n")
    for name, count, races in homonymes:
        race_list = races.split(',')
        print(f"  '{name}': {count}x (Courses: {races})")
else:
    print("✅ Pas d'homonymes - Chaque nom unique!")

# Stats
cursor.execute("SELECT COUNT(DISTINCT horse_name) FROM horses")
unique_names = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM horses")
total = cursor.fetchone()[0]

print(f"\nStats:")
print(f"  Total chevaux: {total}")
print(f"  Noms uniques: {unique_names}")
print(f"  Doublons: {total - unique_names}")

conn.close()
