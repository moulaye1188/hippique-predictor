#!/usr/bin/env python3
"""Advanced PDF parser using column reconstruction"""
import PyPDF2
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional

class AdvancedPDFParserV2:
    """Parse PDFs with vertical column layout"""
    
    @staticmethod
    def extract_columns_from_page(text: str) -> List[Dict]:
        """
        The PDF layout is vertical - each column is on separate lines
        E.g.:
        N°: 01, 02, 03, 04, ...
        AGE: M.3, F.3, M.3, M.3, ...
        CORDE: 2, 8, 9, 13, ...
        POIDS: 62KG, 59KG, 58.5KG, ...
        CHEVAUX: MUST BAY, REVE BLEU, LE FUTUR, ...
        JOCKEYS: C&Y.LERNER, G.BIETOLINI, HA.PANTALL, ...
        ENTRAINEURS: R.THOMAS, M.BARZALONA, T.PICCONE, ...
        """
        
        lines = text.split('\n')
        horses = []
        
        # Find section boundaries
        number_section = []
        age_section = []
        corde_section = []
        weight_section = []
        perf_section = []
        gains_section = []
        name_section = []
        jockey_section = []
        trainer_section = []
        owner_section = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if re.match(r'^N\u00b0', line) or (re.match(r'^\d{2}$', line) and current_section != 'numbers'):
                current_section = 'numbers'
                if re.match(r'^\d{2}$', line):
                    number_section.append(int(line))
                continue
            
            if 'CHEVAUX' in line and 'JOCKEYS' not in line:
                current_section = 'names'
                continue
            elif 'JOCKEYS' in line:
                current_section = 'jockeys'
                continue
            elif 'ENTRAINEURS' in line and current_section != 'trainer':
                current_section = 'trainers'
                continue
            elif 'PROPRIETAIRES' in line:
                current_section = 'owners'
                continue
            elif 'HORAIRES' in line or 'ARRET' in line or 'LES MEILLEURS' in line:
                break
            
            # Parse sections
            if current_section == 'numbers' and re.match(r'^\d{2}$', line):
                number_section.append(int(line))
            elif current_section == 'names' and line and not any(x in line for x in ['JOCKEYS', 'ENTRAINEURS']):
                name_section.append(line)
            elif current_section == 'jockeys' and line:
                jockey_section.append(line)
            elif current_section == 'trainers' and line:
                trainer_section.append(line)
            elif current_section == 'owners' and line:
                owner_section.append(line)
        
        # Reconstruct horses
        max_horses = max(len(number_section), len(name_section), len(jockey_section), len(trainer_section))
        
        for i in range(max_horses):
            horse = {}
            
            if i < len(number_section):
                horse['horse_number'] = number_section[i]
            
            if i < len(name_section):
                horse['horse_name'] = name_section[i]
            
            if i < len(jockey_section):
                horse['jockey'] = jockey_section[i]
            
            if i < len(trainer_section):
                horse['trainer'] = trainer_section[i]
            
            if i < len(owner_section):
                horse['owner'] = owner_section[i]
            
            # Validate
            if 'horse_name' in horse and 'horse_number' in horse:
                horses.append(horse)
        
        return horses

# Test
pdf_path = '/app/backend/sample.pdf'
with open(pdf_path, 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    page1 = reader.pages[1]
    text = page1.extract_text()
    
horses = AdvancedPDFParserV2.extract_columns_from_page(text)
print(f"✅ Extracted {len(horses)} horses")
for h in horses[:5]:
    print(h)
