import pandas as pd
import numpy as np
from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional
import PyPDF2
import io

class DataImporter:
    """Import and parse horse race data from various formats"""
    
    EXPECTED_COLUMNS = [
        'horse_number', 'horse_name', 'description', 'odds', 
        'age', 'wins', 'podiums', 'distance_pref', 'terrain_pref',
        'jockey', 'trainer', 'weight', 'result_position'
    ]
    
    @staticmethod
    def import_csv(file_path: str) -> pd.DataFrame:
        """Import data from CSV file"""
        try:
            df = pd.read_csv(file_path)
            return DataImporter._clean_dataframe(df)
        except Exception as e:
            raise ValueError(f"Error reading CSV: {e}")
    
    @staticmethod
    def import_pdf_text(file_path: str) -> str:
        """Extract text from PDF with structured layout detection"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n---PAGE_BREAK---\n"
            return text
        except Exception as e:
            raise ValueError(f"Error reading PDF: {e}")
    
    @staticmethod
    def parse_text_data(text: str) -> pd.DataFrame:
        """Parse horse race data from free-form or structured text"""
        # Try structured parsing first (tabular format from Le Journal Hippique)
        horses = DataImporter._parse_tabular_format(text)
        if horses:
            return pd.DataFrame(horses)
        
        # Fallback to free-form parsing
        races = []
        lines = text.split('\n')
        
        current_horse = {}
        
        for line in lines:
            line = line.strip()
            if not line or '---PAGE_BREAK---' in line:
                if current_horse and 'horse_name' in current_horse:
                    races.append(current_horse)
                    current_horse = {}
                continue
            
            # Parse horse number at line start (01, 02, etc.)
            if re.match(r'^\d{1,2}\s+', line):
                if current_horse and 'horse_name' in current_horse:
                    races.append(current_horse)
                match = re.match(r'^(\d{1,2})\s+(.+)', line)
                if match:
                    current_horse = {
                        'horse_number': int(match.group(1)),
                        'horse_name': match.group(2).strip()
                    }
            
            # Parse odds (patterns like "77/1", "7/1", etc.)
            odds_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', line)
            if odds_match and current_horse:
                current_horse['odds'] = f"{odds_match.group(1)}/{odds_match.group(2)}"
            
            # Parse result position (format: "1/1", "2-1", "3-2", etc.)
            result_match = re.search(r'(?:place|position|rank|arrivee|arrive):\s*(\d+)', line, re.IGNORECASE)
            if result_match and current_horse:
                current_horse['result_position'] = int(result_match.group(1))
            
            # Parse description (remaining text)
            if current_horse and 'description' not in current_horse:
                if not odds_match and not result_match and len(line) > 3:
                    current_horse['description'] = line
        
        if current_horse and 'horse_name' in current_horse:
            races.append(current_horse)
        
        return pd.DataFrame(races) if races else pd.DataFrame()
    
    @staticmethod
    def _parse_tabular_format(text: str) -> List[Dict]:
        """
        Parse structured tabular format from Le Journal Hippique PDF
        The PDF has a complex layout:
        - PAGE 0: Analysis text with horse descriptions
        - PAGE 1: Main data table with columns:
          N° | AGE | CORDE | POIDS | PERF | GAINS | CHEVAUX | JOCKEYS | ENTRAINEURS | PROPRIETAIRES
        
        Key: Look for lines with format "01  M.3  2  62.KG  1.3.3.5.2  39 618  MUST BAY  C&Y.LERNER  R.THOMAS"
        Strategy: Find lines that START with two digits (horse number 01-20)
        """
        horses = []
        lines = text.split('\n')
        
        # Skip everything before the actual data table
        # The table starts after "N°" header and contains lines like "01  M.3  2  62.KG ..."
        # We look for the pattern where a line starts with 2 digits (horse number)
        
        table_started = False
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            # Skip header and analysis sections
            if any(x in line_stripped for x in 
                   ['CONCURRENTS', 'METRES', 'EUROS', 'QUARTE', 'NOCTURNE', 'PRIX',
                    'Handicapé', 'S\'il trouve', 'Cette fois', 'PMU', 'LES MEILLEURS',
                    'HORAIRES', 'ARRET', 'DEPART', 'TURF', 'TIERCE', 'MAGAZINE',
                    'ENTRAINEURS EN FORME', 'JOCKEYS EN FORME', 'FAVORIS',
                    'SECONDES CHANCES', 'OUTSIDERS', 'FORME :', 'CLASSE :', 'PROGRES',
                    'REGULARITE', 'APTITUDES', 'CLASSEMENT', 'CHEVAUX JOCKEYS ENTRAINEURS']):
                continue
            
            # Detect table start: look for "01  M.3  ..." pattern or "N°" header
            if 'N°' in line_stripped and ('CHEVAUX' in line_stripped or 'AGE' in line_stripped):
                table_started = True
                continue
            
            # Parse table lines
            if table_started:
                # Stop at end markers
                if 'LES MEILLEURS' in line_stripped or 'HORAIRES' in line_stripped or \
                   'ARRET' in line_stripped or '1 2 3 4 5 6 7 8 9' in line_stripped:
                    break
                
                # Match lines starting with horse number (01-20)
                horse_match = re.match(r'^(\d{1,2})\s+(.+)$', line_stripped)
                if not horse_match:
                    continue
                
                horse_num = int(horse_match.group(1))
                
                # Validate horse number is in reasonable range
                if not (1 <= horse_num <= 25):
                    continue
                
                rest = horse_match.group(2)
                
                # Split by multiple spaces or tabs
                parts = re.split(r'\s{2,}|\t+', rest)
                
                if len(parts) < 5:
                    continue
                
                # Format: N° | AGE | CORDE | POIDS | PERF | GAINS | CHEVAUX | JOCKEYS | ENTRAINEURS | PROPRIETAIRES
                # After splitting: parts[0]=age, parts[1]=corde, parts[2]=poids, ..., parts[5+]=horse_name, jockey, trainer, owner
                
                # Find horse name - it should be all caps and come after GAINS
                horse_name = None
                jockey = None
                trainer = None
                owner = None
                age = None
                weight = None
                
                # Parse age (format: M.3, F.3, H.3)
                if len(parts) > 0:
                    age_str = parts[0].strip()
                    age_match = re.search(r'(\d+)', age_str)
                    if age_match:
                        age = int(age_match.group(1))
                
                # Parse weight (format: 62.KG, 59.KG)
                if len(parts) > 2:
                    weight_str = parts[2].strip()
                    weight_match = re.search(r'([\d.]+)', weight_str)
                    if weight_match:
                        try:
                            weight = float(weight_match.group(1))
                        except:
                            pass
                
                # Horse name is typically parts[5] or later (after GAINS column which is numeric)
                # Look for the first part that's NOT purely numeric/dots
                horse_idx = -1
                for i in range(5, len(parts)):
                    part = parts[i].strip()
                    # Horse names are uppercase letters, skip if purely numeric or very short
                    if part and not re.match(r'^[\d.]+$', part) and len(part) > 2:
                        horse_idx = i
                        break
                
                if horse_idx >= 0:
                    horse_name = parts[horse_idx].strip().upper()
                    jockey = parts[horse_idx + 1].strip() if horse_idx + 1 < len(parts) else None
                    trainer = parts[horse_idx + 2].strip() if horse_idx + 2 < len(parts) else None
                    owner = parts[horse_idx + 3].strip() if horse_idx + 3 < len(parts) else None
                
                # Filter invalid entries
                if not horse_name or any(x in horse_name for x in 
                                       ['N°', 'CHEVAUX', 'JOCKEYS', 'ENTRAINEURS', 'GAINS', 'POIDS']):
                    continue
                
                horse = {
                    'horse_number': horse_num,
                    'horse_name': horse_name,
                }
                
                if age:
                    horse['age'] = age
                if weight:
                    horse['weight'] = weight
                if jockey:
                    horse['jockey'] = jockey
                if trainer:
                    horse['trainer'] = trainer
                if owner:
                    horse['owner'] = owner
                
                horses.append(horse)
        
        return horses if horses else []
    
    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize dataframe"""
        # Rename columns to match expected format (case-insensitive)
        column_mapping = {
            'num': 'horse_number',
            'number': 'horse_number',
            'n°': 'horse_number',
            'name': 'horse_name',
            'cheval': 'horse_name',
            'chevaux': 'horse_name',
            'desc': 'description',
            'cote': 'odds',
            'result': 'result_position',
            'position': 'result_position',
            'place': 'result_position',
            'arrivee': 'result_position',
            'arrive': 'result_position',
            'gagnant': 'result_position',
            'jockey': 'jockey',
            'trainer': 'trainer',
            'entraineur': 'trainer',
            'age': 'age',
            'poids': 'weight',
            'weight': 'weight',
            'wins': 'wins',
            'victoires': 'wins',
            'podiums': 'podiums'
        }
        
        # Normalize column names to lowercase for mapping
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Apply mapping
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df[new_col] = df[old_col]
        
        # Convert numeric columns
        numeric_cols = ['horse_number', 'age', 'wins', 'podiums', 'weight', 'result_position']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Fill missing numeric values
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        return df
    
    @staticmethod
    def extract_features(df: pd.DataFrame) -> pd.DataFrame:
        """Extract additional features from raw data"""
        df_features = df.copy()
        
        # Extract numeric features from description/name
        if 'description' in df_features.columns:
            df_features['mentions_wins'] = df_features['description'].astype(str).str.contains(
                r'victo|gagg|invainc|win', case=False, na=False, regex=True
            ).astype(int)
            
            df_features['mentions_podium'] = df_features['description'].astype(str).str.contains(
                r'podium|place|rang', case=False, na=False, regex=True
            ).astype(int)
            
            df_features['mentions_difficulty'] = df_features['description'].astype(str).str.contains(
                r'difficile|faible|probleme|blessure', case=False, na=False, regex=True
            ).astype(int)
            
            df_features['description_length'] = df_features['description'].astype(str).str.len()
        
        return df_features
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate imported data"""
        errors = []
        
        if df.empty:
            errors.append("DataFrame is empty")
            return len(errors) == 0, errors
        
        if 'horse_number' not in df.columns:
            errors.append("Missing 'horse_number' column")
        
        if 'horse_name' not in df.columns:
            errors.append("Missing 'horse_name' column")
        
        # Check for duplicates
        if 'horse_number' in df.columns and df['horse_number'].duplicated().any():
            errors.append("Duplicate horse numbers found")
        
        # Check for result_position data
        if 'result_position' in df.columns:
            non_zero_positions = (df['result_position'] != 0).sum()
            if non_zero_positions == 0:
                errors.append("Warning: No race results (result_position) found in data")
        
        return len(errors) == 0, errors


class OddsFeatureExtractor:
    """Extract features from odds data"""
    
    @staticmethod
    def convert_odds_to_probability(odds_str: str) -> Optional[float]:
        """Convert odds string to implied probability"""
        try:
            if pd.isna(odds_str):
                return None
            
            odds_str = str(odds_str).strip()
            
            if '/' in odds_str:
                parts = odds_str.split('/')
                numerator = float(parts[0])
                denominator = float(parts[1])
                decimal_odds = (numerator + denominator) / denominator
            else:
                decimal_odds = float(odds_str)
            
            if decimal_odds <= 0:
                return None
            
            probability = 1.0 / decimal_odds
            return max(0.0, min(probability, 1.0))
        except:
            return None
    
    @staticmethod
    def extract_odds_features(df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from odds"""
        df_features = df.copy()
        
        # Convert odds to probabilities only if odds column exists
        if 'odds' in df_features.columns:
            df_features['odds_probability'] = df_features['odds'].apply(
                OddsFeatureExtractor.convert_odds_to_probability
            )
            
            # Odds rank (lower odds = better odds = higher probability)
            if df_features['odds_probability'].notna().any():
                df_features['odds_rank'] = df_features['odds_probability'].rank(ascending=False, na_option='bottom')
                df_features['is_favorite'] = (df_features['odds_rank'] == 1).astype(int)
            else:
                df_features['odds_probability'] = 0.0
                df_features['odds_rank'] = 0
                df_features['is_favorite'] = 0
        else:
            df_features['odds_probability'] = 0.0
        
        # Odds movement detection (if we have previous odds)
        if 'odds_previous' in df_features.columns:
            prev_prob = df_features['odds_previous'].apply(OddsFeatureExtractor.convert_odds_to_probability)
            curr_prob = df_features['odds_probability']
            df_features['odds_movement'] = (curr_prob - prev_prob).fillna(0)
        
        return df_features


def import_and_process(file_path: str, file_type: str = 'auto') -> Tuple[pd.DataFrame, List[str]]:
    """
    Main function to import and process race data
    
    Returns:
        Tuple of (processed_dataframe, list_of_errors)
    """
    importer = DataImporter()
    errors = []
    df = None
    
    try:
        if file_type == 'csv' or (file_type == 'auto' and file_path.endswith('.csv')):
            df = importer.import_csv(file_path)
        
        elif file_type == 'pdf' or (file_type == 'auto' and file_path.endswith('.pdf')):
            text = importer.import_pdf_text(file_path)
            df = importer.parse_text_data(text)
        
        elif file_type == 'text':
            # File_path is actually text content
            df = importer.parse_text_data(file_path)
        
        else:
            # Try auto-detect based on content
            df = importer.parse_text_data(file_path)
        
        if df is None or df.empty:
            return None, ["No data could be extracted"]
        
        # Clean and extract features
        df = importer._clean_dataframe(df)
        df = importer.extract_features(df)
        df = OddsFeatureExtractor.extract_odds_features(df)
        
        # Validate
        is_valid, validation_errors = importer.validate_data(df)
        if not is_valid:
            errors.extend(validation_errors)
        
        return df, errors
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, [str(e)]
