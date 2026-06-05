"""Feature Engineering - Extract and encode enriched race data - ULTRA ROBUST"""
import pandas as pd
import numpy as np
from typing import Dict, List
import re


class RaceFeatureEngineer:
    """Extract ML features from enriched race data"""
    
    def __init__(self):
        self.trainers_form_cache = {}
        self.jockeys_form_cache = {}
    
    def engineer_race_features(self, race_data: Dict, horses_df: pd.DataFrame, 
                               classements: Dict, pronostics: Dict, best_week: Dict) -> pd.DataFrame:
        """Create feature matrix from all enriched data"""
        df = horses_df.copy()
        
        # Ensure all required columns exist
        default_columns = {
            'perf': '0',
            'odds_paris_turf': '1/1',
            'odds_tierce_magazine': '1/1',
            'weight': 55.0,
            'sexe_age': '3',
            'corde': 8,
            'gains_historical': 0,
            'trainer': 'Unknown',
            'jockey': 'Unknown',
            'expert_score': 0.5,
            'conditions_score': 0.5,
            'distance_score': 0.5
        }
        
        for col, default in default_columns.items():
            if col not in df.columns:
                df[col] = default
        
        # Fill NaN values carefully - skip None defaults
        for col, default in default_columns.items():
            if default is not None:
                df[col] = df[col].fillna(value=default)
        
        # 1. Parse perf
        df['perf_score'] = df['perf'].apply(self._parse_perf)
        
        # 2. Parse odds
        df['odds_paris_prob'] = df['odds_paris_turf'].apply(self._odds_to_probability)
        df['odds_tierce_prob'] = df['odds_tierce_magazine'].apply(self._odds_to_probability)
        df['odds_consensus'] = (df['odds_paris_prob'] + df['odds_tierce_prob']) / 2
        
        # 3. Weight normalization
        df['weight_normalized'] = self._normalize_weight(df['weight'].astype(float))
        
        # 4. Age
        df['age_encoded'] = df['sexe_age'].apply(self._parse_age)
        
        # 5. Corde
        df['corde_score'] = df['corde'].apply(lambda x: 1 / (1 + abs(float(x) - 8)) if pd.notna(x) else 0.5)
        
        # 5b. CONDITIONS SCORE (NOUVEAU) - Corde + Distance
        # Optimales: corde 4-6, distance 2000-2400m
        distance = float(race_data.get('distance', 2100))
        df['distance_score'] = 1 - abs(distance - 2100) / 2100  # Optimal à 2100m
        df['conditions_score'] = (df['corde_score'] * 0.6 + df['distance_score'] * 0.4)
        
        # 6. Gains
        df['gains_log'] = df['gains_historical'].apply(lambda x: np.log1p(float(x)) if pd.notna(x) and float(x) > 0 else 0)
        
        # 7. Classement
        df['classement_score'] = df['horse_number'].apply(lambda x: self._get_classement_score(x, classements))
        
        # 8. Pronostic
        df['pronostic_score'] = df['horse_number'].apply(lambda x: self._get_pronostic_score(x, pronostics))
        
        # 9. Trainer/Jockey
        df['trainer_ranking'] = df['trainer'].apply(lambda x: self._get_trainer_ranking(x, best_week))
        df['jockey_ranking'] = df['jockey'].apply(lambda x: self._get_jockey_ranking(x, best_week))
        
        # 10. Expert score - POIDS RECALIBRÉS
        # Ancien modèle: trop confiant, sur-pondère pronostics
        # Nouveau: fait confiance au marché (odds) en priorité
        
        classement_weight = 0.20    # Réduit: 0.25 → 0.20
        pronostic_weight = 0.10     # Réduit: 0.25 → 0.10 (consensus pas fiable)
        trainer_weight = 0.25       # Augmenté: 0.20 → 0.25 (trainer = crucial)
        jockey_weight = 0.15        # Réduit: 0.20 → 0.15 (jockey < trainer)
        odds_weight = 0.30          # MAJORÉ: 0.10 → 0.30 (marché a raison!)
        conditions_weight = 0.05    # NOUVEAU: corde + distance
        
        raw_score = (
            df['classement_score'] * classement_weight +
            df['pronostic_score'] * pronostic_weight +
            df['trainer_ranking'] * trainer_weight +
            df['jockey_ranking'] * jockey_weight +
            df['odds_consensus'] * odds_weight +
            df['conditions_score'] * conditions_weight
        )
        
        # Calibration: évite surconfiance (92%) avec fonction tanh
        # tanh(x * 0.8) comprend les probabilités: ne dépasse jamais 0.8
        df['expert_score'] = np.tanh(raw_score * 0.7)
        
        # Bonus: ajouter un facteur "contre-signal" pour outsiders
        # Si odds_consensus bas mais autres scores hauts = possible surprise
        df['outsider_factor'] = (
            (df['classement_score'] + df['pronostic_score']) / 2 - 
            df['odds_consensus']
        ) * 0.15  # Ajuste légèrement si signal contraire
        
        return df
    
    def _parse_perf(self, perf_str: str) -> float:
        if not perf_str or pd.isna(perf_str):
            return 0.0
        try:
            places = [int(x) for x in str(perf_str).split('.')]
            scores = [10 if p == 1 else 8 if p == 2 else 6 if p == 3 else 2 for p in places]
            return float(np.mean(scores)) if scores else 0.0
        except:
            return 0.0
    
    def _odds_to_probability(self, odds_str: str) -> float:
        if not odds_str or pd.isna(odds_str):
            return 0.5
        try:
            parts = str(odds_str).split('/')
            if len(parts) != 2:
                return 0.5
            num = float(parts[0])
            denom = float(parts[1])
            prob = denom / (num + denom)
            return float(max(0.01, min(0.99, prob)))
        except:
            return 0.5
    
    def _normalize_weight(self, weights) -> pd.Series:
        try:
            weights = pd.Series(weights)
            weights_clean = weights.dropna()
            if len(weights_clean) == 0:
                return pd.Series([0.5] * len(weights))
            
            min_w = float(weights_clean.min())
            max_w = float(weights_clean.max())
            
            if max_w == min_w:
                return pd.Series([0.5] * len(weights))
            
            result = (weights.astype(float) - min_w) / (max_w - min_w)
            return result.fillna(value=0.5)
        except:
            return pd.Series([0.5] * len(weights))
    
    def _parse_age(self, sexe_age_str: str) -> int:
        if not sexe_age_str or pd.isna(sexe_age_str):
            return 3
        try:
            match = re.search(r'\.(\d+)', str(sexe_age_str))
            if match:
                return int(match.group(1))
        except:
            pass
        return 3
    
    def _get_classement_score(self, horse_number: int, classements: Dict) -> float:
        if not classements:
            return 0.0
        score = 0.0
        weights = {'FORME': 0.25, 'CLASSE': 0.20, 'PROGRES': 0.15, 'REGULARITE': 0.15, 'FAVORIS': 0.25}
        for category, horses in classements.items():
            weight = weights.get(category, 0.1)
            if horse_number in horses:
                rank = horses.index(horse_number) + 1
                position_score = max(0, 1 - (rank / len(horses)))
                score += weight * position_score
        return float(min(1.0, score))
    
    def _get_pronostic_score(self, horse_number: int, pronostics: Dict) -> float:
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
        return float(min(1.0, score))
    
    def _get_trainer_ranking(self, trainer_name: str, best_week: Dict) -> float:
        if not trainer_name or pd.isna(trainer_name):
            return 0.5
        trainers_in_form = best_week.get('trainers_in_form', [])
        if trainer_name in trainers_in_form:
            rank = trainers_in_form.index(trainer_name)
            return float(max(0.7, 1.0 - (rank / max(len(trainers_in_form), 1))))
        return 0.5
    
    def _get_jockey_ranking(self, jockey_name: str, best_week: Dict) -> float:
        if not jockey_name or pd.isna(jockey_name):
            return 0.5
        jockeys_in_form = best_week.get('jockeys_in_form', [])
        if jockey_name in jockeys_in_form:
            rank = jockeys_in_form.index(jockey_name)
            return float(max(0.7, 1.0 - (rank / max(len(jockeys_in_form), 1))))
        return 0.5
    
    def get_feature_columns(self) -> List[str]:
        return [
            'perf_score', 'odds_paris_prob', 'odds_tierce_prob', 'odds_consensus',
            'weight_normalized', 'age_encoded', 'corde_score', 'gains_log',
            'classement_score', 'pronostic_score', 'trainer_ranking', 'jockey_ranking',
            'conditions_score', 'distance_score',  # NOUVEAU
            'expert_score'
        ]
