"""Weather Integration - Fetch weather data from open-meteo API"""
import requests
from typing import Dict, Optional
from datetime import datetime


class WeatherProvider:
    """Fetch weather data from open-meteo (free, no API key needed)"""
    
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    def get_weather(self, latitude: float, longitude: float, race_date: str) -> Optional[Dict]:
        """
        Fetch weather for a specific race location and date
        
        Args:
            latitude: Race location latitude
            longitude: Race location longitude
            race_date: Race date (YYYY-MM-DD)
        
        Returns:
            Dict with weather info or None if error
        """
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': race_date,
                'end_date': race_date,
                'hourly': 'temperature_2m,weather_code,wind_speed_10m,precipitation',
                'timezone': 'Europe/Paris'
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if 'hourly' not in data:
                return None
            
            # Get noon weather (12:00)
            hourly = data['hourly']
            times = hourly['time']
            
            # Find 12:00 index
            target_time = f"{race_date}T12:00"
            try:
                idx = times.index(target_time)
            except ValueError:
                idx = 0  # Fallback to first hour
            
            weather_code = hourly['weather_code'][idx]
            temp = hourly['temperature_2m'][idx]
            wind = hourly['wind_speed_10m'][idx]
            rain = hourly['precipitation'][idx]
            
            return {
                'date': race_date,
                'temperature': float(temp),
                'wind_speed': float(wind),
                'precipitation': float(rain),
                'condition': self._decode_weather_code(weather_code),
                'weather_code': weather_code
            }
        
        except Exception as e:
            print(f"⚠️ Weather fetch error: {e}")
            return None
    
    def _decode_weather_code(self, code: int) -> str:
        """Decode WMO weather code to human-readable condition"""
        codes = {
            0: 'clear',
            1: 'mainly_clear',
            2: 'partly_cloudy',
            3: 'overcast',
            45: 'foggy',
            48: 'foggy_depositing',
            51: 'drizzle_light',
            53: 'drizzle_moderate',
            55: 'drizzle_heavy',
            61: 'rain_slight',
            63: 'rain_moderate',
            65: 'rain_heavy',
            71: 'snow_slight',
            73: 'snow_moderate',
            75: 'snow_heavy',
            77: 'snow_grains',
            80: 'rain_showers_slight',
            81: 'rain_showers_moderate',
            82: 'rain_showers_violent',
            85: 'snow_showers_slight',
            86: 'snow_showers_heavy',
            95: 'thunderstorm',
            96: 'thunderstorm_with_hail_slight',
            99: 'thunderstorm_with_hail_heavy'
        }
        return codes.get(code, 'unknown')


# Hippodrome coordinates (Paris region)
HIPPODROME_COORDS = {
    'PARISLONGCHAMP': (48.8653, 2.2345),
    'VINCENNES': (48.8405, 2.4317),
    'AUTEUIL': (48.8485, 2.2615),
    'CHANTILLY': (49.2138, 2.4064),
    'DEAUVILLE': (49.3633, 0.0767),
    'SAINT-CLOUD': (48.8658, 2.1978),
    'SAINT-LEU': (49.0131, 2.3819),
}


def get_hippodrome_weather(hippodrome: str, race_date: str) -> Optional[Dict]:
    """
    Convenience function to get weather for a hippodrome
    
    Args:
        hippodrome: Hippodrome name (e.g., 'PARISLONGCHAMP')
        race_date: Race date (YYYY-MM-DD)
    
    Returns:
        Weather dict or None
    """
    coords = HIPPODROME_COORDS.get(hippodrome.upper())
    if not coords:
        print(f"⚠️ Unknown hippodrome: {hippodrome}")
        return None
    
    provider = WeatherProvider()
    return provider.get_weather(coords[0], coords[1], race_date)
