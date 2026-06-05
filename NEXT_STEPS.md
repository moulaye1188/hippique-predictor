# 🚀 PROCHAINES ÉTAPES - Roadmap Complète

## 📊 État Actuel (6 Juin 2026)

### ✅ Vient d'être Fixé
- **Bug critique**: Fallback `expert_score` n'était jamais calculé dans `app.py` → **RÉSOLU**
- **Feature Engineering**: Implémentation robuste avec fallbacks pour données PDF manquantes
- **Formule Expert Score**: Recalibrée avec poids market-aligned (odds: 50%, perf: 25%, conditions: 15%, trainer: 10%)
- **Docker**: Container opérationnel et réactif

### 🔄 État du Pipeline
```
PDF Upload → Parser (horses OK, metadata vide) → Features (avec fallbacks) → Prédictions
```

---

## 📈 PHASE 1: VALIDATION IMMÉDIATE (15-30 min)

### 1️⃣ Test des Scores Non-Zéro
**Objectif**: Vérifier que les prédictions passent de 0% à des valeurs réalistes

**Action**:
```bash
# Terminal 1: Voir les logs en direct
docker-compose logs -f app

# Terminal 2: Uploader le même PDF (28/05/2026)
# Résultats attendus:
# BOX OFFICER (7):     55-65% (favori)
# MUST BAY (1):        35-45% (deuxième favori)
# TI AMO BELLO (9):    30-40% (côté à 8/1)
# COSY BEAR (6):       25-35% (côté à 12/1)
```

**Critères de Succès**:
- ✓ Tous les chevaux ont une probabilité entre 1-99%
- ✓ BOX OFFICER (1er favori aux odds: 7/1) est classé premier
- ✓ La somme des probabilités ≈ 100%

### 2️⃣ Validation contre Résultats Réels
Comparer les prédictions avec le vrai résultat de la course:

| Position | Réel | Prédiction | Score? |
|----------|------|-----------|--------|
| 1ère | BOX OFFICER (7) | BOX OFFICER | ✓ EXACT |
| 2ème | TOO DARN QUICK (11) | TI AMO BELLO? | ? À tester |
| 3ème | REVE BLEU (2) | COSY BEAR? | ? À tester |

---

## 🎯 PHASE 2: AMÉLIORATION DU PARSER (30-60 min)

### Problème
Le PDF parser retourne **dictionnaires vides** pour:
- `classements` (FORME/CLASSE/PROGRES/REGULARITE)
- `pronostics` (expert predictions)
- `best_week` (top trainers/jockeys)

### Solution: Analyser Manuellement la Structure PDF

**Étapes**:
1. Extraire une page du PDF en texte brut
2. Identifier visuellement où sont les sections manquantes
3. Adapter les regex dans `pdf_parser_smart.py`

**Fichier à modifier**: [backend/pdf_parser_smart.py](backend/pdf_parser_smart.py)

**Fonctions à fixer**:
- `_parse_classements_section()` → Cherche "FORME / CLASSE / PROGRES" en JSON ou tableau
- `_parse_pronostics_sources()` → Cherche "TURFOMANIA" et autres sources
- `_parse_best_of_week()` → Cherche "MEILLEUR DE LA SEMAINE"

**Gain Potentiel**: +5-15% en précision des prédictions

---

## 🧠 PHASE 3: ENTRAÎNER UN MODÈLE RÉEL (1-2 heures)

### Étape 1: Collecter Plusieurs Courses
- Uploader 10-20 PDFs de courses différentes
- Laisser le système faire des prédictions fallback
- Attendre les résultats réels

### Étape 2: Créer Dataset d'Entraînement
**Schéma**:
```python
{
    'race_id': 1,
    'horse_number': 7,
    'horse_name': 'BOX OFFICER',
    'features': [0.3, 0.14, 0.5, ...],  # 15 features
    'actual_result': 1,  # 1=gagné, 0=perdu
    'finishing_position': 1,
    'odds_at_race': 0.125  # 7/1
}
```

### Étape 3: Entraîner RandomForest
```bash
# Script: train_model_from_races.py
python -c "
from backend.model_v2 import UpgradedHippiqueModel
model = UpgradedHippiqueModel()
model.train_from_database()  # Charge les 20 dernières courses
print('Model trained!')
"
```

**Résultat**: Modèle sauvegardé dans `/app/models/hippique_model_v2.pkl`

### Étape 4: Basculer du Fallback à Prédictions ML
Une fois le modèle entraîné, `app.py` utilisera automatiquement `model.predict_on_race()` au lieu de `expert_score` fallback.

---

## 🔬 PHASE 4: CALIBRATION FINE (30-45 min)

### Problème Actuel
La prédiction de **92% pour MUST BAY** (qui a terminé 6ème!) montrait une **sur-confiance extrême**.

### Solution: Softmax/Temperature Scaling
```python
# Dans model_v2.py, appliquer un "temperature" aux prédictions
temperatures = [1.0, 1.2, 1.5]  # Tester 3 valeurs
predictions = softmax(raw_predictions / temperature)
# Plus la température est haute, plus les probabilités sont "flattes"
# 1.2-1.5 devrait réduire la sur-confiance
```

### Validation
- BOX OFFICER: 55-65% (pas 92%)
- MUST BAY: 35-45% (pas 92%)
- Distribution plus réaliste

---

## 📱 PHASE 5: INTERFACE UTILISATEUR (Optionnel)

### Améliorations Frontend
```javascript
// Ajouter dans script.js:
1. Graphique "Courbe de probabilité" en temps réel
2. Comparaison avec les odds du marché
3. Historique des 5 dernières courses et taux de succès
4. Afficher le "confidence level" (bas/moyen/élevé)
```

### Dashboard
- Tableau des prédictions triées par probabilité
- Afficher odds vs probabilité (delta = valeur)
- Historique: Courses précédentes + résultats

---

## 🎓 PHASE 6: ANALYSE & INSIGHTS (Long terme)

### Métriques à Tracker
```
- Accuracy top-3: % de fois où le top-3 prédictions contient le gagnant
- Exacta Success: % d'exactas prédites correctement
- Value: € gagnés si on parierait sur les prédictions à > 50%
- Overconfidence Index: écart entre prédictions et réels résultats
```

### Optimisations Avancées
1. **Ensemble Methods**: Combiner RandomForest + GradientBoosting
2. **Cross-Validation**: Tester sur données historiques 2024-2025
3. **Feature Importance**: Savoir quelles features sont vraiment utiles
4. **A/B Testing**: Comparer plusieurs versions de formules

---

## ⏱️ Timeline Recommandée

| Phase | Durée | Priorité |
|-------|-------|----------|
| 1. Validation Scores | 15 min | 🔴 CRITIQUE |
| 2. Fixer Parser | 45 min | 🟡 HAUTE |
| 3. Entraîner Modèle | 90 min | 🟡 HAUTE |
| 4. Calibration | 30 min | 🟢 MOYENNE |
| 5. UI Améliorations | 60 min | 🟢 BASSE |
| 6. Analytics | Continu | 🔵 FUTURE |

---

## 🚨 Risques & Mitigations

| Risque | Impact | Solution |
|--------|--------|----------|
| Scores encore à 0% | ❌ System inop | Déboguer feature_engineering import |
| Parser ne retourne rien | ⚠️ Fallback seulement | Utiliser regex backup ou OCR |
| Modèle sur-apprend | ⚠️ Predictions mauvaises | Cross-validation + regularization |
| Sur-confiance (92%) | ⚠️ Mauvaises paris | Temperature scaling |

---

## 💾 Fichiers Clés à Monitorer

```
✅ MODIFIÉS (à tester):
- backend/app.py (ligne 130-145: fallback fixes)
- backend/feature_engineering.py (lignes 70-120: fallback logic)

⚠️ À AMÉLIORER:
- backend/pdf_parser_smart.py (_parse_classements_section, etc.)
- backend/model_v2.py (ajouter temperature scaling)

📊 À CRÉER:
- backend/train_model_from_races.py (script d'entraînement)
- backend/evaluate_model.py (metrics & validation)
```

---

## 🎯 Objectif Final

**Système de Prédiction Hippique Opérationnel:**
- ✅ PDF Upload → Parsing → Features → Prédictions
- ✅ Scores réalistes (1-99%) basés sur odds + perfs
- ✅ Modèle ML entraîné sur données réelles
- ✅ Calibration fine pour éviter sur-confiance
- ✅ Interface clean et informative

**Succès**: Si le système prédit correctement le Top-3 dans 60%+ des cas 🏆

---

## 🔗 Dépendances

```
Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phases 5-6
(URGENT)   (Optim)    (ML)       (Fine)       (Polish)
```

**Commencer par Phase 1 IMMÉDIATEMENT** ✨
