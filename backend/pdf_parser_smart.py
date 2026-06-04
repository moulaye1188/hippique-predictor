"""PDF Parser - Use structured table extraction"""
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

def convert_to_native_types(obj):
    """Convert NumPy/pandas types to native Python types"""
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


def parse_pdf_smart(file_path: str) -> Tuple[Dict, pd.DataFrame, Dict, Dict, Dict]:
    """
    SMART PDF parsing using structured table extraction
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
            # Extract all text for metadata
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            # Parse race info from text
            race_info = _parse_race_header(full_text)
            
            # Extract horses from structured table
            if len(pdf.pages) >= 2:
                page1 = pdf.pages[1]
                tables = page1.extract_tables()
                
                # Table 0 contains all horse data
                if tables and len(tables) > 0 and tables[0]:
                    horses_list = _parse_horses_from_table(tables[0])
            
            # Parse pronostics and classements from text
            pronostics = _parse_pronostics_sources(full_text)
            classements = _parse_classements_section(full_text)
            best_week = _parse_best_of_week(full_text)
    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
    
    # Convert to DataFrame
    df = pd.DataFrame(horses_list)
    
    # Convert to native types
    race_info = convert_to_native_types(race_info)
    pronostics = convert_to_native_types(pronostics)
    classements = convert_to_native_types(classements)
    best_week = convert_to_native_types(best_week)
    
    return race_info, df, pronostics, classements, best_week


def _parse_horses_from_table(table: List[List]) -> List[Dict]:
    """Parse horses from structured pdfplumber table"""
    horses = []
    
    if len(table) < 2:
        return horses
    
    # Header row
    header = table[0]
    
    # Get column indices
    col_indices = {}
    for idx, col_name in enumerate(header):
        if col_name is None:
            continue
        col_upper = str(col_name).upper()
        
        if 'N°' in col_upper:
            col_indices['number'] = idx
        elif 'CHEVAUX' in col_upper:
            col_indices['name'] = idx
        elif 'JOCKEY' in col_upper:
            col_indices['jockey'] = idx
        elif 'ENTRAINEUR' in col_upper or 'ENTRÂINEUR' in col_upper:
            col_indices['trainer'] = idx
        elif 'PROPRIETAIRE' in col_upper:
            col_indices['owner'] = idx
        elif 'SEXE' in col_upper:
            col_indices['sexe_age'] = idx
        elif 'CORDE' in col_upper:
            col_indices['corde'] = idx
        elif 'POIDS' in col_upper:
            col_indices['weight'] = idx
        elif 'PERF' in col_upper:
            col_indices['perf'] = idx
        elif 'GAINS' in col_upper:
            col_indices['gains'] = idx
        elif 'PARIS' in col_upper or 'TURF' in col_upper:
            col_indices['odds_paris'] = idx
        elif 'TIERCE' in col_upper or 'MAGAZINE' in col_upper:
            col_indices['odds_tierce'] = idx
    
    # Data rows - each cell contains newline-separated values
    if len(table) > 1:
        data_row = table[1]
        
        # Split each cell by newlines to get individual horses
        num_horses = 0
        
        # Count how many horses (from the first column)
        if 'number' in col_indices:
            first_col_data = str(data_row[col_indices['number']])
            num_horses = len([x for x in first_col_data.split('\n') if x.strip()])
        
        # Extract each horse
        for horse_idx in range(num_horses):
            horse = {'horse_number': horse_idx + 1}
            
            for field, col_idx in col_indices.items():
                if col_idx >= len(data_row):
                    continue
                
                cell_value = data_row[col_idx]
                if cell_value is None:
                    continue
                
                # Split cell by newlines and get the horse_idx-th value
                values = str(cell_value).split('\n')
                if horse_idx < len(values):
                    value = values[horse_idx].strip()
                    
                    if not value:
                        continue
                    
                    if field == 'number':
                        try:
                            horse['horse_number'] = int(value)
                        except:
                            pass
                    elif field == 'name':
                        horse['horse_name'] = value
                    elif field == 'jockey':
                        horse['jockey'] = value
                    elif field == 'trainer':
                        horse['trainer'] = value
                    elif field == 'owner':
                        horse['owner'] = value
                    elif field == 'sexe_age':
                        horse['sexe_age'] = value
                    elif field == 'corde':
                        try:
                            horse['corde'] = int(value)
                        except:
                            pass
                    elif field == 'weight':
                        weight_str = value.replace('KG', '').replace('kg', '').replace(',', '.').strip()
                        try:
                            horse['weight'] = float(weight_str)
                        except:
                            pass
                    elif field == 'perf':
                        horse['perf'] = value
                    elif field == 'gains':
                        try:
                            horse['gains_historical'] = int(value.replace(' ', ''))
                        except:
                            pass
                    elif field == 'odds_paris':
                        horse['odds_paris_turf'] = value
                    elif field == 'odds_tierce':
                        horse['odds_tierce_magazine'] = value
            
            # Only add if we have at least number and name
            if 'horse_name' in horse:
                horses.append(horse)
    
    return horses


def _parse_race_header(text: str) -> Dict:
    """Parse race info from text"""
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
    
    # Hippodrome
    hippodromes = ['PARISLONGCHAMP', 'VINCENNES', 'AUTEUIL', 'LAVAL', 'LYON',
                   'MARSEILLE', 'BORDEAUX', 'TOULOUSE', 'CHANTILLY', 'DEAUVILLE']
    for hippo in hippodromes:
        if hippo in text.upper():
            race_info['hippodrome'] = hippo
            break
    
    # Distance
    distance_match = re.search(r'(\d+(?:\s+)?\d*)\s*(?:M|METRES)', text, re.IGNORECASE)
    if distance_match:
        dist_str = distance_match.group(1).replace(' ', '')
        try:
            race_info['distance'] = int(dist_str)
        except:
            pass
    
    # Race type
    for race_type in ['PLAT', 'ATTELE', 'OBSTACLE', 'STEEPLECHASE']:
        if race_type in text.upper():
            race_info['race_type'] = race_type
            break
    
    # Race name
    name_match = re.search(r'(?:SOSAFE|PRIX)\s+(?:PRIX\s+)?([A-Z\s\-\'ÉÈÊÀÂ]+?)(?:\n|\d+\s+CONCURRENTS)', text, re.IGNORECASE)
    if name_match:
        race_info['race_name'] = name_match.group(1).strip()
    
    # Competitors
    comp_match = re.search(r'(\d+)\s*CONCURRENTS?', text, re.IGNORECASE)
    if comp_match:
        race_info['num_competitors'] = int(comp_match.group(1))
    
    return race_info


def _parse_pronostics_sources(text: str) -> Dict[str, List[int]]:
    """Parse external pronostics"""
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
        ('SECONDES_CHANCES', r'SECONDES\s+CHANCES\s+([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('OUTSIDERS', r'(?:^|\n)OUTSIDERS\s+([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
        ('GROS_OUTSIDERS', r'GROS\s+OUTSIDERS\s+([0-9\s\-–]+?)(?=\n[A-Z]|\Z)'),
    ]
    
    for name, pattern in rankings:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            numbers = [int(n) for n in re.findall(r'\d+', match.group(1))]
            if numbers:
                classements[name] = numbers
    
    return classements


def _parse_best_of_week(text: str) -> Dict:
    """Parse best trainers/jockeys"""
    best_week = {}
    
    # Extract trainers in form
    trainers_form = re.findall(r'ENTRAÎN[EU]RS EN FORME\s*:\s*([A-Z\.\s&–\-\n]+?)(?=JOCKEYS|$)', text, re.IGNORECASE)
    if trainers_form:
        names = [n.strip() for n in re.split(r'[–\-]', trainers_form[0]) if n.strip() and len(n.strip()) > 2]
        best_week['trainers_in_form'] = names
    
    # Extract jockeys in form
    jockeys_form = re.findall(r'JOCKEYS EN FORME\s*:\s*([A-Z\.\s–\-\n]+?)(?=FAVORIS|$)', text, re.IGNORECASE)
    if jockeys_form:
        names = [n.strip() for n in re.split(r'[–\-]', jockeys_form[0]) if n.strip() and len(n.strip()) > 2]
        best_week['jockeys_in_form'] = names
    
    return best_week
