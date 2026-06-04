"""Enhanced horse extraction - line by line parsing"""
import re
from typing import List, Dict

def extract_horses_robust(text: str) -> List[Dict]:
    """Extract horses by parsing the PDF text line-by-line"""
    horses = []
    
    # Find the start of the horse table
    table_start = text.find("N° CHEVAUX JOCKEYS")
    if table_start == -1:
        return horses
    
    # Find where table ends (before "LES MEILLEURS")
    table_end = text.find("LES MEILLEURS", table_start)
    if table_end == -1:
        table_end = len(text)
    
    table_text = text[table_start:table_end]
    lines = table_text.split('\n')
    
    # Skip header line
    for line in lines[1:]:
        if not line.strip():
            continue
        
        # Skip lines that are clearly not horse data
        if any(x in line.upper() for x in ['TURF', 'ALSACE', 'NORD', 'TURFOMANIA', 'EQUIDIA', 'PARISIEN', 'MEILLEUR']):
            continue
        
        horse = _parse_horse_line(line)
        if horse and 'horse_name' in horse:
            horses.append(horse)
    
    return horses


def _parse_horse_line(line: str) -> Dict:
    """Parse a single horse line"""
    horse = {}
    
    # Clean up
    line = line.strip()
    if not line:
        return horse
    
    # Split by multiple spaces
    parts = [p for p in re.split(r'\s{2,}', line) if p.strip()]
    
    if len(parts) < 3:
        return horse
    
    # Try to extract number
    try:
        num = int(parts[0])
        horse['horse_number'] = num
    except:
        return horse
    
    # Extract name (usually 2-3 words)
    name_parts = []
    idx = 1
    while idx < len(parts) and len(name_parts) < 3:
        part = parts[idx].strip()
        if part[0].isupper() and part not in ['M.', 'F.', 'H.']:
            name_parts.append(part)
            idx += 1
        else:
            break
    
    if name_parts:
        horse['horse_name'] = ' '.join(name_parts)
    
    # Try to extract remaining fields
    remaining = parts[idx:]
    
    # Pattern: JOCKEY TRAINER OWNER SEXAGE CORDE WEIGHT PERF GAINS ODDS1 ODDS2
    # Usually comes in roughly this order
    
    if len(remaining) >= 1:
        horse['jockey'] = remaining[0] if remaining[0] not in ['M.', 'F.', 'H.'] else ''
    
    if len(remaining) >= 2:
        horse['trainer'] = remaining[1] if remaining[1] not in ['M.', 'F.', 'H.'] else ''
    
    if len(remaining) >= 3:
        # Owner or sexe/age
        part = remaining[2]
        if part[0] in ['M', 'F', 'H'] and len(part) <= 3:
            horse['sexe_age'] = part
        else:
            horse['owner'] = part
    
    # Look for KG (weight indicator)
    kg_idx = -1
    for i, part in enumerate(remaining):
        if 'KG' in part.upper():
            kg_idx = i
            weight_str = part.replace('KG', '').replace('kg', '').replace(',', '.').strip()
            try:
                horse['weight'] = float(weight_str)
            except:
                pass
            break
    
    # Look for odds (contains /)
    odds_count = 0
    for part in remaining:
        if '/' in part:
            odds_count += 1
            if odds_count == 1:
                horse['odds_paris_turf'] = part
            elif odds_count == 2:
                horse['odds_tierce_magazine'] = part
    
    # Look for numbers that could be PERF or GAINS
    numbers = []
    for part in remaining:
        if re.match(r'[\d\.]+', part):
            numbers.append(part)
    
    if numbers:
        # Last numbers are usually odds, so earlier ones are perf/gains
        if len(numbers) >= 2:
            horse['perf'] = numbers[0]
            if not horse.get('odds_paris_turf'):
                horse['gains_historical'] = numbers[1]
    
    return horse


# Test it
if __name__ == '__main__':
    import pdfplumber
    
    with pdfplumber.open('/app/backend/test_full.pdf') as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    horses = extract_horses_robust(full_text)
    print(f"Extracted {len(horses)} horses:\n")
    
    for horse in horses:
        print(f"{horse.get('horse_number')}: {horse.get('horse_name')} - Jockey: {horse.get('jockey')}, Trainer: {horse.get('trainer')}")
