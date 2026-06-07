"""France-Galop Scraper - Get scratch-list (withdrawals, jockey changes, etc.)"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import time
import pandas as pd

logger = logging.getLogger(__name__)

# France-Galop base URLs
FRANCE_GALOP_URL = "https://www.france-galop.com"
PROGRAMMES_URL = f"{FRANCE_GALOP_URL}/programmes"


class FranceGalopScraper:
    """Scrape France-Galop for race information and withdrawals"""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    @staticmethod
    def get_scratch_list(date: Optional[str] = None, hippodrome: Optional[str] = None) -> Dict:
        """
        Get scratch-list (withdrawn horses) for a specific date/hippodrome
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
            hippodrome: Hippodrome name (VINCENNES, PARISLONGCHAMP, etc.)
        
        Returns:
            Dict with structure:
            {
                'date': '2024-11-15',
                'hippodrome': 'VINCENNES',
                'scratches': {
                    'race_number': [horse_numbers],
                    '1': [3, 5, 12],  # Race 1: horses 3, 5, 12 withdrawn
                    '2': [7],
                    ...
                },
                'jockey_changes': {
                    'race_number': {horse_number: 'new_jockey_name'},
                    ...
                },
                'success': True,
                'error': None
            }
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Convert date format from YYYY-MM-DD to DD/MM/YYYY for France-Galop
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_fr = date_obj.strftime('%d/%m/%Y')
            
            # Try to fetch the programmes page
            logger.info(f"Scraping France-Galop for {date_fr}")
            
            # Construct search URL
            search_url = f"{PROGRAMMES_URL}?date={date_fr}"
            if hippodrome:
                search_url += f"&hippodrome={hippodrome}"
            
            response = requests.get(
                search_url,
                headers=FranceGalopScraper.HEADERS,
                timeout=15
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse scratches and jockey changes
            scratches = {}
            jockey_changes = {}
            
            # Look for race sections
            race_elements = soup.find_all('div', class_=['race', 'course', 'epreuve'])
            
            if not race_elements:
                logger.warning(f"No race data found for {date_fr}")
                return {
                    'date': date,
                    'hippodrome': hippodrome or 'ALL',
                    'scratches': {},
                    'jockey_changes': {},
                    'success': False,
                    'error': 'No race data found'
                }
            
            # Parse each race
            for race_elem in race_elements:
                try:
                    race_num = FranceGalopScraper._extract_race_number(race_elem)
                    if not race_num:
                        continue
                    
                    # Extract withdrawn horses
                    withdrawn = FranceGalopScraper._extract_withdrawn_horses(race_elem)
                    if withdrawn:
                        scratches[race_num] = withdrawn
                    
                    # Extract jockey changes
                    jockey_changes_race = FranceGalopScraper._extract_jockey_changes(race_elem)
                    if jockey_changes_race:
                        jockey_changes[race_num] = jockey_changes_race
                
                except Exception as e:
                    logger.warning(f"Error parsing race element: {e}")
                    continue
            
            logger.info(f"Scratch-list retrieved: {len(scratches)} races with withdrawals")
            
            return {
                'date': date,
                'hippodrome': hippodrome or 'ALL',
                'scratches': scratches,
                'jockey_changes': jockey_changes,
                'success': True,
                'error': None
            }
        
        except requests.exceptions.Timeout:
            logger.warning("France-Galop scraper timeout")
            return FranceGalopScraper._get_empty_result(date, hippodrome, "Timeout")
        except requests.exceptions.RequestException as e:
            logger.warning(f"France-Galop scraper request error: {e}")
            return FranceGalopScraper._get_empty_result(date, hippodrome, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in France-Galop scraper: {e}")
            return FranceGalopScraper._get_empty_result(date, hippodrome, str(e))
    
    @staticmethod
    def _extract_race_number(race_elem) -> Optional[str]:
        """Extract race number from race element"""
        try:
            # Try different selectors
            selectors = [
                ('div', 'race-number'),
                ('span', 'numero-epreuve'),
                ('h3', None)
            ]
            
            for tag, class_name in selectors:
                elem = race_elem.find(tag, class_=class_name)
                if elem:
                    text = elem.get_text(strip=True)
                    # Extract number (could be "Race 1", "Epreuve 1", etc.)
                    import re
                    match = re.search(r'\d+', text)
                    if match:
                        return match.group(0)
            
            return None
        except:
            return None
    
    @staticmethod
    def _extract_withdrawn_horses(race_elem) -> List[int]:
        """Extract list of withdrawn horse numbers"""
        withdrawn = []
        try:
            # Look for "withdrawn", "non-partant", "retiré" markers
            text_lower = race_elem.get_text().lower()
            
            # Find horse rows
            horse_rows = race_elem.find_all('tr') or race_elem.find_all('div', class_='horse')
            
            for row in horse_rows:
                row_text = row.get_text().lower()
                
                # Check for withdrawal indicators
                if any(marker in row_text for marker in ['withdrawn', 'non-partant', 'retiré', 'dsq', 'déclaré forfait']):
                    # Extract horse number
                    import re
                    numbers = re.findall(r'\b(\d+)\b', row.get_text())
                    if numbers:
                        try:
                            horse_num = int(numbers[0])
                            if 1 <= horse_num <= 20:  # Sanity check
                                withdrawn.append(horse_num)
                        except:
                            pass
            
            return withdrawn
        except Exception as e:
            logger.debug(f"Error extracting withdrawn horses: {e}")
            return []
    
    @staticmethod
    def _extract_jockey_changes(race_elem) -> Dict[int, str]:
        """Extract jockey changes (horse_number -> new_jockey_name)"""
        changes = {}
        try:
            # Look for "jockey change", "changement de cavalier", etc.
            text_lower = race_elem.get_text().lower()
            
            if 'changement' not in text_lower and 'jockey change' not in text_lower:
                return {}
            
            # Parse jockey change entries
            import re
            pattern = r'(?:cheval|horse)?\s*(\d+).*?(?:jockey|cavalier).*?:\s*([A-Z][a-z\s]+)'
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                try:
                    horse_num = int(match.group(1))
                    jockey_name = match.group(2).strip()
                    if 1 <= horse_num <= 20:
                        changes[horse_num] = jockey_name
                except:
                    pass
            
            return changes
        except:
            return {}
    
    @staticmethod
    def _get_empty_result(date: str, hippodrome: Optional[str], error: str) -> Dict:
        """Return empty result with error"""
        return {
            'date': date,
            'hippodrome': hippodrome or 'ALL',
            'scratches': {},
            'jockey_changes': {},
            'success': False,
            'error': error
        }


class ScratchListFilter:
    """Filter horses based on scratch-list"""
    
    @staticmethod
    def filter_horses(horses_df, scratch_list: Dict) -> tuple:
        """
        Filter out withdrawn horses from dataframe
        
        Args:
            horses_df: DataFrame with horses
            scratch_list: Output from get_scratch_list()
        
        Returns:
            (filtered_df, excluded_horses)
        """
        import pandas as pd
        
        df = horses_df.copy()
        excluded = []
        
        if not scratch_list['success'] or not scratch_list['scratches']:
            return df, excluded
        
        # Get all withdrawn horse numbers from all races
        all_scratches = []
        for race_num, horse_nums in scratch_list['scratches'].items():
            all_scratches.extend(horse_nums)
        
        if not all_scratches:
            return df, excluded
        
        # Filter out withdrawn horses
        if 'horse_number' in df.columns:
            mask = ~df['horse_number'].isin(all_scratches)
            excluded = df[~mask]['horse_number'].tolist()
            df = df[mask].copy()
            
            logger.info(f"Filtered out {len(excluded)} withdrawn horses: {excluded}")
        
        return df, excluded
    
    @staticmethod
    def apply_jockey_changes(horses_df, jockey_changes: Dict) -> pd.DataFrame:
        """
        Update jockey names based on last-minute changes
        
        Args:
            horses_df: DataFrame with horses
            jockey_changes: Dict from scratch_list['jockey_changes']
        
        Returns:
            Updated dataframe
        """
        import pandas as pd
        
        df = horses_df.copy()
        
        if not jockey_changes:
            return df
        
        if 'jockey' not in df.columns or 'horse_number' not in df.columns:
            return df
        
        # Apply jockey changes
        for horse_num, new_jockey in jockey_changes.items():
            mask = df['horse_number'] == horse_num
            if mask.any():
                old_jockey = df.loc[mask, 'jockey'].iloc[0]
                df.loc[mask, 'jockey'] = new_jockey
                logger.info(f"Jockey change: Horse {horse_num}: {old_jockey} → {new_jockey}")
        
        return df


# Test
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test scraper
    print("Testing France-Galop Scraper...")
    print("=" * 60)
    
    # Test for today
    result = FranceGalopScraper.get_scratch_list()
    print(f"Date: {result['date']}")
    print(f"Success: {result['success']}")
    print(f"Error: {result['error']}")
    print(f"Scratches found: {len(result['scratches'])} races with withdrawals")
    print(f"Scratches: {result['scratches']}")
    print(f"Jockey changes: {result['jockey_changes']}")
    
    print("=" * 60)
