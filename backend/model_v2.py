"""Upgraded ML Model - Training with enriched features"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os

from config import MODEL_PATH, SCALER_PATH
from feature_engineering import RaceFeatureEngineer


class UpgradedHippiqueModel:
    """Upgraded model trained on enriched features"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_engineer = RaceFeatureEngineer()
        self.feature_columns = self.feature_engineer.get_feature_columns()
    
    def train(self, races_data: list, model_type='random_forest'):
        """Train model on multiple races"""
        print(f"Training {model_type} model on {len(races_data)} races...\n")
        
        # Engineer features for all races
        X_list = []
        y_list = []
        
        for i, race in enumerate(races_data):
            try:
                horses_df = self.feature_engineer.engineer_race_features(
                    race.get('race_info', {}),
                    race.get('horses', pd.DataFrame()),
                    race.get('classements', {}),
                    race.get('pronostics', {}),
                    race.get('best_week', {})
                )
                
                X = horses_df[self.feature_columns].fillna(value=0.5).values
                
                # Labels: use result_position if available, else use expert_score as proxy
                if 'result_position' in horses_df.columns:
                    y = (horses_df['result_position'] == 1).astype(int).values
                else:
                    # For now, use expert_score as soft labels
                    y = (horses_df['expert_score'] > 0.4).astype(int).values
                
                X_list.append(X)
                y_list.append(y)
                print(f"  Race {i+1}: {len(X)} horses, {np.sum(y)} winners")
            
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
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X_combined, y_combined, test_size=0.2, random_state=42, stratify=y_combined
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
        elif model_type == 'neural_network':
            self.model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
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
                       classements: dict, pronostics: dict, best_week: dict) -> pd.DataFrame:
        """Make predictions for a race"""
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained yet!")
        
        # Engineer features
        features_df = self.feature_engineer.engineer_race_features(
            race_info, horses_df, classements, pronostics, best_week
        )
        
        # Get features
        X = features_df[self.feature_columns].fillna(value=0.5).values
        X_scaled = self.scaler.transform(X)
        
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
        """Save model and scaler"""
        if self.model is None or self.scaler is None:
            print("❌ Nothing to save - model not trained!")
            return False
        
        os.makedirs("/app/models", exist_ok=True)
        
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.scaler, SCALER_PATH)
        print(f"✓ Model saved to {MODEL_PATH}")
        print(f"✓ Scaler saved to {SCALER_PATH}\n")
        return True
    
    def load(self):
        """Load model and scaler"""
        if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
            print("❌ Model files not found!")
            return False
        
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        print(f"✓ Model loaded from {MODEL_PATH}")
        print(f"✓ Scaler loaded from {SCALER_PATH}\n")
        return True
