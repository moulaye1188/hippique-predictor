"""PDF Parser V3 - Complete extraction of all race data"""
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

def convert_to_native_types(obj):
    """Convert NumPy types to native Python types for JSON serialization"""
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

def parse_pdf_complete(file_path: str) -> Tuple[Dict, pd.DataFrame, Dict, Dict]:
    """
    Complete PDF parsing - extracts everything
    Returns: (race_info, horses_df, pronostics_dict, classements_dict)
    """
    try:
        import pdfplumber
    except ImportError:
        return {}, pd.DataFrame(), {}, {}
    
    race_info = {}
    horses_list = []
    pronostics = {}
    classements = {}
    
    try:
        with pdfplumber.open(file_path) as pdf:
            # Page 0: Race info + horses details (text descriptions)
            if len(pdf.pages) >= 1:
                page0_text = pdf.pages[0].extract_text()
                race_info = _extract_race_info(page0_text)
            
            # Page 1: Main table with all horse details
            if len(pdf.pages) >= 2:
                page1 = pdf.pages[1]
                tables = page1.extract_tables()
                if tables:
                    horses_list = _extract_horses_from_table(tables)
            
            # Page 2: Pronostics + Classements
            if len(pdf.pages) >= 3:
                page2_text = pdf.pages[2].extract_text()
                pronostics = _extract_pronostics(page2_text)
                classements = _extract_classements(page2_text)
    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
    
    df = pd.DataFrame(horses_list)
    race_info = convert_to_native_types(race_info)
    
    return race_info, df, pronostics, classements


def _extract_race_info(text: str) -> Dict:
    """Extract race header information"""
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
    name_match = re.search(r'(?:PRIX|SOSAFÉ)\s+([A-Z\s\-\'ÉÈÊÀÂ]+?)(?:\n|$)', text, re.IGNORECASE)
    if name_match:
        race_info['race_name'] = name_match.group(1).strip()
    
    # Competitors count
    comp_match = re.search(r'(\d+)\s*CONCURRENTS?', text, re.IGNORECASE)
    if comp_match:
        race_info['num_competitors'] = int(comp_match.group(1))
    
    # Prize money
    prize_match = re.search(r'([\d\s]+)\s*EUROS', text, re.IGNORECASE)
    if prize_match:
        race_info['prize_money'] = prize_match.group(1).replace(' ', '')
    
    return race_info


def _extract_horses_from_table(tables: List) -> List[Dict]:
    """Extract horses with full details from main table"""
    horses = []
    
    if not tables or len(tables) < 1:
        return horses
    
    table = tables[0]
    if len(table) < 3:
        return horses
    
    # Header row - find column indices
    header = table[0]
    col_map = _map_table_columns(header)
    
    # Data rows (skip header and first row if it's part of header)
    for row_idx in range(1, len(table)):
        row = table[row_idx]
        horse = _parse_horse_row(row, col_map)
        if horse and horse.get('horse_name'):
            horses.append(horse)
    
    return horses


def _map_table_columns(header: List) -> Dict[str, int]:
    """Map column names to indices"""
    col_map = {}
    
    for idx, cell in enumerate(header):
        if not cell:
            continue
        
        cell_upper = str(cell).upper()
        
        if 'N°' in cell_upper or 'NUM' in cell_upper:
            col_map['number'] = idx
        elif 'CHEVAUX' in cell_upper or 'CHEVAL' in cell_upper:
            col_map['name'] = idx
        elif 'JOCKEY' in cell_upper:
            col_map['jockey'] = idx
        elif 'ENTRAÎNEUR' in cell_upper or 'ENTRAINEUR' in cell_upper:
            col_map['trainer'] = idx
        elif 'PROPRIÉTAIRE' in cell_upper or 'PROPRIETAIRE' in cell_upper:
            col_map['owner'] = idx
        elif 'SEXE' in cell_upper:
            col_map['sexe_age'] = idx
        elif 'CORDE' in cell_upper:
            col_map['corde'] = idx
        elif 'POIDS' in cell_upper:
            col_map['weight'] = idx
        elif 'PERF' in cell_upper:
            col_map['perf'] = idx
        elif 'GAINS' in cell_upper:
            col_map['gains'] = idx
        elif 'PARIS' in cell_upper or 'TURF' in cell_upper:
            col_map['paris_turf'] = idx
        elif 'TIERCÉ' in cell_upper or 'TIERCE' in cell_upper or 'MAGAZINE' in cell_upper:
            col_map['tierce_mag'] = idx
    
    return col_map


def _parse_horse_row(row: List, col_map: Dict[str, int]) -> Dict:
    """Parse a single horse row"""
    horse = {}
    
    # Number
    if 'number' in col_map and col_map['number'] < len(row):
        try:
            horse['horse_number'] = int(str(row[col_map['number']]).strip())
        except:
            pass
    
    # Name
    if 'name' in col_map and col_map['name'] < len(row):
        horse['horse_name'] = str(row[col_map['name']]).strip()
    
    # Jockey
    if 'jockey' in col_map and col_map['jockey'] < len(row):
        horse['jockey'] = str(row[col_map['jockey']]).strip()
    
    # Trainer
    if 'trainer' in col_map and col_map['trainer'] < len(row):
        horse['trainer'] = str(row[col_map['trainer']]).strip()
    
    # Owner
    if 'owner' in col_map and col_map['owner'] < len(row):
        horse['owner'] = str(row[col_map['owner']]).strip()
    
    # Sexe/Age (e.g., "M,3" = Male, 3 years)
    if 'sexe_age' in col_map and col_map['sexe_age'] < len(row):
        sexe_age = str(row[col_map['sexe_age']]).strip()
        if ',' in sexe_age:
            sexe, age = sexe_age.split(',')
            horse['sexe'] = sexe.strip()
            try:
                horse['age'] = int(age.strip())
            except:
                pass
    
    # Corde (starting position)
    if 'corde' in col_map and col_map['corde'] < len(row):
        try:
            horse['corde'] = int(str(row[col_map['corde']]).strip())
        except:
            pass
    
    # Weight
    if 'weight' in col_map and col_map['weight'] < len(row):
        weight_str = str(row[col_map['weight']]).strip()
        weight_match = re.search(r'([\d,\.]+)', weight_str)
        if weight_match:
            try:
                horse['weight'] = float(weight_match.group(1).replace(',', '.'))
            except:
                pass
    
    # Performance (e.g., "13.3.2" = 1st, 3rd, 2nd recent races)
    if 'perf' in col_map and col_map['perf'] < len(row):
        horse['perf'] = str(row[col_map['perf']]).strip()
    
    # Gains (historical)
    if 'gains' in col_map and col_map['gains'] < len(row):
        gains_str = str(row[col_map['gains']]).strip()
        try:
            horse['gains_historical'] = int(gains_str.replace(' ', ''))
        except:
            pass
    
    # Paris Turf odds
    if 'paris_turf' in col_map and col_map['paris_turf'] < len(row):
        horse['odds_paris_turf'] = str(row[col_map['paris_turf']]).strip()
    
    # Tiercé Magazine odds
    if 'tierce_mag' in col_map and col_map['tierce_mag'] < len(row):
        horse['odds_tierce_mag'] = str(row[col_map['tierce_mag']]).strip()
    
    return horse


def _extract_pronostics(text: str) -> Dict[str, List[int]]:
    """Extract pronostics from external sources"""
    pronostics = {}
    
    sources = [
        ('TURF-FR.COM', r'TURF-FR\.COM\s+([0-9\s\-]+)'),
        ('L\'ALSACE', r"L'ALSACE\s+([0-9\s\-]+)"),
        ('VOIX DU NORD', r'VOIX DU NORD.*?\(EDITION \d+\)\s+([0-9\s\-]+)'),
        ('TURFOMANIA', r'TURFOMANIA\s+([0-9\s\-]+)'),
        ('EQUIDIA', r'EQUIDIA\s+([0-9\s\-]+)'),
        ('LE PARISIEN', r'LE PARISIEN\s+([0-9\s\-]+)')
    ]
    
    for source_name, pattern in sources:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            numbers_str = match.group(1)
            numbers = [int(n) for n in re.findall(r'\d+', numbers_str)]
            if numbers:
                pronostics[source_name] = numbers
    
    return pronostics


def _extract_classements(text: str) -> Dict[str, Dict]:
    """Extract classements and rankings"""
    classements = {}
    
    # FORME
    forme_match = re.search(r'FORME\s*:\s*([0-9\-\s]+)', text, re.IGNORECASE)
    if forme_match:
        classements['FORME'] = [int(n) for n in re.findall(r'\d+', forme_match.group(1))]
    
    # CLASSE
    classe_match = re.search(r'CLASSE\s*:\s*([0-9\-\s]+)', text, re.IGNORECASE)
    if classe_match:
        classements['CLASSE'] = [int(n) for n in re.findall(r'\d+', classe_match.group(1))]
    
    # PROGRÈS
    progres_match = re.search(r'PROGRÈS\s*:\s*([0-9\-\s]+)', text, re.IGNORECASE)
    if progres_match:
        classements['PROGRES'] = [int(n) for n in re.findall(r'\d+', progres_match.group(1))]
    
    # RÉGULARITÉ
    regularity_match = re.search(r'RÉGULARITÉ\s*:\s*([0-9\-\s]+)', text, re.IGNORECASE)
    if regularity_match:
        classements['REGULARITE'] = [int(n) for n in re.findall(r'\d+', regularity_match.group(1))]
    
    # SECONDES CHANCES
    secondes_match = re.search(r'SECONDES CHANCES\s+([0-9\s\-]+)', text, re.IGNORECASE)
    if secondes_match:
        classements['SECONDES_CHANCES'] = [int(n) for n in re.findall(r'\d+', secondes_match.group(1))]
    
    # OUTSIDERS
    outsiders_match = re.search(r'OUTSIDERS\s+([0-9\s\-]+)', text, re.IGNORECASE)
    if outsiders_match:
        classements['OUTSIDERS'] = [int(n) for n in re.findall(r'\d+', outsiders_match.group(1))]
    
    # GROS OUTSIDERS
    gros_outsiders_match = re.search(r'GROS OUTSIDERS\s+([0-9\s\-]+)', text, re.IGNORECASE)
    if gros_outsiders_match:
        classements['GROS_OUTSIDERS'] = [int(n) for n in re.findall(r'\d+', gros_outsiders_match.group(1))]
    
    # FAVORIS
    favoris_match = re.search(r'FAVORIS\s*:\s*([0-9\-\s]+)', text, re.IGNORECASE)
    if favoris_match:
        classements['FAVORIS'] = [int(n) for n in re.findall(r'\d+', favoris_match.group(1))]
    
    return classements
