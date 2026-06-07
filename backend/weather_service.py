"""Weather Service - Fetch and process weather data from Open-Meteo"""
import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """Weather data provider using Open-Meteo (free, no API key)"""
    
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    @staticmethod
    def get_weather(race_date: str, latitude: float, longitude: float) -> Dict:
        """
        Fetch weather for a specific race location and date
        
        Args:
            race_date: Race date (YYYY-MM-DD)
            latitude: Hippodrome latitude
            longitude: Hippodrome longitude
        
        Returns:
            Weather dict with temperature, wind, precipitation, condition
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
            
            response = requests.get(WeatherService.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if 'hourly' not in data:
                logger.warning("No weather data in response")
                return WeatherService._get_default_weather()
            
            hourly = data['hourly']
            times = hourly['time']
            
            # Get 12:00 (noon) data
            target_time = f"{race_date}T12:00"
            try:
                idx = times.index(target_time)
            except ValueError:
                idx = 0
            
            weather_code = hourly['weather_code'][idx]
            temp = hourly['temperature_2m'][idx]
            wind = hourly['wind_speed_10m'][idx]
            rain = hourly['precipitation'][idx]
            
            return {
                'date': race_date,
                'temperature': float(temp),
                'wind_speed': float(wind),
                'precipitation': float(rain),
                'condition': WeatherService._decode_weather_code(weather_code),
                'weather_code': weather_code
            }
        
        except Exception as e:
            logger.warning(f"Weather fetch error: {e}, using defaults")
            return WeatherService._get_default_weather()
    
    @staticmethod
    def _decode_weather_code(code: int) -> str:
        """Decode WMO weather code"""
        codes = {
            0: 'clear', 1: 'mainly_clear', 2: 'partly_cloudy', 3: 'overcast',
            45: 'foggy', 51: 'drizzle_light', 53: 'drizzle_moderate', 55: 'drizzle_heavy',
            61: 'rain_slight', 63: 'rain_moderate', 65: 'rain_heavy',
            71: 'snow_slight', 73: 'snow_moderate', 75: 'snow_heavy',
            80: 'rain_showers_slight', 81: 'rain_showers_moderate', 82: 'rain_showers_violent',
            95: 'thunderstorm'
        }
        return codes.get(code, 'unknown')
    
    @staticmethod
    def _get_default_weather() -> Dict:
        """Return neutral default weather (no impact)"""
        return {
            'date': 'unknown',
            'temperature': 15.0,  # Neutral temp
            'wind_speed': 5.0,    # Neutral wind
            'precipitation': 0.0, # No rain
            'condition': 'clear',
            'weather_code': 0
        }
    
    @staticmethod
    def get_weather_features_from_dict(weather_dict: Dict) -> Dict:
        """
        Convert weather dict to ML features (0-1 normalized)
        
        Returns:
            Dict with normalized weather features for ML model
        """
        # Temperature: 0°C = 0, 15°C = 0.5, 30°C = 1.0
        temp = weather_dict.get('temperature', 15.0)
        temp_normalized = np.clip((temp + 10) / 40, 0, 1)  # -10 to +30 range
        
        # Wind speed: 0 km/h = 1.0 (good), 30 km/h = 0.5, 50+ km/h = 0.0 (bad)
        wind = weather_dict.get('wind_speed', 5.0)
        wind_factor = max(0, 1.0 - (wind / 50))  # Decreases with wind speed
        
        # Precipitation: 0mm = 1.0 (good), 5mm = 0.5, 20+ mm = 0 (bad)
        rain = weather_dict.get('precipitation', 0.0)
        precipitation_normalized = max(0, 1.0 - (rain / 20))  # More rain = worse conditions
        
        # Track condition based on weather code (simple classification)
        condition = weather_dict.get('condition', 'clear')
        if 'clear' in condition or 'mainly_clear' in condition:
            track_condition_score = 1.0  # Excellent
        elif 'cloudy' in condition or 'overcast' in condition:
            track_condition_score = 0.85  # Good
        elif 'drizzle' in condition or 'rain_slight' in condition:
            track_condition_score = 0.6   # Fair (muddy)
        elif 'rain' in condition or 'showers' in condition:
            track_condition_score = 0.3   # Poor (very muddy)
        elif 'snow' in condition:
            track_condition_score = 0.2   # Very poor
        elif 'thunderstorm' in condition:
            track_condition_score = 0.1   # Dangerous
        else:
            track_condition_score = 0.5   # Unknown
        
        return {
            'temp_normalized': float(temp_normalized),
            'wind_factor': float(wind_factor),
            'precipitation_normalized': float(precipitation_normalized),
            'track_condition_score': float(track_condition_score)
        }


# Import numpy for clip function
import numpy as np
