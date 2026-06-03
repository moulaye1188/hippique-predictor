# 🚀 GUIDE DE LANCEMENT - Prédicteur Hippique

## ⚡ Démarrage Ultra-Rapide (Docker - Recommandé)

### Sur Windows avec PowerShell

```powershell
# 1. Naviguez vers le répertoire du projet
cd "c:\Users\USER\Desktop\projet fintech\algo proba"

# 2. Vérifiez que Docker Desktop est lancé
# Sinon, lancez Docker Desktop depuis le menu Démarrer

# 3. Démarrez l'application
docker-compose up -d

# 4. Attendez 30-40 secondes (entraînement du modèle)

# 5. Ouvrez votre navigateur et allez à:
# http://localhost:5000

# Pour voir les logs en temps réel:
docker-compose logs -f app

# Pour arrêter l'application:
docker-compose down
```

## 🎯 Vérification du Lancement

Une fois lancée, vous devriez voir:
- ✅ Frontend accessible: `http://localhost:5000`
- ✅ API Health: `http://localhost:5000/api/health`
- ✅ Base de données créée: `./data/hippique.db`
- ✅ Modèle entraîné: `./models/race_prediction_model.h5`

## 📊 Utilisation de l'Application

### Page d'Accueil
1. **Onglet "Prédiction"** (défaut)
   - Remplir les infos de la course
   - Entrer les chevaux avec descriptions et cotes
   - Cliquer "Générer Pronostic"
   - Voir les résultats avec graphique

### Exemple de Données à Entrer

**Course:** GRAND NATIONAL DU TROT - LAVAL - 2850m

| # | Nom | Description | Cotes |
|---|-----|-------------|-------|
| 1 | JIBI DU FRUITIER | Ce protégé de la famille Bruneau n'a pu convaincre lors de sa rentrée à Vannes... | 77/1 |
| 2 | KEY OF LOVE | Après avoir animé les débats... elle adore ce parcours lavallois... | 7/1 |
| 10 | JOLIE STAR | Invaincue en trois sorties pour sa première campagne... | 20/1 |

### Format des Cotes
- ✅ Fractionnaire: `77/1`, `7/1`, `5/2`
- ✅ Décimale: `78.0`, `8.0`, `3.5`

## 🛠️ Troubleshooting

### Problem: "Connection refused" (Port 5000)

**Solution:**
```powershell
# Vérifier que Docker tourne
docker ps

# Si vide, lancer Docker Desktop manuellement

# Attendre 40 secondes après docker-compose up
# Le modèle s'entraîne au démarrage (normal)

# Vérifier les logs
docker-compose logs app
```

### Problem: "Docker daemon not running"

**Solution:**
1. Ouvrir Docker Desktop depuis le menu Démarrer
2. Attendre le message "Docker is running"
3. Relancer `docker-compose up -d`

### Problem: Port 5000 déjà utilisé

**Solution:**
```powershell
# Tuer le processus utilisant le port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Ou modifier le port dans docker-compose.yml
# Changer "5000:5000" en "5001:5000"
# Puis accéder à http://localhost:5001
```

### Problem: "No space left on device"

**Solution:**
```powershell
# Nettoyer Docker
docker system prune -a

# Relancer
docker-compose up -d
```

## 📈 Commandes Utiles

```powershell
# Voir l'état des conteneurs
docker-compose ps

# Voir les logs en temps réel
docker-compose logs -f app

# Voir les logs des derniers 100 lignes
docker-compose logs app --tail=100

# Arrêter proprement
docker-compose down

# Arrêter et supprimer les volumes (ATTENTION: supprime les données)
docker-compose down -v

# Redémarrer
docker-compose restart

# Reconstruire l'image (après modification du code)
docker-compose build --no-cache
docker-compose up -d

# Accéder au shell du conteneur
docker exec -it hippique-predictor bash
```

## 📦 Contenu du Projet

```
.
├── 📄 README.md                    # Documentation complète
├── 📄 LAUNCH.md                    # Ce fichier
├── 📄 docker-compose.yml           # Orchestration (À LANCER!)
├── 📄 Dockerfile                   # Configuration Docker
├── 📄 requirements.txt             # Dépendances Python
│
├── 📁 backend/
│   ├── app.py                      # 🔴 API Flask (cœur)
│   ├── model.py                    # 🧠 Modèle Deep Learning
│   ├── data_preparation.py         # 📊 Feature extraction
│   └── database.py                 # 💾 SQLite
│
├── 📁 frontend/
│   ├── index.html                  # 🖥️ Interface web
│   ├── style.css                   # 🎨 Styles
│   └── script.js                   # ⚡ Interactivité
│
├── 📁 data/                        # 📦 Base de données
│   └── hippique.db (créée au démarrage)
│
└── 📁 models/                      # 🤖 Modèles sauvegardés
    └── race_prediction_model.h5 (créé au démarrage)
```

## 🔐 Données

Vos données restent **100% locales**:
- ✅ Base de données: `./data/hippique.db`
- ✅ Modèle: `./models/race_prediction_model.h5`
- ✅ Zéro connexion externe (sauf NLTK data au premier lancement)

## ⚠️ Important

1. **Entraînement du modèle**: Au premier démarrage, le modèle s'entraîne sur ~200 courses synthétiques (1-2 minutes)
2. **Amélioration**: Pour de meilleures prédictions, alimentez le système avec vos propres données historiques
3. **Responsabilité**: Les prédictions sont indicatives - aucune garantie de profit

## 🎓 Architecture Complète

```
User (Navigateur)
    ↓
Frontend HTML/CSS/JS (port 5000)
    ↓
Flask API (Python)
    ↓
┌─────────────────────────────────┐
│ Composants Principaux           │
├─────────────────────────────────┤
│ • Parseur Texte (NLTK)          │
│ • Feature Extraction            │
│ • Conversion Cotes              │
│ • Normalisation Features        │
└─────────────────────────────────┘
    ↓
Deep Learning Model (TensorFlow)
    ↓
Prédictions de Probabilités
    ↓
Stockage SQLite
    ↓
Affichage Résultats (Chart.js)
```

## 📞 Support

**Erreur lors du lancement?**
1. Vérifier que Docker Desktop est bien lancé
2. Attendre 40 secondes après `docker-compose up -d`
3. Consulter les logs: `docker-compose logs app`
4. Redémarrer: `docker-compose down && docker-compose up -d`

---

✅ **Prêt à lancer!**

```powershell
cd "c:\Users\USER\Desktop\projet fintech\algo proba"
docker-compose up -d
# Puis ouvrir http://localhost:5000
```
