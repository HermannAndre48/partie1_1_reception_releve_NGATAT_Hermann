#!/usr/bin/env python3
"""
Phase 1: Ouvrir la caisse
Charge et analyse le fichier releves_klaxo3.csv
"""

import csv
from pathlib import Path
from typing import List, Tuple, Dict

# Définition des champs
FIELDS = [
    'datetime',
    'city',
    'state',
    'country',
    'shape',
    'duration_seconds',
    'duration_hours_min',
    'comments',
    'date_posted',
    'latitude',
    'longitude'
]

def load_csv_data(filepath: str) -> Tuple[List[dict], List[Tuple[int, str, str]], int]:
    """
    Charge le fichier CSV et identifie les lignes problématiques.
    
    Returns:
        - Liste des lignes chargées correctement
        - Liste des lignes problématiques (numéro_ligne, contenu, raison)
        - Nombre total de lignes dans le fichier
    """
    loaded_rows = []
    problematic_rows = []
    total_lines = 0
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        for line_num, row in enumerate(reader, start=1):
            total_lines = line_num
            
            # Vérifier le nombre de champs
            if len(row) != len(FIELDS):
                reason = f"Nombre de champs incorrect: {len(row)} au lieu de {len(FIELDS)}"
                row_preview = ','.join(row[:3]) if len(row) > 0 else ""
                problematic_rows.append((line_num, row_preview, reason))
                continue
            
            # Créer un dictionnaire avec les champs
            try:
                record = dict(zip(FIELDS, row))
                
                # Validation additionnelle: seuls les vrais problèmes de format
                # Vérifier que duration_seconds est numériques SI non vide (peut être décimal)
                if record['duration_seconds']:
                    try:
                        float(record['duration_seconds'])
                    except ValueError:
                        reason = f"duration_seconds invalide: '{record['duration_seconds']}'"
                        row_preview = record['datetime']
                        problematic_rows.append((line_num, row_preview, reason))
                        continue
                
                # Vérifier latitude/longitude si non vide
                if record['latitude']:
                    try:
                        float(record['latitude'])
                    except ValueError:
                        reason = f"latitude invalide: '{record['latitude']}'"
                        row_preview = record['datetime']
                        problematic_rows.append((line_num, row_preview, reason))
                        continue
                
                if record['longitude']:
                    try:
                        float(record['longitude'])
                    except ValueError:
                        reason = f"longitude invalide: '{record['longitude']}'"
                        row_preview = record['datetime']
                        problematic_rows.append((line_num, row_preview, reason))
                        continue
                
                loaded_rows.append(record)
                
            except Exception as e:
                reason = f"Exception: {str(e)}"
                problematic_rows.append((line_num, row[0] if row else "", reason))
    
    return loaded_rows, problematic_rows, total_lines


def analyze_problematic_rows(problematic_rows: List[Tuple[int, str, str]]) -> str:
    """Analyse et documente les lignes problématiques."""
    if not problematic_rows:
        return "Aucune ligne problématique détectée."
    
    analysis = []
    issues = {}
    
    # Grouper par type de problème
    for line_num, content, reason in problematic_rows:
        if reason not in issues:
            issues[reason] = []
        issues[reason].append(line_num)
    
    analysis.append("\nProblèmes identifiés par type:")
    for reason, lines in sorted(issues.items(), key=lambda x: -len(x[1])):
        analysis.append(f"- {len(lines)} lignes: {reason}")
    
    analysis.append(f"\n1ère ligne problématique (ligne {problematic_rows[0][0]}):")
    analysis.append(f"   Raison: {problematic_rows[0][2]}")
    analysis.append(f"   Contenu: {problematic_rows[0][1]}")
    
    return '\n'.join(analysis)


def main():
    filepath = Path('releves_klaxo3.csv')
    
    if not filepath.exists():
        print(f"Erreur: {filepath} non trouvé")
        return
    
    print("Phase 1: Ouvrir la caisse")
    print("=" * 60)
    
    # Charger les données
    loaded_rows, problematic_rows, total_lines = load_csv_data(str(filepath))
    
    # Afficher les résultats
    print(f"\nNombre de lignes totales: {total_lines}")
    print(f"Nombre de lignes chargées: {len(loaded_rows)}")
    print(f"Nombre de lignes problématiques: {len(problematic_rows)}")
    
    # Analyse des problèmes
    print(analyze_problematic_rows(problematic_rows))
    
    # Afficher une ligne valide comme exemple
    if loaded_rows:
        print(f"\nExemple de ligne valide (ligne 1):")
        print(f"  datetime: {loaded_rows[0]['datetime']}")
        print(f"  city: {loaded_rows[0]['city']}")
        print(f"  country: {loaded_rows[0]['country']}")
        print(f"  comments: {loaded_rows[0]['comments'][:100]}...")
    
    return {
        'total_lines': total_lines,
        'loaded_rows': len(loaded_rows),
        'problematic_rows': len(problematic_rows)
    }


if __name__ == '__main__':
    main()
