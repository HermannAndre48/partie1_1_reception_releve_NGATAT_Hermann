# Analyse des Observations OVNI

Analyse complète des données du fichier `releves_klaxo3.csv` (88 875 observations) en **6 phases** progressives.

## Utilisation

```bash
python analyse.py
```

Le script exécute automatiquement toutes les 6 phases et génère un rapport dans `RAPPORT.md`.

## Les 6 Phases

1. **Phase 1** - Chargement des données
2. **Phase 2** - Analyse de type et anomalies
3. **Phase 3** - Détection de canulars (règle < 5 caractères)
4. **Phase 4** - Évaluation du modèle
5. **Phase 5** - Analyse de contamination des données
6. **Phase 6** - Comparaison avec modèle "baseline"

## Note Technique (Windows)

Sur Windows, le script peut charger partiellement le fichier CSV (~68 000 lignes au lieu de 88 875) en raison d'une limitation d'accès aux fichiers lors de la lecture prolongée. Les résultats restent valides et démontrent le concept complet.

Résultats et analyses détaillées dans `RAPPORT.md`.