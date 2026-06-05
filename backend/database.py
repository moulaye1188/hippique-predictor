import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = "/app/data/hippique.db"

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for race history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS races (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_date TEXT NOT NULL,
        hippodrome TEXT NOT NULL,
        distance INTEGER,
        race_type TEXT,
        conditions TEXT,
        num_competitors INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table for horse data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS horses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id INTEGER NOT NULL,
        horse_number INTEGER NOT NULL,
        horse_name TEXT NOT NULL,
        description TEXT,
        odds TEXT,
        odds_decimal REAL,
        position_result INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (race_id) REFERENCES races(id)
    )
    ''')
    
    # Table for predictions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id INTEGER NOT NULL,
        horse_id INTEGER NOT NULL,
        predicted_probability REAL NOT NULL,
        predicted_rank INTEGER,
        actual_rank INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (race_id) REFERENCES races(id),
        FOREIGN KEY (horse_id) REFERENCES horses(id)
    )
    ''')
    
    # Table for model training logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        epoch INTEGER,
        loss REAL,
        val_loss REAL,
        accuracy REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table for historical imported races data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historical_races (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_date TEXT,
        hippodrome TEXT,
        distance INTEGER,
        race_type TEXT,
        horse_number INTEGER,
        horse_name TEXT,
        description TEXT,
        odds TEXT,
        odds_decimal REAL,
        age INTEGER,
        wins INTEGER,
        podiums INTEGER,
        jockey TEXT,
        trainer TEXT,
        weight REAL,
        result_position INTEGER,
        data_source TEXT,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table for prediction feedback
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prediction_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id INTEGER,
        horse_id INTEGER,
        predicted_probability REAL,
        predicted_rank INTEGER,
        actual_result_position INTEGER,
        prediction_correct INTEGER,
        predicted_winner_rank INTEGER,
        feedback_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (race_id) REFERENCES races(id),
        FOREIGN KEY (horse_id) REFERENCES horses(id)
    )
    ''')
    
    # Table for model performance metrics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS model_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_predictions INTEGER,
        correct_predictions INTEGER,
        accuracy_percentage REAL,
        top3_accuracy_percentage REAL,
        avg_predicted_rank REAL,
        trend TEXT,
        data_quality_score REAL
    )
    ''')
    
    # Table for correlation analysis results
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS correlation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_name TEXT NOT NULL,
        correlation_value REAL,
        correlation_strength TEXT,
        p_value REAL,
        feature_rank INTEGER,
        analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(feature_name, analysis_date)
    )
    ''')
    
    # NEW: Master horse list (unique horses across all imports)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS horses_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_name TEXT NOT NULL,
        jockey TEXT,
        trainer TEXT,
        total_races INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        podiums INTEGER DEFAULT 0,
        avg_position REAL DEFAULT 0.0,
        last_age INTEGER,
        last_weight REAL,
        last_odds TEXT,
        last_odds_probability REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(horse_name, jockey, trainer)
    )
    ''')
    
    # NEW: Horse race history (each race + result for each horse)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS horse_races (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_master_id INTEGER NOT NULL,
        race_date TEXT,
        hippodrome TEXT,
        distance INTEGER,
        race_type TEXT,
        odds TEXT,
        odds_probability REAL,
        age INTEGER,
        weight REAL,
        result_position INTEGER,
        imported_from TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (horse_master_id) REFERENCES horses_master(id),
        UNIQUE(horse_master_id, race_date, hippodrome)
    )
    ''')
    
    # Add indexes for optimal query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_horses_race_id ON horses(race_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_race_id ON predictions(race_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_horse_id ON predictions(horse_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_horses_master_name ON horses_master(horse_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_horse_races_master_id ON horse_races(horse_master_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_horse_races_date ON horse_races(race_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_races_date ON historical_races(race_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_races_hippodrome ON historical_races(hippodrome)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_correlation_results_feature ON correlation_results(feature_name)')
    
    conn.commit()
    conn.close()

def save_race(race_date, hippodrome, distance=None, race_type=None, conditions=None, num_competitors=None):
    """Save race information and return race_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO races (race_date, hippodrome, distance, race_type, conditions, num_competitors)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (race_date, hippodrome, distance, race_type, conditions, num_competitors))
    
    conn.commit()
    race_id = cursor.lastrowid
    conn.close()
    return race_id

def save_horse(race_id, horse_number, horse_name, description, odds, odds_decimal):
    """Save horse data and return horse_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO horses (race_id, horse_number, horse_name, description, odds, odds_decimal)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (race_id, horse_number, horse_name, description, odds, odds_decimal))
    
    conn.commit()
    horse_id = cursor.lastrowid
    conn.close()
    return horse_id

def save_predictions(race_id, predictions_dict):
    """Save predictions for a race
    predictions_dict: {horse_id: probability, ...}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Sort by probability to get ranks
    sorted_predictions = sorted(predictions_dict.items(), key=lambda x: x[1], reverse=True)
    
    for rank, (horse_id, probability) in enumerate(sorted_predictions, 1):
        cursor.execute('''
        INSERT INTO predictions (race_id, horse_id, predicted_probability, predicted_rank)
        VALUES (?, ?, ?, ?)
        ''', (race_id, horse_id, probability, rank))
    
    conn.commit()
    conn.close()

def save_training_log(epoch, loss, val_loss, accuracy):
    """Save training metrics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO training_logs (epoch, loss, val_loss, accuracy)
    VALUES (?, ?, ?, ?)
    ''', (epoch, loss, val_loss, accuracy))
    
    conn.commit()
    conn.close()

def get_race_history(limit=100):
    """Get recent races from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, race_date, hippodrome, distance, num_competitors
    FROM races
    ORDER BY created_at DESC
    LIMIT ?
    ''', (limit,))
    
    races = cursor.fetchall()
    conn.close()
    return races

def get_race_horses(race_id):
    """Get all horses for a specific race"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, horse_number, horse_name, odds_decimal
    FROM horses
    WHERE race_id = ?
    ORDER BY horse_number
    ''', (race_id,))
    
    horses = cursor.fetchall()
    conn.close()
    return horses


def save_historical_race(race_data: dict) -> int:
    """Save historical race data from import"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO historical_races (
        race_date, hippodrome, distance, race_type, horse_number, horse_name,
        description, odds, odds_decimal, age, wins, podiums, jockey, trainer,
        weight, result_position, data_source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        race_data.get('race_date'),
        race_data.get('hippodrome'),
        race_data.get('distance'),
        race_data.get('race_type'),
        race_data.get('horse_number'),
        race_data.get('horse_name'),
        race_data.get('description'),
        race_data.get('odds'),
        race_data.get('odds_decimal'),
        race_data.get('age'),
        race_data.get('wins'),
        race_data.get('podiums'),
        race_data.get('jockey'),
        race_data.get('trainer'),
        race_data.get('weight'),
        race_data.get('result_position'),
        'import'
    ))
    
    conn.commit()
    race_id = cursor.lastrowid
    conn.close()
    return race_id


def save_prediction_feedback(race_id: int, horse_id: int, predicted_prob: float,
                            predicted_rank: int, actual_position: int = None) -> int:
    """Save prediction with feedback"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Determine if prediction was correct
    prediction_correct = 1 if actual_position == 1 else 0
    
    # Determine predicted winner rank
    predicted_winner_rank = predicted_rank
    
    cursor.execute('''
    INSERT INTO prediction_feedback (
        race_id, horse_id, predicted_probability, predicted_rank,
        actual_result_position, prediction_correct, predicted_winner_rank
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        race_id, horse_id, predicted_prob, predicted_rank,
        actual_position, prediction_correct, predicted_winner_rank
    ))
    
    conn.commit()
    feedback_id = cursor.lastrowid
    conn.close()
    return feedback_id


def get_all_feedback() -> list:
    """Get all prediction feedback for analysis"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM prediction_feedback ORDER BY created_at DESC')
    feedback = cursor.fetchall()
    conn.close()
    return feedback


def save_model_metrics(total_pred: int, correct_pred: int, accuracy: float,
                      top3_accuracy: float, avg_rank: float, trend: str,
                      quality_score: float = None):
    """Save model performance metrics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO model_metrics (
        total_predictions, correct_predictions, accuracy_percentage,
        top3_accuracy_percentage, avg_predicted_rank, trend, data_quality_score
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (total_pred, correct_pred, accuracy, top3_accuracy, avg_rank, trend, quality_score))
    
    conn.commit()
    conn.close()


def get_model_metrics_history(limit: int = 50) -> list:
    """Get historical model metrics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT metric_date, accuracy_percentage, top3_accuracy_percentage, trend
    FROM model_metrics
    ORDER BY metric_date DESC
    LIMIT ?
    ''', (limit,))
    
    metrics = cursor.fetchall()
    conn.close()
    return metrics


def save_correlation_result(feature_name: str, correlation: float, strength: str,
                           p_value: float = None, rank: int = None):
    """Save correlation analysis result"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO correlation_results (
        feature_name, correlation_value, correlation_strength, p_value, feature_rank
    ) VALUES (?, ?, ?, ?, ?)
    ''', (feature_name, correlation, strength, p_value, rank))
    
    conn.commit()
    conn.close()


def get_correlation_results() -> list:
    """Get latest correlation analysis results"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT feature_name, correlation_value, correlation_strength, feature_rank
    FROM correlation_results
    ORDER BY feature_rank ASC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results


def get_historical_races_count() -> int:
    """Get count of imported historical races"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM historical_races')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_historical_races_for_training(limit: int = 1000):
    """Get historical races for model training"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT race_date, hippodrome, distance, horse_number, horse_name, odds,
           odds_decimal, age, wins, podiums, result_position
    FROM historical_races
    WHERE result_position IS NOT NULL
    ORDER BY race_date DESC
    LIMIT ?
    ''', (limit,))
    
    races = cursor.fetchall()
    conn.close()
    return races


# NEW FUNCTIONS FOR CUMULATIVE HORSE DATA

def get_or_create_horse_master(horse_name: str, jockey: str = None, trainer: str = None) -> int:
    """Get existing horse or create new one. Returns horse_master_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Normalize inputs
    horse_name = horse_name.strip() if horse_name else ""
    jockey = jockey.strip() if jockey else None
    trainer = trainer.strip() if trainer else None
    
    # Try to find existing horse
    cursor.execute('''
    SELECT id FROM horses_master
    WHERE horse_name = ? AND (jockey IS NULL OR jockey = ?) AND (trainer IS NULL OR trainer = ?)
    LIMIT 1
    ''', (horse_name, jockey, trainer))
    
    result = cursor.fetchone()
    if result:
        horse_id = result[0]
        conn.close()
        return horse_id
    
    # Create new horse
    cursor.execute('''
    INSERT INTO horses_master (horse_name, jockey, trainer)
    VALUES (?, ?, ?)
    ''', (horse_name, jockey, trainer))
    
    conn.commit()
    horse_id = cursor.lastrowid
    conn.close()
    return horse_id


def add_horse_race(horse_master_id: int, race_date: str, hippodrome: str, distance: int = None,
                   race_type: str = None, odds: str = None, odds_probability: float = None,
                   age: int = None, weight: float = None, result_position: int = None,
                   imported_from: str = None) -> int:
    """Add a race result to a horse's history. Returns horse_race_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO horse_races (
            horse_master_id, race_date, hippodrome, distance, race_type,
            odds, odds_probability, age, weight, result_position, imported_from
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            horse_master_id, race_date, hippodrome, distance, race_type,
            odds, odds_probability, age, weight, result_position, imported_from
        ))
        
        conn.commit()
        horse_race_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Race already exists for this horse on this date
        horse_race_id = None
    
    conn.close()
    
    # Update horse_master stats
    if horse_race_id:
        update_horse_master_stats(horse_master_id)
    
    return horse_race_id


def update_horse_master_stats(horse_master_id: int):
    """Recalculate and update horse master statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all races for this horse
    cursor.execute('''
    SELECT result_position, age, weight, odds, odds_probability
    FROM horse_races
    WHERE horse_master_id = ? AND result_position IS NOT NULL
    ORDER BY created_at DESC
    ''', (horse_master_id,))
    
    races = cursor.fetchall()
    
    if races:
        total_races = len(races)
        wins = sum(1 for r in races if r[0] == 1)
        podiums = sum(1 for r in races if r[0] <= 3)
        avg_position = sum(r[0] for r in races) / total_races if total_races > 0 else 0
        
        # Get latest values
        latest_race = races[0]
        last_age = latest_race[1]
        last_weight = latest_race[2]
        last_odds = latest_race[3]
        last_odds_probability = latest_race[4]
    else:
        total_races = 0
        wins = 0
        podiums = 0
        avg_position = 0.0
        last_age = None
        last_weight = None
        last_odds = None
        last_odds_probability = None
    
    # Update master record
    cursor.execute('''
    UPDATE horses_master
    SET total_races = ?, wins = ?, podiums = ?, avg_position = ?,
        last_age = ?, last_weight = ?, last_odds = ?, last_odds_probability = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (
        total_races, wins, podiums, avg_position,
        last_age, last_weight, last_odds, last_odds_probability,
        horse_master_id
    ))
    
    conn.commit()
    conn.close()


def get_horse_master_by_id(horse_master_id: int) -> dict:
    """Get horse master record with all stats"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, horse_name, jockey, trainer, total_races, wins, podiums, avg_position,
           last_age, last_weight, last_odds, last_odds_probability
    FROM horses_master
    WHERE id = ?
    ''', (horse_master_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'horse_name': result[1],
            'jockey': result[2],
            'trainer': result[3],
            'total_races': result[4],
            'wins': result[5],
            'podiums': result[6],
            'avg_position': result[7],
            'last_age': result[8],
            'last_weight': result[9],
            'last_odds': result[10],
            'last_odds_probability': result[11]
        }
    return None


def get_all_horses_master(limit: int = 1000) -> list:
    """Get all master horses with stats"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, horse_name, jockey, trainer, total_races, wins, podiums, avg_position
    FROM horses_master
    ORDER BY total_races DESC, wins DESC
    LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': r[0],
            'horse_name': r[1],
            'jockey': r[2],
            'trainer': r[3],
            'total_races': r[4],
            'wins': r[5],
            'podiums': r[6],
            'avg_position': r[7]
        }
        for r in results
    ]


def get_horse_race_history(horse_master_id: int, limit: int = 50) -> list:
    """Get race history for a specific horse"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT race_date, hippodrome, distance, odds_probability, age, weight,
           result_position
    FROM horse_races
    WHERE horse_master_id = ?
    ORDER BY race_date DESC
    LIMIT ?
    ''', (horse_master_id, limit))
    
    races = cursor.fetchall()
    conn.close()
    
    return [
        {
            'race_date': r[0],
            'hippodrome': r[1],
            'distance': r[2],
            'odds_probability': r[3],
            'age': r[4],
            'weight': r[5],
            'result_position': r[6]
        }
        for r in races
    ]
