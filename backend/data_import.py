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
        Format: N° | CHEVAUX | JOCKEYS | ENTRAINEURS | ... | POIDS | ARRIVEE
        Example row: 01 | MUST BAY | A.THOMAS | C.Y.LERNER | ... | 56,0 | 3-3
        
        Key insight: The rightmost columns contain ARRIVEE (yesterday's result)
        Format is typically: 01 | MUST BAY | ... | weights | ARRIVEE
        """
        horses = []
        lines = text.split('\n')
        
        # Find the table section (look for N° | CHEVAUX header or pipe-separated format)
        in_table = False
        table_lines = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Detect table start
            if 'CHEVAUX' in line_stripped or ('N°' in line_stripped and 'JOCKEYS' in line_stripped):
                in_table = True
                continue
            
            # Stop at section breaks
            if in_table and ('LES MEILLEURS' in line_stripped or 'HORAIRES' in line_stripped or 
                            'PMU' in line_stripped or '---PAGE' in line_stripped or
                            re.match(r'^\s*$', line_stripped)):
                break
            
            if in_table and line_stripped:
                table_lines.append(line_stripped)
        
        # Parse each table line
        for line in table_lines:
            if not line or len(line) < 5:
                continue
            
            # Skip header lines
            if 'CHEVAUX' in line or 'JOCKEYS' in line or 'ENTRAINEURS' in line or \
               'PROPRIET' in line or 'POIDS' in line or 'PERF' in line or \
               'GAINS' in line or 'TURF' in line:
                continue
            
            try:
                # Parse pipe-separated or space-separated columns
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                else:
                    # Try space-separated with varying spaces
                    parts = re.split(r'\s{2,}', line)
                
                if len(parts) < 2:
                    continue
                
                # Extract number and horse name from first two parts
                horse_num_match = re.match(r'^(\d{1,2})', parts[0])
                if not horse_num_match:
                    continue
                
                horse_num = int(horse_num_match.group(1))
                horse_name = parts[1].strip() if len(parts) > 1 else None
                
                # Filter invalid horse names
                if not horse_name or horse_name in ['CHEVAUX', 'N°', 'JOCKEYS', 'ENTRAINEURS']:
                    continue
                
                # Skip lines that are clearly headers or totals
                if any(x in horse_name.upper() for x in ['MEILLEUR', 'TOTAL', 'HEURE', 'DEPART']):
                    continue
                
                horse = {
                    'horse_number': horse_num,
                    'horse_name': horse_name
                }
                
                # Try to extract jockey (usually part 2)
                if len(parts) > 2:
                    jockey = parts[2].strip()
                    if jockey and jockey not in ['JOCKEYS', 'ENTRAINEURS', ''] and len(jockey) > 1:
                        horse['jockey'] = jockey
                
                # Try to extract trainer (usually part 3)
                if len(parts) > 3:
                    trainer = parts[3].strip()
                    if trainer and trainer not in ['ENTRAINEURS', ''] and len(trainer) > 1:
                        horse['trainer'] = trainer
                
                # Extract age (usually part 4-5, format: M.3, F.3, etc.)
                if len(parts) > 4:
                    age_str = parts[4].strip()
                    age_match = re.search(r'(\d+)', age_str)
                    if age_match:
                        horse['age'] = int(age_match.group(1))
                
                # Last 1-2 parts usually contain: POIDS (weight) and ARRIVEE (result position)
                # Format of ARRIVEE: "3-3", "1/1", "1-4/1", etc.
                # We'll process right-to-left
                
                # Last part is ARRIVEE (result position) - format like "3-3", "1/1", "2", etc.
                if len(parts) >= 2:
                    last_part = parts[-1].strip()
                    # Parse arrival/position - first number is the rank
                    arrival_match = re.search(r'^(\d+)(?:[/-].*)?', last_part)
                    if arrival_match:
                        result_pos = int(arrival_match.group(1))
                        # Only set if it's a valid position (1-20)
                        if 1 <= result_pos <= 20:
                            horse['result_position'] = result_pos
                
                # Try weight from second-to-last if available
                if len(parts) >= 3:
                    weight_str = parts[-2].strip()
                    weight_match = re.search(r'([\d.]+)\s*(?:kg|KG)?', weight_str)
                    if weight_match:
                        try:
                            horse['weight'] = float(weight_match.group(1))
                        except:
                            pass
                
                horses.append(horse)
            
            except (ValueError, IndexError) as e:
                continue
        
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
