"""Open-Meteo Weather Service - Get weather data for races"""
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"


class WeatherService:
    """Fetch historical weather data from Open-Meteo"""
    
    @staticmethod
    def get_weather(date: str, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Get weather data for a specific date and location
        
        Args:
            date: Date string (YYYY-MM-DD format)
            latitude: Race location latitude
            longitude: Race location longitude
        
        Returns:
            Dict with weather features or None if error
            
        Example:
            weather = WeatherService.get_weather('2024-11-15', 48.8566, 2.3522)
            # Returns: {
            #     'temperature': 12.5,
            #     'windspeed': 15.3,
            #     'winddirection': 230,
            #     'precipitation': 0.5,
            #     'weathercode': 61
            # }
        """
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': date,
                'end_date': date,
                'hourly': 'temperature_2m,windspeed_10m,winddirection_10m,precipitation',
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode',
                'timezone': 'Europe/Paris',
                'temperature_unit': 'celsius'
            }
            
            response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract daily weather (race typically in afternoon)
            if 'daily' in data and len(data['daily']['time']) > 0:
                daily = data['daily']
                
                weather_dict = {
                    'temperature_max': float(daily['temperature_2m_max'][0]) if daily['temperature_2m_max'][0] is not None else 15.0,
                    'temperature_min': float(daily['temperature_2m_min'][0]) if daily['temperature_2m_min'][0] is not None else 10.0,
                    'precipitation': float(daily['precipitation_sum'][0]) if daily['precipitation_sum'][0] is not None else 0.0,
                    'windspeed_max': float(daily['windspeed_10m_max'][0]) if daily['windspeed_10m_max'][0] is not None else 10.0,
                    'weathercode': int(daily['weathercode'][0]) if daily['weathercode'][0] is not None else 0,
                }
                
                # Calculate average temperature
                weather_dict['temperature_avg'] = (weather_dict['temperature_max'] + weather_dict['temperature_min']) / 2
                
                # Classify track condition based on precipitation
                weather_dict['track_condition'] = WeatherService._classify_track_condition(
                    weather_dict['precipitation'],
                    weather_dict['weathercode']
                )
                
                logger.info(f"Weather fetched for {date} @ ({latitude}, {longitude}): {weather_dict}")
                return weather_dict
            else:
                logger.warning(f"No daily data returned for {date}")
                return WeatherService._get_default_weather()
        
        except requests.exceptions.Timeout:
            logger.warning(f"Weather API timeout for {date}")
            return WeatherService._get_default_weather()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Weather API error: {e}")
            return WeatherService._get_default_weather()
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            return WeatherService._get_default_weather()
    
    @staticmethod
    def _classify_track_condition(precipitation_mm: float, weathercode: int) -> str:
        """
        Classify track condition based on weather data
        
        weathercode: WMO Weather interpretation codes
        - 0: Clear sky
        - 1-3: Mostly clear/cloudy
        - 45-48: Foggy
        - 51-67: Drizzle/Rain
        - 80-82: Rain showers
        - 85-86: Snow showers
        """
        if precipitation_mm > 5.0:
            return 'heavy'  # Très boueux
        elif precipitation_mm > 1.0:
            return 'soft'   # Mou/léger boue
        elif weathercode >= 80:  # Rain showers
            return 'soft'
        elif weathercode >= 51 and weathercode <= 67:  # Rain/Drizzle
            return 'good'   # Juste humide mais roulant
        else:
            return 'good'   # Sec
    
    @staticmethod
    def _get_default_weather() -> Dict:
        """Return default weather when API fails"""
        return {
            'temperature_max': 15.0,
            'temperature_min': 10.0,
            'precipitation': 0.0,
            'windspeed_max': 10.0,
            'temperature_avg': 12.5,
            'weathercode': 0,
            'track_condition': 'good'
        }
    
    @staticmethod
    def get_weather_features_from_dict(weather_dict: Dict) -> Dict:
        """
        Convert raw weather dict to ML features
        
        Args:
            weather_dict: Output from get_weather()
        
        Returns:
            Dict with normalized features for ML
        """
        features = {
            'temp_normalized': (weather_dict['temperature_avg'] + 20) / 40,  # Normalize to 0-1
            'wind_factor': min(1.0, weather_dict['windspeed_max'] / 40),  # Headwind penalty
            'precipitation_normalized': min(1.0, weather_dict['precipitation'] / 10),
            'track_condition_score': WeatherService._track_condition_to_score(weather_dict['track_condition']),
        }
        return features
    
    @staticmethod
    def _track_condition_to_score(condition: str) -> float:
        """Convert track condition to numeric score"""
        conditions = {
            'good': 0.9,    # Optimal
            'soft': 0.7,    # Slightly slower
            'heavy': 0.5    # Much slower
        }
        return conditions.get(condition, 0.7)


# Test
if __name__ == '__main__':
    # Test: Weather for Vincennes racecourse (Nov 15, 2024)
    weather = WeatherService.get_weather('2024-11-15', 48.8381, 2.3953)
    print("Weather:", weather)
    
    features = WeatherService.get_weather_features_from_dict(weather)
    print("ML Features:", features)
