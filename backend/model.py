import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pathlib import Path
import json
import os

MODEL_PATH = "/app/models/race_prediction_model.h5"
METADATA_PATH = "/app/models/model_metadata.json"

class RacePredictionModel:
    """Deep Learning model for horse race prediction"""
    
    def __init__(self, input_dim=5, model_path=MODEL_PATH):
        self.input_dim = input_dim
        self.model_path = model_path
        self.model = None
        self.history = None
        self.is_trained = False
    
    def build_model(self):
        """Build neural network architecture"""
        self.model = keras.Sequential([
            layers.Input(shape=(self.input_dim,)),
            
            # First hidden layer with dropout
            layers.Dense(128, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Second hidden layer
            layers.Dense(64, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Third hidden layer
            layers.Dense(32, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.Dropout(0.2),
            
            # Output layer - softmax for probability distribution
            layers.Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC()]
        )
        
        print(self.model.summary())
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=50, batch_size=16):
        """Train the model"""
        if self.model is None:
            self.build_model()
        
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                min_lr=1e-5
            )
        ]
        
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        self.save_model()
    
    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            self.load_model()
        
        predictions = self.model.predict(X, verbose=0)
        return predictions.flatten()
    
    def predict_race(self, features_array):
        """
        Predict probabilities for all horses in a race
        
        Args:
            features_array: (n_horses, n_features) array
        
        Returns:
            probabilities: Normalized probabilities summing to 1.0
        """
        raw_predictions = self.predict(features_array)
        
        # Softmax to ensure probabilities sum to 1
        exp_predictions = np.exp(raw_predictions - np.max(raw_predictions))
        probabilities = exp_predictions / exp_predictions.sum()
        
        return probabilities
    
    def save_model(self):
        """Save model to disk"""
        os.makedirs(os.path.dirname(self.model_path) or '.', exist_ok=True)
        
        if self.model is not None:
            self.model.save(self.model_path)
            
            # Save metadata
            metadata = {
                'input_dim': self.input_dim,
                'is_trained': self.is_trained,
                'model_version': '1.0'
            }
            
            os.makedirs(os.path.dirname(METADATA_PATH) or '.', exist_ok=True)
            with open(METADATA_PATH, 'w') as f:
                json.dump(metadata, f)
            
            print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load model from disk"""
        if os.path.exists(self.model_path):
            self.model = keras.models.load_model(self.model_path)
            self.is_trained = True
            print(f"Model loaded from {self.model_path}")
        else:
            print(f"Model not found at {self.model_path}, building new model")
            self.build_model()


def create_synthetic_training_data(n_samples=200):
    """
    Create synthetic training data for initial model training
    Simulates historical race data
    """
    np.random.seed(42)
    
    n_horses_per_race = 10
    n_races = n_samples
    
    X = []
    y = []
    
    for _ in range(n_races):
        # Generate features for horses in this race
        race_features = np.random.rand(n_horses_per_race, 5)
        
        # Bias: horses with higher odds_probability (last feature) tend to win
        odds_bias = race_features[:, -1]
        
        # Generate winner based on combined score
        combined_score = 0.6 * odds_bias + 0.4 * (
            0.3 * race_features[:, 0] +  # sentiment
            0.3 * race_features[:, 1] +  # keywords
            0.2 * race_features[:, 2] +  # experience
            0.2 * race_features[:, 3]    # confidence
        )
        
        # Softmax to get probabilities
        exp_scores = np.exp(combined_score - np.max(combined_score))
        probs = exp_scores / exp_scores.sum()
        
        # Add some noise
        probs = probs * np.random.uniform(0.8, 1.2, n_horses_per_race)
        probs = probs / probs.sum()
        
        X.append(race_features)
        y.append(probs)
    
    X = np.vstack(X)
    y = np.hstack(y)
    
    return X, y


def initialize_model(input_dim=5):
    """Initialize and optionally train a model"""
    model = RacePredictionModel(input_dim=input_dim)
    
    # Try to load existing model
    if os.path.exists(MODEL_PATH):
        model.load_model()
    else:
        # Create and train on synthetic data
        print("Training model on synthetic data...")
        model.build_model()
        
        X_train, y_train = create_synthetic_training_data(n_samples=200)
        
        # Split into train and validation
        split_idx = int(0.8 * len(X_train))
        X_train_set = X_train[:split_idx]
        y_train_set = y_train[:split_idx]
        X_val_set = X_train[split_idx:]
        y_val_set = y_train[split_idx:]
        
        model.train(
            X_train_set, y_train_set,
            X_val_set, y_val_set,
            epochs=30,
            batch_size=16
        )
    
    return model
