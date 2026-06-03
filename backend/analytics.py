import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from typing import Dict, List, Tuple
import json

class PredictionAnalytics:
    """Analyze prediction accuracy and model performance"""
    
    def __init__(self, db_connection=None):
        """Initialize analytics engine"""
        self.db = db_connection
        self.predictions_history = []
    
    def load_prediction_history(self) -> List[Dict]:
        """Load all predictions with results from database"""
        if self.db:
            # Will be implemented when database is updated
            pass
        return self.predictions_history
    
    def add_prediction_result(self, race_id: int, predictions: List[Dict], 
                             actual_winner: int = None):
        """
        Add a prediction result to history
        
        Args:
            race_id: ID of the race
            predictions: List of prediction dicts with horse_id and probability
            actual_winner: Horse ID that actually won (if known)
        """
        record = {
            'race_id': race_id,
            'predictions': predictions,
            'actual_winner': actual_winner,
            'prediction_correct': False,
            'predicted_winner_rank': None
        }
        
        if actual_winner:
            # Check if predicted winner matches actual
            sorted_preds = sorted(predictions, key=lambda x: x['probability'], reverse=True)
            if sorted_preds[0]['horse_id'] == actual_winner:
                record['prediction_correct'] = True
            
            # Find rank of actual winner in predictions
            for i, pred in enumerate(sorted_preds):
                if pred['horse_id'] == actual_winner:
                    record['predicted_winner_rank'] = i + 1
                    break
        
        self.predictions_history.append(record)
    
    def calculate_accuracy(self) -> Dict[str, float]:
        """
        Calculate various accuracy metrics
        
        Returns:
            Dictionary with accuracy metrics
        """
        if not self.predictions_history:
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0.0,
                'top3_accuracy': 0.0,
                'avg_predicted_rank': 0.0
            }
        
        # Filter predictions with actual results
        completed = [p for p in self.predictions_history if p['actual_winner']]
        
        if not completed:
            return {
                'total_predictions': len(self.predictions_history),
                'correct_predictions': 0,
                'accuracy': 0.0,
                'top3_accuracy': 0.0,
                'avg_predicted_rank': 0.0
            }
        
        correct = sum(1 for p in completed if p['prediction_correct'])
        
        # Top 3 accuracy (did actual winner appear in top 3 predictions?)
        top3_correct = sum(1 for p in completed if p['predicted_winner_rank'] and p['predicted_winner_rank'] <= 3)
        
        # Average rank of actual winner in predictions
        ranks = [p['predicted_winner_rank'] for p in completed if p['predicted_winner_rank']]
        avg_rank = np.mean(ranks) if ranks else 0
        
        return {
            'total_predictions': len(self.predictions_history),
            'completed_predictions': len(completed),
            'correct_predictions': correct,
            'accuracy': round(correct / len(completed) * 100, 2) if completed else 0.0,
            'top3_accuracy': round(top3_correct / len(completed) * 100, 2) if completed else 0.0,
            'avg_predicted_rank': round(avg_rank, 2),
            'accuracy_trend': self._calculate_trend()
        }
    
    def _calculate_trend(self) -> str:
        """Calculate if accuracy is improving over time"""
        if len(self.predictions_history) < 10:
            return "insufficient_data"
        
        # Compare first 5 vs last 5
        first_5 = self.predictions_history[:5]
        last_5 = self.predictions_history[-5:]
        
        first_acc = sum(1 for p in first_5 if p['prediction_correct']) / len(first_5)
        last_acc = sum(1 for p in last_5 if p['prediction_correct']) / len(last_5)
        
        if last_acc > first_acc * 1.1:
            return "improving"
        elif last_acc < first_acc * 0.9:
            return "declining"
        else:
            return "stable"
    
    def get_accuracy_over_time(self) -> List[Dict]:
        """
        Get accuracy metrics as a time series
        
        Returns:
            List of dicts with cumulative accuracy at each step
        """
        cumulative = []
        correct_count = 0
        total_count = 0
        
        for pred in self.predictions_history:
            if pred['actual_winner']:
                total_count += 1
                if pred['prediction_correct']:
                    correct_count += 1
                
                cumulative.append({
                    'race_number': total_count,
                    'accuracy': round(correct_count / total_count * 100, 2),
                    'correct': correct_count,
                    'total': total_count
                })
        
        return cumulative
    
    def get_confusion_matrix_data(self) -> Dict:
        """
        Get confusion matrix data (predictions vs reality)
        
        Returns:
            Dictionary with confusion matrix info
        """
        completed = [p for p in self.predictions_history if p['actual_winner']]
        
        if not completed:
            return {
                'correct_predictions': 0,
                'incorrect_predictions': 0,
                'accuracy_rate': 0,
                'error_rate': 0
            }
        
        correct = sum(1 for p in completed if p['prediction_correct'])
        incorrect = len(completed) - correct
        
        return {
            'correct_predictions': correct,
            'incorrect_predictions': incorrect,
            'accuracy_rate': round(correct / len(completed) * 100, 2),
            'error_rate': round(incorrect / len(completed) * 100, 2),
            'total_races': len(completed)
        }
    
    def get_statistics_by_hippodrome(self) -> Dict[str, Dict]:
        """
        Get performance statistics grouped by hippodrome
        
        Returns:
            Dictionary with stats per hippodrome
        """
        stats = {}
        
        # This would be populated from database with hippodrome info
        for pred in self.predictions_history:
            if 'hippodrome' not in pred:
                continue
            
            hippo = pred['hippodrome']
            if hippo not in stats:
                stats[hippo] = {
                    'total': 0,
                    'correct': 0,
                    'accuracy': 0.0
                }
            
            stats[hippo]['total'] += 1
            if pred['prediction_correct']:
                stats[hippo]['correct'] += 1
            stats[hippo]['accuracy'] = round(
                stats[hippo]['correct'] / stats[hippo]['total'] * 100, 2
            )
        
        return stats
    
    def get_performance_summary(self) -> Dict:
        """
        Get comprehensive performance summary
        
        Returns:
            Dictionary with all performance metrics
        """
        accuracy_metrics = self.calculate_accuracy()
        confusion = self.get_confusion_matrix_data()
        
        return {
            'accuracy': accuracy_metrics,
            'confusion_matrix': confusion,
            'accuracy_timeline': self.get_accuracy_over_time(),
            'trend': accuracy_metrics.get('accuracy_trend', 'unknown'),
            'predictions_count': len(self.predictions_history),
            'recommendation': self._get_recommendation(accuracy_metrics)
        }
    
    def _get_recommendation(self, accuracy_metrics: Dict) -> str:
        """Generate recommendation based on performance"""
        acc = accuracy_metrics.get('accuracy', 0)
        trend = accuracy_metrics.get('accuracy_trend', 'stable')
        
        if acc >= 60 and trend == 'improving':
            return "Model is performing well and improving! Keep training."
        elif acc >= 50 and trend in ['stable', 'improving']:
            return "Model is adequate. Consider importing more data for better accuracy."
        elif acc >= 40 and trend == 'improving':
            return "Model is developing. More training data needed."
        elif trend == 'improving':
            return "Model shows promise despite current accuracy. Continue training."
        elif trend == 'declining':
            return "⚠️ Model accuracy is declining. Review recent data quality."
        else:
            return "Model needs more training data and feedback to improve."


class ModelPerformanceTracker:
    """Track model metrics during training and inference"""
    
    def __init__(self):
        self.metrics_history = []
    
    def add_epoch_metrics(self, epoch: int, loss: float, val_loss: float, 
                         accuracy: float, val_accuracy: float):
        """Record metrics for an epoch"""
        self.metrics_history.append({
            'epoch': epoch,
            'loss': loss,
            'val_loss': val_loss,
            'accuracy': accuracy,
            'val_accuracy': val_accuracy
        })
    
    def get_best_epoch(self) -> Dict:
        """Get epoch with best validation accuracy"""
        if not self.metrics_history:
            return {}
        
        return min(self.metrics_history, key=lambda x: x['val_loss'])
    
    def get_metrics_summary(self) -> Dict:
        """Get summary of all metrics"""
        if not self.metrics_history:
            return {}
        
        final = self.metrics_history[-1]
        best = self.get_best_epoch()
        
        return {
            'final_epoch': final['epoch'],
            'final_loss': round(final['loss'], 4),
            'final_val_loss': round(final['val_loss'], 4),
            'final_accuracy': round(final['accuracy'] * 100, 2),
            'final_val_accuracy': round(final['val_accuracy'] * 100, 2),
            'best_epoch': best.get('epoch', 0),
            'best_val_loss': round(best.get('val_loss', 0), 4),
            'best_val_accuracy': round(best.get('val_accuracy', 0) * 100, 2)
        }
