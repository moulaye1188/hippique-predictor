"""Upgraded ML Model - Training with enriched features"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os

from config import MODEL_PATH, SCALER_PATH, PIPELINE_PATH
from feature_engineering import RaceFeatureEngineer


class UpgradedHippiqueModel:
    """Upgraded model trained on enriched features"""
    
    def __init__(self):
        self.model = None
        self.pipeline = None  # Contains imputation + scaling
        self.feature_engineer = RaceFeatureEngineer()
        self.feature_columns = self.feature_engineer.get_feature_columns()
    
    def train(self, races_data: list, model_type='random_forest'):
        """Train model on multiple races - WITH TEMPORAL SPLIT"""
        print(f"Training {model_type} model on {len(races_data)} races...\n")
        
        # Engineer features for all races
        X_list = []
        y_list = []
        race_dates = []
        
        for i, race in enumerate(races_data):
            try:
                horses_df = self.feature_engineer.engineer_race_features(
                    race.get('race_info', {}),
                    race.get('horses', pd.DataFrame()),
                    race.get('classements', {}),
                    race.get('pronostics', {}),
                    race.get('best_week', {})
                )
                
                # ✅ CRITICAL FIX: Only use races with real result_position labels
                if 'result_position' not in horses_df.columns:
                    print(f"  ⚠️  Race {i+1}: Skipped (no result_position column)")
                    continue
                
                # Skip if all result_position values are NaN
                if horses_df['result_position'].isna().all():
                    print(f"  ⚠️  Race {i+1}: Skipped (all result_position are NaN)")
                    continue
                
                X = horses_df[self.feature_columns].values
                y = (horses_df['result_position'] == 1).astype(int).values
                
                X_list.append(X)
                y_list.append(y)
                
                # ✅ TEMPORAL FIX: Track race dates for chronological split
                race_date = race.get('race_info', {}).get('date', '1900-01-01')
                race_dates.extend([race_date] * len(X))
                
                print(f"  Race {i+1}: {len(X)} horses, {np.sum(y)} winners, date={race_date}")
            
            except Exception as e:
                print(f"  ❌ Error processing race {i+1}: {e}")
                continue
        
        if not X_list:
            print("❌ No valid races to train on!")
            return False
        
        X_combined = np.vstack(X_list)
        y_combined = np.concatenate(y_list)
        
        print(f"\nTotal samples: {len(X_combined)}")
        print(f"Winners: {np.sum(y_combined)}")
        print(f"Non-winners: {len(y_combined) - np.sum(y_combined)}\n")
        
        # ✅ TEMPORAL FIX: Sort by date for chronological split (not random)
        sorted_indices = sorted(range(len(race_dates)), key=lambda i: race_dates[i])
        X_combined_sorted = X_combined[sorted_indices]
        y_combined_sorted = y_combined[sorted_indices]
        
        # Split 80/20 chronologically (older=train, newer=test)
        split_idx = int(0.8 * len(X_combined_sorted))
        X_train = X_combined_sorted[:split_idx]
        X_test = X_combined_sorted[split_idx:]
        y_train = y_combined_sorted[:split_idx]
        y_test = y_combined_sorted[split_idx:]
        
        print(f"Train set: {len(X_train)} samples (older races)")
        print(f"Test set:  {len(X_test)} samples (newer races)\n")
        
        # ✅ ROBUSTNESS FIX: Use Pipeline with SimpleImputer for proper scaling
        self.pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),  # Median imputation (not naive 0.5)
            ('scaler', StandardScaler())
        ])
        
        X_train_scaled = self.pipeline.fit_transform(X_train)
        X_test_scaled = self.pipeline.transform(X_test)
        
        # ✅ CLASS IMBALANCE FIX: Add class_weight='balanced' for imbalanced data
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'  # ← FIX: Handle imbalanced classes
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                random_state=42
            )
        elif model_type == 'neural_network':
            self.model = MLPClassifier(
                hidden_layer_sizes=(64, 32),
                max_iter=500,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        print("=" * 60)
        print(f"Training Complete - {model_type}")
        print("=" * 60)
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1-Score:  {f1:.4f}\n")
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            feature_importance = list(zip(self.feature_columns, importances))
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            print("Top 5 Important Features:")
            for i, (feature, importance) in enumerate(feature_importance[:5], 1):
                print(f"  {i}. {feature}: {importance:.4f}")
            print()
        
        return True
    
    def predict_on_race(self, race_info: dict, horses_df: pd.DataFrame, 
                       classements: dict, pronostics: dict, best_week: dict,
                       excluded_horses: list = None) -> pd.DataFrame:
        """
        Make predictions for a race
        
        Args:
            race_info: Race information dict
            horses_df: DataFrame with horses
            classements: Race classements dict
            pronostics: Race pronostics dict
            best_week: Best week dict
            excluded_horses: List of horse numbers to exclude (e.g., [3, 4, 8])
        
        Returns:
            DataFrame with predictions, excluding non-partants
        """
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained yet!")
        
        # Engineer features
        features_df = self.feature_engineer.engineer_race_features(
            race_info, horses_df, classements, pronostics, best_week
        )
        
        # Filter out excluded horses
        if excluded_horses:
            excluded_horses = [int(h) for h in excluded_horses]
            features_df = features_df[~features_df['horse_number'].isin(excluded_horses)].copy()
            print(f"ℹ️  Excluded horses: {excluded_horses}")
            print(f"ℹ️  Horses remaining for prediction: {len(features_df)}")
        
        if len(features_df) == 0:
            print("❌ No valid horses to predict on after exclusions!")
            return pd.DataFrame()
        
        # Get features
        X = features_df[self.feature_columns].values
        X_scaled = self.pipeline.transform(X)
        
        # Predict probabilities
        if hasattr(self.model, 'predict_proba'):
            y_proba = self.model.predict_proba(X_scaled)[:, 1]
        else:
            y_proba = self.model.predict(X_scaled).astype(float)
        
        # Add to dataframe
        features_df['predicted_probability'] = y_proba
        features_df['predicted_rank'] = features_df['predicted_probability'].rank(ascending=False).astype(int)
        
        return features_df.sort_values('predicted_rank')
    
    def save(self):
        """Save model and pipeline"""
        if self.model is None or self.pipeline is None:
            print("❌ Nothing to save - model not trained!")
            return False
        
        os.makedirs(os.path.dirname(MODEL_PATH) or '.', exist_ok=True)
        
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.pipeline, PIPELINE_PATH)
        print(f"✓ Model saved to {MODEL_PATH}")
        print(f"✓ Pipeline saved to {PIPELINE_PATH}\n")
        return True
    
    def load(self):
        """Load model and pipeline"""
        if not os.path.exists(MODEL_PATH) or not os.path.exists(PIPELINE_PATH):
            print("❌ Model files not found!")
            return False
        
        self.model = joblib.load(MODEL_PATH)
        self.pipeline = joblib.load(PIPELINE_PATH)
        print(f"✓ Model loaded from {MODEL_PATH}")
        print(f"✓ Pipeline loaded from {PIPELINE_PATH}\n")
        return True
