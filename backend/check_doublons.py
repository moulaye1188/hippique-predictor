#!/usr/bin/env python3
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Compter total
cursor.execute("SELECT COUNT(*) FROM horses")
total = cursor.fetchone()[0]
print(f"Total chevaux: {total}")

# Doublons
cursor.execute("""
SELECT race_id, horse_number, horse_name, COUNT(*) as count
FROM horses
GROUP BY race_id, horse_number
HAVING COUNT(*) > 1
""")

doublons = cursor.fetchall()
if doublons:
    print(f"❌ {len(doublons)} doublons trouvés:")
    for race_id, horse_num, name, count in doublons:
        print(f"  Race {race_id} - #{horse_num} {name}: {count}x")
else:
    print("✅ Pas de doublons - Chaque cheval unique!")

# Stats par course
cursor.execute("SELECT race_id, COUNT(*) FROM horses GROUP BY race_id")
races = cursor.fetchall()
print(f"\nCourses chargées:")
for race_id, count in races:
    print(f"  Race {race_id}: {count} chevaux")

conn.close()
