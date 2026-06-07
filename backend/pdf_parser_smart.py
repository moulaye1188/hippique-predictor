"""PDF Parser - Use structured table extraction"""
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from hippodrome_coords import get_hippodrome_coords

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


def parse_pdf_smart(file_path: str) -> Tuple[Dict, pd.DataFrame, Dict, Dict, Dict, Dict]:
    """
    SMART PDF parsing using structured table extraction
    NOW RETURNS: race_info, horses_df, pronostics, classements, best_week, arrivals
    """
    try:
        import pdfplumber
    except ImportError:
        return {}, pd.DataFrame(), {}, {}, {}, {}
    
    race_info = {}
    horses_list = []
    pronostics = {}
    classements = {}
    best_week = {}
    arrivals = {}
    
    try:
        with pdfplumber.open(file_path) as pdf:
            # Optimization: Extract text only from first 3 pages (most PDF data is here)
            full_text = ""
            pages_to_extract = min(3, len(pdf.pages))  # Limit to first 3 pages
            for i in range(pages_to_extract):
                full_text += pdf.pages[i].extract_text() + "\n"
            
            # Parse race info from text
            race_info = _parse_race_header(full_text)
            
            # Extract horses from structured tables
            # Handle split/multi-column tables
            if len(pdf.pages) >= 2:
                page = pdf.pages[1]
                tables = page.extract_tables()
                
                if tables:
                    print(f"ℹ️  Found {len(tables)} table(s) on page 2")
                    
                    # Try to merge split tables if they have the same structure
                    merged_tables = _merge_split_tables(tables)
                    
                    # Extract horses from all tables
                    for table_idx, table in enumerate(merged_tables):
                        if table and len(table) > 0:
                            print(f"📋 Processing table {table_idx + 1}...")
                            extracted = _parse_horses_from_table(table)
                            print(f"   ✓ Found {len(extracted)} horses")
                            horses_list.extend(extracted)
                    
                    if horses_list:
                        print(f"✅ Total horses extracted: {len(horses_list)}")
            
            # Parse pronostics and classements from text
            pronostics = _parse_pronostics_sources(full_text)
            classements = _parse_classements_section(full_text)
            best_week = _parse_best_of_week(full_text)
            
            # NEW: Parse race arrivals (results) from PDF
            arrivals = _parse_race_arrivals(full_text)
    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
    
    # Convert to DataFrame
    df = pd.DataFrame(horses_list)
    
    # ✅ NEW: Add GPS coordinates from hippodrome mapping
    if 'hippodrome' in race_info:
        coords = get_hippodrome_coords(race_info['hippodrome'])
        race_info['latitude'] = coords['latitude']
        race_info['longitude'] = coords['longitude']
    
    # ✅ NEW: Ensure date is in correct format for weather API (YYYY-MM-DD)
    if 'race_date' in race_info and race_info['race_date']:
        # race_date should already be YYYY-MM-DD from _parse_race_header
        race_info['date'] = race_info['race_date']
    
    # Convert to native types
    race_info = convert_to_native_types(race_info)
    pronostics = convert_to_native_types(pronostics)
    classements = convert_to_native_types(classements)
    best_week = convert_to_native_types(best_week)
    arrivals = convert_to_native_types(arrivals)
    
    return race_info, df, pronostics, classements, best_week, arrivals


def _parse_race_arrivals(text: str) -> Dict:
    """
    Extract race arrivals (results) from PDF text
    Looks for patterns like "Arrivée : 7 - 11 - 2 - 15"
    """
    arrivals = {}
    
    # Pattern 1: Standard French format "ARRIVÉE : 7 - 11 - 2 - 15"
    patterns = [
        r'ARRIVÉE\s*:\s*(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)',
        r'Arrivée\s*:\s*(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)',
        r'ARRIVÉE\s+(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)',
        r'Arrivée\s+(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            horse_1 = int(match.group(1))
            horse_2 = int(match.group(2))
            horse_3 = int(match.group(3))
            horse_4 = int(match.group(4))
            
            arrivals['1st'] = horse_1
            arrivals['2nd'] = horse_2
            arrivals['3rd'] = horse_3
            arrivals['4th'] = horse_4
            arrivals['quartet'] = [horse_1, horse_2, horse_3, horse_4]
            
            print(f"✅ Race arrivals found: {arrivals['quartet']}")
            return arrivals
    
    # If no arrivals found
    print("⚠️  No race arrivals found in PDF")
    return {}


def _merge_split_tables(tables: List[List]) -> List[List]:
    """
    Detect and merge split/multi-column tables
    
    Some PDFs have horses table split into 2 columns (left + right)
    This function detects and merges them into one coherent table
    
    Args:
        tables: List of tables extracted from PDF page
    
    Returns:
        List of merged tables (handles split column cases)
    """
    if not tables or len(tables) == 0:
        return tables
    
    # If only 1 table, return as-is
    if len(tables) <= 1:
        return tables
    
    # Check if first 2 tables look like split columns
    # They should have same header structure
    if len(tables) >= 2:
        table1 = tables[0]
        table2 = tables[1]
        
        # Verify both have headers (at least 2 rows)
        if len(table1) >= 2 and len(table2) >= 2:
            header1 = table1[0]
            header2 = table2[0]
            
            # Check if headers are similar (both have N° and CHEVAUX columns)
            header1_str = ' '.join([str(h).upper() if h else '' for h in header1])
            header2_str = ' '.join([str(h).upper() if h else '' for h in header2])
            
            has_numero_both = ('N°' in header1_str and 'N°' in header2_str)
            has_chevaux_both = ('CHEVAL' in header1_str and 'CHEVAL' in header2_str)
            
            if has_numero_both and has_chevaux_both:
                print("🔀 Detected split table (2-column format)!")
                print("   Merging left and right columns...")
                
                # Merge by concatenating rows
                # Get number of rows in each table
                rows1 = len(table1) - 1  # exclude header
                rows2 = len(table2) - 1  # exclude header
                
                # Create merged table with same header
                merged = [header1]  # Use header from table1
                
                # If they have same row count, it's a left-right split
                if rows1 == rows2:
                    # Merge row by row: table1 data + table2 data
                    for i in range(1, len(table1)):
                        merged_row = list(table1[i]) if table1[i] else []
                        table2_row = list(table2[i]) if table2[i] else []
                        
                        # Append table2 columns to table1
                        merged_row.extend(table2_row)
                        merged.append(merged_row)
                else:
                    # Different row counts: they're sequential (top-bottom)
                    # Add all rows from table1 then table2
                    for i in range(1, len(table1)):
                        merged.append(table1[i])
                    for i in range(1, len(table2)):
                        merged.append(table2[i])
                
                print(f"   Result: {len(merged)-1} horses total")
                return [merged] + tables[2:]  # Return merged table + rest
    
    # No split detected, return tables as-is
    return tables


def _parse_horses_from_table(table: List[List]) -> List[Dict]:
    """
    Parse horses from structured pdfplumber table
    Handles both single-column and split (2-column) table formats
    """
    horses = []
    
    if len(table) < 2:
        return horses
    
    # Header row
    header = table[0]
    
    # Count expected columns (to detect if we have 2 sets)
    num_header_cols = len(header)
    print(f"📊 Table structure: {num_header_cols} columns")
    
    # Get column indices - try to find ALL matching columns
    col_indices_left = _find_horse_columns(header, 0)
    
    # Check if we have a second set of columns (split table)
    col_indices_right = {}
    if num_header_cols > 12:  # More columns than expected for single table
        print("🔄 Detected possible 2-column format within single table...")
        # Try to find a second set of horse columns
        mid_point = num_header_cols // 2
        col_indices_right = _find_horse_columns(header, mid_point)
    
    # Data rows - each cell contains newline-separated values
    if len(table) > 1:
        data_row = table[1]
        
        # Count horses from left section
        num_horses_left = 0
        if 'number' in col_indices_left:
            first_col_data = str(data_row[col_indices_left['number']])
            num_horses_left = len([x for x in first_col_data.split('\n') if x.strip()])
        
        # Count horses from right section (if exists)
        num_horses_right = 0
        if col_indices_right and 'number' in col_indices_right:
            try:
                first_col_data = str(data_row[col_indices_right['number']])
                num_horses_right = len([x for x in first_col_data.split('\n') if x.strip()])
            except:
                num_horses_right = 0
        
        print(f"   Left section: {num_horses_left} horses")
        if col_indices_right:
            print(f"   Right section: {num_horses_right} horses")
        
        # Extract horses from left section
        for horse_idx in range(num_horses_left):
            horse = _extract_horse_from_row(data_row, col_indices_left, horse_idx)
            if 'horse_name' in horse:
                horses.append(horse)
        
        # Extract horses from right section (if exists)
        if col_indices_right:
            for horse_idx in range(num_horses_right):
                horse = _extract_horse_from_row(data_row, col_indices_right, horse_idx)
                if 'horse_name' in horse:
                    # Adjust horse number if coming from right section
                    if 'horse_number' in horse:
                        horse['horse_number'] += num_horses_left
                    horses.append(horse)
    
    return horses


def _find_horse_columns(header: List, start_idx: int = 0) -> Dict[str, int]:
    """
    Find horse column indices starting from a given position
    Searches for expected column names and returns their indices
    """
    col_indices = {}
    
    # Search in header starting from start_idx
    for idx in range(start_idx, min(start_idx + 15, len(header))):  # Expected max 12 columns for horse data
        if idx >= len(header):
            break
            
        col_name = header[idx]
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
        elif 'CORDE' in col_upper or 'DIST' in col_upper:
            col_indices['corde'] = idx
        elif 'CHRONO' in col_upper or 'POIDS' in col_upper:
            col_indices['weight'] = idx
        elif 'PERF' in col_upper:
            col_indices['perf'] = idx
        elif 'GAINS' in col_upper:
            col_indices['gains'] = idx
        elif 'PARIS' in col_upper or 'TURF' in col_upper:
            col_indices['odds_paris'] = idx
        elif 'TIERCE' in col_upper or 'MAGAZINE' in col_upper:
            col_indices['odds_tierce'] = idx
    
    return col_indices


def _extract_horse_from_row(data_row: List, col_indices: Dict[str, int], horse_idx: int) -> Dict:
    """
    Extract a single horse's data from a data row at given index
    """
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
    
    return horse


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
    """Parse external pronostics - fixed for PDF format"""
    pronostics = {}
    
    sources = [
        ('TURF-FR.COM', r'TURF-FR\.COM\s+([0-9\s\-–]+)(?:\n|$)'),
        ('L\'ALSACE', r"L'ALSACE\s+([0-9\s\-–]+)(?:\n|$)"),
        ('VOIX DU NORD', r'VOIX DU NORD.*?(?:\n\s*)?([0-9\s\-–]+)(?:\n|$)'),
        ('TURFOMANIA', r'TURFOMANIA\s+([0-9\s\-–]+)(?:\n|$)'),
        ('EQUIDIA', r'EQUIDIA\s+([0-9\s\-–]+)(?:\n|$)'),
        ('LE PARISIEN', r'LE PARISIEN\s+([0-9\s\-–]+)(?:\n|$)')
    ]
    
    for source_name, pattern in sources:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            # Extract numbers from matched group (handles dashes and spaces)
            numbers_str = match.group(1)
            numbers = [int(n) for n in re.findall(r'\d+', numbers_str)]
            if numbers:
                pronostics[source_name] = numbers
    
    return pronostics


def _parse_classements_section(text: str) -> Dict[str, List[int]]:
    """Parse rankings from APTITUDES section"""
    classements = {}
    
    # Key rankings under APTITUDES section
    rankings = [
        ('FORME', r'FORME\s*[:–]\s*([0-9\s\-–]+)'),
        ('CLASSE', r'CLASSE\s*[:–]\s*([0-9\s\-–]+)'),
        ('PROGRES', r'PROGR[EÉ]S\s*[:–]\s*([0-9\s\-–]+)'),
        ('REGULARITE', r'R[EÉ]GULARIT[EÉ]\s*[:–]\s*([0-9\s\-–]+)'),
        ('FAVORIS', r'FAVORIS\s*[:–]\s*([0-9\s\-–]+)'),
    ]
    
    for name, pattern in rankings:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Extract all numbers from the matched group
            numbers_str = match.group(1)
            numbers = [int(n) for n in re.findall(r'\d+', numbers_str)]
            if numbers:
                classements[name] = numbers
    
    # Also capture secondary rankings
    secondary = [
        ('SECONDES_CHANCES', r'SECONDES\s+CHANCES\s+([0-9\s\-–]+?)(?:\n|$)'),
        ('OUTSIDERS', r'(?<!\w)OUTSIDERS\s+([0-9\s\-–]+?)(?:\n|$)'),
        ('GROS_OUTSIDERS', r'GROS\s+OUTSIDERS\s+([0-9\s\-–]+?)(?:\n|$)'),
    ]
    
    for name, pattern in secondary:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            numbers = [int(n) for n in re.findall(r'\d+', match.group(1))]
            if numbers:
                classements[name] = numbers
    
    return classements


def _parse_best_of_week(text: str) -> Dict:
    """Parse best trainers/jockeys in form"""
    best_week = {}
    
    # Extract trainers in form (after "ENTRAINEURS EN FORME :")
    trainers_pattern = r'ENTRAÎN[EU]RS\s+EN\s+FORME\s*:\s*([A-Z\.\s&–\-\n]+?)(?=JOCKEYS|$)'
    trainers_match = re.search(trainers_pattern, text, re.IGNORECASE | re.MULTILINE)
    if trainers_match:
        text_block = trainers_match.group(1)
        # Split by dashes and filter valid names
        names = [n.strip() for n in re.split(r'[–\-]', text_block)]
        names = [n for n in names if n and len(n) > 2 and re.search(r'[A-Z]', n)]
        if names:
            best_week['trainers_in_form'] = names
    
    # Extract jockeys in form (after "JOCKEYS EN FORME :")
    jockeys_pattern = r'JOCKEYS\s+EN\s+FORME\s*:\s*([A-Z\.\s–\-\n]+?)(?=FAVORIS|EN\s+FIN|$)'
    jockeys_match = re.search(jockeys_pattern, text, re.IGNORECASE | re.MULTILINE)
    if jockeys_match:
        text_block = jockeys_match.group(1)
        # Split by dashes and filter valid names
        names = [n.strip() for n in re.split(r'[–\-]', text_block)]
        names = [n for n in names if n and len(n) > 2 and re.search(r'[A-Z]', n)]
        if names:
            best_week['jockeys_in_form'] = names
    
    return best_week
