#!/usr/bin/env python3
"""Test PDF parser"""
from data_import import import_and_process
import pandas as pd

df, errors = import_and_process('/app/backend/sample.pdf')

if df is not None and not df.empty:
    print("✅ EXTRACTION RÉUSSIE!")
    print(f"Chevaux extraits: {len(df)}")
    print("\nColonnes:", list(df.columns))
    print("\nPremiers chevaux:")
    cols = [c for c in ['horse_number', 'horse_name', 'age', 'weight', 'jockey', 'trainer'] if c in df.columns]
    print(df[cols].head(16).to_string())
else:
    print(f"❌ Erreur: {errors}")
