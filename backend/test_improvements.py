#!/usr/bin/env python3
"""
TEST - Model Improvements Comparison
Compare old predictions vs new predictions with improved features
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from feature_engineering import RaceFeatureEngineer

# Race data from 28/05/2026 (QUARTE - Arrivée réelle: 7-11-2-15)
RACE_28_05_DATA = {
    'race_date': '28/05/2026',
    'hippodrome': 'TEST',
    'distance': 2100,  # meters
}

HORSES_DATA = [
    {'horse_number': 2, 'horse_name': 'REVE BLEU', 'jockey': 'M.BARZALONA', 'trainer': 'G.BIETOLINI',
     'weight': 59, 'perf': '5.7.1.3', 'odds_paris_turf': '14/1', 'odds_tierce_magazine': '15/1', 'gains_historical': 18560},
    
    {'horse_number': 6, 'horse_name': 'COSY BEAR', 'jockey': 'C.LECOEUVRE', 'trainer': 'P&J.BRANDT',
     'weight': 57, 'perf': '3.2.2.2.3', 'odds_paris_turf': '12/1', 'odds_tierce_magazine': '10/1', 'gains_historical': 25389},
    
    {'horse_number': 7, 'horse_name': 'BOX OFFICER', 'jockey': 'T.BACHELOT', 'trainer': 'S.WATTEL',
     'weight': 57, 'perf': '3.1.4.2.0', 'odds_paris_turf': '7/1', 'odds_tierce_magazine': '5/1', 'gains_historical': 23909},
    
    {'horse_number': 1, 'horse_name': 'MUST BAY', 'jockey': 'R.THOMAS', 'trainer': 'C&Y.LERNER',
     'weight': 62, 'perf': '1.3.3.5.2', 'odds_paris_turf': '10/1', 'odds_tierce_magazine': '8/1', 'gains_historical': 39618},
    
    {'horse_number': 10, 'horse_name': 'SOFT DREAM', 'jockey': 'M.GRANDIN', 'trainer': 'V.HEAD',
     'weight': 55, 'perf': '2.1.1.6.6', 'odds_paris_turf': '15/1', 'odds_tierce_magazine': '17/1', 'gains_historical': 25230},
    
    {'horse_number': 3, 'horse_name': 'LE FUTUR', 'jockey': 'T.PICCONE', 'trainer': 'HA.PANTALL',
     'weight': 55, 'perf': '9.1.6.1.8', 'odds_paris_turf': '45/1', 'odds_tierce_magazine': '47/1', 'gains_historical': 18340},
    
    {'horse_number': 14, 'horse_name': 'NOTIONI FAL', 'jockey': 'A.LEMAITRE', 'trainer': 'P.GROUALLE',
     'weight': 55, 'perf': '1.5.3.3.6', 'odds_paris_turf': '26/1', 'odds_tierce_magazine': '29/1', 'gains_historical': 23285},
    
    {'horse_number': 5, 'horse_name': 'ZARLAND', 'jockey': 'C.SOUMILLON', 'trainer': 'S.WATTEL',
     'weight': 58, 'perf': '6.5.3.3', 'odds_paris_turf': '19/1', 'odds_tierce_magazine': '21/1', 'gains_historical': 8899},
    
    {'horse_number': 9, 'horse_name': 'TI AMO BELLO', 'jockey': 'C.DEMURO', 'trainer': 'M.PITART',
     'weight': 55, 'perf': '5.5.1.7.6', 'odds_paris_turf': '8/1', 'odds_tierce_magazine': '6/1', 'gains_historical': 20544},
    
    {'horse_number': 13, 'horse_name': 'ENCORE RIDGE', 'jockey': 'C.GROSBOIS', 'trainer': 'L.GADBIN',
     'weight': 54, 'perf': '1.5.4.2', 'odds_paris_turf': '31/1', 'odds_tierce_magazine': '28/1', 'gains_historical': 15672},
    
    {'horse_number': 15, 'horse_name': 'MISTER BLACK', 'jockey': 'A.HAMELIN', 'trainer': 'C&Y.LERNER',
     'weight': 55, 'perf': '2.2.0.4.9', 'odds_paris_turf': '13/1', 'odds_tierce_magazine': '11/1', 'gains_historical': 16694},
    
    {'horse_number': 4, 'horse_name': 'ANDEOL', 'jockey': 'M.GUYON', 'trainer': 'C.FERLAND',
     'weight': 55, 'perf': '7.1.4', 'odds_paris_turf': '24/1', 'odds_tierce_magazine': '23/1', 'gains_historical': 12066},
    
    {'horse_number': 12, 'horse_name': 'XTRAMOUR', 'jockey': 'A.CRASTUS', 'trainer': 'X.BLANCHET',
     'weight': 55, 'perf': '6.5.1.4.3', 'odds_paris_turf': '42/1', 'odds_tierce_magazine': '39/1', 'gains_historical': 17346},
    
    {'horse_number': 16, 'horse_name': 'BOURBON MOON', 'jockey': 'E.HARDOUIN', 'trainer': 'M.DELZANGLES',
     'weight': 55, 'perf': '1.2.0.5.5', 'odds_paris_turf': '37/1', 'odds_tierce_magazine': '40/1', 'gains_historical': 15722},
    
    {'horse_number': 8, 'horse_name': 'ZELZARA', 'jockey': 'A.MADAMET', 'trainer': 'Y.BARBEROT',
     'weight': 55, 'perf': '8.2.7.6.7', 'odds_paris_turf': '18/1', 'odds_tierce_magazine': '16/1', 'gains_historical': 33809},
    
    {'horse_number': 11, 'horse_name': 'TOO DARN QUICK', 'jockey': 'A.POUCHIN', 'trainer': 'A.FABRE',
     'weight': 55, 'perf': '4.6.5.3.8', 'odds_paris_turf': '11/1', 'odds_tierce_magazine': '9/1', 'gains_historical': 10176},
]

ACTUAL_RESULT = [7, 11, 2, 15]  # Actual quartet


def calculate_score_old_version(row):
    """OLD scoring (before improvements)"""
    try:
        # OLD weights
        perf_score = float(row.get('perf_score', 0)) / 10 * 0.25
        odds_consensus = (float(row.get('odds_paris_prob', 0.5)) + float(row.get('odds_tierce_prob', 0.5))) / 2
        odds_score = odds_consensus * 0.50
        conditions_score = float(row.get('conditions_score', 0.5)) * 0.15
        trainer_score = float(row.get('trainer_ranking', 0.5)) * 0.10
        
        return perf_score + odds_score + conditions_score + trainer_score
    except:
        return 0.0


def odds_to_prob(odds_str: str) -> float:
    """Convert odds to probability"""
    if not odds_str:
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


def test_model_improvements():
    """Compare old vs new predictions"""
    
    print("=" * 80)
    print("🎯 MODEL IMPROVEMENTS TEST - Race 28/05/2026")
    print("=" * 80)
    print(f"\nActual Quartet Result: {ACTUAL_RESULT}")
    print("(7: BOX OFFICER, 11: TOO DARN QUICK, 2: REVE BLEU, 15: MISTER BLACK)\n")
    
    # Create DataFrame
    df = pd.DataFrame(HORSES_DATA)
    
    # Calculate odds probabilities
    df['odds_paris_prob'] = df['odds_paris_turf'].apply(odds_to_prob)
    df['odds_tierce_prob'] = df['odds_tierce_magazine'].apply(odds_to_prob)
    df['odds_consensus'] = (df['odds_paris_prob'] + df['odds_tierce_prob']) / 2
    
    # Engineer features
    engineer = RaceFeatureEngineer()
    df_engineered = engineer.engineer_race_features(RACE_28_05_DATA, df, {}, {}, {})
    
    # Calculate OLD scores (before improvements)
    print("=" * 80)
    print("BEFORE IMPROVEMENTS (Old Weighting):")
    print("=" * 80)
    old_scores = []
    for idx, row in df_engineered.iterrows():
        old_score = calculate_score_old_version(row)
        old_scores.append({'horse': int(row['horse_number']), 'name': row['horse_name'], 'score': old_score})
    
    old_scores_sorted = sorted(old_scores, key=lambda x: x['score'], reverse=True)
    old_quartet = [h['horse'] for h in old_scores_sorted[:4]]
    
    print(f"\n{'Rank':<6} {'N°':<4} {'Name':<20} {'Score':<8} {'In Actual?':<12}")
    print("-" * 60)
    for rank, item in enumerate(old_scores_sorted[:10], 1):
        in_actual = "✓ YES" if item['horse'] in ACTUAL_RESULT else ""
        print(f"{rank:<6} {item['horse']:<4} {item['name']:<20} {item['score']:.4f}  {in_actual:<12}")
    
    print(f"\nOLD Prediction: {old_quartet}")
    
    # Calculate NEW scores (after improvements)
    print("\n" + "=" * 80)
    print("AFTER IMPROVEMENTS (New Weighting + Features):")
    print("=" * 80)
    
    new_scores = []
    for idx, row in df_engineered.iterrows():
        new_score = float(row.get('expert_score', 0.0))
        new_scores.append({'horse': int(row['horse_number']), 'name': row['horse_name'], 'score': new_score})
    
    new_scores_sorted = sorted(new_scores, key=lambda x: x['score'], reverse=True)
    new_quartet = [h['horse'] for h in new_scores_sorted[:4]]
    
    print(f"\n{'Rank':<6} {'N°':<4} {'Name':<20} {'Score':<8} {'In Actual?':<12}")
    print("-" * 60)
    for rank, item in enumerate(new_scores_sorted[:10], 1):
        in_actual = "✓ YES" if item['horse'] in ACTUAL_RESULT else ""
        print(f"{rank:<6} {item['horse']:<4} {item['name']:<20} {item['score']:.4f}  {in_actual:<12}")
    
    print(f"\nNEW Prediction: {new_quartet}")
    
    # Comparison
    print("\n" + "=" * 80)
    print("📊 COMPARISON:")
    print("=" * 80)
    
    old_accuracy = len([h for h in old_quartet if h in ACTUAL_RESULT]) / 4
    new_accuracy = len([h for h in new_quartet if h in ACTUAL_RESULT]) / 4
    
    print(f"\nOLD Quartet Prediction: {old_quartet}")
    print(f"Actual Quartet:        {ACTUAL_RESULT}")
    print(f"Correctness:           {old_accuracy*100:.1f}% ({sum(1 for h in old_quartet if h in ACTUAL_RESULT)}/4)")
    
    print(f"\nNEW Quartet Prediction: {new_quartet}")
    print(f"Actual Quartet:        {ACTUAL_RESULT}")
    print(f"Correctness:           {new_accuracy*100:.1f}% ({sum(1 for h in new_quartet if h in ACTUAL_RESULT)}/4)")
    
    print(f"\n🎯 IMPROVEMENT: {(new_accuracy - old_accuracy)*100:+.1f}% {'✓' if new_accuracy > old_accuracy else '✗'}")
    
    # Detailed analysis of key horses
    print("\n" + "=" * 80)
    print("🔍 DETAILED ANALYSIS:")
    print("=" * 80)
    
    key_horses = {7: 'BOX OFFICER', 11: 'TOO DARN QUICK', 2: 'REVE BLEU', 15: 'MISTER BLACK'}
    
    for horse_num, horse_name in key_horses.items():
        horse_row = df_engineered[df_engineered['horse_number'] == horse_num].iloc[0]
        old_score = calculate_score_old_version(horse_row)
        new_score = float(horse_row.get('expert_score', 0.0))
        
        old_rank = next(i+1 for i, h in enumerate(old_scores_sorted) if h['horse'] == horse_num)
        new_rank = next(i+1 for i, h in enumerate(new_scores_sorted) if h['horse'] == horse_num)
        
        print(f"\n{horse_num}: {horse_name}")
        print(f"  OLD: Rank {old_rank}/16, Score {old_score:.4f}")
        print(f"  NEW: Rank {new_rank}/16, Score {new_score:.4f}")
        print(f"  CHANGE: Rank {new_rank-old_rank:+d}, Score {new_score-old_score:+.4f}")
        print(f"  Actual Result: 1st={horse_num==7}, 2nd={horse_num==11}, 3rd={horse_num==2}, 4th={horse_num==15}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_model_improvements()
