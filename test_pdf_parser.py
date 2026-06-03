#!/usr/bin/env python3
"""Test script to verify PDF parser works with Le Journal Hippique format"""

import sys
sys.path.insert(0, 'backend')

from data_import import DataImporter, OddsFeatureExtractor
import pandas as pd

# Sample text extracted from the Le Journal Hippique PDF you showed
SAMPLE_TEXT = """
N°  CHEVAUX  JOCKEYS  ENTRAINEURS  PROPRIETAIRES  SEXE  AGE  CORDE  POIDS  PERF.  GAINS  ARRIVEE
01  MUST BAY  A.THOMAS  C.Y.LERNER  J.C.BRUN  M.3  2  6,0  57,0  13.32  39618  3-3
02  REVE BLEU  M.BARZALONA  G.BIETOLINI  ARGE. RASING  F.3  8  59,6G  57.1.3  18 560  1-4/1
03  LE FUTUR  T.PICCONE  HA.PANTALL  PH.LASSEN  M.3  9  58.5KG  9.1.6.3  18 340  4-5/1
04  ANDÉOL  M.GUYON  C.FERLAND  WERTH. & FRERE  M.3  13  58.5.KG  7.1.4  12 066  2-4/1
05  ZARLAND  C.SOUMILLON  S.WATTEL  R.BAUGUENAULT  M.3  7  58.KG  6.5.3.3  8 889  2-4/1
06  COSY BEAR  C.LECOEURVRE  P&J.BRANDT  F.BLICHFELDT  H.3  5  57.KG  3.12.2.3  25 389  1-2/1
07  BOX OFFICER  T.BACHELOT  S.WATTEL  EC.NORMANDY.SPRIT  H.3  4  57.KG  3.1.4.2.0  23 909  7/1
08  ZELZARA  A.MADAMET  Y.BARBERDT  J.MESTRALLET  F.3  6  56.5KG  8.27.6.7  33 889  1-8/1
09  TI AMO BELLO  C.DEMURO  M.PITART  EC.METAL  M.3  1  56.5KG  5.1.7.6  20 544  8/1
10  SOFT DREAM  M.GRANDIN  V.HEAD  EC. C. MARZOOCO  M.3  15  55.5KG  2.11.6.8  25 230  1-5/1
11  TOO DARN QUICK  A.POUCHIN  A.FABRE  B.ED.DE.ROTHSCHILD  M.3  12  55.5KG  6.6.3.3.8  10 176  1-1/1
12  XTRAMOUR  A.CRASTUS  X.BLANCHET  X.DOUMEN  M.3  10  54.5KG  6.5.1.4.3  17 346  4-2/3
13  ENCORE RIDGE  C.GROSBOIS  L.GADBIN  C.STEDMAN  H.3  16  54.KG  1.5.4.2  15 672  3-1/1
14  NOTIONI FAL  A.LEMAITRE  P.GROUALLE  FAL.STUD.SAS  F.3  11  53.5KG  1.5.3.1.6  23 285  2-6/1
15  MISTER BLACK  A.HAMELIN  C&Y.LERNER  O.GHORGHAR  H.3  3  53.5KG  2.20.4.9  16 604  1-3/1
16  BOURBON MOON  E.HARDOUIN  M.DELZANGLES  M.MOTSCHMANN  F.3  14  52.5KG  1.20.5.5  15 722  3-7/1

LES MEILLEURS DE LA SEMAINE
ENTRAINEURS  JOCKEYS
1 - FH. GRAFFARD  1 - C. DEMURO
"""

def test_parser():
    """Test the PDF parser"""
    print("=" * 60)
    print("Testing PDF Parser for Le Journal Hippique Format")
    print("=" * 60)
    
    # Test tabular parsing
    horses = DataImporter._parse_tabular_format(SAMPLE_TEXT)
    
    print(f"\n✓ Parsed {len(horses)} horses from tabular format\n")
    
    if horses:
        print("Sample parsed horses:")
        for horse in horses[:3]:
            print(f"  #{horse.get('horse_number')}: {horse.get('horse_name')} " + 
                  f"(Result: {horse.get('result_position', 'N/A')})")
        
        # Create DataFrame
        df = pd.DataFrame(horses)
        print(f"\nDataFrame shape: {df.shape}")
        print(f"\nColumns: {list(df.columns)}")
        
        # Show key columns
        print("\nKey extracted data:")
        display_cols = ['horse_number', 'horse_name', 'jockey', 'trainer', 'result_position']
        available_cols = [c for c in display_cols if c in df.columns]
        print(df[available_cols].head(10).to_string())
        
        # Check result_position data
        has_results = (df['result_position'] > 0).sum()
        print(f"\n✓ {has_results} horses have result_position data")
        
        # Process with full pipeline
        print("\n" + "=" * 60)
        print("Processing with full pipeline...")
        print("=" * 60)
        
        df_clean = DataImporter._clean_dataframe(df)
        df_features = DataImporter.extract_features(df_clean)
        df_final = OddsFeatureExtractor.extract_odds_features(df_features)
        
        print(f"\nFinal DataFrame shape: {df_final.shape}")
        print(f"Final columns: {list(df_final.columns)}")
        
        print("\nFinal processed data (first 5 horses):")
        show_cols = ['horse_number', 'horse_name', 'result_position', 'age', 
                     'jockey', 'trainer', 'odds_probability']
        show_cols = [c for c in show_cols if c in df_final.columns]
        print(df_final[show_cols].head(5).to_string())
        
        # Validation
        print("\n" + "=" * 60)
        print("Validation Results")
        print("=" * 60)
        is_valid, errors = DataImporter.validate_data(df_final)
        if is_valid:
            print("✓ Data validation passed!")
        else:
            print("Validation warnings:")
            for error in errors:
                print(f"  ⚠ {error}")
        
        return True
    else:
        print("✗ No horses parsed!")
        return False


if __name__ == '__main__':
    success = test_parser()
    sys.exit(0 if success else 1)
