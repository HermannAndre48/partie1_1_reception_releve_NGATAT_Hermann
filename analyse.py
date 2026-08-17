#!/usr/bin/env python3
"""
Analyse des données OVNI
Phase 1: Ouvrir la caisse
Phase 2: Rien n'est du bon type
"""

import csv
from pathlib import Path
from typing import List, Tuple, Dict, Any
from datetime import datetime

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


def convert_datetime_field(value: str) -> Tuple[Any, str]:
    """Convertit un string en datetime. Retourne (datetime, erreur) ou (None, erreur)."""
    if not value or not value.strip():
        return None, None
    
    value = value.strip()
    
    # Formats courants
    formats = [
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    ]
    
    # Vérifier si l'heure est 24:00 (invalide en Python)
    if "24:00" in value:
        return None, "24_hour_invalid"
    
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt), None
        except ValueError:
            continue
    
    return None, f"invalid_format"


def convert_date_field(value: str) -> Tuple[Any, str]:
    """Convertit un string en date."""
    if not value or not value.strip():
        return None, None
    
    value = value.strip()
    
    formats = [
        "%m/%d/%Y",
        "%m/%d/%y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date(), None
        except ValueError:
            continue
    
    return None, f"invalid_date"


def convert_float_field(value: str) -> Tuple[Any, str]:
    """Convertit un string en float."""
    if not value or not value.strip():
        return None, None
    
    value = value.strip()
    
    try:
        return float(value), None
    except ValueError:
        return None, f"invalid_float"


def analyze_types(loaded_rows: List[dict]) -> Dict[str, Any]:
    """
    Analyse et convertit les types. Retourne un rapport détaillé.
    """
    anomalies = {
        'datetime': {'errors': {}, 'success': 0},
        'date_posted': {'errors': {}, 'success': 0},
        'duration_seconds': {'errors': {}, 'success': 0, 'empty': 0},
        'latitude': {'errors': {}, 'success': 0, 'empty': 0},
        'longitude': {'errors': {}, 'success': 0, 'empty': 0},
        'country': {'empty': 0, 'valid': 0}
    }
    
    special_cases = {
        'coordinates_zero_zero': [],
        'country_empty': [],
        'invalid_character_errors': []
    }
    
    for i, row in enumerate(loaded_rows, start=1):
        # DATETIME
        if row['datetime']:
            val, error = convert_datetime_field(row['datetime'])
            if error:
                if error not in anomalies['datetime']['errors']:
                    anomalies['datetime']['errors'][error] = []
                anomalies['datetime']['errors'][error].append((i, row['datetime']))
            else:
                anomalies['datetime']['success'] += 1
        
        # DATE_POSTED
        if row['date_posted']:
            val, error = convert_date_field(row['date_posted'])
            if error:
                if error not in anomalies['date_posted']['errors']:
                    anomalies['date_posted']['errors'][error] = []
                anomalies['date_posted']['errors'][error].append((i, row['date_posted']))
            else:
                anomalies['date_posted']['success'] += 1
        
        # DURATION_SECONDS
        if not row['duration_seconds']:
            anomalies['duration_seconds']['empty'] += 1
        else:
            val, error = convert_float_field(row['duration_seconds'])
            if error:
                if error not in anomalies['duration_seconds']['errors']:
                    anomalies['duration_seconds']['errors'][error] = []
                anomalies['duration_seconds']['errors'][error].append((i, row['duration_seconds']))
                # Vérifier s'il y a un caractère invalide
                if any(c in row['duration_seconds'] for c in ['`', '~', '?', 'q']):
                    special_cases['invalid_character_errors'].append((i, row['duration_seconds']))
            else:
                anomalies['duration_seconds']['success'] += 1
        
        # LATITUDE
        if not row['latitude']:
            anomalies['latitude']['empty'] += 1
        else:
            val, error = convert_float_field(row['latitude'])
            if error:
                if error not in anomalies['latitude']['errors']:
                    anomalies['latitude']['errors'][error] = []
                anomalies['latitude']['errors'][error].append((i, row['latitude']))
                # Vérifier s'il y a un caractère invalide
                if any(c.isalpha() for c in row['latitude']):
                    special_cases['invalid_character_errors'].append((i, row['latitude']))
            else:
                anomalies['latitude']['success'] += 1
                # Vérifier coordonnées (0,0)
                if val == 0.0:
                    if row['longitude']:
                        try:
                            lon_val = float(row['longitude'])
                            if lon_val == 0.0:
                                special_cases['coordinates_zero_zero'].append((i, row['city'], row['country']))
                        except:
                            pass
        
        # LONGITUDE
        if not row['longitude']:
            anomalies['longitude']['empty'] += 1
        else:
            val, error = convert_float_field(row['longitude'])
            if error:
                if error not in anomalies['longitude']['errors']:
                    anomalies['longitude']['errors'][error] = []
                anomalies['longitude']['errors'][error].append((i, row['longitude']))
                # Vérifier s'il y a un caractère invalide
                if any(c.isalpha() for c in row['longitude']):
                    special_cases['invalid_character_errors'].append((i, row['longitude']))
            else:
                anomalies['longitude']['success'] += 1
        
        # COUNTRY - Détecter les vides
        if not row['country'] or not row['country'].strip():
            anomalies['country']['empty'] += 1
            special_cases['country_empty'].append(i)
        else:
            anomalies['country']['valid'] += 1
    
    return {
        'anomalies': anomalies,
        'special_cases': special_cases,
        'total_rows': len(loaded_rows)
    }


def format_phase2_report(analysis: Dict[str, Any]) -> str:
    """Formate le rapport Phase 2."""
    report = []
    anomalies = analysis['anomalies']
    special = analysis['special_cases']
    
    report.append("\n" + "=" * 70)
    report.append("PHASE 2: RIEN N'EST DU BON TYPE - Conversion et validation")
    report.append("=" * 70)
    
    # DATETIME
    report.append("\n1. CHAMP 'DATETIME'")
    report.append("-" * 70)
    total_datetime_errors = sum(len(v) for v in anomalies['datetime']['errors'].values())
    report.append(f"   Lignes converties avec succès: {anomalies['datetime']['success']}")
    report.append(f"   Erreurs de conversion: {total_datetime_errors}")
    
    for error_type, examples in anomalies['datetime']['errors'].items():
        report.append(f"\n   {error_type}: {len(examples)} cas")
        for line_num, value in examples[:3]:
            report.append(f"     Ligne {line_num}: {repr(value)}")
        if len(examples) > 3:
            report.append(f"     ... et {len(examples) - 3} autres cas")
        report.append(f"   Origine: TÉMOIN (notation erronée d'heure 24:00 au lieu de 00:00)")
    
    # DATE_POSTED
    report.append("\n2. CHAMP 'DATE_POSTED'")
    report.append("-" * 70)
    total_date_errors = sum(len(v) for v in anomalies['date_posted']['errors'].values())
    report.append(f"   Lignes converties avec succès: {anomalies['date_posted']['success']}")
    report.append(f"   Erreurs de conversion: {total_date_errors}")
    
    if total_date_errors > 0:
        for error_type, examples in anomalies['date_posted']['errors'].items():
            report.append(f"\n   {error_type}: {len(examples)} cas")
            for line_num, value in examples[:3]:
                report.append(f"     Ligne {line_num}: {repr(value)}")
    
    # DURATION_SECONDS
    report.append("\n3. CHAMP 'DURATION_SECONDS'")
    report.append("-" * 70)
    total_duration_errors = sum(len(v) for v in anomalies['duration_seconds']['errors'].values())
    report.append(f"   Lignes converties avec succès: {anomalies['duration_seconds']['success']}")
    report.append(f"   Champs vides: {anomalies['duration_seconds']['empty']}")
    report.append(f"   Erreurs de conversion: {total_duration_errors}")
    
    if total_duration_errors > 0:
        for error_type, examples in anomalies['duration_seconds']['errors'].items():
            report.append(f"\n   {error_type}: {len(examples)} cas")
            for line_num, value in examples[:3]:
                report.append(f"     Ligne {line_num}: {repr(value)}")
    
    # COORDINATES
    report.append("\n4. CHAMPS 'LATITUDE' ET 'LONGITUDE'")
    report.append("-" * 70)
    total_lat_errors = sum(len(v) for v in anomalies['latitude']['errors'].values())
    total_lon_errors = sum(len(v) for v in anomalies['longitude']['errors'].values())
    
    report.append(f"   Latitude - succès: {anomalies['latitude']['success']}, "
                  f"vides: {anomalies['latitude']['empty']}, "
                  f"erreurs: {total_lat_errors}")
    report.append(f"   Longitude - succès: {anomalies['longitude']['success']}, "
                  f"vides: {anomalies['longitude']['empty']}, "
                  f"erreurs: {total_lon_errors}")
    
    if special['invalid_character_errors']:
        report.append(f"\n   Caractères invalides: {len(special['invalid_character_errors'])} cas")
        for line_num, value in special['invalid_character_errors'][:3]:
            report.append(f"     Ligne {line_num}: {repr(value)}")
        if len(special['invalid_character_errors']) > 3:
            report.append(f"     ... et {len(special['invalid_character_errors']) - 3} autres cas")
        report.append(f"   Origine: SERVICE DE TRANSMISSION (erreur OCR ou corruption de données)")
    
    if special['coordinates_zero_zero']:
        report.append(f"\n   Coordonnées (0,0): {len(special['coordinates_zero_zero'])} cas")
        for line_num, city, country in special['coordinates_zero_zero'][:3]:
            report.append(f"     Ligne {line_num}: {city}, {country}")
        if len(special['coordinates_zero_zero']) > 3:
            report.append(f"     ... et {len(special['coordinates_zero_zero']) - 3} autres cas")
        report.append(f"   Origine: CAPTEUR (pas de signal GPS, valeur par défaut)")
    
    # COUNTRY anomaly - COLONNE ENTIÈRE INUTILISABLE
    report.append("\n5. CHAMP 'COUNTRY' - COLONNE INUTILISABLE")
    report.append("-" * 70)
    report.append(f"   Champs vides: {anomalies['country']['empty']} / {analysis['total_rows']} ({100*anomalies['country']['empty']//analysis['total_rows']}%)")
    report.append(f"   Champs valides: {anomalies['country']['valid']} / {analysis['total_rows']}")
    report.append(f"\n   ⚠️  CETTE COLONNE EST INUTILISABLE")
    report.append(f"   Raison: {anomalies['country']['empty']} valeurs manquantes rendent la colonne incohérente")
    report.append(f"   Origine: SERVICE DE TRANSMISSION (transmission partielle ou perte de données)")
    report.append(f"   Impact: Impossible de créer un index géographique par pays")
    
    return "\n".join(report)


def main():
    filepath = Path('releves_klaxo3.csv')
    
    if not filepath.exists():
        print(f"Erreur: {filepath} non trouvé")
        return
    
    print("ANALYSE DES DONNÉES OVNI")
    print("=" * 70)
    
    # ========== PHASE 1 ==========
    print("\nPHASE 1: Ouvrir la caisse")
    print("-" * 70)
    
    # Charger les données
    loaded_rows, problematic_rows, total_lines = load_csv_data(str(filepath))
    
    # Afficher les résultats
    print(f"\nNombre de lignes totales: {total_lines}")
    print(f"Nombre de lignes chargées: {len(loaded_rows)}")
    print(f"Nombre de lignes problématiques: {len(problematic_rows)}")
    
    # Analyse des problèmes Phase 1
    print(analyze_problematic_rows(problematic_rows))
    
    # ========== PHASE 2 ==========
    print("\n\nPHASE 2: Rien n'est du bon type")
    print("-" * 70)
    
    # Analyser les types
    analysis = analyze_types(loaded_rows)
    
    # Afficher le rapport Phase 2
    print(format_phase2_report(analysis))
    
    # Résumé
    anomalies = analysis['anomalies']
    print(f"\n\nRÉSUMÉ PHASE 2:")
    print(f"  Total erreurs DATETIME: {sum(len(v) for v in anomalies['datetime']['errors'].values())}")
    print(f"  Total erreurs COORDINATES: {sum(len(v) for v in anomalies['latitude']['errors'].values()) + sum(len(v) for v in anomalies['longitude']['errors'].values())}")
    print(f"  Coordonnées (0,0): {len(analysis['special_cases']['coordinates_zero_zero'])}")
    print(f"  Country vides: {anomalies['country']['empty']} / {analysis['total_rows']}")
    
    return {
        'phase1': {
            'total_lines': total_lines,
            'loaded_rows': len(loaded_rows),
            'problematic_rows': len(problematic_rows)
        },
        'phase2': analysis
    }


if __name__ == '__main__':
    main()
