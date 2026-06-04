"""Smart horse data extraction - combine descriptions + minimal table data"""
import re
from typing import Dict, List

def extract_horses_smart(text: str) -> List[Dict]:
    """
    Smart extraction:
    1. Get names from descriptions
    2. Get jockey/trainer from table using pattern matching
    3. Get odds and other fields separately
    """
    horses = {}
    
    # Step 1: Extract names from descriptions
    desc_pattern = r'(\d+)\s*-\s*([A-Z][A-Z\s\-]+?)\s*:'
    for match in re.finditer(desc_pattern, text):
        num = int(match.group(1))
        name = match.group(2).strip()
        horses[num] = {'horse_number': num, 'horse_name': name}
    
    # Step 2: Extract from table - look for JOCKEY TRAINER patterns
    # Pattern: NAME JOCKEY_INITIALS TRAINER_NAME
    # Find the data lines (they all start with a number)
    table_start = text.find('N° CHEVAUX JOCKEYS')
    if table_start == -1:
        return list(horses.values())
    
    table_end = text.find('LES MEILLEURS', table_start)
    if table_end == -1:
        table_end = len(text)
    
    table_section = text[table_start:table_end]
    
    # Extract data per horse number
    for line_match in re.finditer(r'(\d{2})\s+(.{60,300})(?=\n\d{2}\s|$)', table_section):
        try:
            num = int(line_match.group(1))
            data_line = line_match.group(2)
            
            # Extract jockey (after horse name, usually 1-2 word with dots)
            jockey_match = re.search(r'([A-Z]\.[A-Z\w]+(?:\s+[A-Z]\.[A-Z\w]+)?)', data_line)
            if jockey_match:
                horses[num]['jockey'] = jockey_match.group(1)
            
            # Extract trainer (after jockey, multiple words possibly)
            trainer_match = re.search(r'[A-Z]\.[A-Z\w]+\s+([A-Z][A-Z\.\s&\w\-]{3,30}?)\s+(?:[A-Z]\.?\d|[A-Z]\.?\s)', data_line)
            if trainer_match:
                horses[num]['trainer'] = trainer_match.group(1).strip()
            
            # Extract sexe/age (M.3, F.3, etc.)
            sexage_match = re.search(r'([MFH]\.\d)', data_line)
            if sexage_match:
                horses[num]['sexe_age'] = sexage_match.group(1)
            
            # Extract weight (NUMBER.KG or NUMBER,KG)
            weight_match = re.search(r'(\d+[.,]\d)\s*\.?KG', data_line)
            if weight_match:
                horses[num]['weight'] = float(weight_match.group(1).replace(',', '.'))
            
            # Extract perf (numbers with dots like 1.3.3.5.2)
            perf_match = re.search(r'(\d\.\d(?:\.\d)+)', data_line)
            if perf_match:
                horses[num]['perf'] = perf_match.group(1)
            
            # Extract odds (XX/1 pattern)
            odds_matches = re.findall(r'(\d+/\d+)', data_line)
            if len(odds_matches) >= 1:
                horses[num]['odds_paris_turf'] = odds_matches[0]
            if len(odds_matches) >= 2:
                horses[num]['odds_tierce_magazine'] = odds_matches[1]
        
        except Exception as e:
            print(f"Error parsing line {num}: {e}")
    
    return sorted(list(horses.values()), key=lambda x: x.get('horse_number', 0))


# Test
if __name__ == '__main__':
    import pdfplumber
    
    with pdfplumber.open('/app/backend/test_full.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    horses = extract_horses_smart(full_text)
    
    print(f"Extracted {len(horses)} horses:\n")
    print(f"{'#':3} {'Name':20} {'Jockey':15} {'Trainer':25} {'Weight':8} {'Perf':10}")
    print("-" * 90)
    
    for h in horses:
        print(f"{h.get('horse_number',0):3d} {h.get('horse_name',''):20s} {h.get('jockey',''):15s} {h.get('trainer',''):25s} {str(h.get('weight','')):8s} {h.get('perf',''):10s}")
