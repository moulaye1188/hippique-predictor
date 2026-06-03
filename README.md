# Prédicteur de Courses Hippiques - Deep Learning

🐴 **Application complète de prédiction de courses hippiques utilisant le Deep Learning**

## 🚀 Démarrage Rapide

### Avec Docker (Recommandé)

```bash
# 1. Vous placer dans le répertoire du projet
cd "c:\Users\USER\Desktop\projet fintech\algo proba"

# 2. Lancer avec docker-compose
docker-compose up -d

# 3. Accéder à l'application
# Ouvrir un navigateur et aller à: http://localhost:5000
```

### Sans Docker (Installation locale)

```bash
# 1. Créer un environnement virtuel
python -m venv venv

# 2. Activer l'environnement (Windows)
venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer le serveur Flask
cd backend
python app.py

# 5. Ouvrir http://localhost:5000 dans le navigateur
```

## 📋 Structure du Projet

```
.
├── backend/
│   ├── app.py                 # API Flask principale
│   ├── model.py               # Modèle Deep Learning
│   ├── database.py            # Gestion SQLite
│   └── data_preparation.py    # Feature extraction & preprocessing
├── frontend/
│   ├── index.html            # Interface web
│   ├── style.css             # Styles
│   └── script.js             # JavaScript frontend
├── data/                      # Base de données SQLite (créée automatiquement)
├── models/                    # Modèles sauvegardés (créés automatiquement)
├── Dockerfile                # Configuration Docker
├── docker-compose.yml        # Orchestration Docker
├── requirements.txt          # Dépendances Python
└── README.md                 # Ce fichier
```

## 🧠 Architecture du Modèle

### Features d'Entrée
- **Sentiment textuel** (analyse du texte de description)
- **Mots-clés** (victoires, podiums, expérience)
- **Historique** (mentions de performances)
- **Confiance** (indications de favoris)
- **Cotes de marché** (probabilités implicites)

### Architecture Neural Network
```
Input (5 features)
    ↓
Dense(128) + BatchNorm + Dropout(0.3)
    ↓
Dense(64) + BatchNorm + Dropout(0.3)
    ↓
Dense(32) + Dropout(0.2)
    ↓
Dense(1, sigmoid) → Probability
    ↓
Softmax normalization → 100%
```

### Entraînement
- **Loss:** Binary Crossentropy
- **Optimizer:** Adam (learning_rate=0.001)
- **Régularisation:** L2 (0.001)
- **Early Stopping:** Patience=10
- **Batch Size:** 16
- **Epochs:** 30-50

## 📊 Comment Utiliser

### 1. **Remplir les Informations de la Course**
   - Date, Hippodrome, Distance, Type de course

### 2. **Entrer les Chevaux**
   - Numéro, Nom, Description (texte), Cotes (ex: 77/1)
   - Le système parse le texte pour extraire des features

### 3. **Générer le Pronostic**
   - Cliquer sur "Générer Pronostic"
   - Le modèle analyse les données et retourne les probabilités

### 4. **Consulter les Résultats**
   - Classement des chevaux par probabilité
   - Graphique interactif
   - Historique des prédictions

## 🔧 Configuration

### Variables d'Environnement
```bash
FLASK_APP=app.py
FLASK_ENV=development
PYTHONUNBUFFERED=1
```

### Ports
- **5000**: Application Flask (Frontend + API)

### Volumes Docker
- `./data/` → `/app/data/` (Base de données SQLite)
- `./models/` → `/app/models/` (Modèles sauvegardés)
- `./backend/` → `/app/backend/` (Code backend)
- `./frontend/` → `/app/frontend/` (Code frontend)

## 📡 API Endpoints

### POST `/api/predict`
Générer une prédiction pour une course

**Request:**
```json
{
  "race_date": "2026-06-03",
  "hippodrome": "LAVAL",
  "distance": 2850,
  "race_type": "ATTELE",
  "conditions": "GRAND NATIONAL DU TROT",
  "horses": [
    {
      "number": 1,
      "name": "JIBI DU FRUITIER",
      "description": "...",
      "odds": "77/1"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "race_id": 1,
  "predictions": [
    {
      "rank": 1,
      "horse_name": "KEY OF LOVE",
      "predicted_probability": 0.35,
      "confidence": 0.35
    }
  ],
  "analysis": {
    "predicted_winner": "KEY OF LOVE",
    "winner_confidence": 0.35,
    "top_3": ["KEY OF LOVE", "JOLIE STAR", "JIBI DU FRUITIER"]
  }
}
```

### GET `/api/races`
Récupérer l'historique des courses

### GET `/api/races/<race_id>`
Détails d'une course spécifique

### GET `/api/health`
Vérifier l'état de l'application

## ⚠️ Limitations Importantes

1. **Données d'entraînement:** Le modèle est entraîné sur des données synthétiques. Pour de meilleurs résultats, alimentez-le avec de véritables données historiques.

2. **Facteurs imprévisibles:** Le modèle ne peut pas capturer:
   - La météo du jour
   - La forme physique actuelle du cheval
   - Les incidents en course
   - Les changements de jockey

3. **Probabilités implicites:** Les cotes contiennent déjà les probabilités du marché. Les prédictions du modèle ne guarantissent pas de profit.

4. **Usage responsable:** 
   - ⚠️ Ne jamais parier plus que vous ne pouvez vous permettre de perdre
   - À utiliser à titre informatif et éducatif uniquement
   - Les résultats réels dépendent de nombreuses variables non contrôlables

## 🛠️ Troubleshooting

### Docker ne démarre pas
```bash
# Vérifier les logs
docker-compose logs app

# Reconstruire l'image
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Erreur de connexion (Connection refused)
- Attendre 30-40 secondes après le démarrage
- Vérifier que le port 5000 est libre
- Vérifier les logs avec `docker-compose logs app`

### Modèle non trouvé
- Le modèle est créé automatiquement au premier démarrage
- Patience: l'entraînement prend 1-2 minutes

### Base de données verrouillée
- Arrêter tous les conteneurs: `docker-compose down`
- Supprimer le volume: `rm -rf data/hippique.db`
- Relancer: `docker-compose up -d`

## 📚 Technologies Utilisées

- **Backend:** Python 3.11, Flask, TensorFlow/Keras
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Database:** SQLite3
- **NLP:** NLTK (sentiment analysis, tokenization)
- **ML:** scikit-learn, NumPy, Pandas
- **Containerization:** Docker, Docker Compose
- **Visualisation:** Chart.js

## 🔐 Sécurité

- Les données sont traitées localement
- Pas de transmission vers des serveurs externes
- CORS activé pour le développement
- Validation des inputs côté serveur

## 📈 Amélioration Future

- [ ] Support de données historiques réelles
- [ ] Entraînement en continu avec nouveaux résultats
- [ ] API de scraping automatique (avec permissions légales)
- [ ] Dashboard de statistiques détaillées
- [ ] Alertes et notifications
- [ ] Support multi-hippodrome
- [ ] Modèles spécialisés par type de course

## 📄 Licence

Projet éducatif et informatif. Aucune garantie sur les résultats.

## 👨‍💻 Support

Pour des questions ou des améliorations:
1. Vérifier les logs: `docker-compose logs -f app`
2. Consulter la documentation des dépendances
3. Vérifier que tous les ports sont disponibles

---

**Version:** 1.0  
**Dernière mise à jour:** 2026-06-03  
**État:** ✅ Production-Ready
