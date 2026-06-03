from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import os
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename

# Import our modules
from database import (init_database, save_race, save_horse, save_predictions, get_race_history, 
                     get_race_horses, save_historical_race, save_prediction_feedback, get_all_feedback,
                     save_model_metrics, get_model_metrics_history, save_correlation_result,
                     get_correlation_results, get_historical_races_for_training,
                     get_or_create_horse_master, add_horse_race, get_all_horses_master)
from data_preparation import prepare_race_data
from model import initialize_model
from data_import import import_and_process, OddsFeatureExtractor
from correlation_analysis import CorrelationAnalyzer
from model_retraining import ModelRetrainer, prepare_features_for_training
from analytics import PredictionAnalytics
from pdf_integration import parse_pdf_file
from pdf_integration import parse_pdf_file
from advanced_pdf_parser import AdvancedPDFParser
from pdf_parser_v2 import parse_pdf_with_pdfplumber

# Initialize Flask app
app = Flask(__name__, 
            template_folder='/app/frontend',
            static_folder='/app/frontend',
            static_url_path='/')

CORS(app)

# Initialize database and model
try:
    init_database()
    print("Database initialized")
except Exception as e:
    print(f"Database initialization error: {e}")

try:
    prediction_model = initialize_model(input_dim=5)
    print("Model initialized")
except Exception as e:
    print(f"Model initialization error: {e}")
    prediction_model = None


@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')


@app.route('/api/predict', methods=['POST'])
def predict_race():
    """
    Predict race outcome
    
    Expected JSON format:
    {
        "race_date": "2026-06-03",
        "hippodrome": "LAVAL",
        "distance": 2850,
        "race_type": "ATTELE",
        "conditions": "GRAND NATIONAL DU TROT",
        "horses": [
            {
                "number": 1,
                "name": "JIBI DU FRUITIER",
                "description": "...",
                "odds": "77/1"
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'horses' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        horses = data.get('horses', [])
        if len(horses) == 0:
            return jsonify({'error': 'No horses provided'}), 400
        
        # Save race info to database
        race_id = save_race(
            race_date=data.get('race_date', datetime.now().isoformat()),
            hippodrome=data.get('hippodrome', ''),
            distance=data.get('distance'),
            race_type=data.get('race_type', ''),
            conditions=data.get('conditions', ''),
            num_competitors=len(horses)
        )
        
        # Prepare data
        features_array, horses_info, implicit_probs = prepare_race_data(horses)
        
        # Get predictions from model
        if prediction_model is not None and features_array.shape[0] > 0:
            try:
                predictions = prediction_model.predict_race(features_array)
            except Exception as e:
                print(f"Model prediction error: {e}, using implicit probabilities")
                predictions = np.array(implicit_probs)
        else:
            # Fallback to implicit probabilities from odds
            predictions = np.array(implicit_probs)
        
        # Normalize predictions
        if np.sum(predictions) > 0:
            predictions = predictions / np.sum(predictions)
        else:
            predictions = np.ones(len(horses)) / len(horses)
        
        # Save predictions to database
        predictions_dict = {}
        results = []
        
        for i, (horse, prob, info) in enumerate(zip(horses, predictions, horses_info)):
            # Save horse to database
            horse_id = save_horse(
                race_id=race_id,
                horse_number=info['number'],
                horse_name=info['name'],
                description=horse.get('description', ''),
                odds=info['odds'],
                odds_decimal=info['decimal_odds']
            )
            
            predictions_dict[horse_id] = float(prob)
            
            results.append({
                'rank': i + 1,
                'horse_number': info['number'],
                'horse_name': info['name'],
                'odds': info['odds'],
                'decimal_odds': info['decimal_odds'] or 0,
                'odds_probability': info['odds_probability'] or 0,
                'predicted_probability': float(prob),
                'confidence': float(prob)
            })
        
        # Save to database
        save_predictions(race_id, predictions_dict)
        
        # Sort by probability
        results = sorted(results, key=lambda x: x['predicted_probability'], reverse=True)
        
        return jsonify({
            'success': True,
            'race_id': race_id,
            'race_date': data.get('race_date'),
            'hippodrome': data.get('hippodrome'),
            'predictions': results,
            'analysis': {
                'total_horses': len(horses),
                'predicted_winner': results[0]['horse_name'] if results else None,
                'winner_confidence': results[0]['predicted_probability'] if results else 0,
                'top_3': [r['horse_name'] for r in results[:3]]
            }
        }), 200
    
    except Exception as e:
        print(f"Error in predict_race: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/races', methods=['GET'])
def get_races():
    """Get historical races"""
    try:
        limit = request.args.get('limit', 50, type=int)
        races = get_race_history(limit=limit)
        
        races_list = [
            {
                'id': r[0],
                'date': r[1],
                'hippodrome': r[2],
                'distance': r[3],
                'competitors': r[4]
            }
            for r in races
        ]
        
        return jsonify({'success': True, 'races': races_list}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/races/<int:race_id>', methods=['GET'])
def get_race_detail(race_id):
    """Get details of a specific race"""
    try:
        horses = get_race_horses(race_id)
        
        horses_list = [
            {
                'id': h[0],
                'number': h[1],
                'name': h[2],
                'odds_decimal': h[3]
            }
            for h in horses
        ]
        
        return jsonify({'success': True, 'horses': horses_list}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': prediction_model is not None,
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/import', methods=['POST'])
def import_data():
    """Import horse race data from CSV or PDF - CUMULATIVE SYSTEM"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save temporarily
        temp_path = f"/tmp/{secure_filename(file.filename)}"
        file.save(temp_path)
        
        # Import and process
        df, errors = import_and_process(temp_path)
        
        if df is None:
            return jsonify({'error': 'Failed to import file', 'details': errors}), 400
        
        # Process each horse and add to cumulative system
        saved_count = 0
        new_horses = 0
        updated_horses = 0
        
        for _, row in df.iterrows():
            try:
                # Convert NaN to None
                row_dict = row.to_dict()
                row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
                
                horse_name = row_dict.get('horse_name', '')
                jockey = row_dict.get('jockey')
                trainer = row_dict.get('trainer')
                
                if not horse_name:
                    continue
                
                # Get or create horse master
                horse_master_id = get_or_create_horse_master(horse_name, jockey, trainer)
                
                # Check if new or existing
                if horse_master_id > 0:
                    # Add race to horse's history
                    race_date = row_dict.get('race_date', datetime.now().isoformat()[:10])
                    odds_str = row_dict.get('odds')
                    odds_prob = OddsFeatureExtractor.convert_odds_to_probability(odds_str)
                    
                    horse_race_id = add_horse_race(
                        horse_master_id=horse_master_id,
                        race_date=race_date,
                        hippodrome=row_dict.get('hippodrome'),
                        distance=row_dict.get('distance'),
                        race_type=row_dict.get('race_type'),
                        odds=odds_str,
                        odds_probability=odds_prob,
                        age=row_dict.get('age'),
                        weight=row_dict.get('weight'),
                        result_position=row_dict.get('result_position'),
                        imported_from=file.filename
                    )
                    
                    # Track new vs updated
                    if horse_race_id:
                        saved_count += 1
                        if horse_master_id > 0:  # Simple heuristic
                            updated_horses += 1
                    else:
                        new_horses += 1
                
                # Also save to historical_races for backward compatibility
                save_historical_race(row_dict)
                
            except Exception as e:
                print(f"Error processing race: {e}")
                continue
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Get updated horse list stats
        all_horses = get_all_horses_master(limit=100)
        total_horses_in_system = len(all_horses)
        
        # Convert NaN to None for JSON serialization
        preview_df = df.head(5).astype(object).where(pd.notna(df.head(5)), None)
        preview_data = preview_df.to_dict(orient='records')
        
        return jsonify({
            'success': True,
            'imported_races': saved_count,
            'total_records': len(df),
            'total_horses_in_system': total_horses_in_system,
            'new_horses_added': new_horses,
            'updated_horses': updated_horses,
            'columns': list(df.columns),
            'preview': preview_data,
            'message': f'Imported {saved_count} races. {total_horses_in_system} unique horses in system.'
        }), 200
    
    except Exception as e:
        print(f"Error in import_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/load-race-from-pdf', methods=['POST'])
def load_race_from_pdf():
    """
    Load a complete race from PDF file
    - Extracts race information (date, hippodrome, distance, type, name)
    - Extracts horses and their details
    - Stores everything in cumulative system
    - Generates predictions immediately
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save temporarily
        temp_path = f"/tmp/{secure_filename(file.filename)}"
        file.save(temp_path)
        
        # Parse PDF - use new pdfplumber parser
        race_info, horses_df = parse_pdf_file(temp_path)
        
        # Validate
        if horses_df is None or horses_df.empty:
            return jsonify({'error': 'Failed to extract horses from PDF'}), 400
        
        # Create race in database
        race_id = save_race(
            race_date=race_info.get('race_date'),
            hippodrome=race_info.get('hippodrome'),
            distance=race_info.get('distance'),
            race_type=race_info.get('race_type'),
            conditions=race_info.get('race_name'),
            num_competitors=race_info.get('num_competitors')
        )
        
        # Add horses to cumulative system
        saved_horses_count = 0
        new_horses_count = 0
        predictions_list = []
        predictions_dict = {}
        
        for _, row in horses_df.iterrows():
            try:
                row_dict = row.to_dict()
                row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
                
                horse_name = row_dict.get('horse_name', '')
                jockey = row_dict.get('jockey')
                trainer = row_dict.get('trainer')
                
                if not horse_name:
                    continue
                
                # Get or create horse master
                horse_master_id = get_or_create_horse_master(horse_name, jockey, trainer)
                
                if horse_master_id > 0:
                    # Add race to horse's history
                    odds_str = row_dict.get('odds')
                    odds_prob = OddsFeatureExtractor.convert_odds_to_probability(odds_str)
                    
                    horse_race_id = add_horse_race(
                        horse_master_id=horse_master_id,
                        race_date=race_info.get('race_date'),
                        hippodrome=race_info.get('hippodrome'),
                        distance=race_info.get('distance'),
                        race_type=race_info.get('race_type'),
                        odds=odds_str,
                        odds_probability=odds_prob,
                        age=row_dict.get('age'),
                        weight=row_dict.get('weight'),
                        result_position=row_dict.get('result_position'),
                        imported_from=f"PDF: {file.filename}"
                    )
                    
                    if horse_race_id:
                        saved_horses_count += 1
                        new_horses_count += 1
                    
                    # Also save horse to race horses table for predictions
                    horse_id = save_horse(
                        race_id=race_id,
                        horse_number=row_dict.get('horse_number', 0),
                        horse_name=horse_name,
                        description=row_dict.get('description', ''),
                        odds=odds_str,
                        odds_decimal=OddsFeatureExtractor.convert_odds_to_probability(odds_str)
                    )
                    predictions_dict[horse_id] = odds_prob or 0.5
                    
            except Exception as e:
                print(f"Error processing horse: {e}")
                continue
        
        # Generate predictions
        if prediction_model is not None and len(predictions_dict) > 0:
            try:
                # Prepare features from horses
                features_list = []
                for idx, (_, row) in enumerate(horses_df.iterrows()):
                    row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
                    odds_prob = OddsFeatureExtractor.convert_odds_to_probability(row_dict.get('odds'))
                    features = [
                        odds_prob or 0.5,
                        row_dict.get('age', 0) / 20,  # normalize age
                        row_dict.get('weight', 0) / 100,  # normalize weight
                        0.5,  # placeholder for other features
                        0.5
                    ]
                    features_list.append(features)
                
                features_array = np.array(features_list)
                
                # Get predictions
                predictions = prediction_model.predict_race(features_array)
                if np.sum(predictions) > 0:
                    predictions = predictions / np.sum(predictions)
                else:
                    predictions = np.ones(len(horses_df)) / len(horses_df)
                
                # Build results
                for idx, (horse_id, pred_prob) in enumerate(sorted(predictions_dict.items(), key=lambda x: x[1], reverse=True)):
                    row = horses_df.iloc[idx] if idx < len(horses_df) else None
                    if row is not None:
                        predictions_list.append({
                            'horse_id': horse_id,
                            'horse_name': row.get('horse_name', 'Unknown'),
                            'horse_number': row.get('horse_number'),
                            'predicted_probability': float(predictions[idx]),
                            'odds_probability': pred_prob,
                            'rank': idx + 1
                        })
                
                # Save predictions to DB
                save_predictions(race_id, predictions_dict)
                
            except Exception as e:
                print(f"Error generating predictions: {e}")
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'race_id': race_id,
            'race_info': race_info,
            'horses_imported': saved_horses_count,
            'new_horses': new_horses_count,
            'predictions': predictions_list[:10],  # Top 10 predictions
            'message': f'Race loaded! {saved_horses_count} horses imported, {new_horses_count} new to system.'
        }), 200
    
    except Exception as e:
        print(f"Error in load_race_from_pdf: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/horses', methods=['GET'])
def get_horses_list():
    """Get all master horses with cumulative stats"""
    try:
        limit = request.args.get('limit', 100, type=int)
        horses = get_all_horses_master(limit=limit)
        
        return jsonify({
            'success': True,
            'total_horses': len(horses),
            'horses': horses
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['GET'])
def analyze_correlations():
    """Analyze correlations between features and outcomes"""
    try:
        # Get historical races for analysis
        historical_races = get_historical_races_for_training(limit=500)
        
        if not historical_races:
            return jsonify({'error': 'No historical data available for analysis'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_races, columns=[
            'race_date', 'hippodrome', 'distance', 'horse_number', 'horse_name',
            'odds', 'odds_decimal', 'age', 'wins', 'podiums', 'result_position'
        ])
        
        # Perform analysis
        analyzer = CorrelationAnalyzer(df)
        report = analyzer.generate_report()
        
        # Save results
        for factor in report.get('top_factors', []):
            save_correlation_result(
                feature_name=factor['feature'],
                correlation=factor['correlation'],
                strength=factor['strength'],
                rank=factor['rank']
            )
        
        return jsonify({
            'success': True,
            'analysis_date': datetime.now().isoformat(),
            'total_samples': report['total_samples'],
            'top_factors': report['top_factors'],
            'feature_groups': report['feature_groups']
        }), 200
    
    except Exception as e:
        print(f"Error in analyze_correlations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback on prediction (actual result)"""
    try:
        data = request.get_json()
        
        required = ['race_id', 'horse_id', 'predicted_rank', 'actual_position']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        race_id = data['race_id']
        horse_id = data['horse_id']
        predicted_rank = data['predicted_rank']
        actual_position = data['actual_position']
        predicted_prob = data.get('predicted_probability', 0.0)
        
        # Save feedback
        feedback_id = save_prediction_feedback(
            race_id=race_id,
            horse_id=horse_id,
            predicted_prob=predicted_prob,
            predicted_rank=predicted_rank,
            actual_position=actual_position
        )
        
        # Trigger retraining if we have enough feedback
        all_feedback = get_all_feedback()
        if len(all_feedback) >= 10:
            try:
                # Get historical data for retraining
                historical_races = get_historical_races_for_training(limit=500)
                if historical_races:
                    df = pd.DataFrame(historical_races, columns=[
                        'race_date', 'hippodrome', 'distance', 'horse_number', 'horse_name',
                        'odds', 'odds_decimal', 'age', 'wins', 'podiums', 'result_position'
                    ])
                    
                    # Prepare data
                    X, y = prepare_features_for_training(df)
                    
                    if len(X) > 10:
                        # Fine-tune model
                        retrainer = ModelRetrainer(model_path='/app/models/race_prediction_model.h5',
                                                 input_dim=X.shape[1])
                        retrainer.incremental_train(X, y, epochs=3, verbose=0)
                        print("Model retraining completed")
            except Exception as e:
                print(f"Error during retraining: {e}")
        
        return jsonify({
            'success': True,
            'feedback_id': feedback_id,
            'message': 'Feedback recorded successfully'
        }), 200
    
    except Exception as e:
        print(f"Error in submit_feedback: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get dashboard metrics and learning data"""
    try:
        # Get all feedback for analysis
        all_feedback = get_all_feedback()
        
        # Get master horses stats
        all_horses = get_all_horses_master(limit=1000)
        total_unique_horses = len(all_horses)
        total_races_tracked = sum(h['total_races'] for h in all_horses) if all_horses else 0
        
        if not all_feedback:
            return jsonify({
                'success': True,
                'accuracy': 0,
                'total_predictions': 0,
                'correct_predictions': 0,
                'trend': 'insufficient_data',
                'total_unique_horses': total_unique_horses,
                'total_races_tracked': total_races_tracked,
                'message': 'No prediction feedback yet'
            }), 200
        
        # Calculate metrics
        total = len(all_feedback)
        correct = sum(1 for f in all_feedback if f[5] == 1)  # f[5] is prediction_correct
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Get metrics history
        metrics_history = get_model_metrics_history(limit=30)
        accuracy_timeline = [
            {'race_number': i+1, 'accuracy': m[1]} for i, m in enumerate(metrics_history)
        ]
        
        # Get correlation results
        correlations = get_correlation_results()
        top_factors = [
            {
                'feature': c[0],
                'correlation': round(c[1], 4) if c[1] else 0,
                'strength': c[2]
            }
            for c in correlations[:10]
        ]
        
        return jsonify({
            'success': True,
            'accuracy': round(accuracy, 2),
            'total_predictions': total,
            'correct_predictions': correct,
            'total_unique_horses': total_unique_horses,
            'total_races_tracked': total_races_tracked,
            'accuracy_timeline': accuracy_timeline,
            'top_factors': top_factors,
            'trend': 'stable',
            'recommendations': _get_recommendations(accuracy)
        }), 200
    
    except Exception as e:
        print(f"Error in get_dashboard_data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/retrain', methods=['POST'])
def trigger_retrain():
    """Manually trigger model retraining"""
    try:
        # Get historical data
        historical_races = get_historical_races_for_training(limit=500)
        
        if not historical_races:
            return jsonify({'error': 'No historical data available'}), 400
        
        df = pd.DataFrame(historical_races, columns=[
            'race_date', 'hippodrome', 'distance', 'horse_number', 'horse_name',
            'odds', 'odds_decimal', 'age', 'wins', 'podiums', 'result_position'
        ])
        
        # Prepare data
        X, y = prepare_features_for_training(df)
        
        if len(X) < 10:
            return jsonify({'error': 'Not enough data for retraining (need at least 10 samples)'}), 400
        
        # Split data
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Retrain
        retrainer = ModelRetrainer(model_path='/app/models/race_prediction_model.h5',
                                 input_dim=X.shape[1])
        
        history = retrainer.fine_tune(X_train, y_train, X_test, y_test, epochs=10, verbose=0)
        eval_results = retrainer.evaluate_on_new_data(X_test, y_test)
        
        return jsonify({
            'success': True,
            'message': 'Model retraining completed',
            'training_results': history,
            'evaluation': eval_results,
            'samples_used': len(X_train)
        }), 200
    
    except Exception as e:
        print(f"Error in trigger_retrain: {e}")
        return jsonify({'error': str(e)}), 500


def _get_recommendations(accuracy: float) -> list:
    """Generate recommendations based on accuracy"""
    recommendations = []
    
    if accuracy >= 60:
        recommendations.append("Model is performing well")
    elif accuracy >= 50:
        recommendations.append("Good performance. Continue collecting feedback data")
    elif accuracy >= 40:
        recommendations.append("Model needs more training data")
    else:
        recommendations.append("Model needs significant improvement. Import more historical data")
    
    if accuracy < 50:
        recommendations.append("Import more PDF/CSV files with historical race data")
    
    return recommendations


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
