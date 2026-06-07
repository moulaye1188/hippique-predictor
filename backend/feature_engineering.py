"""Feature Engineering - Extract and encode enriched race data - ULTRA ROBUST"""
import pandas as pd
import numpy as np
from typing import Dict, List
import re
import logging
from weather_service import WeatherService

logger = logging.getLogger(__name__)


class RaceFeatureEngineer:
    """Extract ML features from enriched race data"""
    
    def __init__(self):
        self.trainers_form_cache = {}
        self.jockeys_form_cache = {}
    
    def engineer_race_features(self, race_data: Dict, horses_df: pd.DataFrame, 
                               classements: Dict, pronostics: Dict, best_week: Dict) -> pd.DataFrame:
        """Create feature matrix from all enriched data - WITH WEATHER"""
        df = horses_df.copy()
        
        # ✅ NEW: Fetch weather data from Open-Meteo
        weather_dict = None
        if 'date' in race_data and 'latitude' in race_data and 'longitude' in race_data:
            weather_dict = WeatherService.get_weather(
                race_data['date'],
                race_data['latitude'],
                race_data['longitude']
            )
            logger.info(f"Weather integrated for race {race_data.get('race_number', 'unknown')}: {weather_dict}")
        else:
            logger.warning("Missing date/location in race_data - using default weather")
            weather_dict = WeatherService._get_default_weather()
        
        weather_features = WeatherService.get_weather_features_from_dict(weather_dict)
        
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
        
        # 1. Parse perf WITH TREND ANALYSIS (NEW - Better!)
        df['perf_score'] = df['perf'].apply(self._parse_perf)
        df['perf_trend'] = df['perf'].apply(self._parse_perf_trend)  # NEW: Tendance récente
        
        # 2. Parse odds - SEPARATED (NEW - Tiercé weighs more!)
        df['odds_paris_prob'] = df['odds_paris_turf'].apply(self._odds_to_probability)
        df['odds_tierce_prob'] = df['odds_tierce_magazine'].apply(self._odds_to_probability)
        # IMPROVED: Tiercé odds are MORE reliable than Paris odds
        df['odds_weighted'] = (df['odds_paris_prob'] * 0.30 + df['odds_tierce_prob'] * 0.70)  # 70% tiercé!
        
        # 3. Weight normalization WITH DISTANCE PENALTY (NEW!)
        distance = float(race_data.get('distance', 2100))
        df['weight_normalized'] = self._normalize_weight(df['weight'].astype(float))
        df['weight_penalty'] = df['weight'].apply(lambda w: self._weight_penalty(float(w), distance))  # NEW!
        
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
        df.loc[df['pronostic_score'] == 0, 'pronostic_score'] = df.loc[df['pronostic_score'] == 0, 'odds_weighted']
        
        # 9. Trainer/Jockey - FALLBACK si vide
        df['trainer_ranking'] = df['trainer'].apply(lambda x: self._get_trainer_ranking(x, best_week))
        df['trainer_ranking'] = df['trainer_ranking'].fillna(value=0.5)  # Default neutre
        
        df['jockey_ranking'] = df['jockey'].apply(lambda x: self._get_jockey_ranking(x, best_week))
        df['jockey_ranking'] = df['jockey_ranking'].fillna(value=0.5)  # Default neutre
        
        # ✅ NEW: Weather features (opened-meteo)
        df['temp_normalized'] = weather_features['temp_normalized']
        df['wind_factor'] = weather_features['wind_factor']
        df['precipitation_normalized'] = weather_features['precipitation_normalized']
        df['track_condition_score'] = weather_features['track_condition_score']
        logger.debug(f"Weather features added: temp={weather_features['temp_normalized']:.2f}, wind={weather_features['wind_factor']:.2f}, precip={weather_features['precipitation_normalized']:.2f}")
        
        # 10. Expert score - IMPROVED WEIGHTS (V4 - With Recent Form Boost!)
        # Based on race analysis: Tiercé odds are 3x more reliable than Paris odds
        # NEW V4: Recent form is VERY important (momentum matters!)
        
        perf_weight = 0.08            # DECREASED (older perf less relevant)
        odds_weight = 0.50            # DECREASED (to make room for recent form)
        perf_trend_weight = 0.20      # DOUBLED (from 0.10) - Recent form is crucial
        momentum_weight = 0.08        # NEW (uptrend bonus)
        consistency_weight = 0.05     # NEW (stable form > volatile)
        conditions_weight = 0.07      # Slightly reduced
        weight_penalty_weight = 0.02  # Reduced
        
        # NEW: Calculate momentum and consistency
        df['momentum_score'] = df['perf'].apply(self._parse_momentum)
        df['consistency_score'] = df['perf'].apply(self._parse_consistency)
        
        # Calculate raw score with NEW formula (V4)
        raw_score = (
            (df['perf_score'] / 10) * perf_weight +           # Normalize perf
            (df['perf_trend'] / 10) * perf_trend_weight +      # BOOSTED: Recent trend crucial
            (df['momentum_score'] / 10) * momentum_weight +    # NEW: Uptrend bonus
            (df['consistency_score'] / 10) * consistency_weight +  # NEW: Stability matters
            df['odds_weighted'] * odds_weight +                # Market odds
            df['conditions_score'] * conditions_weight +       # Conditions
            df['weight_penalty'] * weight_penalty_weight +     # Weight penalty
            df['trainer_ranking'] * 0.05                       # Trainer reduced
        )
        
        # Calibration: simple clip (0-1) pour probabilités réalistes
        df['expert_score'] = np.clip(raw_score, 0.01, 0.99)  # Entre 1% et 99%
        
        # DEBUG: Ajouter un log des scores pour analyse
        df['debug_info'] = (
            "perf=" + (df['perf_score'] / 10 * perf_weight).round(3).astype(str) + 
            " trend=" + (df['perf_trend'] / 10 * perf_trend_weight).round(3).astype(str) +
            " odds=" + (df['odds_weighted'] * odds_weight).round(3).astype(str) +
            " wpen=" + (df['weight_penalty'] * weight_penalty_weight).round(3).astype(str)
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
    
    def _parse_perf_trend(self, perf_str: str) -> float:
        """Analyze recent performance trend - AGGRESSIVE RECENT WEIGHTING"""
        if not perf_str or pd.isna(perf_str):
            return 5.0  # Neutre
        try:
            places = [int(x) for x in str(perf_str).split('.')]
            if len(places) == 0:
                return 5.0
            
            scores = [10 if p == 1 else 8 if p == 2 else 6 if p == 3 else 2 for p in places]
            
            # V2 BOOST: Much more aggressive weighting on recent races
            if len(scores) >= 10:
                # Last 10 races with exponential decay
                trend_score = (
                    scores[-1] * 2.0 +      # Last race: 200% weight (VERY recent!)
                    scores[-2] * 1.8 +      # -2 races: 180%
                    scores[-3] * 1.5 +      # -3 races: 150%
                    scores[-4] * 1.2 +      # -4 races: 120%
                    scores[-5] * 0.9 +      # -5 races: 90%
                    scores[-6] * 0.6 +      # -6 races: 60%
                    scores[-7] * 0.4 +      # -7 races: 40%
                    scores[-8] * 0.3 +      # -8 races: 30%
                    scores[-9] * 0.2 +      # -9 races: 20%
                    scores[-10] * 0.1       # -10 races: 10%
                ) / 10.8  # Normalize by total weight
            elif len(scores) >= 5:
                # 5-9 recent races
                trend_score = (
                    scores[-1] * 2.0 +      # Last race: 200% weight
                    scores[-2] * 1.6 +      # -2: 160%
                    scores[-3] * 1.2 +      # -3: 120%
                    scores[-4] * 0.8 +      # -4: 80%
                    scores[-5] * 0.4        # -5: 40%
                ) / 6.0  # Normalize
            elif len(scores) >= 3:
                # Only 3-4 races
                trend_score = (
                    scores[-1] * 2.0 +      # Last race: double weight
                    scores[-2] * 1.3 +      # -2: 130%
                    scores[-3] * 0.7        # -3: 70%
                ) / 4.0
            else:
                # Only 1-2 races
                trend_score = np.mean(scores)
            
            return float(trend_score)
        except:
            return 5.0
    
    def _parse_momentum(self, perf_str: str) -> float:
        """Detect uptrend or downtrend in recent performance
        
        Returns: 
            10 = strong uptrend (improving)
            5 = stable (no trend)
            0 = strong downtrend (declining)
        """
        if not perf_str or pd.isna(perf_str):
            return 5.0
        try:
            places = [int(x) for x in str(perf_str).split('.')]
            if len(places) < 3:
                return 5.0  # Not enough data
            
            scores = [10 if p == 1 else 8 if p == 2 else 6 if p == 3 else 2 for p in places]
            
            # Compare recent 3 races vs previous 3 races
            if len(scores) >= 6:
                recent_3 = np.mean(scores[-3:])
                previous_3 = np.mean(scores[-6:-3])
            elif len(scores) >= 3:
                recent_3 = np.mean(scores[-2:])
                previous_3 = np.mean(scores[:-2]) if len(scores) > 2 else scores[0]
            else:
                return 5.0
            
            # Momentum: positive if recent > previous
            momentum = recent_3 - previous_3  # Range: -8 to +8
            
            # Scale to 0-10 range
            momentum_score = 5.0 + (momentum / 8.0) * 5.0  # Linear scale
            momentum_score = np.clip(momentum_score, 0, 10)
            
            return float(momentum_score)
        except:
            return 5.0
    
    def _parse_consistency(self, perf_str: str) -> float:
        """Measure consistency/stability of recent performances
        
        Returns:
            10 = very consistent (stable form)
            5 = average consistency
            0 = highly variable (unpredictable)
        """
        if not perf_str or pd.isna(perf_str):
            return 5.0
        try:
            places = [int(x) for x in str(perf_str).split('.')]
            if len(places) < 2:
                return 5.0
            
            scores = [10 if p == 1 else 8 if p == 2 else 6 if p == 3 else 2 for p in places]
            
            # Focus on recent races only (last 5)
            recent_scores = scores[-5:] if len(scores) >= 5 else scores
            
            # Low variance = consistent = good
            variance = np.var(recent_scores)
            std_dev = np.std(recent_scores)
            
            # Normalize: max variance ~= 16 (from 2 to 10)
            # Consistency = inverse of normalized variance
            max_variance = 16  # (10-2)^2
            consistency_score = max(0, 10 - (variance / max_variance) * 10)
            consistency_score = np.clip(consistency_score, 0, 10)
            
            return float(consistency_score)
        except:
            return 5.0
    
    def _weight_penalty(self, weight_kg: float, distance_m: float) -> float:
        """Calculate weight penalty based on distance (NEW - More accurate!)"""
        reference_weight = 55.0  # kg
        delta_weight = weight_kg - reference_weight
        
        # More distance = more penalty for extra weight
        if distance_m > 2400:
            penalty_factor = 0.01 * delta_weight   # 1% penalty per kg
        elif distance_m > 2100:
            penalty_factor = 0.008 * delta_weight  # 0.8% penalty per kg
        elif distance_m > 1800:
            penalty_factor = 0.005 * delta_weight  # 0.5% penalty per kg
        else:
            penalty_factor = 0.003 * delta_weight  # 0.3% penalty per kg (short races)
        
        # Apply penalty - lighter horses benefit
        return float(max(0.5, min(1.0, 1.0 - penalty_factor)))

    
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
            'perf_score', 'perf_trend',                 # Performance (with trend boost)
            'odds_paris_prob', 'odds_tierce_prob', 'odds_weighted',  # Odds
            'weight_normalized', 'weight_penalty',      # Weight
            'age_encoded', 'corde_score', 'gains_log',
            'classement_score', 'pronostic_score', 'trainer_ranking', 'jockey_ranking',
            'conditions_score', 'distance_score',
            # Weather features from Open-Meteo
            'temp_normalized', 'wind_factor', 'precipitation_normalized', 'track_condition_score',
            # ✅ NEW V2: Recent form quality indicators
            'momentum_score', 'consistency_score'
            # NOTE: expert_score removed (was causing data leakage)
        ]
