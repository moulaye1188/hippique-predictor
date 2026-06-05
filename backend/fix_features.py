#!/usr/bin/env python3
# Fix fillna in feature_engineering.py

content = """\"\"\"Feature Engineering - Extract and encode enriched race data - ROBUST VERSION\"\"\"
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import re


class RaceFeatureEngineer:
    \"\"\"Extract ML features from enriched race data\"\"\"
    
    def __init__(self):
        self.trainers_form_cache = {}
        self.jockeys_form_cache = {}
    
    def engineer_race_features(self, race_data: Dict, horses_df: pd.DataFrame, 
                               classements: Dict, pronostics: Dict, best_week: Dict) -> pd.DataFrame:
        \"\"\"Create feature matrix from all enriched data - SAFE VERSION\"\"\"
        df = horses_df.copy()
        
        # Ensure all required columns exist with defaults
        default_columns = {
            'perf': '0',
            'odds_paris_turf': None,
            'odds_tierce_magazine': None,
            'weight': 55.0,
            'sexe_age': '3',
            'corde': 8,
            'gains_historical': 0,
            'trainer': 'Unknown',
            'jockey': 'Unknown',
            'expert_score': 0.5
        }
        
        for col, default in default_columns.items():
            if col not in df.columns:
                df[col] = default
        
        # Fill NaN values
        for col, default in default_columns.items():
            df[col] = df[col].fillna(value=default)
        
        # 1. Parse and encode perf
        df['perf_score'] = df['perf'].apply(self._parse_perf)
        
        # 2. Parse and encode odds
        df['odds_paris_prob'] = df['odds_paris_turf'].apply(self._odds_to_probability)
        df['odds_tierce_prob'] = df['odds_tierce_magazine'].apply(self._odds_to_probability)
        df['odds_consensus'] = (df['odds_paris_prob'] + df['odds_tierce_prob']) / 2
        
        # 3. Weight normalization
        df['weight_normalized'] = self._normalize_weight(df['weight'])
        
        # 4. Encode sexe/age
        df['age_encoded'] = df['sexe_age'].apply(self._parse_age)
        
        # 5. Corde (starting position)
        df['corde_score'] = df['corde'].apply(lambda x: 1 / (1 + abs(x - 8)) if pd.notna(x) else 0.5)
        
        # 6. Gains historical - log scale
        df['gains_log'] = df['gains_historical'].apply(lambda x: np.log1p(x) if pd.notna(x) and x > 0 else 0)
        
        # 7. Classement scoring
        df['classement_score'] = df['horse_number'].apply(
            lambda x: self._get_classement_score(x, classements)
        )
        
        # 8. Pronostic consensus
        df['pronostic_score'] = df['horse_number'].apply(
            lambda x: self._get_pronostic_score(x, pronostics)
        )
        
        # 9. Trainer and jockey rankings
        df['trainer_ranking'] = df['trainer'].apply(
            lambda x: self._get_trainer_ranking(x, best_week)
        )
        df['jockey_ranking'] = df['jockey'].apply(
            lambda x: self._get_jockey_ranking(x, best_week)
        )
        
        # 10. Combined expert score
        df['expert_score'] = (
            df['classement_score'] * 0.25 +
            df['pronostic_score'] * 0.25 +
            df['trainer_ranking'] * 0.20 +
            df['jockey_ranking'] * 0.20 +
            df['odds_consensus'] * 0.10
        )
        
        return df
    
    def _parse_perf(self, perf_str: str) -> float:
        \"\"\"Parse performance string\"\"\"
        if not perf_str or pd.isna(perf_str):
            return 0.0
        try:
            places = [int(x) for x in str(perf_str).split('.')]
            scores = [10 if p == 1 else 8 if p == 2 else 6 if p == 3 else 2 for p in places]
            return np.mean(scores) if scores else 0.0
        except:
            return 0.0
    
    def _odds_to_probability(self, odds_str: str) -> float:
        \"\"\"Convert odds to probability\"\"\"
        if not odds_str or pd.isna(odds_str):
            return 0.5
        try:
            parts = str(odds_str).split('/')
            if len(parts) != 2:
                return 0.5
            numerator = float(parts[0])
            denominator = float(parts[1])
            probability = denominator / (numerator + denominator)
            return max(0.01, min(0.99, probability))
        except:
            return 0.5
    
    def _normalize_weight(self, weights: pd.Series) -> pd.Series:
        \"\"\"Normalize weights to 0-1\"\"\"
        weights_clean = weights.dropna()
        if len(weights_clean) == 0:
            return pd.Series([0.5] * len(weights))
        
        min_w = weights_clean.min()
        max_w = weights_clean.max()
        
        if max_w == min_w:
            return pd.Series([0.5] * len(weights))
        
        return (weights - min_w) / (max_w - min_w)
    
    def _parse_age(self, sexe_age_str: str) -> int:
        \"\"\"Extract age from sexe/age string\"\"\"
        if not sexe_age_str or pd.isna(sexe_age_str):
            return 3
        try:
            match = re.search(r'\\.(\\d+)', str(sexe_age_str))
            if match:
                return int(match.group(1))
        except:
            pass
        return 3
    
    def _get_classement_score(self, horse_number: int, classements: Dict) -> float:
        \"\"\"Score based on classements\"\"\"
        if not classements:
            return 0.0
        
        score = 0.0
        weights = {
            'FORME': 0.25,
            'CLASSE': 0.20,
            'PROGRES': 0.15,
            'REGULARITE': 0.15,
            'FAVORIS': 0.25
        }
        
        for category, horses in classements.items():
            weight = weights.get(category, 0.1)
            if horse_number in horses:
                rank = horses.index(horse_number) + 1
                position_score = max(0, 1 - (rank / len(horses)))
                score += weight * position_score
        
        return min(1.0, score)
    
    def _get_pronostic_score(self, horse_number: int, pronostics: Dict) -> float:
        \"\"\"Score based on external pronostics\"\"\"
        if not pronostics:
            return 0.5
        
        total_sources = len(pronostics)
        appears_in_top3 = 0
        appears_in_top1 = 0
        
        for source, horses in pronostics.items():
            if horse_number in horses[:3]:
                appears_in_top3 += 1
                if horse_number == horses[0]:
                    appears_in_top1 += 1
        
        score = (appears_in_top3 / total_sources) * 0.7 + (appears_in_top1 / total_sources) * 0.3
        return min(1.0, score)
    
    def _get_trainer_ranking(self, trainer_name: str, best_week: Dict) -> float:
        \"\"\"Score based on trainer in best of week\"\"\"
        if not trainer_name or pd.isna(trainer_name):
            return 0.5
        
        trainers_in_form = best_week.get('trainers_in_form', [])
        
        if trainer_name in trainers_in_form:
            rank = trainers_in_form.index(trainer_name)
            return max(0.7, 1.0 - (rank / max(len(trainers_in_form), 1)))
        
        return 0.5
    
    def _get_jockey_ranking(self, jockey_name: str, best_week: Dict) -> float:
        \"\"\"Score based on jockey in best of week\"\"\"
        if not jockey_name or pd.isna(jockey_name):
            return 0.5
        
        jockeys_in_form = best_week.get('jockeys_in_form', [])
        
        if jockey_name in jockeys_in_form:
            rank = jockeys_in_form.index(jockey_name)
            return max(0.7, 1.0 - (rank / max(len(jockeys_in_form), 1)))
        
        return 0.5
    
    def get_feature_columns(self) -> List[str]:
        \"\"\"Return list of feature columns\"\"\"
        return [
            'perf_score',
            'odds_paris_prob',
            'odds_tierce_prob',
            'odds_consensus',
            'weight_normalized',
            'age_encoded',
            'corde_score',
            'gains_log',
            'classement_score',
            'pronostic_score',
            'trainer_ranking',
            'jockey_ranking',
            'expert_score'
        ]
"""

with open('/app/backend/feature_engineering.py', 'w') as f:
    f.write(content)

print("✅ Fixed")
