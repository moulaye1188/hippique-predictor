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
        """Fallback parser - NOT USED (old, broken)"""
        return []
    
    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize dataframe"""
        if df.empty:
            return df
            
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
                    df[col] = df[col].fillna(value=0)
    
    @staticmethod
    def extract_features(df: pd.DataFrame) -> pd.DataFrame:
        """Extract additional features from raw data"""
        if df.empty:
            return df
            
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
        if df.empty:
            return df
            
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
            df_features['odds_movement'] = (curr_prob - prev_prob).fillna(value=0)
        
        return df_features


def import_and_process(file_path: str, file_type: str = 'auto') -> Tuple[pd.DataFrame, List[str]]:
    """
    Main function to import and process race data
    ALWAYS uses new pdfplumber parser for PDFs via pdf_integration
    
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
            # Use new pdfplumber parser (via pdf_integration wrapper)
            try:
                from pdf_integration import parse_pdf_file
                race_info, df = parse_pdf_file(file_path)
                
                # Add race info to dataframe as columns
                if df is not None and not df.empty and race_info:
                    for key, val in race_info.items():
                        if val is not None:
                            df[key] = val
                            
                print(f"[PDF Parser] Successfully extracted {len(df)} horses from PDF")
            except Exception as e:
                print(f"[PDF Parser] Error with pdfplumber: {e}")
                import traceback
                traceback.print_exc()
                df = None
            
            # Fallback if parsing failed
            if df is None or df.empty:
                print("[PDF Parser] Fallback: using old text parser (deprecated)")
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
        print(f"[Import] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return None, [str(e)]
