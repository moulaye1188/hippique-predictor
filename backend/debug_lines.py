#!/usr/bin/env python3
"""Debug - print raw text structure"""
import PyPDF2

pdf_path = '/app/backend/sample.pdf'

with open(pdf_path, 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    page1 = reader.pages[1]
    text = page1.extract_text()
    
    lines = text.split('\n')
    print("PAGE 1 - ALL LINES WITH POSITION:\n")
    for idx, line in enumerate(lines):
        if line.strip():
            print(f"{idx:3d}: {line[:100]}")
