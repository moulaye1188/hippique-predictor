#!/usr/bin/env python3
from pdf_integration import parse_pdf_file

race_info, df = parse_pdf_file('/app/backend/sample.pdf')
print(f"Race info: {race_info}")
print(f"DF type: {type(df)}")
is_empty = df.empty if df is not None else True
print(f"DF empty: {is_empty}")
if df is not None and not df.empty:
    print(f"DF rows: {len(df)}")
    print(df[['horse_number', 'horse_name']].head())
else:
    print("❌ No data!")
