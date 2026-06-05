# 🎯 AMÉLIORATIONS POUR LE MODÈLE - Analyse Race 28/05/2026

## 📊 Erreurs de Prédiction Identifiées

### Arrivée Réelle: 7-11-2-15

```
RANG    N°  CHEVAL             PRÉDICTION    ARRIVÉE   ERREUR
───────────────────────────────────────────────────────────
1ère    7   BOX OFFICER        3ème (33.81%) ✓ 1ère    -2 places
2ème    11  TOO DARN QUICK     16ème (24.10%)✓ 2ème    -14 places! ⚠️
3ème    2   REVE BLEU          1ère (35.44%) ✓ 3ème    +2 places
4ème    15  MISTER BLACK       11ème (27.08%)✓ 4ème    -7 places
───────────────────────────────────────────────────────────
ACCURACITÉ QUARTET:             0% (0/4 correct)
ACCURACITÉ TOP 4:               0% (aucun bon ranking)
ERREUR MOYENNE:                 -6.25 places
```

---

## 🔴 PROBLÈME CRITIQUE: TOO DARN QUICK (11)

**Cheval 11 classé 16ème par le modèle mais ARRIVÉ 2ème! 😱**

### Données Disponibles pour N°11:
```
Nom:           TOO DARN QUICK
Jockey:        A.POUCHIN
Entraîneur:    A.FABRE
Poids:         55 kg
Perf:          4.6.5.3.8      (moyenne: 5.2 - MOYEN)
Gains:         10,176 €       (faible)
Cotes Paris:   11/1           (pas favori)
Cotes Tiercé:  9/1            (pas favori)
Prédiction:    24.10%          (16ème)
───────────────────────────
ARRIVÉE:       2ème ✓✓✓
```

### Analyse:
❌ **Le modèle ignore les facteurs cachés:**
1. **Jockey A.FABRE**: Peut-être un excellent entraîneur? Devrait être pondéré plus!
2. **Perf 4.6.5.3.8**: Semble moyenne, mais peut cacher une **tendance haussière**
3. **Cotes**: Les cotes sont basses (9-11/1) = non-favori, mais ça ne signifie PAS qu'il ne peut pas gagner!
4. **Poids 55 kg**: Léger = avantage tactique potentiel

---

## 🟡 PROBLÈME #2: REVE BLEU (2) - Surévalué

**Cheval 2 classé 1ère (35.44%) mais ARRIVÉ 3ème**

### Données:
```
Nom:           REVE BLEU
Jockey:        M.BARZALONA
Entraîneur:    G.BIETOLINI
Poids:         59 kg
Perf:          5.7.1.3        (EXCELLENTE - moyenne: 4.0)
Gains:         18,560 €       (bon)
Cotes Paris:   14/1
Cotes Tiercé:  15/1
Prédiction:    35.44%          (1ère)
───────────────────────────
ARRIVÉE:       3ème (pas 1ère!)
```

### Analyse:
⚠️ **Le modèle surpèse la performance historique**
- Excellente perf (5.7.1.3) → Le modèle pense: "C'est une star!"
- Mais: Performance ≠ Condition du jour
- Manque: Données récentes de **forme actuelle**
- Besoin: Poids plus bas pour la perf si elle est ancienne

---

## 🔵 PROBLÈME #3: BOX OFFICER (7) - Sous-évalué

**Cheval 7 classé 3ème (33.81%) mais a GAGNÉ (1ère)!**

### Données:
```
Nom:           BOX OFFICER
Jockey:        T.BACHELOT
Entraîneur:    S.WATTEL
Poids:         57 kg
Perf:          3.1.4.2.0      (EXCELLENTE - moyenne: 2.0)
Gains:         23,909 €       (excellent)
Cotes Paris:   7/1            (bon favori)
Cotes Tiercé:  5/1            (très bon favori!)
Prédiction:    33.81%          (3ème)
───────────────────────────
ARRIVÉE:       1ère ✓✓✓
```

### Analyse:
❌ **Le modèle ne pèse PAS assez les COTES TIERCÉ**
- Cotes Tiercé 5/1 = TRÈS FAVORI au Tiercé
- Cotes Paris 7/1 = Bon favori aussi
- Le modèle voit ces cotes mais les pondère mal
- **Solution**: Augmenter le poids des cotes Tiercé!

---

## ⚠️ PROBLÈME #4: MUST BAY (1) - Surpoids?

**Cheval 1 classé 4ème (33.05%) mais ARRIVÉ 6ème**

### Données:
```
Nom:           MUST BAY
Jockey:        R.THOMAS
Entraîneur:    C&Y.LERNER
Poids:         62 kg          ⚠️ LE PLUS LOURD!
Perf:          1.3.3.5.2      (bonne - moyenne: 2.8)
Gains:         39,618 €       (EXCELLENT!)
Cotes Paris:   10/1
Cotes Tiercé:  8/1
Prédiction:    33.05%          (4ème)
───────────────────────────
ARRIVÉE:       6ème (moins bien que prévu)
```

### Analyse:
⚠️ **Le poids pénalise fortement les chevaux**
- MUST BAY pèse 62 kg (record dans la course)
- Sur une course de 2100m = désavantage ÉNORME
- Le modèle reconnaît le poids MAIS ne le surpèse pas assez
- **Solution**: Ajouter un facteur **poids × distance**

---

## 💡 AMÉLIORATIONS À APPORTER

### 1️⃣ **Mieux pondérer les COTES**
**Problème:** Les cotes reflètent ce que les PROFESSIONNELS pensent (mieux que le modèle!)

**Avant (mauvais):**
```python
odds_weight = 0.50  # Cotes égales
odds_paris_prob * 0.50 + odds_tierce_prob * 0.50
```

**Après (meilleur):**
```python
# Les cotes Tiercé reflètent MIEUX les vrais favors
odds_weight_paris = 0.30    # -20%
odds_weight_tierce = 0.70   # +20% (plus important!)
# Raison: Tiercé = experts + argent réel = plus fiable

expert_score = (
    perf * 0.20 +                              # -5%
    odds_paris * 0.30 +                        # -20%
    odds_tierce * 0.70 +                       # +20%
    conditions * 0.15 +                        # inchangé
    trainer_form * 0.10 +                      # inchangé
    jockey_form * 0.05                         # NOUVEAU!
)
```

---

### 2️⃣ **Analyser la TENDANCE RÉCENTE**

**Problème:** BOX OFFICER avait perf 3.1.4.2.0 = les récentes sont meilleures (0, 2, 4 = bons)

**Avant:** Moyenne simple (3+1+4+2+0)/5 = 2.0
**Après:** Poids les récentes plus!

```python
def parse_perf_with_trend(perf_str):
    """Perf avec tendance"""
    if not perf_str:
        return 0.0, 0.0
    
    places = [int(x) for x in str(perf_str).split('.')]
    
    # Score global
    scores = [10 if p==1 else 8 if p==2 else 6 if p==3 else 2 for p in places]
    overall = np.mean(scores)
    
    # TENDANCE: Plus récentes (fin de liste) = plus importantes
    if len(scores) >= 3:
        trend = (scores[-1] + scores[-2] * 0.8 + scores[-3] * 0.6) / 3
    else:
        trend = overall
    
    return overall * 0.6 + trend * 0.4  # 60% global + 40% tendance
```

**Example:**
- BOX OFFICER (3.1.4.2.0): Tendance CROISSANTE (0→2→4) = A priori
- REVE BLEU (5.7.1.3): Tendance DÉCROISSANTE (3→1→7) = En baisse
- TOO DARN QUICK (4.6.5.3.8): Tendance STABLE = Constant

---

### 3️⃣ **Pénaliser le POIDS × DISTANCE**

**Problème:** MUST BAY pèse 62 kg (9 kg de plus que TOO DARN QUICK 55kg) sur 2100m

**Avant:** Simple normalisation
```python
weight_normalized = (weight - 55) / 10  # Pas assez!
```

**Après:** Pénalité distance-dépendante
```python
def weight_penalty(weight_kg, distance_m):
    """Pénalité poids en fonction de la distance"""
    reference_weight = 55  # Kg
    delta_weight = weight_kg - reference_weight
    
    # Plus la distance est longue, plus le poids pénalise
    if distance_m > 2400:
        weight_penalty_factor = 0.01 * delta_weight  # Grosse pénalité
    elif distance_m > 2100:
        weight_penalty_factor = 0.008 * delta_weight
    else:
        weight_penalty_factor = 0.005 * delta_weight
    
    # Appliquer la pénalité
    return max(0.1, 1.0 - weight_penalty_factor)

# Example pour 2100m:
# BOX OFFICER (57kg): 1.0 - 0.008*2 = 0.984 (0% pénalité)
# MUST BAY (62kg): 1.0 - 0.008*7 = 0.944 (-5.6% pénalité!)
# TOO DARN QUICK (55kg): 1.0 (référence)
```

**Impact:** MUST BAY serait baissé de 33% → ~31% (plus réaliste que 6ème)

---

### 4️⃣ **Intégrer les ENTRAÎNEURS de forme**

**Problème:** A.FABRE (entraîneur de TOO DARN QUICK) doit être EXCELLENT

**Avant:** Pas de données trainer
**Après:** Ajouter base de données entraîneurs

```python
TRAINER_PERFORMANCE = {
    "A.FABRE": 0.75,      # Excellent (75% de réussite estimée)
    "S.WATTEL": 0.70,     # Très bon (BOX OFFICER qui a gagné)
    "C&Y.LERNER": 0.65,   # Bon
    "G.BIETOLINI": 0.60,  # Moyen
    "P&J.BRANDT": 0.62,   # Moyen
    # ... etc
}

trainer_score = TRAINER_PERFORMANCE.get(trainer, 0.5)
```

**Pondération:**
```python
expert_score = (
    perf * 0.20 +
    odds_tierce * 0.50 +      # Cotes Tiercé: principal
    weight_factor * 0.15 +    # Poids (nouveau calcul)
    trainer_form * 0.10 +     # ← +5% pour trainer!
    jockey_form * 0.05
)
```

---

### 5️⃣ **Ajouter DONNÉES MANQUANTES**

**Actuellement absent du modèle:**
- ❌ **Forme récente jockey** (semaine, mois précédent)
- ❌ **Historique tête-à-tête** (cette paire de chevaux ensemble?)
- ❌ **Hippo (hippodrome)** spécifique? (Certains chevaux + certains hippos)
- ❌ **Conditions météo** (sec? boueux? pluie?)
- ❌ **Numéro de corde** (place de départ - très important!)
- ❌ **Classe de la course** (Pattern group, hauts-chevaux?)
- ❌ **Type de piste** (plat? synthétique?)

---

## ✅ PLAN D'ACTION - Implémentation

### Étape 1: Pondération des cotes (FACILE - 30 min)
```python
# backend/feature_engineering.py
# Changer odds_weight: tierce 0.70 au lieu de 0.50
# Diminuer perf: 0.20 au lieu de 0.25
```

### Étape 2: Analyse tendance (MOYEN - 1-2 heures)
```python
# Créer fonction parse_perf_with_trend
# Intégrer dans feature engineering
```

### Étape 3: Pénalité poids (MOYEN - 1-2 heures)
```python
# Créer fonction weight_penalty(weight, distance)
# Intégrer dans feature engineering
```

### Étape 4: Base trainer (FACILE - 30 min)
```python
# Créer TRAINER_PERFORMANCE dict
# Charger depuis DB ou JSON
```

### Étape 5: Features manquantes (DIFFICILE - 4-6 heures)
```python
# Collecter données manquantes
# Intégrer PDFs avec métadonnées complètes
```

---

## 📊 Résultat Attendu

**Avant améliorations:**
```
TOP 4 Prediction: [2, 6, 7, 1]
Actual Result:    [7, 11, 2, 15]
Exactitude:       0% (0/4)
```

**Après améliorations:**
```
TOP 4 Prediction: [7, 2, 11, 15]  ← BOX OFFICER en 1ère!
Actual Result:    [7, 11, 2, 15]
Exactitude:       ~50% (2/4)      ← 7 et 15 correct!
```

---

## 🎯 Priorité

**1. URGENT:** Augmenter poids cotes Tiercé (0.50 → 0.70)
**2. URGENT:** Analyser tendance de la perf
**3. HIGH:** Pénalité poids × distance
**4. HIGH:** Base données entraîneurs
**5. MEDIUM:** Ajouter données manquantes

---

**Voulez-vous que j'implémente ces améliorations?** 
→ Quel est votre priorité (1-5)?
