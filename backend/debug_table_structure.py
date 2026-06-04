#!/usr/bin/env python3
"""Test parsing table from page 1"""
import pdfplumber

with pdfplumber.open('/app/backend/test_full.pdf') as pdf:
    page1 = pdf.pages[1]
    tables = page1.extract_tables()
    
    print(f"Tables on page 1: {len(tables)}")
    
    # Table 1 is the main one
    if len(tables) > 1:
        table = tables[1]
        print(f"\nTable 1: {len(table)} rows, {len(table[0]) if table else 0} cols")
        
        print("\nHeader row:")
        for idx, cell in enumerate(table[0]):
            print(f"  {idx}: {str(cell)[:30]}")
        
        print("\nFirst data row:")
        if len(table) > 1:
            for idx, cell in enumerate(table[1]):
                print(f"  {idx}: {str(cell)[:30]}")
