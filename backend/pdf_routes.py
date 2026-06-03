"""
New API endpoint for loading races directly from PDF
This should be added to app.py
"""

from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
import pandas as pd
import numpy as np


def register_pdf_routes(app, prediction_model, save_race, save_horse, save_predictions,
                       get_or_create_horse_master, add_horse_race, get_all_horses_master):
    """Register new PDF loading routes"""
    
    @app.route('/api/load-race-from-pdf', methods=['POST'])
    def load_race_from_pdf():
        """
        Load a complete race from PDF file
        - Extracts race information (date, hippodrome, distance, type, name)
        - Extracts horses and their details  
        - Stores everything in cumulative system
        - Generates predictions immediately
        """
        from advanced_pdf_parser import AdvancedPDFParser
        from data_import import OddsFeatureExtractor
        
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Save temporarily
            temp_path = f"/tmp/{secure_filename(file.filename)}"
            file.save(temp_path)
            
            # Parse PDF
            parser = AdvancedPDFParser()
            race_info, horses_df = parser.parse_pdf(temp_path)
            
            # Validate
            is_valid, errors = parser.validate_race_info()
            if not is_valid:
                return jsonify({'error': 'Invalid PDF data', 'details': errors}), 400
            
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
                    
                    # Sort by probability
                    sorted_horses = sorted(
                        enumerate(horses_df.iterrows()),
                        key=lambda x: predictions[x[0]],
                        reverse=True
                    )
                    
                    # Build results
                    for rank, (idx, (_, row)) in enumerate(sorted_horses, 1):
                        row_dict = row.to_dict()
                        predictions_list.append({
                            'rank': rank,
                            'horse_number': row_dict.get('horse_number'),
                            'horse_name': row_dict.get('horse_name', 'Unknown'),
                            'predicted_probability': float(predictions[idx]),
                            'odds_probability': OddsFeatureExtractor.convert_odds_to_probability(row_dict.get('odds')) or 0.5
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
