import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import Tuple, List
import os

class ModelRetrainer:
    """Fine-tune and retrain the model with new data"""
    
    def __init__(self, model_path: str, input_dim: int = 5):
        self.model_path = model_path
        self.input_dim = input_dim
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load existing model or create new one"""
        if os.path.exists(self.model_path):
            try:
                self.model = keras.models.load_model(self.model_path)
                print(f"✅ Loaded existing model from {self.model_path}")
            except Exception as e:
                print(f"❌ Error loading model: {e}, creating new one")
                self._build_model()
        else:
            self._build_model()
    
    def _build_model(self):
        """Build a fresh neural network"""
        self.model = keras.Sequential([
            keras.layers.Input(shape=(self.input_dim,)),
            keras.layers.Dense(128, activation='relu', 
                             kernel_regularizer=keras.regularizers.l2(0.001)),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(64, activation='relu', 
                             kernel_regularizer=keras.regularizers.l2(0.001)),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation='relu', 
                             kernel_regularizer=keras.regularizers.l2(0.001)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC()]
        )
        print("✅ Built new model")
    
    def fine_tune(self, X_train: np.ndarray, y_train: np.ndarray, 
                  X_val: np.ndarray = None, y_val: np.ndarray = None,
                  epochs: int = 10, batch_size: int = 16, verbose: int = 1) -> dict:
        """
        Fine-tune model with new data (transfer learning)
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            epochs: Number of epochs
            batch_size: Batch size
            verbose: Verbosity level
        
        Returns:
            Dictionary with training history
        """
        if self.model is None:
            self._build_model()
        
        # Reduce learning rate for fine-tuning
        for layer in self.model.layers[:-2]:
            layer.trainable = False
        
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=5,
                restore_best_weights=True,
                verbose=verbose
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=3,
                min_lr=1e-6,
                verbose=verbose
            )
        ]
        
        validation_data = (X_val, y_val) if (X_val is not None and y_val is not None) else None
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        # Re-enable all layers
        for layer in self.model.layers:
            layer.trainable = True
        
        # Save model
        self.save_model()
        
        return self._history_to_dict(history)
    
    def incremental_train(self, X_train: np.ndarray, y_train: np.ndarray,
                         epochs: int = 5, batch_size: int = 16, 
                         verbose: int = 1) -> dict:
        """
        Incremental training on new data (without recompiling)
        
        Args:
            X_train: Training features
            y_train: Training labels
            epochs: Number of epochs
            batch_size: Batch size
            verbose: Verbosity level
        
        Returns:
            Dictionary with training history
        """
        if self.model is None:
            self._build_model()
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose
        )
        
        self.save_model()
        
        return self._history_to_dict(history)
    
    def evaluate_on_new_data(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate model on new data
        
        Args:
            X_test: Test features
            y_test: Test labels
        
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        loss, accuracy, auc = self.model.evaluate(X_test, y_test, verbose=0)
        
        predictions = self.model.predict(X_test, verbose=0)
        predictions_binary = (predictions > 0.5).astype(int).flatten()
        
        return {
            'loss': round(float(loss), 4),
            'accuracy': round(float(accuracy) * 100, 2),
            'auc': round(float(auc), 4),
            'predictions_sample': predictions[:5].flatten().tolist()
        }
    
    def predict_with_confidence(self, X: np.ndarray) -> List[Tuple[float, float]]:
        """
        Make predictions with confidence scores
        
        Args:
            X: Features
        
        Returns:
            List of (prediction, confidence) tuples
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        predictions = self.model.predict(X, verbose=0).flatten()
        
        # Confidence = distance from 0.5 (50%)
        confidence = np.abs(predictions - 0.5) * 2
        
        return list(zip(predictions.tolist(), confidence.tolist()))
    
    def save_model(self):
        """Save model to disk"""
        os.makedirs(os.path.dirname(self.model_path) or '.', exist_ok=True)
        self.model.save(self.model_path)
        print(f"✅ Model saved to {self.model_path}")
    
    def get_model_summary(self) -> dict:
        """Get model architecture summary"""
        if self.model is None:
            return {}
        
        total_params = self.model.count_params()
        trainable_params = sum([tf.keras.backend.count_params(w) 
                               for w in self.model.trainable_weights])
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'layers': len(self.model.layers),
            'input_shape': str(self.model.input_shape),
            'output_shape': str(self.model.output_shape)
        }
    
    @staticmethod
    def _history_to_dict(history) -> dict:
        """Convert Keras history to dictionary"""
        result = {
            'epochs': len(history.history.get('loss', [])),
            'final_loss': round(float(history.history['loss'][-1]), 4),
            'final_accuracy': round(float(history.history.get('accuracy', [0])[-1]) * 100, 2),
        }
        
        if 'val_loss' in history.history:
            result['final_val_loss'] = round(float(history.history['val_loss'][-1]), 4)
            result['final_val_accuracy'] = round(
                float(history.history.get('val_accuracy', [0])[-1]) * 100, 2
            )
        
        return result


def prepare_features_for_training(features_df, target_column='result_position') -> Tuple:
    """
    Prepare features and labels for training
    
    Args:
        features_df: DataFrame with features
        target_column: Name of target column
    
    Returns:
        Tuple of (X, y) normalized
    """
    # Select numeric features
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove target from features if present
    if target_column in numeric_cols:
        numeric_cols.remove(target_column)
    
    X = features_df[numeric_cols].fillna(value=0).values
    
    # Create target: 1 if position is 1 (winner), 0 otherwise
    if target_column in features_df.columns:
        y = (features_df[target_column] == 1).astype(int).values
    else:
        # If no target, assume first horse wins
        y = np.concatenate([np.array([1]), np.zeros(len(features_df) - 1)])
    
    # Normalize features to 0-1
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    X_range = X_max - X_min
    X_range[X_range == 0] = 1  # Avoid division by zero
    X_normalized = (X - X_min) / X_range
    
    return X_normalized, y
