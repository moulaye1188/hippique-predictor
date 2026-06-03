#!/usr/bin/env python3
"""Debug PDF structure"""
import PyPDF2

pdf_path = '/app/backend/sample.pdf'

try:
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f"Total pages: {len(reader.pages)}\n")
        
        # Extract all text
        for page_idx, page in enumerate(reader.pages[:3]):
            text = page.extract_text()
            print(f"\n{'='*70}")
            print(f"PAGE {page_idx}")
            print('='*70)
            if text:
                print(text[:4000])
            else:
                print("No text extracted")
                
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
