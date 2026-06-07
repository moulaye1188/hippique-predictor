"""Test script - Verify weather integration works"""
import sys
sys.path.insert(0, '/app/backend') if '/' in __file__ else None

from weather_service import WeatherService
from hippodrome_coords import get_hippodrome_coords
import json

print("=" * 60)
print("WEATHER SERVICE TEST")
print("=" * 60)

# Test 1: Get Vincennes coordinates
print("\n1️⃣  Test hippodrome coordinates:")
vincennes = get_hippodrome_coords('VINCENNES')
print(f"   Vincennes: Lat={vincennes['latitude']}, Lon={vincennes['longitude']}")

# Test 2: Fetch weather for a test date
print("\n2️⃣  Test weather API (Open-Meteo):")
test_date = '2024-11-15'  # November 15, 2024
print(f"   Fetching weather for {test_date} at Vincennes...")

weather = WeatherService.get_weather(
    test_date,
    vincennes['latitude'],
    vincennes['longitude']
)
print(f"   ✅ Weather data received:")
print(f"      - Temperature: {weather['temperature_avg']:.1f}°C")
print(f"      - Precipitation: {weather['precipitation']:.1f}mm")
print(f"      - Wind speed: {weather['windspeed_max']:.1f} km/h")
print(f"      - Track condition: {weather['track_condition']}")

# Test 3: Convert to ML features
print("\n3️⃣  Test ML feature conversion:")
features = WeatherService.get_weather_features_from_dict(weather)
print(f"   ✅ ML Features:")
print(f"      - temp_normalized: {features['temp_normalized']:.3f}")
print(f"      - wind_factor: {features['wind_factor']:.3f}")
print(f"      - precipitation_normalized: {features['precipitation_normalized']:.3f}")
print(f"      - track_condition_score: {features['track_condition_score']:.3f}")

# Test 4: Paris-Longchamp
print("\n4️⃣  Test Paris-Longchamp:")
longchamp = get_hippodrome_coords('PARISLONGCHAMP')
weather_paris = WeatherService.get_weather(
    '2024-11-10',
    longchamp['latitude'],
    longchamp['longitude']
)
print(f"   ✅ Paris-Longchamp weather (2024-11-10):")
print(f"      - Track condition: {weather_paris['track_condition']}")
print(f"      - Wind: {weather_paris['windspeed_max']:.1f} km/h")

print("\n" + "=" * 60)
print("✅ WEATHER SERVICE TEST PASSED")
print("=" * 60)
