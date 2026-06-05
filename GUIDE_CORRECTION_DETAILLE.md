# 📋 Guide de Correction Détaillé - Codebase

> **Pour corriger les problèmes identifiés vous-même**

---

## 🔴 PRIORITÉ 1: PROBLÈMES CRITIQUES

### **Correction #1: Fixer wsgi.py (Incohérence modèle)**

**Fichier:** `backend/wsgi.py`

**AVANT:**
```python
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_database
from model import initialize_model  # ❌ ANCIEN MODÈLE

# Initialize database on startup
print("Initializing database...")
try:
    init_database()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# Initialize model on startup
print("Initializing prediction model...")
try:
    model = initialize_model(input_dim=5)  # ❌ ANCIEN
    print("✅ Prediction model initialized successfully")
except Exception as e:
    print(f"⚠️ Model initialization warning: {e}")
```

**APRÈS (À copier-coller):**
```python
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

# wsgi_with_deps.py gère les dépendances, on la laisse faire le travail
# Ce fichier est juste un wrapper simple pour WSGI

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🐴 HIPPIQUE PREDICTOR v2 - Starting via WSGI")
    print("="*50)
    print("Frontend: http://localhost:5000")
    print("API Health: http://localhost:5000/api/health")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Pourquoi:** 
- ✓ Aligne avec app.py (qui utilise model_v2)
- ✓ Supprime la dépendance circulaire
- ✓ Cohérent avec le Docker

---

### **Correction #2: Créer un fichier config.py (Chemins relatifs)**

**Créer nouveau fichier:** `backend/config.py`

```python
"""Configuration centralisée - Support Windows + Docker"""
import os
from pathlib import Path

# Détecte l'environnement (Docker vs Local)
IN_DOCKER = os.path.exists('/app/backend')

# Répertoire de base
if IN_DOCKER:
    BASE_DIR = Path('/app')
else:
    # Sur Windows/Linux local, utilise le chemin relative du script
    BASE_DIR = Path(__file__).parent.parent

# Répertoires de données
DATA_DIR = BASE_DIR / 'data'
MODELS_DIR = BASE_DIR / 'models'
FRONTEND_DIR = BASE_DIR / 'frontend'

# Créer les dossiers s'ils n'existent pas
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Chemins de fichiers
DB_PATH = str(DATA_DIR / 'hippique.db')
MODEL_PATH = str(MODELS_DIR / 'hippique_model_v2.pkl')
SCALER_PATH = str(MODELS_DIR / 'scaler_v2.pkl')

# Configuration Flask
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = FLASK_ENV == 'development'
STATIC_FOLDER = str(FRONTEND_DIR)

# Logging
LOG_DIR = DATA_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = str(LOG_DIR / 'app.log')
```

**Étapes d'intégration:**

1. **Dans app.py (ligne 1-20):**
   ```python
   # AVANT:
   import sys
   sys.path.insert(0, '/app/backend')
   from flask import Flask
   app = Flask(__name__, static_folder='/app/frontend', static_url_path='')
   
   # APRÈS:
   import sys
   import os
   from pathlib import Path
   
   # Ajouter le répertoire backend au path
   sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
   
   from config import STATIC_FOLDER, DB_PATH, MODEL_PATH
   from flask import Flask
   
   app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')
   ```

2. **Dans database.py (ligne 5):**
   ```python
   # AVANT:
   DB_PATH = "/app/data/hippique.db"
   
   # APRÈS:
   from config import DB_PATH
   ```

3. **Dans database_schema_v2.py (ligne 5):**
   ```python
   # AVANT:
   DB_PATH = "/app/data/hippique.db"
   
   # APRÈS:
   from config import DB_PATH
   ```

4. **Dans model_v2.py (ligne 12-13):**
   ```python
   # AVANT:
   MODEL_PATH = "/app/models/hippique_model_v2.pkl"
   SCALER_PATH = "/app/models/scaler_v2.pkl"
   
   # APRÈS:
   from config import MODEL_PATH, SCALER_PATH
   ```

---

## 🟠 PRIORITÉ 2: PROBLÈMES IMPORTANTS

### **Correction #3: Nettoyer les fichiers dépréciés**

**À SUPPRIMER (40+ fichiers):**

```bash
# Fichiers App dépréciés
del backend\app_old.py
del backend\app_v2.py

# Modèles dépréciés
del backend\model.py

# Database dépréciée
del backend\database.py

# PDF Parsers dépréciés
del backend\pdf_parser_v2.py
del backend\pdf_parser_v3.py
del backend\pdf_parser_final.py
del backend\pdf_parser_ultimate.py
del backend\advanced_pdf_parser.py

# WSGI dépréciés
del backend\wsgi_with_deps.py  (OU METTRE À JOUR - voir bonus)

# Extracteurs/Fixers dépréciés
del backend\extract_horses_strategy2.py
del backend\horse_extractor_robust.py
del backend\fix_app_json.py
del backend\fix_features.py
del backend\fix_import.py
del backend\fix_parser_final.py
del backend\fix_parser_v3.py

# Tests fragmentés à déplacer dans /tests/
# (À créer dossier tests/)
mkdir backend\tests
move backend\test_*.py backend\tests\
move backend\debug_*.py backend\tests\debug\  (créer dossier debug/)
move backend\analyze_*.py backend\tests\debug\
move backend\import_*.py backend\tests\debug\

# Fichiers textes orphelins
del backend\page_0_text.txt
del backend\page_1_text.txt
del backend\page_2_text.txt  (s'il existe)
```

**Résultat final - backend/ plus propre:**
```
backend/
├── app.py                      ✓
├── config.py                   ✓ (NOUVEAU)
├── model_v2.py                 ✓
├── feature_engineering.py      ✓
├── database.py                 ✓ (MAINTENU)
├── database_schema_v2.py       ✓
├── pdf_parser_smart.py         ✓
├── pdf_routes.py               ✓
├── data_preparation.py         ✓
├── wsgi.py                     ✓ (RÉPARÉ)
├── tests/                      📁 (NOUVEAU)
│   ├── test_*.py
│   ├── test_model_v2.py
│   ├── test_smart.py
│   └── debug/
│       ├── debug_*.py
│       ├── analyze_*.py
│       └── fix_*.py
└── __pycache__/
```

---

### **Correction #4: Fixer la gestion d'erreurs**

**Fichier:** `backend/app.py` (lignes 40-50)

**AVANT:**
```python
# Load model
model = UpgradedHippiqueModel()
try:
    model.load()
    print("✓ Model V2 loaded successfully")
except:  # ❌ BARE EXCEPT - MAUVAIS!
    print("⚠ Model V2 not found - predictions will use expert scores only")
```

**APRÈS:**
```python
# Load model
model = UpgradedHippiqueModel()
try:
    model.load()
    logger.info("✓ Model V2 loaded successfully")
except FileNotFoundError as e:
    logger.warning(f"⚠ Model V2 not found: {e}")
    logger.warning("Predictions will use expert scores only")
except Exception as e:
    logger.error(f"❌ Unexpected error loading model: {e}")
    logger.warning("Predictions will use expert scores only")
```

**Fichier:** `backend/app.py` (lignes 75-90, dans la route PDF)

**AVANT:**
```python
try:
    # Parse PDF
    race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart(temp_path)
    
    if horses_df.empty:
        return jsonify({'error': 'Failed to extract horses from PDF'}), 400
    
    # ... rest of code
except:  # ❌ BARE EXCEPT
    pass
```

**APRÈS:**
```python
try:
    # Parse PDF
    race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart(temp_path)
    
    if horses_df.empty:
        logger.error("Failed to extract horses from PDF")
        return jsonify({'error': 'Failed to extract horses from PDF'}), 400
    
    # ... rest of code

except FileNotFoundError as e:
    logger.error(f"PDF file not found: {e}")
    return jsonify({'error': 'PDF file not found'}), 400
except ValueError as e:
    logger.error(f"PDF parsing error: {e}")
    return jsonify({'error': f'PDF parsing error: {str(e)}'}), 400
except Exception as e:
    logger.error(f"Unexpected error processing PDF: {e}", exc_info=True)
    return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
finally:
    # Clean up temp file
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.debug(f"Cleaned up temp file: {temp_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temp file: {e}")
```

---

### **Correction #5: Ajouter le logging**

**Fichier:** `backend/app.py` (À ajouter au TOP du fichier, ligne 1)

**AJOUTER:**
```python
"""Updated Flask routes - Integrate new frontend + Model V2"""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent.parent / 'data' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / 'app.log'

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler - rotate every 10MB, keep 5 backups
file_handler = RotatingFileHandler(
    str(LOG_FILE),
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("="*60)
logger.info("🐴 Hippique Predictor v2 - Starting")
logger.info("="*60)
```

**Puis remplacer tous les `print()` par `logger.info()`, `logger.warning()`, etc.**

Exemple:
```python
# AVANT:
print("✓ Model V2 loaded successfully")

# APRÈS:
logger.info("✓ Model V2 loaded successfully")
```

---

## 🟡 PRIORITÉ 3: AMÉLIORATIONS QUALITÉ

### **Correction #6: Créer structure de tests**

**Créer dossier:** `backend/tests/`

```bash
mkdir backend\tests
mkdir backend\tests\debug
mkdir backend\tests\fixtures
```

**Créer fichier:** `backend/tests/conftest.py`

```python
"""Pytest configuration and fixtures"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from config import DB_PATH

@pytest.fixture
def app():
    """Create app for testing"""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up test database"""
    yield
    # Cleanup code here
```

**Créer fichier:** `backend/tests/test_api.py`

```python
"""Test API routes"""
import pytest
from io import BytesIO

def test_health_check(client):
    """Test /api/health endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['version'] == '2.0'

def test_index(client):
    """Test root endpoint"""
    response = client.get('/')
    assert response.status_code == 200

def test_missing_pdf_file(client):
    """Test upload without file"""
    response = client.post('/api/load-race-from-pdf')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
```

**Lancer les tests:**
```bash
cd backend
pip install pytest pytest-cov
pytest tests/ -v --cov=.
```

---

### **Correction #7: Créer fichier .env**

**Créer fichier:** `.env` (à la racine du projet)

```env
# Environnement
FLASK_ENV=development
DEBUG=True

# Chemins (optionnel si config.py gère)
# Laissez vides - config.py détecte automatiquement

# Model
MODEL_THRESHOLD=0.5
BATCH_SIZE=32

# PDF Processing
MAX_PDF_SIZE_MB=50

# Logging
LOG_LEVEL=INFO
```

**Utiliser dans app.py:**
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Charge les variables du fichier .env

DEBUG = os.getenv('DEBUG', 'False') == 'True'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
```

---

### **Correction #8: Ajouter type hints**

**Exemple dans app.py:**

**AVANT:**
```python
@app.route('/api/load-race-from-pdf', methods=['POST'])
def load_race_from_pdf_v2():
    """Load race from PDF, parse, save to DB, and predict"""
```

**APRÈS:**
```python
from typing import Dict, Tuple
from flask import Response

@app.route('/api/load-race-from-pdf', methods=['POST'])
def load_race_from_pdf_v2() -> Tuple[Response, int]:
    """Load race from PDF, parse, save to DB, and predict
    
    Returns:
        Tuple[Response, int]: JSON response and HTTP status code
        
    Raises:
        ValueError: If PDF parsing fails
        FileNotFoundError: If uploaded file not found
    """
```

---

## ✅ CHECKLIST DE CORRECTION

```
PRIORITÉ 1 - CRITIQUE:
☐ Étape 1: Créer config.py
☐ Étape 2: Mettre à jour app.py pour utiliser config.py
☐ Étape 3: Mettre à jour database.py pour utiliser config.py
☐ Étape 4: Mettre à jour database_schema_v2.py pour utiliser config.py
☐ Étape 5: Mettre à jour model_v2.py pour utiliser config.py
☐ Étape 6: Corriger wsgi.py
☐ Étape 7: Tester: python app.py (local)

PRIORITÉ 2 - IMPORTANT:
☐ Étape 8: Ajouter logging à app.py
☐ Étape 9: Remplacer bare excepts par specific exceptions
☐ Étape 10: Créer dossier tests/ et déplacer fichiers test
☐ Étape 11: Supprimer fichiers dépréciés

PRIORITÉ 3 - QUALITÉ:
☐ Étape 12: Créer .env avec variables
☐ Étape 13: Ajouter type hints dans app.py
☐ Étape 14: Créer tests de base (conftest.py, test_api.py)
☐ Étape 15: Documenter dans README.md
```

---

## 🧪 TESTER LES CORRECTIONS

### **Test 1: Vérifier imports locaux (Windows)**
```bash
cd backend
python -c "from config import DB_PATH, MODEL_PATH; print(f'DB: {DB_PATH}'); print(f'Model: {MODEL_PATH}')"
```

**Résultat attendu:**
```
DB: c:\Users\USER\Desktop\projet fintech\algo proba\data\hippique.db
Model: c:\Users\USER\Desktop\projet fintech\algo proba\models\hippique_model_v2.pkl
```

### **Test 2: Lancer app localement**
```bash
cd backend
python app.py
```

**Résultat attendu:**
```
============================================================
🐴 Hippique Predictor v2 - Starting Server
============================================================
Frontend: http://localhost:5000
API Health: http://localhost:5000/api/health
============================================================
 * Running on http://127.0.0.1:5000
```

### **Test 3: Tester health check**
```bash
curl http://localhost:5000/api/health
```

**Résultat attendu:**
```json
{"status": "healthy", "version": "2.0", "model_loaded": true}
```

### **Test 4: Docker - Vérifier les imports**
```bash
docker-compose up -d
docker-compose logs app | grep "Model V2\|Error\|WARNING"
```

---

## 📝 NOTES IMPORTANTES

1. **AVANT de supprimer**, faites un backup:
   ```bash
   git init
   git add .
   git commit -m "Before cleanup"
   ```

2. **Après chaque correction**, testez:
   ```bash
   python -m py_compile backend/app.py  # Vérifier syntaxe
   ```

3. **Logging automatique** - Les fichiers vont dans:
   ```
   data/logs/app.log
   ```

4. **Si Docker change**, mettre à jour `config.py`:
   ```python
   IN_DOCKER = os.path.exists('/app/backend')
   ```

5. **Pour la production**, mettez `.env`:
   ```env
   FLASK_ENV=production
   DEBUG=False
   LOG_LEVEL=WARNING
   ```

---

## 🆘 SI VOUS AVEZ DES ERREURS

**Erreur: `ModuleNotFoundError: No module named 'config'`**
→ Assurez-vous que `config.py` est dans le dossier `backend/`

**Erreur: `DB_PATH` est dans `/app/data/`**
→ `config.py` ne détecte pas Docker. Vérifier: `if os.path.exists('/app/backend')`

**Erreur: Logs ne s'écrivent pas**
→ Vérifier permissions d'écriture dans `data/logs/`

**Docker plante**
→ Relancer et vérifier logs: `docker-compose logs -f app`

---

## 💪 BONNE CHANCE!

Vous avez maintenant un guide complet pour corriger votre codebase. Commencez par la **PRIORITÉ 1**, puis montez graduellement. Testez après chaque étape! 🚀

