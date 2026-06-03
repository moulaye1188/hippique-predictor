"""
Advanced PDF parser for horse racing PDFs (Le Journal Hippique)
Extracts race information AND generates predictions immediately
"""

import re
import pandas as pd
import PyPDF2
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class RaceInfoExtractor:
    """Extract race information from Le Journal Hippique PDF"""
    
    @staticmethod
    def extract_race_date(text: str) -> Optional[str]:
        """Extract race date from text like 'QUARTE" DU JEUDI 04 JUIN 2026'"""
        patterns = [
            r'DU\s+(?:LUNDI|MARDI|MERCREDI|JEUDI|VENDREDI|SAMEDI|DIMANCHE)\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    day, month, year = match.groups()
                    # Convert month name to number
                    months = {
                        'JANVIER': '01', 'FÉVRIER': '02', 'MARS': '03', 'AVRIL': '04',
                        'MAI': '05', 'JUIN': '06', 'JUILLET': '07', 'AOÛT': '08',
                        'SEPTEMBRE': '09', 'OCTOBRE': '10', 'NOVEMBRE': '11', 'DÉCEMBRE': '12'
                    }
                    month_num = months.get(month.upper(), month)
                    return f"{year}-{month_num}-{day.zfill(2)}"
        
        return None
    
    @staticmethod
    def extract_hippodrome(text: str) -> Optional[str]:
        """Extract hippodrome name"""
        # Look for known hippodromes
        hippodromes = [
            'PARISLONGCHAMP', 'VINCENNES', 'AUTEUIL', 'LAVAL', 'LYON',
            'MARSEILLE', 'BORDEAUX', 'TOULOUSE', 'CHANTILLY', 'DEAUVILLE',
            'LE MANS', 'MAURE', 'ENGHIEN', 'BOURGANEUF'
        ]
        
        for hippo in hippodromes:
            if hippo in text.upper():
                return hippo
        
        return None
    
    @staticmethod
    def extract_distance(text: str) -> Optional[int]:
        """Extract race distance in meters"""
        # Look for patterns like "1 600 METRES" or "1600 METRES"
        match = re.search(r'(\d+(?:\s+)?\d*)\s*(?:M|METRES|METER)', text, re.IGNORECASE)
        if match:
            distance_str = match.group(1).replace(' ', '')
            try:
                return int(distance_str)
            except:
                pass
        
        return None
    
    @staticmethod
    def extract_race_type(text: str) -> Optional[str]:
        """Extract race type (PLAT, ATTELE, etc.)"""
        race_types = ['PLAT', 'ATTELE', 'OBSTACLE', 'STEEPLECHASE', 'HAIES']
        
        for rtype in race_types:
            if rtype in text.upper():
                return rtype
        
        return None
    
    @staticmethod
    def extract_race_name(text: str) -> Optional[str]:
        """Extract race name like 'PRIX DE L'HOTEL CARNAVALET'"""
        # Look for pattern starting with PRIX or GRANDE COURSE etc.
        match = re.search(r'(PRIX\s+[A-Z\s\-\']+|GRANDE\s+[A-Z\s\-\']+|COURSES\s+[A-Z\s\-\']+)', 
                         text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    @staticmethod
    def extract_num_competitors(text: str) -> Optional[int]:
        """Extract number of competitors"""
        match = re.search(r'(\d+)\s*CONCURRENTS?', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return None
    
    @staticmethod
    def extract_prize_money(text: str) -> Optional[str]:
        """Extract prize money"""
        # Look for patterns like "50 900 EUROS"
        match = re.search(r'([\d\s]+)\s*(EUROS?|F(?:\s+CFA)?)', text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
        
        return None
    
    @staticmethod
    def extract_race_number(text: str) -> Optional[int]:
        """Extract race number like '6ème COURSE'"""
        match = re.search(r'(\d+)(?:ère|ème|e)\s+COURSE', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return None
    
    @staticmethod
    def extract_race_info(text: str) -> Dict:
        """Extract all race information from PDF text"""
        
        race_info = {
            'race_date': RaceInfoExtractor.extract_race_date(text),
            'hippodrome': RaceInfoExtractor.extract_hippodrome(text),
            'distance': RaceInfoExtractor.extract_distance(text),
            'race_type': RaceInfoExtractor.extract_race_type(text),
            'race_name': RaceInfoExtractor.extract_race_name(text),
            'num_competitors': RaceInfoExtractor.extract_num_competitors(text),
            'prize_money': RaceInfoExtractor.extract_prize_money(text),
            'race_number': RaceInfoExtractor.extract_race_number(text),
        }
        
        return race_info


class ResultExtractor:
    """Extract race results from PDF"""
    
    @staticmethod
    def extract_arrival(text: str) -> Optional[List[int]]:
        """Extract race arrival/results like '2 - 3 - 12 - 1'"""
        # Look for patterns like "ARRIVEE : 2 - 3 - 12 - 1" or "Arrivée : 16 - 6 - 14 - 15 - 4"
        patterns = [
            r'ARRIVÉE?\s*:\s*([\d\s\-]+?)(?:\n|NPO)',
            r'Arrivée\s*:\s*([\d\s\-]+?)(?:\n|NPO)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                arrival_str = match.group(1)
                # Extract numbers
                numbers = re.findall(r'\d+', arrival_str)
                return [int(n) for n in numbers if n]
        
        return None


class AdvancedPDFParser:
    """Advanced PDF parser that extracts both race info and horses"""
    
    def __init__(self):
        self.race_info = {}
        self.horses_data = []
    
    def parse_pdf(self, file_path: str) -> Tuple[Dict, pd.DataFrame]:
        """
        Parse PDF and extract race info + horses
        Returns: (race_info_dict, horses_dataframe)
        """
        # Extract text from PDF
        text = self._extract_text_from_pdf(file_path)
        
        # Extract race information
        self.race_info = RaceInfoExtractor.extract_race_info(text)
        self.race_info['arrival'] = ResultExtractor.extract_arrival(text)
        
        # Extract horses data (using existing parser)
        from data_import import DataImporter
        horses = DataImporter._parse_tabular_format(text)
        self.horses_data = horses
        
        # Create DataFrame
        df = pd.DataFrame(horses)
        
        return self.race_info, df
    
    @staticmethod
    def _extract_text_from_pdf(file_path: str) -> str:
        """Extract all text from PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        
        return text
    
    def validate_race_info(self) -> Tuple[bool, List[str]]:
        """Validate extracted race information"""
        errors = []
        
        if not self.race_info.get('race_date'):
            errors.append("Race date not found")
        
        if not self.race_info.get('hippodrome'):
            errors.append("Hippodrome not found")
        
        if not self.race_info.get('distance'):
            errors.append("Distance not found")
        
        if not self.horses_data:
            errors.append("No horses data found")
        
        return len(errors) == 0, errors
    
    def get_race_summary(self) -> str:
        """Get a readable summary of extracted race"""
        summary = f"""
╔══════════════════════════════════════════════════════════╗
║           RACE INFORMATION EXTRACTED                     ║
╚══════════════════════════════════════════════════════════╝

Date: {self.race_info.get('race_date', 'N/A')}
Hippodrome: {self.race_info.get('hippodrome', 'N/A')}
Race Name: {self.race_info.get('race_name', 'N/A')}
Distance: {self.race_info.get('distance', 'N/A')} m
Type: {self.race_info.get('race_type', 'N/A')}
Number: {self.race_info.get('race_number', 'N/A')}
Competitors: {self.race_info.get('num_competitors', 'N/A')}
Prize: {self.race_info.get('prize_money', 'N/A')}
Arrival: {self.race_info.get('arrival', 'N/A')}

Horses: {len(self.horses_data)} extracted

────────────────────────────────────────────────────────────
"""
        return summary


def test_parser():
    """Test the advanced parser"""
    print("Advanced PDF Parser Test")
    print("=" * 60)
    
    # This would be called with a real PDF
    # parser = AdvancedPDFParser()
    # race_info, df = parser.parse_pdf("sample.pdf")
    # print(parser.get_race_summary())
    # print(df)


if __name__ == '__main__':
    test_parser()
