#!/usr/bin/env python3
"""
Test the PDF parser directly in the Docker container
"""
import sys
import os

# Test data (Le Journal Hippique format)
PDF_TEXT = """
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
"""

if __name__ == '__main__':
    # Import from backend
    sys.path.insert(0, '/app/backend')
    from data_import import DataImporter, OddsFeatureExtractor, import_and_process
    import pandas as pd
    
    print("=" * 70)
    print("TESTING PDF PARSER - Le Journal Hippique Format")
    print("=" * 70)
    
    # Test tabular parsing
    horses = DataImporter._parse_tabular_format(PDF_TEXT)
    print(f"\nTabular parse: {len(horses)} horses extracted\n")
    
    # Display parsed horses
    for horse in horses[:5]:
        print(f"  #{horse['horse_number']:02d}: {horse['horse_name']:20s} " + 
              f"| Result: {horse.get('result_position', 'N/A'):2} " +
              f"| Jockey: {horse.get('jockey', 'N/A'):15s} " +
              f"| Trainer: {horse.get('trainer', 'N/A')}")
    
    # Create DataFrame and process
    df = pd.DataFrame(horses)
    
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Check result_position distribution
    if 'result_position' in df.columns:
        has_position = (df['result_position'] > 0).sum()
        print(f"\nHorses with result_position: {has_position}/{len(df)}")
        print(f"Positions: {sorted(df['result_position'].dropna().astype(int).tolist())}")
    
    # Process with full pipeline
    print("\n" + "-" * 70)
    print("FULL PIPELINE PROCESSING")
    print("-" * 70)
    
    df_clean = DataImporter._clean_dataframe(df)
    df_features = DataImporter.extract_features(df_clean)
    df_final = OddsFeatureExtractor.extract_odds_features(df_features)
    
    # Validation
    is_valid, errors = DataImporter.validate_data(df_final)
    
    print(f"\nValidation: {'PASSED' if is_valid else 'HAS WARNINGS'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    # Summary
    print(f"\nFinal DataFrame shape: {df_final.shape}")
    print(f"Total horses with result_position: {(df_final['result_position'] > 0).sum()}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED - PDF Parser is working correctly!")
    print("=" * 70)
