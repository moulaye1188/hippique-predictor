"""Database schema v2 - Add enriched PDF data columns"""
import sqlite3
from pathlib import Path

DB_PATH = "/app/data/hippique.db"

def migrate_to_schema_v2():
    """Add new columns for enriched PDF data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Alter races table - add new race info
        cursor.execute("ALTER TABLE races ADD COLUMN race_name TEXT")
        print("✓ Added race_name to races")
    except sqlite3.OperationalError:
        print("✗ race_name already exists in races")
    
    try:
        cursor.execute("ALTER TABLE races ADD COLUMN race_number INTEGER")
        print("✓ Added race_number to races")
    except sqlite3.OperationalError:
        print("✗ race_number already exists in races")
    
    try:
        cursor.execute("ALTER TABLE races ADD COLUMN race_type_bet TEXT")
        print("✓ Added race_type_bet to races")
    except sqlite3.OperationalError:
        print("✗ race_type_bet already exists in races")
    
    try:
        cursor.execute("ALTER TABLE races ADD COLUMN prize_money_eur TEXT")
        print("✓ Added prize_money_eur to races")
    except sqlite3.OperationalError:
        print("✗ prize_money_eur already exists in races")
    
    try:
        cursor.execute("ALTER TABLE races ADD COLUMN prize_money_fcfa TEXT")
        print("✓ Added prize_money_fcfa to races")
    except sqlite3.OperationalError:
        print("✗ prize_money_fcfa already exists in races")
    
    try:
        cursor.execute("ALTER TABLE races ADD COLUMN race_time TEXT")
        print("✓ Added race_time to races")
    except sqlite3.OperationalError:
        print("✗ race_time already exists in races")
    
    # Alter horses table - add enriched data
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN jockey TEXT")
        print("✓ Added jockey to horses")
    except sqlite3.OperationalError:
        print("✗ jockey already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN trainer TEXT")
        print("✓ Added trainer to horses")
    except sqlite3.OperationalError:
        print("✗ trainer already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN owner TEXT")
        print("✓ Added owner to horses")
    except sqlite3.OperationalError:
        print("✗ owner already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN sexe_age TEXT")
        print("✓ Added sexe_age to horses")
    except sqlite3.OperationalError:
        print("✗ sexe_age already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN corde INTEGER")
        print("✓ Added corde to horses")
    except sqlite3.OperationalError:
        print("✗ corde already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN weight REAL")
        print("✓ Added weight to horses")
    except sqlite3.OperationalError:
        print("✗ weight already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN perf TEXT")
        print("✓ Added perf to horses")
    except sqlite3.OperationalError:
        print("✗ perf already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN gains_historical INTEGER")
        print("✓ Added gains_historical to horses")
    except sqlite3.OperationalError:
        print("✗ gains_historical already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN odds_paris_turf TEXT")
        print("✓ Added odds_paris_turf to horses")
    except sqlite3.OperationalError:
        print("✗ odds_paris_turf already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN odds_tierce_magazine TEXT")
        print("✓ Added odds_tierce_magazine to horses")
    except sqlite3.OperationalError:
        print("✗ odds_tierce_magazine already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN odds_probability_paris REAL")
        print("✓ Added odds_probability_paris to horses")
    except sqlite3.OperationalError:
        print("✗ odds_probability_paris already exists in horses")
    
    try:
        cursor.execute("ALTER TABLE horses ADD COLUMN odds_probability_tierce REAL")
        print("✓ Added odds_probability_tierce to horses")
    except sqlite3.OperationalError:
        print("✗ odds_probability_tierce already exists in horses")
    
    # NEW TABLES FOR PRONOSTICS AND RANKINGS
    
    # Table for pronostics from external sources
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS race_pronostics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id INTEGER NOT NULL,
        source TEXT NOT NULL,
        horse_numbers TEXT NOT NULL,
        rank_1 INTEGER,
        rank_2 INTEGER,
        rank_3 INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (race_id) REFERENCES races(id),
        UNIQUE(race_id, source)
    )
    ''')
    print("✓ Created race_pronostics table")
    
    # Table for race classements/rankings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS race_classements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        horse_numbers TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (race_id) REFERENCES races(id),
        UNIQUE(race_id, category)
    )
    ''')
    print("✓ Created race_classements table")
    
    # Table for best of week
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS best_of_week (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_date TEXT,
        trainers_in_form TEXT,
        jockeys_in_form TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✓ Created best_of_week table")
    
    # Update horses_master with enriched fields
    try:
        cursor.execute("ALTER TABLE horses_master ADD COLUMN owner TEXT")
        print("✓ Added owner to horses_master")
    except sqlite3.OperationalError:
        print("✗ owner already exists in horses_master")
    
    try:
        cursor.execute("ALTER TABLE horses_master ADD COLUMN sexe_age TEXT")
        print("✓ Added sexe_age to horses_master")
    except sqlite3.OperationalError:
        print("✗ sexe_age already exists in horses_master")
    
    try:
        cursor.execute("ALTER TABLE horses_master ADD COLUMN perf TEXT")
        print("✓ Added perf to horses_master")
    except sqlite3.OperationalError:
        print("✗ perf already exists in horses_master")
    
    # Update horse_races with enriched fields
    try:
        cursor.execute("ALTER TABLE horse_races ADD COLUMN perf TEXT")
        print("✓ Added perf to horse_races")
    except sqlite3.OperationalError:
        print("✗ perf already exists in horse_races")
    
    try:
        cursor.execute("ALTER TABLE horse_races ADD COLUMN corde INTEGER")
        print("✓ Added corde to horse_races")
    except sqlite3.OperationalError:
        print("✗ corde already exists in horse_races")
    
    try:
        cursor.execute("ALTER TABLE horse_races ADD COLUMN owner TEXT")
        print("✓ Added owner to horse_races")
    except sqlite3.OperationalError:
        print("✗ owner already exists in horse_races")
    
    try:
        cursor.execute("ALTER TABLE horse_races ADD COLUMN sexe_age TEXT")
        print("✓ Added sexe_age to horse_races")
    except sqlite3.OperationalError:
        print("✗ sexe_age already exists in horse_races")
    
    try:
        cursor.execute("ALTER TABLE horse_races ADD COLUMN odds_paris_turf TEXT")
        print("✓ Added odds_paris_turf to horse_races")
    except sqlite3.OperationalError:
        print("✗ odds_paris_turf already exists in horse_races")
    
    try:
        cursor.execute("ALTER TABLE horse_races ADD COLUMN odds_tierce_magazine TEXT")
        print("✓ Added odds_tierce_magazine to horse_races")
    except sqlite3.OperationalError:
        print("✗ odds_tierce_magazine already exists in horse_races")
    
    try:
        cursor.execute("ALTER TABLE horse_races ADD COLUMN gains_historical INTEGER")
        print("✓ Added gains_historical to horse_races")
    except sqlite3.OperationalError:
        print("✗ gains_historical already exists in horse_races")
    
    conn.commit()
    conn.close()
    print("\n✅ Migration to schema v2 complete!")


# NEW FUNCTIONS FOR SAVING ENRICHED DATA

def save_race_enriched(race_info: dict) -> int:
    """Save race with all enriched data. Returns race_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO races (
        race_date, hippodrome, distance, race_type, race_name, race_number,
        race_type_bet, prize_money_eur, prize_money_fcfa, race_time, num_competitors
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        race_info.get('race_date'),
        race_info.get('hippodrome'),
        race_info.get('distance'),
        race_info.get('race_type'),
        race_info.get('race_name'),
        race_info.get('race_number'),
        race_info.get('race_type_bet'),
        race_info.get('prize_money_eur'),
        race_info.get('prize_money_fcfa'),
        race_info.get('race_time'),
        race_info.get('num_competitors')
    ))
    
    conn.commit()
    race_id = cursor.lastrowid
    conn.close()
    return race_id


def save_horse_enriched(race_id: int, horse_data: dict) -> int:
    """Save horse with all enriched data. Returns horse_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO horses (
        race_id, horse_number, horse_name, jockey, trainer, owner,
        sexe_age, corde, weight, perf, gains_historical,
        odds, odds_paris_turf, odds_tierce_magazine,
        odds_decimal
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        race_id,
        horse_data.get('horse_number'),
        horse_data.get('horse_name'),
        horse_data.get('jockey'),
        horse_data.get('trainer'),
        horse_data.get('owner'),
        horse_data.get('sexe_age'),
        horse_data.get('corde'),
        horse_data.get('weight'),
        horse_data.get('perf'),
        horse_data.get('gains_historical'),
        horse_data.get('odds'),  # Keeping for backward compatibility
        horse_data.get('odds_paris_turf'),
        horse_data.get('odds_tierce_magazine'),
        horse_data.get('odds_decimal')  # Will compute from odds if needed
    ))
    
    conn.commit()
    horse_id = cursor.lastrowid
    conn.close()
    return horse_id


def save_race_pronostics(race_id: int, pronostics: dict):
    """Save pronostics from external sources"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for source, horse_numbers in pronostics.items():
        # Store as comma-separated string
        horse_str = ','.join(map(str, horse_numbers))
        
        # Extract top 3
        rank_1 = horse_numbers[0] if len(horse_numbers) > 0 else None
        rank_2 = horse_numbers[1] if len(horse_numbers) > 1 else None
        rank_3 = horse_numbers[2] if len(horse_numbers) > 2 else None
        
        cursor.execute('''
        INSERT OR REPLACE INTO race_pronostics (race_id, source, horse_numbers, rank_1, rank_2, rank_3)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (race_id, source, horse_str, rank_1, rank_2, rank_3))
    
    conn.commit()
    conn.close()


def save_race_classements(race_id: int, classements: dict):
    """Save classements/rankings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for category, horse_numbers in classements.items():
        horse_str = ','.join(map(str, horse_numbers))
        
        cursor.execute('''
        INSERT OR REPLACE INTO race_classements (race_id, category, horse_numbers)
        VALUES (?, ?, ?)
        ''', (race_id, category, horse_str))
    
    conn.commit()
    conn.close()


def save_race_arrivals(race_id: int, arrivals: dict, horses_df=None) -> bool:
    """
    Save race arrivals (results) to database
    arrivals should be {'quartet': [7, 11, 2, 15], '1st': 7, '2nd': 11, '3rd': 2, '4th': 15}
    """
    if not arrivals or 'quartet' not in arrivals:
        print("⚠️  No valid arrivals data to save")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        quartet = arrivals.get('quartet', [])
        
        # Update each horse with their position
        for position, horse_number in enumerate(quartet, 1):
            cursor.execute('''
            UPDATE horses 
            SET position_result = ? 
            WHERE race_id = ? AND horse_number = ?
            ''', (position, race_id, horse_number))
        
        conn.commit()
        print(f"✅ Race {race_id} arrivals saved: {quartet}")
        return True
    
    except Exception as e:
        print(f"❌ Error saving race arrivals: {e}")
        return False
    finally:
        conn.close()


def get_race_with_enriched_data(race_id: int) -> dict:
    """Get complete race data with all enriched fields"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get race info
    cursor.execute('SELECT * FROM races WHERE id = ?', (race_id,))
    race = dict(cursor.fetchone()) if cursor.fetchone() else {}
    cursor.execute('SELECT * FROM races WHERE id = ?', (race_id,))
    race = dict(cursor.fetchone()) if cursor.fetchone() else {}
    
    # Get all horses
    cursor.execute('SELECT * FROM horses WHERE race_id = ? ORDER BY horse_number', (race_id,))
    horses = [dict(row) for row in cursor.fetchall()]
    
    # Get pronostics
    cursor.execute('SELECT source, horse_numbers FROM race_pronostics WHERE race_id = ?', (race_id,))
    pronostics = {row[0]: [int(x) for x in row[1].split(',')] for row in cursor.fetchall()}
    
    # Get classements
    cursor.execute('SELECT category, horse_numbers FROM race_classements WHERE race_id = ?', (race_id,))
    classements = {row[0]: [int(x) for x in row[1].split(',')] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        'race': race,
        'horses': horses,
        'pronostics': pronostics,
        'classements': classements
    }
