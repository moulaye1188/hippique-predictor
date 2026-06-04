#!/usr/bin/env python3
"""Debug PDF structure"""
import pdfplumber

with pdfplumber.open('/app/backend/test_full.pdf') as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    for page_idx, page in enumerate(pdf.pages):
        print(f"\n{'='*60}")
        print(f"PAGE {page_idx}:")
        print(f"{'='*60}")
        
        text = page.extract_text()
        if text:
            print(f"Text length: {len(text)} chars")
            print(f"First 300 chars:\n{text[:300]}")
        
        tables = page.extract_tables()
        if tables:
            print(f"Tables found: {len(tables)}")
            for t_idx, table in enumerate(tables):
                print(f"  Table {t_idx}: {len(table)} rows, {len(table[0]) if table else 0} cols")
