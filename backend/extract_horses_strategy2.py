#!/usr/bin/env python3
"""Extract horses from DESCRIPTIONS + minimal table data"""
import re

import pdfplumber

with pdfplumber.open('/app/backend/test_full.pdf') as pdf:
    full_text = ""
    for page in pdf.pages:
        full_text += page.extract_text() + "\n"

# Strategy: Extract from descriptions first
# Format: "1 - MUST BAY : Description text..."

print("=" * 80)
print("EXTRACTING FROM DESCRIPTIONS")
print("=" * 80 + "\n")

desc_pattern = r'(\d+)\s*-\s*([A-Z\s]+?)\s*:\s*([^0-9].*?)(?=\n\d+\s*-|\n\n|$)'
matches = re.finditer(desc_pattern, full_text, re.IGNORECASE | re.DOTALL)

descriptions = {}
for match in matches:
    num = int(match.group(1))
    name = match.group(2).strip()
    desc = ' '.join(match.group(3).strip().split())  # Normalize whitespace
    descriptions[num] = {'name': name, 'desc': desc[:150]}  # First 150 chars
    print(f"{num}: {name}")

print(f"\nFound {len(descriptions)} horses from descriptions\n")

# Now extract minimal data from inline table
print("=" * 80)
print("EXTRACTING FROM TABLE DATA")
print("=" * 80 + "\n")

# Simple pattern: number NAME JOCKEY TRAINER
# 01 MUST BAY R.THOMAS C&Y.LERNER

table_pattern = r'(\d{2})\s+([A-Z][A-Z\s]{3,}?)\s+([A-Z\.]+?)\s+([A-Z\.\&\s]+?)\s+([MFH]\.\d)'

matches = re.finditer(table_pattern, full_text)

table_data = {}
for match in matches:
    num = int(match.group(1))
    name = match.group(2).strip()
    jockey = match.group(3).strip()
    trainer = match.group(4).strip()
    sexe_age = match.group(5).strip()
    
    table_data[num] = {
        'name': name,
        'jockey': jockey,
        'trainer': trainer,
        'sexe_age': sexe_age
    }
    print(f"{num}: {name} | {jockey} | {trainer} | {sexe_age}")

print(f"\nFound {len(table_data)} horses from table\n")

# Merge
print("=" * 80)
print("MERGED DATA")
print("=" * 80 + "\n")

for num in sorted(set(list(descriptions.keys()) + list(table_data.keys()))):
    desc_info = descriptions.get(num, {})
    table_info = table_data.get(num, {})
    
    name = desc_info.get('name') or table_info.get('name', 'UNKNOWN')
    jockey = table_info.get('jockey', 'N/A')
    trainer = table_info.get('trainer', 'N/A')
    
    print(f"{num:2d}: {name:20s} | {jockey:15s} | {trainer:20s}")
