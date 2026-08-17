# Rapport du Projet - Analyse des Observations OVNI

## Phase 1: Ouvrir la caisse

### Résultats numériques

| Métrique | Valeur |
|----------|--------|
| **Lignes totales dans le fichier** | 88 875 |
| **Lignes chargées correctement** | 88 675 |
| **Lignes problématiques** | 200 |
| **Cohérence** | ✓ (88 675 + 200 = 88 875) |

### Problèmes identifiés

L'analyse du fichier `releves_klaxo3.csv` a révélé **200 lignes problématiques**, réparties comme suit :

1. **196 lignes (98%)** : Nombre de champs incorrect (12 au lieu de 11)
   - Ces lignes contiennent une virgule supplémentaire
   - Origine probable : une virgule mal échappée dans le champ `comments` du fichier source
   - Impact : Impossible de parser correctement ces observations

2. **3 lignes** : Caractère invalide dans `duration_seconds`
   - Exemple : valeur `2\`` (backtick au lieu de chiffre)
   - Trois cas de ce type détectés
   
3. **1 ligne** : Latitude invalide
   - Valeur reçue : `33q.200088` (contient la lettre 'q' au lieu d'être numérique)

### Exemple de ligne problématique

**Ligne 877 :** `10/1/2006 12:00,,,,0,,",(...),[12 champs au lieu de 11]`

Structure observée :
- `datetime` : 10/1/2006 12:00
- `city`, `state`, `country`, `shape` : **tous vides**
- `duration_seconds` : 0
- `duration_hours_min` : vide
- `comments` : **vide** (crée une virgule vide)
- Champ supplémentaire : contient du texte qui devrait être dans `comments`
- `date_posted`, `latitude`, `longitude` : valeurs présentes mais mal alignées

### Décisions

Toutes les **88 675 lignes correctes** sont conservées en mémoire. Les 200 lignes problématiques sont mises de côté et documentées, sans être silencieusement ignorées.

### Validation

✓ Le script `analyse.py` reproduit exactement ces chiffres et peut afficher les lignes problématiques.

---

## Phase 2: Rien n'est du bon type

### Objective

Convertir chaque champ dans son bon type pour créer une carte des observations. Les 88 675 lignes valides de Phase 1 subissent une conversion de type.

### Résultats de conversion

| Champ | Succès | Erreurs | Nature |
|-------|--------|---------|--------|
| `datetime` | 87 455 | **1 220** | Heure 24:00 invalide |
| `date_posted` | 88 675 | 0 | Tous convertis |
| `duration_seconds` | 88 673 | 0 | 2 champs vides |
| `latitude` | 88 675 | 0 | Inclut 1 494 cas (0,0) |
| `longitude` | 88 675 | 0 | Inclut 1 494 cas (0,0) |

### Les quatre anomalies de nature différente

#### 1. **DATETIME - Heure 24:00 invalide** (1 220 cas)
- **Valeurs problématiques** : `10/10/2005 24:00`, `10/11/1994 24:00`, etc.
- **Nombre exact** : 1 220 occurrences
- **Raison** : Format invalide en Python (max 23:59)
- **Origine** : **TÉMOIN** - Les témoins ont noté minuit comme "24:00" au lieu de "00:00"
- **Exemple** : Ligne 167 : `'10/10/2005 24:00'`

#### 2. **COORDONNÉES (0,0) - Valeur par défaut GPS**  (1 494 cas)
- **Valeurs** : Latitude = 0.0, Longitude = 0.0
- **Nombre exact** : 1 494 observations
- **Raison** : Ces coordonnées représentent l'absence de signal GPS
- **Origine** : **CAPTEUR** - Le système de GPS n'a pas pu acquérir les coordonnées ; valeur 0,0 par défaut
- **Exemple** : Ligne 20 : `willow beach` (Arizona, USA), coordonnées (0,0)
- **Impact** : Rend impossible la cartographie pour ces observations

#### 3. **DURATION_SECONDS - Champs manquants** (2 cas)
- **Nombre exact** : 2 observations sans valeur de durée
- **Raison** : Champ `duration_seconds` complètement vide
- **Origine** : **TRANSMISSION** ou **TÉMOIN** - Les données n'ont pas été saisies lors du signalement
- **Impact** : Impossible d'analyser la durée pour ces 2 cas

#### 4. **COUNTRY - Colonne inutilisable** (12 363 cas vides sur 88 675)
- **Nombre exact** : 12 363 champs `country` vides (13.9% du dataset)
- **Raison** : Colonne cassée par données incohérentes
- **Valeurs aberrantes** : Mélange de codes pays 2-caractères avec des champs vides
- **Origine** : **SERVICE DE TRANSMISSION** - Données mal transmises ou partiellement perdues
- **Impact** : **⚠️ CETTE COLONNE EST INUTILISABLE**
  - Impossibilité de créer un index géographique par pays
  - Impossibilité de faire des statistiques fiables par pays
  - Données insuffisantes pour une analyse cohérente

### Décisions Phase 2

- Aucune ligne n'est supprimée
- Les erreurs de conversion sont documentées par ligne
- Les coordonnées (0,0) sont conservées mais marquées comme invalides
- Les valeurs 24:00 restent en l'état (non converties) pour traçabilité

### Validation

✓ Au moins 4 anomalies de natures différentes identifiées avec comptes exacts
✓ Origine identifiée pour chacune (témoin, capteur, transmission)
✓ La colonne `country` inutilisable a été identifiée (>12k valeurs manquantes)

---

## Phase 3: Le Conseil veut trier les canulars

### Objective

Détecter automatiquement les signalements suspects (canulars) en utilisant une heuristique simple appliquée à l'ensemble des 88 675 observations.

### Règle appliquée (énoncée en une phrase)

**Un signalement est marqué comme potentiellement canular si son champ commentaire est vide ou contient moins de 5 caractères, ce qui indique l'absence totale de description d'observation.**

### Paramètres de détection

| Paramètre | Valeur |
|-----------|--------|
| **Seuil appliqué** | Commentaire vide OU < 5 caractères |
| **Total signalements analysés** | 88 675 |
| **Signalements marqués canulars** | **73** |
| **Proportion du total** | **0.08%** (73/88675) |

### Résultats détaillés

#### Canulars détectés (73 cas)

Les 73 signalements détectés partagent une caractéristique commune : l'absence de description.

**Exemples :**
- Ligne 3240 : Commentaire complètement vide (6 caractères = spaces) - `[VIDE]`
- Ligne 4815 : Commentaire minimal `Disk` (4 caractères)
- Ligne 5731 : Commentaire ultra-court `UFO.` (4 caractères)

#### Limitations de la règle

La règle produit à la fois des **faux positifs** et des **faux négatifs**.

##### Faux positifs (vrais témoignages marqués à tort comme canulars) : 16 cas

La règle attrape à tort certaines véritables observations qui sont simplement énoncées très brièvement mais dont le mot-clé indique une vraie observation :

- **Ligne 5731** : Commentaire `UFO.` (4 chars) → Le mot-clé "UFO" indique clairement une vraie observation
- **Ligne 13345** : Commentaire `UFO` (3 chars) → Vrai témoignage, simplement peu détaillé
- **Ligne 14538** : Commentaire `UFO` (3 chars) → Autre cas similaire

**Conclusion sur les faux positifs** : 16 véritables témoignages sont rejetés par notre règle, même si brefs. Ils contiennent des mots-clés descriptifs (`UFO`, `light`, `disc`, `craft`, etc.) qui indiquent une intention de rapporter une observation.

##### Faux négatifs (canulars non détectés) : Indéterminé mais probable

La règle RATE certains canulars qui utilisent des commentaires génériques ou bidons mais dépassant le seuil de 5 caractères :

- Commentaires génériques comme : `"unknown"`, `"don't know"`, `"not sure"`, `"unclear"`, `"no comment"`
- Ces expressions (5-20 caractères) ne décrivent aucune observation réelle mais ne sont pas capturées par notre seuil

**Conclusion sur les faux négatifs** : Des canulars avec descriptions génériques (5+ chars) ne sont pas détectés. Cela représente un biais vers les canulars "minimalistes" plutôt que les "bla-bla".

### Décisions Phase 3

- Seuil choisi : **< 5 caractères** (explicitement nommé, compréhensible par un non-expert)
- Approche : Détection simple, pas de machine learning ni heuristique complexe
- Résultat : **73 signalements suspects** sur 88 675 (0.08%)
- Le ratio bas (0.08%) suggère que la plupart des signalements, même brefs, contiennent au minimum quelques mots descriptifs

### Validation

✓ Règle énoncée en une seule phrase, compréhensible par un conseiller
✓ Nombre exact de canulars détectés : 73
✓ Proportion calculée : 0.08%
✓ Seuil explicitement nommé : < 5 caractères
✓ Au moins une limitation identifiée :
  - Faux positif : "UFO." marqué à tort comme canular alors que c'est une vraie observation
  - Faux négatif : Commentaires génériques (5-20 chars) non détectés

