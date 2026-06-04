"""Updated Flask routes - Integrate new frontend + Model V2"""
import sys
sys.path.insert(0, '/app/backend')

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import os

from pdf_parser_smart import parse_pdf_smart
from database_schema_v2 import save_race_enriched, save_horse_enriched, save_race_pronostics, save_race_classements
from database import get_or_create_horse_master, add_horse_race, get_all_horses_master
from model_v2 import UpgradedHippiqueModel

app = Flask(__name__, static_folder='/app/frontend', static_url_path='')
CORS(app)

# Load model
model = UpgradedHippiqueModel()
try:
    model.load()
    print("✓ Model V2 loaded successfully")
except:
    print("⚠ Model V2 not found - predictions will use expert scores only")


# Serve new frontend
@app.route('/')
def index():
    """Serve new frontend"""
    return send_from_directory('/app/frontend', 'index.html')


@app.route('/styles.css')
def styles():
    return send_from_directory('/app/frontend', 'style.css')


@app.route('/script.js')
def script():
    return send_from_directory('/app/frontend', 'script.js')


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
            # Parse PDF
            race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart(temp_path)
            
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
            
            # Make predictions
            if model.model is not None:
                predictions_df = model.predict_on_race(
                    race_info, horses_df, classements, pronostics, best_week
                )
                predictions_list = predictions_df.to_dict(orient='records')
            else:
                # Fallback: use expert_score
                horses_df['predicted_probability'] = horses_df.get('expert_score', 0)
                horses_df['predicted_rank'] = horses_df['predicted_probability'].rank(ascending=False).astype(int)
                predictions_list = horses_df.sort_values('predicted_rank').to_dict(orient='records')
            
            return jsonify({
                'success': True,
                'race_id': race_id,
                'race_info': race_info,
                'horses_imported': horses_saved,
                'pronostics': pronostics,
                'classements': classements,
                'predictions': predictions_list,
                'message': f'Course chargée! {horses_saved} chevaux importés'
            }), 200
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
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
    """Get dashboard statistics"""
    try:
        horses = get_all_horses_master()
        
        total_unique_horses = len(horses)
        total_races_tracked = sum(h.get('total_races', 0) for h in horses)
        
        return jsonify({
            'total_unique_horses': total_unique_horses,
            'total_races_tracked': total_races_tracked,
            'model_status': 'Prêt' if model.model is not None else 'En développement',
            'data_quality': 'Excellente' if total_races_tracked >= 100 else 'Bonne' if total_races_tracked >= 50 else 'Acceptable' if total_races_tracked >= 20 else 'Faible'
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
    except:
        pass
    
    print("\n" + "="*60)
    print("🚀 Hippique Predictor v2 - Starting Server")
    print("="*60)
    print("Frontend: http://localhost:5000")
    print("API: http://localhost:5000/api")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
