#!/usr/bin/env python3
"""Test the complete flow"""
from data_import import import_and_process

print("Testing import_and_process with PDF...")
df, errors = import_and_process('/app/backend/sample.pdf')

if df is not None:
    print(f"✅ Success: {len(df)} horses extracted")
    print("\nFirst 5 horses:")
    cols = [c for c in df.columns if c in ['horse_number', 'horse_name', 'jockey', 'trainer']]
    print(df[cols].head(16).to_string())
else:
    print(f"❌ Error: {errors}")
