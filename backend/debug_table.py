#!/usr/bin/env python3
import pdfplumber

with pdfplumber.open('/app/backend/sample.pdf') as pdf:
    page = pdf.pages[1]
    tables = page.extract_tables()
    
    print(f"Total tables: {len(tables)}")
    
    if tables:
        table = tables[0]
        print(f"Table 0 has {len(table)} rows")
        
        header_row = table[0]
        print(f"\nHeader row ({len(header_row)} columns):")
        for idx, col in enumerate(header_row):
            print(f"  {idx}: {str(col)[:40]}")
        
        # Check if num_col found
        num_col = None
        for idx, header in enumerate(header_row):
            h = str(header).upper() if header else ""
            print(f"  Checking col {idx}: '{h}'")
            if 'N°' in h:
                num_col = idx
                print(f"    -> FOUND N° at {idx}!")
                break
        
        print(f"\nnum_col = {num_col}")
