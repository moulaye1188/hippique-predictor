import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from typing import Dict, List, Tuple
import json

class CorrelationAnalyzer:
    """Analyze correlations between features and race outcomes"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with race data
        
        Args:
            df: DataFrame with columns including 'result_position' (target)
        """
        self.df = df.copy()
        self.correlations = {}
        self.feature_importance = {}
        self.target_column = 'result_position'
    
    def prepare_data(self) -> pd.DataFrame:
        """Prepare data for correlation analysis"""
        df = self.df.copy()
        
        # Select only numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove NaN values
        df_numeric = df[numeric_cols].dropna()
        
        return df_numeric
    
    def calculate_correlations(self) -> Dict[str, float]:
        """
        Calculate Pearson correlation between all features and target
        
        Returns:
            Dictionary with feature names and correlation values
        """
        df_numeric = self.prepare_data()
        
        if self.target_column not in df_numeric.columns:
            # If no target column, use first numeric column as proxy
            target_col = df_numeric.columns[0]
        else:
            target_col = self.target_column
        
        target = df_numeric[target_col]
        correlations = {}
        
        for col in df_numeric.columns:
            if col == target_col:
                continue
            
            try:
                # Handle case where result_position might indicate winner (1 = win)
                # Lower position numbers = better outcome
                feature = df_numeric[col]
                
                if len(feature) > 2:
                    corr, pvalue = pearsonr(feature, target)
                    # Negate if position-based (lower = better)
                    if target_col == 'result_position':
                        corr = -corr  # Invert so higher feature → better (lower position)
                    correlations[col] = {
                        'pearson': corr,
                        'pvalue': pvalue,
                        'strength': self._correlation_strength(corr)
                    }
            except Exception as e:
                continue
        
        self.correlations = correlations
        return correlations
    
    def rank_feature_importance(self) -> List[Tuple[str, float]]:
        """
        Rank features by absolute correlation strength
        
        Returns:
            List of (feature_name, correlation_value) sorted by importance
        """
        if not self.correlations:
            self.calculate_correlations()
        
        ranked = sorted(
            [(feat, data['pearson']) for feat, data in self.correlations.items()],
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return ranked
    
    def get_top_factors(self, top_n: int = 10) -> List[Dict]:
        """
        Get top N most important factors
        
        Returns:
            List of dicts with factor info
        """
        ranked = self.rank_feature_importance()
        
        top_factors = []
        for i, (feature, corr) in enumerate(ranked[:top_n]):
            top_factors.append({
                'rank': i + 1,
                'feature': feature,
                'correlation': round(corr, 4),
                'strength': self._correlation_strength(corr),
                'direction': 'positive' if corr > 0 else 'negative',
                'abs_strength': abs(corr)
            })
        
        return top_factors
    
    def get_correlation_matrix(self) -> pd.DataFrame:
        """
        Get full correlation matrix for all numeric features
        
        Returns:
            Correlation matrix as DataFrame
        """
        df_numeric = self.prepare_data()
        return df_numeric.corr()
    
    def _correlation_strength(self, corr: float) -> str:
        """Classify correlation strength"""
        abs_corr = abs(corr)
        
        if abs_corr >= 0.7:
            return "Very Strong"
        elif abs_corr >= 0.5:
            return "Strong"
        elif abs_corr >= 0.3:
            return "Moderate"
        elif abs_corr >= 0.1:
            return "Weak"
        else:
            return "Very Weak"
    
    def get_feature_groups(self) -> Dict[str, List[str]]:
        """
        Group features by type for easier interpretation
        
        Returns:
            Dictionary of feature groups
        """
        feature_groups = {
            'odds_features': [],
            'horse_features': [],
            'performance_features': [],
            'text_features': [],
            'context_features': []
        }
        
        for col in self.df.columns:
            if 'odds' in col.lower() or 'probability' in col.lower():
                feature_groups['odds_features'].append(col)
            elif 'age' in col.lower() or 'weight' in col.lower():
                feature_groups['horse_features'].append(col)
            elif 'win' in col.lower() or 'podium' in col.lower():
                feature_groups['performance_features'].append(col)
            elif 'mention' in col.lower() or 'description' in col.lower():
                feature_groups['text_features'].append(col)
            else:
                feature_groups['context_features'].append(col)
        
        return feature_groups
    
    def generate_report(self) -> Dict:
        """
        Generate comprehensive correlation analysis report
        
        Returns:
            Dictionary with full analysis results
        """
        self.calculate_correlations()
        
        report = {
            'total_samples': len(self.df),
            'total_features': len(self.correlations),
            'top_factors': self.get_top_factors(10),
            'feature_groups': self.get_feature_groups(),
            'correlations': {
                feat: data['pearson'] for feat, data in self.correlations.items()
            },
            'summary': {
                'strongest_positive': max(
                    [(f, d['pearson']) for f, d in self.correlations.items() 
                     if d['pearson'] > 0],
                    key=lambda x: x[1],
                    default=(None, 0)
                ),
                'strongest_negative': min(
                    [(f, d['pearson']) for f, d in self.correlations.items() 
                     if d['pearson'] < 0],
                    key=lambda x: x[1],
                    default=(None, 0)
                )
            }
        }
        
        return report


def analyze_race_data(df: pd.DataFrame) -> Dict:
    """
    Convenience function to analyze a dataframe
    
    Returns:
        Dictionary with analysis results
    """
    analyzer = CorrelationAnalyzer(df)
    return analyzer.generate_report()
