#!/usr/bin/env python3
"""Retrain model with all races from database"""
import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.model_v2 import UpgradedHippiqueModel
from backend.database import Database
from backend.config import DB_PATH

def load_races_from_db():
    """Load all races from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("📊 Loading races from database...\n")
    
    # Get all races
    cursor.execute("""
        SELECT id, hippodrome, date, race_number, race_name, race_type_bet 
        FROM races 
        ORDER BY date
    """)
    
    races = cursor.fetchall()
    print(f"✓ Found {len(races)} races in database\n")
    
    races_data = []
    
    for race_id, hippodrome, race_date, race_number, race_name, race_type in races:
        try:
            # Load horses for this race
            cursor.execute("""
                SELECT 
                    horse_number, horse_name, jockey, trainer, 
                    corde, weight, perf, gains_historical,
                    odds_paris_turf, odds_tierce, 
                    sexe_age, result_position
                FROM horses
                WHERE race_id = ?
                ORDER BY horse_number
            """, (race_id,))
            
            horses_rows = cursor.fetchall()
            
            if not horses_rows:
                continue
            
            # Convert to DataFrame
            horses_df = pd.DataFrame(horses_rows, columns=[
                'horse_number', 'horse_name', 'jockey', 'trainer',
                'corde', 'weight', 'perf', 'gains_historical',
                'odds_paris_turf', 'odds_tierce',
                'sexe_age', 'result_position'
            ])
            
            # Convert types
            horses_df['horse_number'] = horses_df['horse_number'].astype(int)
            horses_df['weight'] = pd.to_numeric(horses_df['weight'], errors='coerce')
            horses_df['gains_historical'] = pd.to_numeric(horses_df['gains_historical'], errors='coerce')
            horses_df['result_position'] = pd.to_numeric(horses_df['result_position'], errors='coerce')
            
            # Build race_info dict
            race_info = {
                'hippodrome': hippodrome,
                'race_date': race_date,
                'date': race_date,
                'race_number': race_number,
                'race_name': race_name,
                'race_type': race_type,
                'latitude': None,
                'longitude': None
            }
            
            races_data.append({
                'race_info': race_info,
                'horses': horses_df,
                'classements': {},  # Not needed for training
                'pronostics': {},
                'best_week': {}
            })
            
            print(f"  Race {len(races_data):2d}: {hippodrome:15s} | {race_date} | {len(horses_df)} horses | Winners: {int(horses_df['result_position'].eq(1).sum())}")
            
        except Exception as e:
            print(f"  ❌ Error loading race {race_id}: {e}")
            continue
    
    conn.close()
    
    print(f"\n✓ Successfully loaded {len(races_data)} races\n")
    return races_data


def main():
    """Main retraining function"""
    print("=" * 80)
    print("🐴 MODEL RETRAINING SCRIPT")
    print("=" * 80)
    print()
    
    # Load races
    races_data = load_races_from_db()
    
    if not races_data:
        print("❌ No races to train on!")
        return False
    
    # Initialize model
    print("🔧 Initializing model...\n")
    model = UpgradedHippiqueModel()
    
    # Train with different model types
    models_to_train = ['random_forest']  # Can add 'gradient_boosting' if desired
    
    for model_type in models_to_train:
        print(f"\n{'='*80}")
        print(f"Training {model_type.upper()} model")
        print(f"{'='*80}\n")
        
        success = model.train(races_data, model_type=model_type)
        
        if not success:
            print(f"❌ Training failed for {model_type}")
            return False
        
        # Save model
        if model.save():
            print(f"✅ {model_type} model trained and saved successfully!")
        else:
            print(f"❌ Failed to save {model_type} model")
            return False
    
    print("\n" + "=" * 80)
    print("✅ RETRAINING COMPLETE")
    print("=" * 80)
    print(f"\nModel files saved to:")
    print(f"  - Models: /app/models/")
    print(f"\nYou can now test the model with:")
    print(f"  python backend/app.py")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
