# Exemple API Request/Response - Hippique Predictor

## Requête POST /api/predict

### Format de la Requête

```json
{
  "race_date": "2026-06-03",
  "hippodrome": "LAVAL",
  "distance": 2850,
  "race_type": "ATTELE",
  "conditions": "GRAND NATIONAL DU TROT (6ème Etape du G.N.T.)",
  "horses": [
    {
      "number": 1,
      "name": "JIBI DU FRUITIER",
      "description": "Ce protégé de la famille Bruneau n'a pu convaincre lors de sa rentrée à Vannes et sera seulement plaqué cette fois. Il s'attaque à forte partie et aura de meilleures opportunités prochainement. Sa tâche s'annonce difficile.",
      "odds": "77/1"
    },
    {
      "number": 2,
      "name": "KEY OF LOVE",
      "description": "Après avoir animé les débats dans le Prix du Perreux (Gr.3), le 13 mai à Vincennes, elle a simplement été dominée par l'excellent Lord Délo. Elle adore ce parcours lavallois (trois podiums en quatre sorties) et ne devrait pas décevoir.",
      "odds": "7/1"
    },
    {
      "number": 10,
      "name": "JOLIE STAR",
      "description": "Invaincue en trois sorties pour sa première campagne. Elle bénéficie d'un très bon potentiel de progression. À surveiller de près.",
      "odds": "20/1"
    }
  ]
}
```

### Format de la Réponse (Success 200)

```json
{
  "success": true,
  "race_id": 1,
  "race_date": "2026-06-03",
  "hippodrome": "LAVAL",
  "predictions": [
    {
      "rank": 1,
      "horse_number": 2,
      "horse_name": "KEY OF LOVE",
      "odds": "7/1",
      "decimal_odds": 8.0,
      "odds_probability": 0.125,
      "predicted_probability": 0.3487,
      "confidence": 0.3487
    },
    {
      "rank": 2,
      "horse_number": 10,
      "horse_name": "JOLIE STAR",
      "odds": "20/1",
      "decimal_odds": 21.0,
      "odds_probability": 0.047619,
      "predicted_probability": 0.2654,
      "confidence": 0.2654
    },
    {
      "rank": 3,
      "horse_number": 1,
      "horse_name": "JIBI DU FRUITIER",
      "odds": "77/1",
      "decimal_odds": 78.0,
      "odds_probability": 0.012821,
      "predicted_probability": 0.1234,
      "confidence": 0.1234
    }
  ],
  "analysis": {
    "total_horses": 3,
    "predicted_winner": "KEY OF LOVE",
    "winner_confidence": 0.3487,
    "top_3": ["KEY OF LOVE", "JOLIE STAR", "JIBI DU FRUITIER"]
  }
}
```

### Réponse d'Erreur (400/500)

```json
{
  "error": "Missing required fields"
}
```

## Autres Endpoints

### GET /api/health

**Réponse:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2026-06-03T10:30:45.123456"
}
```

### GET /api/races?limit=50

**Réponse:**
```json
{
  "success": true,
  "races": [
    {
      "id": 1,
      "date": "2026-06-03",
      "hippodrome": "LAVAL",
      "distance": 2850,
      "competitors": 10
    }
  ]
}
```

### GET /api/races/1

**Réponse:**
```json
{
  "success": true,
  "horses": [
    {
      "id": 1,
      "number": 1,
      "name": "JIBI DU FRUITIER",
      "odds_decimal": 78.0
    },
    {
      "id": 2,
      "number": 2,
      "name": "KEY OF LOVE",
      "odds_decimal": 8.0
    }
  ]
}
```

## Exemples cURL

### Prédiction Simple

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "race_date": "2026-06-03",
    "hippodrome": "LAVAL",
    "distance": 2850,
    "horses": [
      {
        "number": 1,
        "name": "Cheval 1",
        "description": "Bon cheval en forme",
        "odds": "5/1"
      }
    ]
  }'
```

### Vérifier la Santé

```bash
curl http://localhost:5000/api/health
```

### Récupérer l'Historique

```bash
curl http://localhost:5000/api/races?limit=10
```

## Formats de Cotes Supportés

### Fractionnaire
- `77/1` → 78.0 (décimal) → 1.28% probabilité
- `7/1` → 8.0 (décimal) → 12.5% probabilité
- `1/2` → 1.5 (décimal) → 66.67% probabilité
- `5/2` → 3.5 (décimal) → 28.57% probabilité

### Décimale
- `78.0` → 78.0 (décimal) → 1.28% probabilité
- `8.0` → 8.0 (décimal) → 12.5% probabilité

## Interprétation des Résultats

### Predicted Probability
- Probabilité que le modèle assigne au cheval
- Somme de tous les chevaux = 100%
- Basée sur features textuelles + cotes

### Odds Probability
- Probabilité implicite calculée à partir des cotes
- Représente le consensus du marché
- Ne tient pas compte du texte

### Confidence
- Identique à predicted_probability
- Indicateur de sûreté du pronostic

## Interprétation des Descriptions

### Mots-clés Positifs
- **Invaincue/invaincu:** Cheval jamais battu → +1.0 boost
- **Excellent:** Performance exceptionnelle → +0.9 boost
- **Podium(s):** Bon classement passé → +0.7 boost
- **Adore:** Aime le parcours → +0.8 boost
- **Victoires:** Historique de gains → +0.9 boost

### Mots-clés Négatifs
- **Difficile:** Tâche compliquée → -0.8 malus
- **Plaqué:** Relégué → -0.6 malus
- **Dominée:** Surpassé(e) → -0.8 malus
- **Rentrée:** Retour après repos → -0.4 malus
- **Blessure:** Problème physique → -0.9 malus

## Notes Techniques

### Feature Engineering
1. **Sentiment Score:** Analyse du ton du texte (-1 à 1)
2. **Keyword Score:** Détection des mots-clés importants
3. **Experience Score:** Mentions d'historique et d'expérience
4. **Confidence Score:** Indicateurs de favori
5. **Odds Probability:** Conversion des cotes en probabilités

### Architecture du Modèle
```
Input (5 features)
  ↓
Dense(128, relu) + BatchNorm + Dropout(0.3)
  ↓
Dense(64, relu) + BatchNorm + Dropout(0.3)
  ↓
Dense(32, relu) + Dropout(0.2)
  ↓
Dense(1, sigmoid)
  ↓
Softmax Normalization
  ↓
Output: Probabilities (sum = 100%)
```

### Loss Function
- **Binary Crossentropy:** Pour la classification
- **L2 Regularization:** 0.001 (éviter overfitting)
- **Early Stopping:** Patience = 10 epochs
- **Learning Rate:** 0.001 (Adam optimizer)

## Limitations et Avertissements

1. ⚠️ Le modèle est basé sur des données synthétiques au démarrage
2. ⚠️ Les performances réelles dépendent de la qualité des données historiques
3. ⚠️ Les facteurs imprévisibles (météo, forme du jour) ne sont pas captés
4. ⚠️ Les cotes contiennent déjà les probabilités du marché
5. ⚠️ Aucune garantie de profit - usage informatif uniquement

## Performance Expected

### Avec Données Synthétiques (Démarrage)
- Accuracy: ~70%
- Loss: 0.4-0.6

### Avec Données Réelles (Après Entraînement)
- Accuracy: 60-80% (dépend de la qualité)
- Correlation avec marché: ~0.7-0.85

## Testing en Ligne de Commande

### Avec PowerShell
```powershell
$body = @{
    race_date = "2026-06-03"
    hippodrome = "LAVAL"
    horses = @(@{
        number = 1
        name = "Test"
        description = "Test horse invaincue"
        odds = "5/1"
    })
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:5000/api/predict `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### Avec Python
```python
import requests
import json

url = "http://localhost:5000/api/predict"
payload = {
    "race_date": "2026-06-03",
    "hippodrome": "LAVAL",
    "horses": [
        {
            "number": 1,
            "name": "Test",
            "description": "Cheval invaincue",
            "odds": "5/1"
        }
    ]
}

response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2))
```

---

**Version:** 1.0  
**API Status:** ✅ Fully Functional  
**Documentation:** Complete
