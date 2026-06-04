"""PDF Parser FINAL - Complete and robust extraction"""
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


def parse_pdf_final(file_path: str) -> Tuple[Dict, pd.DataFrame, Dict, Dict, Dict]:
    """
    FINAL complete PDF parsing
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
            # Extract all text from all pages
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            # Parse race info
            race_info = _parse_race_header(full_text)
            
            # Parse horses
            horses_list = _parse_horses_from_text(full_text)
            
            # Parse results from previous race
            results = _parse_previous_results(full_text)
            race_info.update(results)
            
            # Parse pronostics (external sources)
            pronostics = _parse_pronostics_sources(full_text)
            
            # Parse classements (rankings)
            classements = _parse_classements_section(full_text)
            
            # Parse best of week
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


def _parse_race_header(text: str) -> Dict:
    """Parse main race header information"""
    race_info = {}
    
    # Date: "QUARTE" DU JEUDI 28 MAI 2026
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
    
    # Race type: QUARTE, TIERCÉ, etc.
    race_type_match = re.search(r'"(QUARTE|TIERCÉ|QUARTÉ|QUINTÉ|TRIO|CLASSIQUE)"', text)
    if race_type_match:
        race_info['race_type_bet'] = race_type_match.group(1)
    
    # Hippodrome
    hippodromes = ['PARISLONGCHAMP', 'VINCENNES', 'AUTEUIL', 'LAVAL', 'LYON',
                   'MARSEILLE', 'BORDEAUX', 'TOULOUSE', 'CHANTILLY', 'DEAUVILLE',
                   'SAINT-CLOUD', 'LONGCHAMP']
    for hippo in hippodromes:
        if hippo in text.upper():
            race_info['hippodrome'] = hippo
            break
    
    # Race condition (NOCTURNE, etc)
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
    
    # Race name: SOSAFE PRIX DES EPINETTES
    name_match = re.search(r'(?:SOSAFE|PRIX)\s+(?:PRIX\s+)?([A-Z\s\-\'ÉÈÊÀÂ]+?)(?:\n|\d+\s+CONCURRENTS)', text, re.IGNORECASE)
    if name_match:
        race_info['race_name'] = name_match.group(1).strip()
    
    # Number of competitors
    comp_match = re.search(r'(\d+)\s*CONCURRENTS?', text, re.IGNORECASE)
    if comp_match:
        race_info['num_competitors'] = int(comp_match.group(1))
    
    # Race number: 6ème COURSE
    race_num_match = re.search(r'(\d+)(?:ème|e)\s*COURSE', text, re.IGNORECASE)
    if race_num_match:
        race_info['race_number'] = int(race_num_match.group(1))
    
    # Prize money: 52 800 EUROS
    prize_match = re.search(r'([\d\s]+)\s*EUROS\s*\(ENV\.\s*([\d\s]+)\s*F\s*CFA\)', text, re.IGNORECASE)
    if prize_match:
        race_info['prize_money_eur'] = prize_match.group(1).replace(' ', '')
        race_info['prize_money_fcfa'] = prize_match.group(2).replace(' ', '')
    
    # Race time
    time_match = re.search(r'DÉPART\s+DE\s+LA\s+COURSE\s*:\s*(\d{1,2})h\s*(\d{2})', text, re.IGNORECASE)
    if time_match:
        race_info['race_time'] = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
    
    return race_info


def _parse_horses_from_text(text: str) -> List[Dict]:
    """Parse horses from text descriptions and table data"""
    horses = []
    
    # Extract horse descriptions first (1 - NAME : Description...)
    descriptions = {}
    desc_pattern = r'(\d+)\s*-\s*([A-Z\s]+?)\s*:\s*([^0-9].*?)(?=\n\d+\s*-|$)'
    for match in re.finditer(desc_pattern, text, re.IGNORECASE | re.DOTALL):
        num = int(match.group(1))
        name = match.group(2).strip()
        desc = match.group(3).strip().replace('\n', ' ')
        descriptions[num] = {'horse_name': name, 'description': desc}
    
    # Extract table data - look for lines with horse details
    # Pattern: number HORSENAME JOCKEY TRAINER OWNER SEXAGE CORDE WEIGHT PERF GAINS PARIS TIERCE
    table_lines = re.findall(
        r'(\d{2})\s+([A-Z\s]+?)\s+([A-Z\.]+?)\s+([A-Z\.\s&]+?)\s+([A-Z\.\s&]+?)\s+([MF]\.?\d)\s+(\d+)\s+([\d,\.]+)\.KG\s+([\d\.]+)\s+(\d+)\s+(\d+/\d+)\s+(\d+/\d+)',
        text
    )
    
    for match in table_lines:
        num = int(match[0])
        horse = {
            'horse_number': num,
            'horse_name': match[1].strip(),
            'jockey': match[2].strip(),
            'trainer': match[3].strip(),
            'owner': match[4].strip(),
            'sexe_age': match[5].strip(),
            'corde': int(match[6]),
            'weight': float(match[7].replace(',', '.')),
            'perf': match[8],  # e.g., "1.3.3.5.2"
            'gains_historical': int(match[9]),
            'odds_paris_turf': match[10],
            'odds_tierce_magazine': match[11],
        }
        
        # Parse sexe and age
        if '.' in horse['sexe_age']:
            parts = horse['sexe_age'].split('.')
            horse['sexe'] = parts[0]
            try:
                horse['age'] = int(parts[1])
            except:
                pass
        
        # Add description if available
        if num in descriptions:
            horse['description'] = descriptions[num]['description']
        
        horses.append(horse)
    
    return horses


def _parse_previous_results(text: str) -> Dict:
    """Parse results from previous race"""
    results = {}
    
    # "4+1" DU DIMANCHE 24/05/2026
    prev_date_match = re.search(r'"([^"]+)"\s+DU\s+(?:LUNDI|MARDI|MERCREDI|JEUDI|VENDREDI|SAMEDI|DIMANCHE)\s+(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if prev_date_match:
        results['previous_race_type'] = prev_date_match.group(1)
        results['previous_race_date'] = f"{prev_date_match.group(4)}-{prev_date_match.group(3).zfill(2)}-{prev_date_match.group(2).zfill(2)}"
    
    # Arrivée: 4 – 1 – 5 – 2 – 7 OU 4 – 1 – 5 – 7 – 2
    arrival_match = re.search(r'Arrivée\s*:\s*([\d\s–\-OU]+)', text, re.IGNORECASE)
    if arrival_match:
        arrival_str = arrival_match.group(1)
        numbers = re.findall(r'\d+', arrival_str)
        results['previous_arrival'] = numbers
    
    # Gains information
    gains_matches = re.findall(r'(Ordre|Désordre|Bonus|Couplé.*?)\s*:\s*([\d\s]+)\s*F', text, re.IGNORECASE)
    if gains_matches:
        results['previous_gains'] = {match[0].lower(): match[1].replace(' ', '') for match in gains_matches}
    
    return results


def _parse_pronostics_sources(text: str) -> Dict[str, List[int]]:
    """Parse pronostics from external prediction sources"""
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
            numbers_str = match.group(1)
            numbers = [int(n) for n in re.findall(r'\d+', numbers_str)]
            if numbers:
                pronostics[source_name] = numbers
    
    return pronostics


def _parse_classements_section(text: str) -> Dict[str, List[int]]:
    """Parse rankings and classifications"""
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
    """Parse best trainers and jockeys of the week"""
    best_week = {}
    
    # Best trainers
    trainers_match = re.search(r'ENTRAINEURS\s*\n(.*?)(?=JOCKEYS|$)', text, re.IGNORECASE | re.DOTALL)
    if trainers_match:
        trainers_text = trainers_match.group(1)
        trainers = []
        for match in re.finditer(r'(\d+)\s*–\s*([A-Z\.\s&]+?)(?=\n|$)', trainers_text):
            trainers.append({
                'rank': int(match.group(1)),
                'name': match.group(2).strip()
            })
        if trainers:
            best_week['best_trainers'] = trainers
    
    # Best jockeys
    jockeys_match = re.search(r'JOCKEYS\s*\n(.*?)(?=ENTRAINEURS EN FORME|$)', text, re.IGNORECASE | re.DOTALL)
    if jockeys_match:
        jockeys_text = jockeys_match.group(1)
        jockeys = []
        for match in re.finditer(r'(\d+)\s*–\s*([A-Z\.\s]+?)(?=\n|$)', jockeys_text):
            jockeys.append({
                'rank': int(match.group(1)),
                'name': match.group(2).strip()
            })
        if jockeys:
            best_week['best_jockeys'] = jockeys
    
    # Best trainers in form
    trainers_form = re.findall(r'ENTRAÎN[EU]RS EN FORME\s*:\s*([A-Z\.\s&–\-\n]+?)(?=JOCKEYS|$)', text, re.IGNORECASE)
    if trainers_form:
        names = [n.strip() for n in re.split(r'[–\-]', trainers_form[0]) if n.strip()]
        best_week['trainers_in_form'] = names
    
    # Best jockeys in form
    jockeys_form = re.findall(r'JOCKEYS EN FORME\s*:\s*([A-Z\.\s–\-\n]+?)(?=FAVORIS|$)', text, re.IGNORECASE)
    if jockeys_form:
        names = [n.strip() for n in re.split(r'[–\-]', jockeys_form[0]) if n.strip()]
        best_week['jockeys_in_form'] = names
    
    return best_week
