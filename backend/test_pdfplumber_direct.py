#!/usr/bin/env python3
from pdf_parser_v2 import parse_pdf_with_pdfplumber

try:
    race_info, df = parse_pdf_with_pdfplumber('/app/backend/sample.pdf')
    print(f"✅ Race info: {race_info}")
    print(f"✅ Horses in df: {len(df) if df is not None else 'None'}")
    if df is not None and not df.empty:
        print("\nFirst 5:")
        print(df[['horse_number', 'horse_name']].head())
    else:
        print("❌ DataFrame empty or None!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
