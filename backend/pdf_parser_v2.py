"""PDF Parser using pdfplumber for table extraction"""
import re
import pandas as pd
import numpy as np
import PyPDF2
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

def parse_pdf_with_pdfplumber(file_path: str) -> Tuple[Dict, pd.DataFrame]:
    """
    Parse PDF using pdfplumber to extract tables
    Returns: (race_info, horses_dataframe)
    """
    try:
        import pdfplumber
    except ImportError:
        return {}, pd.DataFrame()
    
    race_info = {}
    horses = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            # First page for race info
            if len(pdf.pages) >= 1:
                page0_text = pdf.pages[0].extract_text()
                race_info = _extract_race_info_from_text(page0_text)
            
            # Second page for horses data (table)
            if len(pdf.pages) >= 2:
                page = pdf.pages[1]
                tables = page.extract_tables()
                
                if tables:
                    horses = _parse_horses_from_table(tables[0])
    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    
    df = pd.DataFrame(horses)
    
    # Convert to native types for JSON serialization
    race_info = convert_to_native_types(race_info)
    
    return race_info, df


def _extract_race_info_from_text(text: str) -> Dict:
    """Extract race information from first page text"""
    race_info = {}
    
    # Extract date (e.g., "DU JEUDI 28 MAI 2026")
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
        month = months.get(month_name.upper(), month_name)
        race_info['race_date'] = f"{year}-{month}-{day.zfill(2)}"
    
    # Extract hippodrome
    hippodromes = ['PARISLONGCHAMP', 'VINCENNES', 'AUTEUIL', 'LAVAL', 'LYON',
                   'MARSEILLE', 'BORDEAUX', 'TOULOUSE', 'CHANTILLY', 'DEAUVILLE']
    for hippo in hippodromes:
        if hippo in text.upper():
            race_info['hippodrome'] = hippo
            break
    
    # Extract distance (e.g., "2 100 METRES")
    distance_match = re.search(r'(\d+(?:\s+)?\d*)\s*(?:M|METRES)', text, re.IGNORECASE)
    if distance_match:
        dist_str = distance_match.group(1).replace(' ', '')
        try:
            race_info['distance'] = int(dist_str)
        except:
            pass
    
    # Extract race type
    for race_type in ['PLAT', 'ATTELE', 'OBSTACLE', 'STEEPLECHASE']:
        if race_type in text.upper():
            race_info['race_type'] = race_type
            break
    
    # Extract race name
    name_match = re.search(r'PRIX\s+([A-Z\s\-\']+?)(?:\n|$)', text, re.IGNORECASE)
    if name_match:
        race_info['race_name'] = name_match.group(1).strip()
    
    # Extract competitors count
    comp_match = re.search(r'(\d+)\s*CONCURRENTS?', text, re.IGNORECASE)
    if comp_match:
        race_info['num_competitors'] = int(comp_match.group(1))
    
    return race_info


def _parse_horses_from_table(table: List[List]) -> List[Dict]:
    """Parse horses from a pdfplumber table"""
    if len(table) < 2:
        return []
    
    header_row = table[0]
    data_row = table[1]
    
    # Find column indices
    num_col = None
    name_col = None
    jockey_col = None
    trainer_col = None
    weight_col = None
    age_col = None
    
    for idx, header in enumerate(header_row):
        h = str(header).upper() if header else ""
        if 'N°' in h:
            num_col = idx
        elif 'CHEVAUX' in h:
            name_col = idx
        elif 'JOCKEYS' in h and 'ENTRAINEURS' not in h:
            jockey_col = idx
        elif 'ENTRAINEURS' in h:
            trainer_col = idx
        elif 'POIDS' in h:
            weight_col = idx
        elif 'AGE' in h or 'SEXE' in h:
            age_col = idx
    
    horses = []
    
    # Extract data by splitting cell contents by newlines
    if num_col is not None:
        num_data = str(data_row[num_col]).split('\n') if data_row[num_col] else []
        name_data = str(data_row[name_col]).split('\n') if name_col and data_row[name_col] else []
        jockey_data = str(data_row[jockey_col]).split('\n') if jockey_col and data_row[jockey_col] else []
        trainer_data = str(data_row[trainer_col]).split('\n') if trainer_col and data_row[trainer_col] else []
        weight_data = str(data_row[weight_col]).split('\n') if weight_col and data_row[weight_col] else []
        age_data = str(data_row[age_col]).split('\n') if age_col and data_row[age_col] else []
        
        # Match by line position
        for i in range(len(num_data)):
            horse_num_str = num_data[i].strip() if i < len(num_data) else ""
            
            try:
                horse_num = int(horse_num_str)
            except:
                continue
            
            horse = {
                'horse_number': int(horse_num),  # Ensure native int
                'horse_name': name_data[i].strip() if i < len(name_data) else "",
            }
            
            if i < len(jockey_data) and jockey_data[i].strip():
                horse['jockey'] = jockey_data[i].strip()
            
            if i < len(trainer_data) and trainer_data[i].strip():
                horse['trainer'] = trainer_data[i].strip()
            
            if i < len(weight_data):
                weight_str = weight_data[i].strip()
                weight_match = re.search(r'([\d,\.]+)', weight_str)
                if weight_match:
                    try:
                        weight = float(weight_match.group(1).replace(',', '.'))
                        horse['weight'] = weight
                    except:
                        pass
            
            if i < len(age_data):
                age_str = age_data[i].strip()
                age_match = re.search(r'(\d+)', age_str)
                if age_match:
                    horse['age'] = int(age_match.group(1))
            
            if horse.get('horse_name'):
                horses.append(horse)
    
    return horses
