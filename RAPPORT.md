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
