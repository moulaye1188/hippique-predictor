"""ULTIMATE PDF Parser - Intelligent merging of all data sources"""
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

def convert_to_native_types(obj):
    """Convert NumPy/pandas types to native Python types for JSON"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, pd.DataFrame):
        return obj.astype(object).where(pd.notna(obj), None).to_dict(orient='records')
    return obj


def parse_pdf_ultimate(file_path: str) -> Tuple[Dict, pd.DataFrame, Dict, Dict, Dict]:
    """
    ULTIMATE complete PDF parsing - extracts EVERYTHING
    Returns: (race_info, horses_df, pronostics_dict, classements_dict, best_week_dict)
    """
    try:
        import pdfplumber
    except ImportError:
        return {}, pd.DataFrame(), {}, {}, {}
    
    race_info = {}
    horses_list = []
    pronostics = {}
    classements = {}
    best_week = {}
    
    try:
        with pdfplumber.open(file_path) as pdf:
            # Extract all text
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            # Parse everything
            race_info = _parse_race_header(full_text)
            horses_list = _extract_all_horses(full_text)
            results = _parse_previous_results(full_text)
            race_info.update(results)
            pronostics = _parse_pronostics_sources(full_text)
            classements = _parse_classements_section(full_text)
            best_week = _parse_best_of_week(full_text)
    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
    
    # Convert to DataFrame
    df = pd.DataFrame(horses_list)
    
    # Convert all to native types
    race_info = convert_to_native_types(race_info)
    pronostics = convert_to_native_types(pronostics)
    classements = convert_to_native_types(classements)
    best_week = convert_to_native_types(best_week)
    
    return race_info, df, pronostics, classements, best_week


def _extract_all_horses(text: str) -> List[Dict]:
    """Extract horses by merging descriptions + table data intelligently"""
    
    # Step 1: Extract from horse descriptions (1 - NAME : description...)
    descriptions = _extract_horse_descriptions(text)
    
    # Step 2: Extract from table (number NAME JOCKEY TRAINER...)
    table_data = _extract_horse_table_data(text)
    
    # Step 3: Merge intelligently
    horses = _merge_horse_data(descriptions, table_data)
    
    return horses


def _extract_horse_descriptions(text: str) -> Dict[int, Dict]:
    """Extract horse descriptions from free text"""
    descriptions = {}
    
    # Pattern: "1 - NAME : description..."
    # Find where descriptions start (after header info)
    desc_start = text.find("1 - MUST BAY")
    if desc_start == -1:
        return descriptions
    
    # Find where descriptions end (before results or results section)
    desc_end = text.find("RESULTATS DES COURSES", desc_start)
    if desc_end == -1:
        desc_end = text.find("N° CHEVAUX", desc_start)
    
    desc_text = text[desc_start:desc_end]
    
    # Parse each description
    pattern = r'(\d+)\s*-\s*([A-Z\s]+?)\s*:\s*([^0-9].*?)(?=\n\d+\s*-|\n\n|$)'
    for match in re.finditer(pattern, desc_text, re.IGNORECASE | re.DOTALL):
        try:
            num = int(match.group(1))
            name = match.group(2).strip()
            desc = ' '.join(match.group(3).strip().split())[:200]
            
            descriptions[num] = {
                'horse_number': num,
                'horse_name': name,
                'description': desc
            }
        except:
            pass
    
    return descriptions


def _extract_horse_table_data(text: str) -> Dict[int, Dict]:
    """Extract horse data from inline table format"""
    table_data = {}
    
    # Find table section
    table_start = text.find("N° CHEVAUX JOCKEYS")
    if table_start == -1:
        return table_data
    
    table_end = text.find("LES MEILLEURS", table_start)
    if table_end == -1:
        table_end = len(text)
    
    table_text = text[table_start:table_end]
    lines = table_text.split('\n')
    
    # Process each line (skip header)
    for line in lines[1:]:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        
        # Skip non-horse lines
        if any(x in line.upper() for x in ['TURF', 'ALSACE', 'NORD', 'MEILLEUR', 'ENTRAINEURS']):
            continue
        
        horse_data = _parse_table_line(line)
        if horse_data and 'horse_number' in horse_data:
            table_data[horse_data['horse_number']] = horse_data
    
    return table_data


def _parse_table_line(line: str) -> Dict:
    """Parse a single table line intelligently"""
    horse = {}
    
    # Extract horse number first
    match = re.match(r'^(\d{2})\s+(.+)$', line)
    if not match:
        return horse
    
    try:
        horse['horse_number'] = int(match.group(1))
    except:
        return horse
    
    remainder = match.group(2)
    
    # Split by multiple spaces to get fields
    fields = [f.strip() for f in re.split(r'\s{2,}', remainder) if f.strip()]
    
    if len(fields) < 1:
        return horse
    
    # Extract name - usually first field(s) that are all uppercase letters/spaces
    name_parts = []
    idx = 0
    while idx < len(fields) and len(name_parts) < 3:
        field = fields[idx]
        # Check if it looks like a name (uppercase letters, maybe numbers)
        if re.match(r'^[A-Z\s\-]+$', field) and field not in ['M', 'F', 'H']:
            name_parts.append(field)
            idx += 1
        else:
            break
    
    if name_parts:
        horse['horse_name'] = ' '.join(name_parts)
    
    # Extract remaining fields
    remaining = fields[idx:]
    
    # Jockey (usually initials or short name, contains dots often)
    if remaining and '.' in remaining[0]:
        horse['jockey'] = remaining.pop(0)
    elif remaining and re.match(r'^[A-Z]\.[A-Z]', remaining[0]):
        horse['jockey'] = remaining.pop(0)
    elif remaining:
        horse['jockey'] = remaining.pop(0)
    
    # Trainer
    if remaining:
        horse['trainer'] = remaining.pop(0)
    
    # Owner
    if remaining and not re.match(r'^[MFH]\.\d$', remaining[0]):
        horse['owner'] = remaining.pop(0)
    
    # Sex/Age (M.3, F.3, H.3)
    for i, field in enumerate(remaining):
        if re.match(r'^[MFH]\.\d', field):
            horse['sexe_age'] = field
            remaining.pop(i)
            break
    
    # Corde (number after sexe/age)
    if remaining and re.match(r'^\d+$', remaining[0]):
        try:
            horse['corde'] = int(remaining.pop(0))
        except:
            pass
    
    # Weight (contains KG)
    for i, field in enumerate(remaining):
        if 'KG' in field.upper():
            weight_str = field.replace('KG', '').replace('kg', '').replace(',', '.').strip()
            try:
                horse['weight'] = float(weight_str)
            except:
                pass
            remaining.pop(i)
            break
    
    # Performance (dots separated numbers like "1.3.3.5.2")
    for i, field in enumerate(remaining):
        if re.match(r'^\d+\.\d+', field):
            horse['perf'] = field
            remaining.pop(i)
            break
    
    # Gains (numbers)
    for i, field in enumerate(remaining):
        if re.match(r'^\d+$', field) and len(field) >= 4:
            try:
                horse['gains_historical'] = int(field)
            except:
                pass
            remaining.pop(i)
            break
    
    # Odds (contains /)
    odds_found = 0
    for i, field in enumerate(remaining):
        if '/' in field:
            odds_found += 1
            if odds_found == 1:
                horse['odds_paris_turf'] = field
            elif odds_found == 2:
                horse['odds_tierce_magazine'] = field
    
    return horse


def _merge_horse_data(descriptions: Dict, table_data: Dict) -> List[Dict]:
    """Intelligently merge descriptions and table data"""
    merged = []
    
    # Merge all unique horse numbers
    all_numbers = sorted(set(list(descriptions.keys()) + list(table_data.keys())))
    
    for num in all_numbers:
        desc = descriptions.get(num, {})
        table = table_data.get(num, {})
        
        # Start with table data (more complete), add description
        horse = {**table}
        horse.update({k: v for k, v in desc.items() if k not in horse or not horse[k]})
        
        # Ensure we have at least number and name
        if 'horse_number' not in horse:
            horse['horse_number'] = num
        if 'horse_name' not in horse:
            horse['horse_name'] = f"HORSE {num}"
        
        merged.append(horse)
    
    return merged


def _parse_race_header(text: str) -> Dict:
    """Parse main race header information"""
    race_info = {}
    
    # Date
    date_match = re.search(
        r'DU\s+(?:LUNDI|MARDI|MERCREDI|JEUDI|VENDREDI|SAMEDI|DIMANCHE)\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
        text, re.IGNORECASE
    )
    if date_match:
        day, month_name, year = date_match.groups()
        months = {
            'JANVIER': '01', 'FÉVRIER': '02', 'MARS': '03', 'AVRIL': '04',
            'MAI': '05', 'JUIN': '06', 'JUILLET': '07', 'AOÛT': '08',
            'SEPTEMBRE': '09', 'OCTOBRE': '10', 'NOVEMBRE': '11', 'DÉCEMBRE': '12'
        }
        month = months.get(month_name.upper(), '01')
        race_info['race_date'] = f"{year}-{month}-{day.zfill(2)}"
    
    # Race type (QUARTE, TIERCÉ, etc)
    race_type_match = re.search(r'"(QUARTE|TIERCÉ|QUARTÉ|QUINTÉ|TRIO|CLASSIQUE)"', text)
    if race_type_match:
        race_info['race_type_bet'] = race_type_match.group(1)
    
    # Hippodrome
    hippodromes = ['PARISLONGCHAMP', 'VINCENNES', 'AUTEUIL', 'LAVAL', 'LYON',
                   'MARSEILLE', 'BORDEAUX', 'TOULOUSE', 'CHANTILLY', 'DEAUVILLE']
    for hippo in hippodromes:
        if hippo in text.upper():
            race_info['hippodrome'] = hippo
            break
    
    # Condition
    if 'NOCTURNE' in text.upper():
        race_info['condition'] = 'NOCTURNE'
    
    # Distance
    distance_match = re.search(r'(\d+(?:\s+)?\d*)\s*(?:M|METRES)', text, re.IGNORECASE)
    if distance_match:
        dist_str = distance_match.group(1).replace(' ', '')
        try:
            race_info['distance'] = int(dist_str)
        except:
            pass
    
    # Race name
    name_match = re.search(r'(?:SOSAFE|PRIX)\s+(?:PRIX\s+)?([A-Z\s\-\'ÉÈÊÀÂ]+?)(?:\n|\d+\s+CONCURRENTS)', text, re.IGNORECASE)
    if name_match:
        race_info['race_name'] = name_match.group(1).strip()
    
    # Number of competitors
    comp_match = re.search(r'(\d+)\s*CONCURRENTS?', text, re.IGNORECASE)
    if comp_match:
        race_info['num_competitors'] = int(comp_match.group(1))
    
    # Race number
    race_num_match = re.search(r'(\d+)(?:ème|e)\s*COURSE', text, re.IGNORECASE)
    if race_num_match:
        race_info['race_number'] = int(race_num_match.group(1))
    
    # Prize money
    prize_match = re.search(r'([\d\s]+)\s*EUROS\s*\(ENV\.\s*([\d\s]+)\s*F\s*CFA\)', text, re.IGNORECASE)
    if prize_match:
        race_info['prize_money_eur'] = prize_match.group(1).replace(' ', '')
        race_info['prize_money_fcfa'] = prize_match.group(2).replace(' ', '')
    
    # Race time
    time_match = re.search(r'DÉPART\s+DE\s+LA\s+COURSE\s*:\s*(\d{1,2})h\s*(\d{2})', text, re.IGNORECASE)
    if time_match:
        race_info['race_time'] = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
    
    return race_info


def _parse_previous_results(text: str) -> Dict:
    """Parse results from previous race"""
    results = {}
    
    # Previous race date and type
    prev_date_match = re.search(r'"([^"]+)"\s+DU\s+(?:LUNDI|MARDI|MERCREDI|JEUDI|VENDREDI|SAMEDI|DIMANCHE)\s+(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if prev_date_match:
        results['previous_race_type'] = prev_date_match.group(1)
        results['previous_race_date'] = f"{prev_date_match.group(4)}-{prev_date_match.group(3).zfill(2)}-{prev_date_match.group(2).zfill(2)}"
    
    # Arrival
    arrival_match = re.search(r'Arrivée\s*:\s*([\d\s–\-OU]+)', text, re.IGNORECASE)
    if arrival_match:
        numbers = re.findall(r'\d+', arrival_match.group(1))
        results['previous_arrival'] = numbers
    
    return results


def _parse_pronostics_sources(text: str) -> Dict[str, List[int]]:
    """Parse pronostics from external sources"""
    pronostics = {}
    
    sources = [
        ('TURF-FR.COM', r'TURF-FR\.COM\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('L\'ALSACE', r"L'ALSACE\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)"),
        ('VOIX DU NORD', r'VOIX DU NORD.*?\(EDITION\s+\d+\)\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('TURFOMANIA', r'TURFOMANIA\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('EQUIDIA', r'EQUIDIA\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('LE PARISIEN', r'LE PARISIEN\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)')
    ]
    
    for source_name, pattern in sources:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            numbers = [int(n) for n in re.findall(r'\d+', match.group(1))]
            if numbers:
                pronostics[source_name] = numbers
    
    return pronostics


def _parse_classements_section(text: str) -> Dict[str, List[int]]:
    """Parse rankings"""
    classements = {}
    
    rankings = [
        ('FORME', r'FORME\s*:\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('CLASSE', r'CLASSE\s*:\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('PROGRES', r'PROGR[EÉ]S\s*:\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('REGULARITE', r'R[EÉ]GULARIT[EÉ]\s*:\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('FAVORIS', r'FAVORIS\s*:\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('SECONDES_CHANCES', r'SECONDES\s+CHANCES\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('OUTSIDERS', r'OUTSIDERS\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('GROS_OUTSIDERS', r'GROS\s+OUTSIDERS\s*([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
    ]
    
    for name, pattern in rankings:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            numbers = [int(n) for n in re.findall(r'\d+', match.group(1))]
            if numbers:
                classements[name] = numbers
    
    return classements


def _parse_best_of_week(text: str) -> Dict:
    """Parse best trainers and jockeys"""
    best_week = {}
    
    # Trainers in form
    trainers_form = re.findall(r'ENTRAÎN[EU]RS EN FORME\s*:\s*([A-Z\.\s&–\-\n]+?)(?=JOCKEYS|$)', text, re.IGNORECASE)
    if trainers_form:
        names = [n.strip() for n in re.split(r'[–\-]', trainers_form[0]) if n.strip() and len(n.strip()) > 2]
        best_week['trainers_in_form'] = names
    
    # Jockeys in form
    jockeys_form = re.findall(r'JOCKEYS EN FORME\s*:\s*([A-Z\.\s–\-\n]+?)(?=FAVORIS|$)', text, re.IGNORECASE)
    if jockeys_form:
        names = [n.strip() for n in re.split(r'[–\-]', jockeys_form[0]) if n.strip() and len(n.strip()) > 2]
        best_week['jockeys_in_form'] = names
    
    return best_week
