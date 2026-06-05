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
        
        # Ensure all required columns exist (ONLY base columns)
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
            'expert_score': 0.5
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
        # Créé APRÈS corde_score pour éviter NaN
        distance = float(race_data.get('distance', 2100))
        df['distance_score'] = 1 - abs(distance - 2100) / 2100  # Optimal à 2100m
        df['conditions_score'] = (df['corde_score'] * 0.6 + df['distance_score'] * 0.4)
        
        # 6. Gains
        df['gains_log'] = df['gains_historical'].apply(lambda x: np.log1p(float(x)) if pd.notna(x) and float(x) > 0 else 0)
        
        # 7. Classement - FALLBACK si vide
        df['classement_score'] = df['horse_number'].apply(lambda x: self._get_classement_score(x, classements))
        # Si parser ne retourne rien, utiliser perf_score comme proxy
        df['classement_score'] = df['classement_score'].fillna(value=0.0)
        df.loc[df['classement_score'] == 0, 'classement_score'] = df.loc[df['classement_score'] == 0, 'perf_score'] / 10  # Normalize perf as fallback
        
        # 8. Pronostic - FALLBACK si vide
        df['pronostic_score'] = df['horse_number'].apply(lambda x: self._get_pronostic_score(x, pronostics))
        df['pronostic_score'] = df['pronostic_score'].fillna(value=0.0)
        # Si vide, base sur odds (le marché sait mieux)
        df.loc[df['pronostic_score'] == 0, 'pronostic_score'] = df.loc[df['pronostic_score'] == 0, 'odds_consensus']
        
        # 9. Trainer/Jockey - FALLBACK si vide
        df['trainer_ranking'] = df['trainer'].apply(lambda x: self._get_trainer_ranking(x, best_week))
        df['trainer_ranking'] = df['trainer_ranking'].fillna(value=0.5)  # Default neutre
        
        df['jockey_ranking'] = df['jockey'].apply(lambda x: self._get_jockey_ranking(x, best_week))
        df['jockey_ranking'] = df['jockey_ranking'].fillna(value=0.5)  # Default neutre
        
        # 10. Expert score - POIDS RECALIBRÉS - VERSION ROBUSTE
        # Nouvelle approche: utilise principalement les ODDS + perf + conditions
        # Car le parser peut ne pas retourner classements/pronostics
        
        # Simplification: poids plus pragmatiques basés sur fiabilité
        perf_weight = 0.25       # Performance historique fiable
        odds_weight = 0.50       # Les odds reflètent le marché = PRIORITÉ!
        conditions_weight = 0.15 # Conditions de course
        trainer_weight = 0.10    # Info trainer si disponible
        
        raw_score = (
            df['perf_score'] / 10 * perf_weight +           # Normalize perf (0-10 → 0-1)
            df['odds_consensus'] * odds_weight +             # Les odds sont fiables
            df['conditions_score'] * conditions_weight +      # Corde + distance
            df['trainer_ranking'] * trainer_weight           # Entraîneur de forme
        )
        
        # Calibration: simple clip (0-1) pour probabilités réalistes
        df['expert_score'] = np.clip(raw_score, 0.01, 0.99)  # Entre 1% et 99%
        
        # DEBUG: Ajouter un log des scores
        df['debug_info'] = (
            "perf=" + (df['perf_score'] / 10 * perf_weight).round(2).astype(str) + 
            " odds=" + (df['odds_consensus'] * odds_weight).round(2).astype(str) +
            " cond=" + (df['conditions_score'] * conditions_weight).round(2).astype(str)
        )
        
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
