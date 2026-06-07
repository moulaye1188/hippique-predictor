"""Horse Stats V2 - Calculate averages with result tracking"""
import sqlite3
from config import DB_PATH
from typing import Dict, Tuple


class HorseStatsCalculator:
    """Calculate horse statistics including results and weather"""
    
    def __init__(self):
        self.db = DB_PATH
    
    def get_horse_identity(self, horse_name: str, jockey: str, trainer: str) -> Tuple[str, bool]:
        """
        Get unique horse ID (name+jockey+trainer)
        Returns: (identity_key, is_new)
        """
        identity = f"{horse_name}|{jockey}|{trainer}".upper()
        
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM horse_identities WHERE identity_key = ?", (identity,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return identity, False
        return identity, True
    
    def register_horse_performance(self, horse_name: str, jockey: str, trainer: str,
                                  race_date: str, hippodrome: str, distance: int,
                                  odds: float, position: int = None, weather: Dict = None):
        """
        Register a horse's performance in a race.
        When results arrive (position != None), recalculate stats.
        """
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        identity = f"{horse_name}|{jockey}|{trainer}".upper()
        
        # Ensure identity exists
        cursor.execute("""
            INSERT OR IGNORE INTO horse_identities (identity_key, horse_name, jockey, trainer)
            VALUES (?, ?, ?, ?)
        """, (identity, horse_name, jockey, trainer))
        
        # Insert performance record
        weather_json = str(weather) if weather else None
        cursor.execute("""
            INSERT INTO horse_performances (identity_key, race_date, hippodrome, distance, odds, position, weather)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (identity, race_date, hippodrome, distance, odds, position, weather_json))
        
        conn.commit()
        conn.close()
        
        # Recalculate stats if result provided
        if position is not None:
            self.recalculate_stats(identity)
    
    def recalculate_stats(self, identity: str):
        """Recalculate all stats for a horse based on completed races"""
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        # Get all completed performances
        cursor.execute("""
            SELECT position, odds, distance, weather
            FROM horse_performances
            WHERE identity_key = ? AND position IS NOT NULL
            ORDER BY race_date DESC
        """, (identity,))
        
        races = cursor.fetchall()
        
        if not races:
            conn.close()
            return
        
        # Calculate stats
        total_races = len(races)
        wins = sum(1 for pos, _, _, _ in races if pos == 1)
        podiums = sum(1 for pos, _, _, _ in races if pos <= 3)
        avg_position = sum(pos for pos, _, _, _ in races) / total_races
        
        # Weighted recent form (last 5 races weighted higher)
        recent_form = 0
        weights = [1.0, 0.8, 0.6, 0.4, 0.2]
        for i, (pos, _, _, _) in enumerate(races[:5]):
            score = 10 if pos == 1 else 8 if pos == 2 else 6 if pos == 3 else 2
            recent_form += score * weights[i]
        recent_form = recent_form / sum(weights[:min(5, total_races)])
        
        # Weather correlation (simple average by condition)
        weather_stats = self._analyze_weather_correlation(races)
        
        # Update or insert stats
        cursor.execute("""
            INSERT OR REPLACE INTO horse_stats (identity_key, total_races, wins, podiums, avg_position, recent_form, weather_stats)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (identity, total_races, wins, podiums, avg_position, recent_form, str(weather_stats)))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Updated stats for {identity}: {total_races} races, {wins} wins, avg_pos={avg_position:.2f}, form={recent_form:.1f}")
    
    def _analyze_weather_correlation(self, races) -> Dict:
        """Analyze performance by weather condition"""
        weather_perf = {}
        
        for pos, odds, distance, weather_str in races:
            if not weather_str:
                continue
            
            # Parse weather (simplified)
            weather = eval(weather_str) if isinstance(weather_str, str) else weather_str
            condition = weather.get('condition', 'unknown')
            
            if condition not in weather_perf:
                weather_perf[condition] = {'wins': 0, 'races': 0, 'avg_pos': []}
            
            weather_perf[condition]['races'] += 1
            if pos == 1:
                weather_perf[condition]['wins'] += 1
            weather_perf[condition]['avg_pos'].append(pos)
        
        # Calculate percentages
        return {
            cond: {
                'win_rate': data['wins'] / data['races'],
                'avg_position': sum(data['avg_pos']) / len(data['avg_pos']),
                'races': data['races']
            }
            for cond, data in weather_perf.items()
        }
    
    def get_horse_stats(self, horse_name: str, jockey: str, trainer: str) -> Dict:
        """Get current stats for a horse"""
        identity = f"{horse_name}|{jockey}|{trainer}".upper()
        
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT total_races, wins, podiums, avg_position, recent_form
            FROM horse_stats
            WHERE identity_key = ?
        """, (identity,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'total_races': result[0],
                'wins': result[1],
                'podiums': result[2],
                'avg_position': result[3],
                'recent_form': result[4],
                'win_rate': result[1] / result[0] if result[0] > 0 else 0
            }
        
        return {
            'total_races': 0,
            'wins': 0,
            'podiums': 0,
            'avg_position': 0,
            'recent_form': 5.0,  # Neutre
            'win_rate': 0
        }
