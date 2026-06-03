#!/usr/bin/env python3
from pdf_parser_v2 import parse_pdf_with_pdfplumber

race_info, df = parse_pdf_with_pdfplumber('/app/backend/sample.pdf')
print("✅ EXTRACTION RÉUSSIE!")
print(f"Race: {race_info}")
print(f"\nChevaux: {len(df)}")
cols = [c for c in ['horse_number', 'horse_name', 'age', 'weight', 'jockey', 'trainer'] if c in df.columns]
print(df[cols].head(16).to_string())
