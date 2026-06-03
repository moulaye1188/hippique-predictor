#!/usr/bin/env python3
"""Test pdfplumber table extraction"""
import pdfplumber

pdf_path = '/app/backend/sample.pdf'

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[1]
    
    # Extract tables
    tables = page.extract_tables()
    print(f"Found {len(tables)} tables\n")
    
    if tables:
        for t_idx, table in enumerate(tables):
            print(f"\n{'='*70}")
            print(f"TABLE {t_idx} ({len(table)} rows)")
            print('='*70)
            
            # Print first few rows
            for row_idx, row in enumerate(table[:20]):
                print(f"Row {row_idx}: {row}")
