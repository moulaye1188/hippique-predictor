"""Updated Flask routes - Integrate new frontend + Model V2"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import json
import numpy as np
import pandas as pd

# Import config
from config import STATIC_FOLDER, DB_PATH, MODEL_PATH, SCALER_PATH

from pdf_parser_smart import parse_pdf_smart
from database_schema_v2 import save_race_enriched, save_horse_enriched, save_race_pronostics, save_race_classements, save_race_arrivals
from database import get_or_create_horse_master, add_horse_race, get_all_horses_master
from dashboard_stats import get_dashboard_stats
from model_v2 import UpgradedHippiqueModel

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')
CORS(app)

# Clean JSON encoder - handles NaN and NaT
def clean_for_json(obj):
    """Recursively clean object for JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, (float, np.floating)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif pd.isna(obj):
        return None
    return obj

# Load model
model = UpgradedHippiqueModel()
try:
    model.load()
    print("✓ Model V2 loaded successfully")
except FileNotFoundError as e:
    print(f"⚠ Model V2 not found ({e})")
    print("Predictions will use expert scores only")
except Exception as e:
    print(f"⚠ Error loading model: {e}")
    print("Predictions will use expert scores only")


# Serve new frontend
@app.route('/')
def index():
    """Serve new frontend"""
    return send_from_directory(STATIC_FOLDER, 'index.html')


@app.route('/styles.css')
def styles():
    return send_from_directory(STATIC_FOLDER, 'style.css')


@app.route('/script.js')
def script():
    return send_from_directory(STATIC_FOLDER, 'script.js')


# API Routes

@app.route('/api/load-race-from-pdf', methods=['POST'])
def load_race_from_pdf_v2():
    """Load race from PDF, parse, save to DB, and predict"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            file.save(tmp.name)
            temp_path = tmp.name
        
        try:
            # Parse PDF (now includes arrivals/results)
            race_info, horses_df, pronostics, classements, best_week, arrivals = parse_pdf_smart(temp_path)
            
            if horses_df.empty:
                return jsonify({'error': 'Failed to extract horses from PDF'}), 400
            
            # Save to DB
            race_id = save_race_enriched(race_info)
            
            horses_saved = 0
            for idx, row in horses_df.iterrows():
                save_horse_enriched(race_id, row.to_dict())
                horses_saved += 1
            
            # Save pronostics and classements
            if pronostics:
                save_race_pronostics(race_id, pronostics)
            if classements:
                save_race_classements(race_id, classements)
            
            # Update master horses
            for idx, row in horses_df.iterrows():
                horse_name = row.get('horse_name')
                if horse_name:
                    horse_master_id = get_or_create_horse_master(
                        horse_name, row.get('jockey'), row.get('trainer')
                    )
                    add_horse_race(
                        horse_master_id,
                        race_info.get('race_date'),
                        race_info.get('hippodrome'),
                        distance=race_info.get('distance'),
                        race_type=race_info.get('race_type'),
                        odds=row.get('odds_paris_turf'),
                        weight=row.get('weight'),
                        imported_from=temp_path
                    )
            
            # NEW: Save race arrivals (results) if found in PDF
            if arrivals:
                print(f"✅ Race arrivals found in PDF: {arrivals.get('quartet')}")
                if save_race_arrivals(race_id, arrivals, horses_df):
                    print("🔄 Retraining model with new race results...")
                    # Retrain model with the new data
                    try:
                        model.train()
                        model.save()
                        print("✅ Model retrained with new race data!")
                    except Exception as e:
                        print(f"⚠️  Could not retrain model: {e}")
            
            # Make predictions
            if model.model is not None:
                predictions_df = model.predict_on_race(
                    race_info, horses_df, classements, pronostics, best_week
                )
                predictions_list = predictions_df.to_dict(orient='records')
            else:
                # Fallback: Engineer features and use expert_score
                from feature_engineering import RaceFeatureEngineer
                feature_engineer = RaceFeatureEngineer()
                features_df = feature_engineer.engineer_race_features(
                    race_info, horses_df, classements, pronostics, best_week
                )
                features_df['predicted_probability'] = features_df['expert_score']
                features_df['predicted_rank'] = features_df['predicted_probability'].rank(ascending=False).astype(int)
                predictions_list = features_df.sort_values('predicted_rank').to_dict(orient='records')
            
            response_data = {
                'success': True,
                'race_id': race_id,
                'race_info': clean_for_json(race_info),
                'horses_imported': horses_saved,
                'pronostics': clean_for_json(pronostics),
                'classements': clean_for_json(classements),
                'predictions': clean_for_json(predictions_list),
                'message': f'Course chargée! {horses_saved} chevaux importés'
            }
            
            return jsonify(response_data), 200
        
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Failed to clean up temp file: {e}")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/horses', methods=['GET'])
def get_horses():
    """Get all horses from master database"""
    try:
        horses = get_all_horses_master(limit=1000)
        
        total_races = sum(h.get('total_races', 0) for h in horses)
        total_wins = sum(h.get('wins', 0) for h in horses)
        total_podiums = sum(h.get('podiums', 0) for h in horses)
        
        return jsonify({
            'total_horses': len(horses),
            'total_races': total_races,
            'total_wins': total_wins,
            'total_podiums': total_podiums,
            'horses': horses
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get comprehensive dashboard statistics"""
    try:
        stats = get_dashboard_stats()
        
        return jsonify({
            'total_unique_horses': stats['total_unique_horses'],
            'total_races_imported': stats['total_races_imported'],
            'races_with_results': stats['races_with_results'],
            'data_quality': stats['data_quality'],
            'quality_score': stats['quality_score'],
            'model_learning_status': stats['model_learning_status'],
            'model_can_learn': stats['model_can_learn'],
            'last_result_date': stats['last_result_date'],
            'model_status': 'Prêt' if model.model is not None else 'En développement'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'model_loaded': model.model is not None
    }), 200


if __name__ == '__main__':
    # Initialize database if needed
    try:
        from database import init_database
        from database_schema_v2 import migrate_to_schema_v2
        init_database()
        migrate_to_schema_v2()
    except Exception as e:
        print(f"Warning: Database init issue: {e}")
    
    print("\n" + "="*60)
    print("🚀 Hippique Predictor v2 - Starting Server")
    print("="*60)
    print("Frontend: http://localhost:5000")
    print("API: http://localhost:5000/api")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
