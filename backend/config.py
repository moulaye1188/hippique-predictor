"""Configuration centralisée - Support Windows + Docker"""
import os
from pathlib import Path

# Détecte l'environnement (Docker vs Local)
IN_DOCKER = os.path.exists('/app/backend')

# Répertoire de base
if IN_DOCKER:
    BASE_DIR = Path('/app')
else:
    # Sur Windows/Linux local, utilise le chemin relatif du script
    BASE_DIR = Path(__file__).parent.parent

# Répertoires de données
DATA_DIR = BASE_DIR / 'data'
MODELS_DIR = BASE_DIR / 'models'
FRONTEND_DIR = BASE_DIR / 'frontend'

# Créer les dossiers s'ils n'existent pas
DATA_DIR.mkdir(exist_ok=True, parents=True)
MODELS_DIR.mkdir(exist_ok=True, parents=True)

# Chemins de fichiers
DB_PATH = str(DATA_DIR / 'hippique.db')
MODEL_PATH = str(MODELS_DIR / 'hippique_model_v2.pkl')
SCALER_PATH = str(MODELS_DIR / 'scaler_v2.pkl')
PIPELINE_PATH = str(MODELS_DIR / 'pipeline_v2.pkl')

# Configuration Flask
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = FLASK_ENV == 'development'
STATIC_FOLDER = str(FRONTEND_DIR)

# Logging
LOG_DIR = DATA_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True, parents=True)
LOG_FILE = str(LOG_DIR / 'app.log')
