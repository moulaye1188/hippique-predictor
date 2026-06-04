#!/usr/bin/env python3
"""Analyze PDF tables structure in detail"""
import pdfplumber
import pandas as pd

with pdfplumber.open('/app/backend/test_full.pdf') as pdf:
    print(f"Total pages: {len(pdf.pages)}\n")
    
    for page_idx, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        print(f"{'='*80}")
        print(f"PAGE {page_idx}: {len(tables)} tables")
        print(f"{'='*80}\n")
        
        for table_idx, table in enumerate(tables):
            if not table:
                print(f"Table {table_idx}: Empty\n")
                continue
            
            rows = len(table)
            cols = len(table[0]) if table[0] else 0
            
            print(f"Table {table_idx}: {rows} rows × {cols} cols")
            
            # Show as DataFrame for clarity
            df = pd.DataFrame(table[1:], columns=table[0] if rows > 0 else [])
            
            # Show first few rows
            print(f"\nFirst 3 rows:")
            print(df.head(3).to_string())
            print(f"\nColumn names: {list(df.columns)}\n")
            print("-" * 80 + "\n")
