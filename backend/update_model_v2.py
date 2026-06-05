#!/usr/bin/env python3
with open('/app/backend/model_v2.py', 'r') as f:
    content = f.read()

old = 'from feature_engineering import RaceFeatureEngineer\n\nMODEL_PATH = "/app/models/hippique_model_v2.pkl"\nSCALER_PATH = "/app/models/scaler_v2.pkl"'
new = 'from config import MODEL_PATH, SCALER_PATH\nfrom feature_engineering import RaceFeatureEngineer'

content = content.replace(old, new)

with open('/app/backend/model_v2.py', 'w') as f:
    f.write(content)

print("✅ Updated model_v2.py to use config.py")
