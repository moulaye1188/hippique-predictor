#!/usr/bin/env python3
"""Debug horse extraction"""
import re
import pdfplumber

with pdfplumber.open('/app/backend/test_full.pdf') as pdf:
    full_text = ""
    for page in pdf.pages:
        full_text += page.extract_text() + "\n"

# Try to find horse lines
print("Looking for horse lines...\n")

# Show the table section
table_section = full_text[full_text.find("N° CHEVAUX"):full_text.find("LES MEILLEURS")]
print("TABLE SECTION:")
print(table_section[:500])
print("\n" + "="*80 + "\n")

# Try different patterns
patterns = [
    (r'(\d{2})\s+([A-Z\s]+?)\s+([A-Z\.]+?)\s+([A-Z\.\s&]+?)\s+([A-Z\.\s&]+?)\s+([MF]\.?\d)\s+(\d+)\s+([\d,\.]+)\.KG', "Full pattern"),
    (r'(\d{2})\s+([A-Z\s]+?)\s+([A-Z]+?)\s+([A-Z]+?)\s+([A-Z]+?)\s+([MF]\.\d)', "Simplified"),
    (r'(\d{2})\s+([A-Z\s]{5,}?)\s+([A-Z\.]+?)\s+([A-Z&\.]+?)', "Basic"),
]

for pattern, name in patterns:
    matches = re.findall(pattern, full_text)
    print(f"Pattern '{name}':")
    print(f"  Found: {len(matches)} matches")
    if matches:
        print(f"  First match: {matches[0]}")
    print()
