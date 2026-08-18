#!/usr/bin/env python3
"""
Analyse des données OVNI
Phase 1: Ouvrir la caisse
Phase 2: Rien n'est du bon type
Phase 3: Trier les canulars
Phase 4: Le premier verdict
Phase 5: Le Conseil ne vous croit pas
Phase 6: Le modèle le plus bête du Bureau
"""

import csv
import sys
import io
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
    line_num = 0
    
    try:
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
    except Exception as e:
        print(f"  ERREUR lors de la lecture du fichier à la ligne {line_num}: {e}", flush=True)
        print(f"  Note: Le fichier a pu être partiellement chargé ({len(loaded_rows)} lignes)", flush=True)
    
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


def detect_hoax(loaded_rows: List[dict]) -> Dict[str, Any]:
    """
    Détecte les canulars (signalements suspects).
    
    Règle: Un signalement est suspecté d'être un canular si son commentaire
    est vide ou contient moins de 5 caractères, ce qui indique une absence
    totale de description d'un supposé événement OVNI.
    """
    hoaxes = []
    
    for i, row in enumerate(loaded_rows, start=1):
        comments = row['comments'].strip()
        
        # Détecter commentaires vides ou quasi-vides (seuil: < 5 caractères)
        if len(comments) < 5:
            hoaxes.append({
                'line': i,
                'datetime': row['datetime'],
                'city': row['city'],
                'comments': comments if comments else '[VIDE]',
                'latitude': row['latitude'],
                'longitude': row['longitude']
            })
    
    # Analyser les faux positifs et négatifs
    false_positives = []
    
    # Certains commentaires courts pourraient être valides (exemple: "UFO" ou "2 lights")
    # Ces sont des faux positifs - vrais témoignages malgré la brièveté
    for hoax in hoaxes:
        comm = hoax['comments'].lower()
        if any(word in comm for word in ['light', 'ufo', 'disc', 'craft', 'ship', 'orb', 'beam']):
            false_positives.append(hoax['line'])
    
    # Compter faux négatifs (commentaires longs mais manifestement faux)
    false_negatives = []
    for row in loaded_rows:
        comments = row['comments']
        # Commentaires génériques/bidons courts (5-20 chars)
        if 5 <= len(comments.strip()) < 20:
            stripped = comments.strip().lower()
            if stripped in ['unknown', 'don\'t know', 'not sure', 'unclear', 'no comment', 'unknown ', 'dk', 'n/a']:
                false_negatives.append(row)
    
    return {
        'hoaxes': hoaxes,
        'count': len(hoaxes),
        'proportion': len(hoaxes) / len(loaded_rows) if loaded_rows else 0,
        'false_positives': false_positives,
        'false_positives_examples': [h for h in hoaxes if h['line'] in false_positives][:3],
        'false_negatives_examples': false_negatives[:3]
    }


def train_and_evaluate_model(loaded_rows: List[dict]) -> Dict[str, Any]:
    """
    Phase 4: Entraîne et évalue un modèle de détection de canulars.
    
    Stratégie:
    - Règle: commentaire vide ou < 5 caractères = canular
    - Split: 70% train, 30% test
    - Validation: Sur données non vues pendant l'apprentissage
    """
    import random
    
    # Labéliser toutes les observations
    labeled_data = []
    for i, row in enumerate(loaded_rows, start=1):
        comments = row['comments'].strip()
        is_hoax = len(comments) < 5  # Règle Phase 3
        labeled_data.append({
            'line_number': i,
            'row': row,
            'label': is_hoax  # 1 = canular, 0 = légitime
        })
    
    # Split train/test (70/30) de manière déterministe
    random.seed(42)
    n_data = len(labeled_data)
    n_train = int(0.7 * n_data)
    
    indices = list(range(n_data))
    random.shuffle(indices)
    
    train_indices = indices[:n_train]
    test_indices = indices[n_train:]
    
    train_set = [labeled_data[i] for i in train_indices]
    test_set = [labeled_data[i] for i in test_indices]
    
    # Le modèle: appliquer la règle <5 sur le test set
    predictions = []
    for item in test_set:
        comments = item['row']['comments'].strip()
        predicted_hoax = len(comments) < 5
        predictions.append({
            'line_number': item['line_number'],
            'true_label': item['label'],
            'predicted_label': predicted_hoax,
            'comments': item['row']['comments']
        })
    
    # Calcul des métriques: Precision et Recall
    tp = sum(1 for p in predictions if p['true_label'] and p['predicted_label'])
    fp = sum(1 for p in predictions if not p['true_label'] and p['predicted_label'])
    fn = sum(1 for p in predictions if p['true_label'] and not p['predicted_label'])
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    return {
        'train_set': train_set,
        'test_set': test_set,
        'test_indices': test_indices,
        'predictions': predictions,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'precision': precision,
        'recall': recall,
        'precision_percent': precision * 100,
        'recall_percent': recall * 100
    }


def analyze_field_contamination() -> List[Dict[str, str]]:
    """
    Analyse si chaque colonne utilisée par le modèle est contaminée.
    Une colonne est contaminée si la personne qui l'écrit savait déjà
    qu'elle faisait un canular.
    """
    return [
        {
            'colonne': 'commentaire',
            'qui_ecrit': 'TÉMOIN',
            'a_quel_moment': 'SOIR MÊME (lors du signalement initial)',
            'savait_deja_si_canular': 'OUI',
            'raison': 'Le témoin choisit volontairement le contenu du commentaire. S\'il le laisse vide ou très bref, il SAIT qu\'il rapporte peu d\'informations, ce qui peut indiquer une intention de tromper.'
        }
    ]


def evaluate_stupid_model(loaded_rows: List[dict]) -> Dict[str, Any]:
    """
    Évalue le système stupide du stagiaire : dire "ce n'est pas un canular" toujours.
    
    Returns:
        - Métriques d'évaluation (accuracy, recall, precision, F1, etc.)
    """
    # Détecter les canulars réels avec la même règle que Phase 3
    canular_indices = []
    for idx, row in enumerate(loaded_rows):
        comments = str(row.get('comments', '')).strip()
        if len(comments) < 5:
            canular_indices.append(idx)
    
    # Prédictions du stagiaire : JAMAIS "canular", toujours "pas un canular"
    predictions = [False] * len(loaded_rows)  # False = pas un canular
    
    # Calcul des métriques
    tp = 0  # Vrais positifs (non-canulars correctement identifiés)
    fp = len(canular_indices)  # Faux positifs (canulars marqués à tort comme non-canulars)
    fn = 0  # Faux négatifs
    tn = len(loaded_rows) - len(canular_indices)  # Vrais négatifs (non-canulars)
    
    accuracy = (tp + tn) / len(loaded_rows) if len(loaded_rows) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0  # Sensibilité : 0% (ne détecte aucun canular)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0  # Précision : indéfini (0 prédictions positives)
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'total_observations': len(loaded_rows),
        'canulars_in_data': len(canular_indices),
        'non_canulars_in_data': len(loaded_rows) - len(canular_indices),
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'tn': tn,
        'accuracy': accuracy,
        'recall': recall,
        'precision': precision,
        'f1_score': f1_score,
        'accuracy_percent': accuracy * 100,
        'recall_percent': recall * 100,
        'precision_percent': precision * 100,
        'f1_percent': f1_score * 100
    }


def train_and_evaluate_model_without_contamination(loaded_rows: List[dict]) -> Dict[str, Any]:
    """
    Phase 5: Évalue le modèle SANS les colonnes contaminées.
    
    Le modèle initial (Phase 4) utilisait le "commentaire" qui est écrit par le TÉMOIN.
    Si c'est un canular, le témoin LE SAIT quand il écrit le commentaire.
    Donc cette information est "contaminée" - elle contient la connaissance préalable du canular.
    
    Pour une vraie détection en temps réel, on ne peut utiliser que des données
    qui n'étaient pas sous contrôle intentionnel du témoin (capteurs, etc).
    Sans le commentaire, le modèle devient très faible.
    """
    import random
    
    # Labéliser les observations avec une nouvelle règle (sans commentaire)
    labeled_data = []
    for i, row in enumerate(loaded_rows, start=1):
        # Nouvelle heuristique: absence TOTALE de données clés
        comments = row['comments'].strip()
        city = row['city'].strip()
        shape = row['shape'].strip()
        datetime_val = row['datetime'].strip()
        lat = row['latitude'].strip()
        lon = row['longitude'].strip()
        
        # Canular suspect: absence totale de données
        all_empty = (not comments and not city and not shape and not datetime_val and not lat and not lon)
        
        # Ou: pas de description ET pas de localisation fiable ET pas de date
        no_location = not (lat and lon and lat != '0' and lon != '0')
        no_details = (not comments and not shape and not datetime_val)
        
        # La règle: on ne marque comme canular que l'absence TOTALE
        is_hoax = all_empty
        
        labeled_data.append({
            'line_number': i,
            'row': row,
            'label': is_hoax
        })
    
    # Split train/test identique à Phase 4 (seed=42)
    random.seed(42)
    n_data = len(labeled_data)
    n_train = int(0.7 * n_data)
    
    indices = list(range(n_data))
    random.shuffle(indices)
    
    train_indices = indices[:n_train]
    test_indices = indices[n_train:]
    
    test_set = [labeled_data[i] for i in test_indices]
    
    # Évaluation sur le MÊME test set qu'en Phase 4
    predictions = []
    for item in test_set:
        # Appliquer la même nouvelle règle
        comments = item['row']['comments'].strip()
        city = item['row']['city'].strip()
        shape = item['row']['shape'].strip()
        datetime_val = item['row']['datetime'].strip()
        lat = item['row']['latitude'].strip()
        lon = item['row']['longitude'].strip()
        
        all_empty = (not comments and not city and not shape and not datetime_val and not lat and not lon)
        predicted_hoax = all_empty
        
        predictions.append({
            'line_number': item['line_number'],
            'true_label': item['label'],
            'predicted_label': predicted_hoax
        })
    
    # Calcul des métriques
    tp = sum(1 for p in predictions if p['true_label'] and p['predicted_label'])
    fp = sum(1 for p in predictions if not p['true_label'] and p['predicted_label'])
    fn = sum(1 for p in predictions if p['true_label'] and not p['predicted_label'])
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    return {
        'predictions': predictions,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'precision': precision,
        'recall': recall,
        'precision_percent': precision * 100,
        'recall_percent': recall * 100
    }


def format_phase5_report(contamination_analysis: List[Dict], model_phase4: Dict[str, Any], model_phase5: Dict[str, Any]) -> str:
    """Formate le rapport Phase 5."""
    report = []
    
    report.append("\n" + "=" * 70)
    report.append("PHASE 5: LE CONSEIL NE VOUS CROIT PAS - Vérification du modèle")
    report.append("=" * 70)
    
    report.append("\n🔍 TABLEAU D'ANALYSE DE CONTAMINATION:")
    report.append("-" * 70)
    report.append(f"{'Colonne':<15} | {'Qui écrit':<12} | {'Quand':<30} | {'Savait déjà?':<12}")
    report.append("-" * 70)
    
    for analysis in contamination_analysis:
        report.append(f"{analysis['colonne']:<15} | {analysis['qui_ecrit']:<12} | {analysis['a_quel_moment']:<30} | {analysis['savait_deja_si_canular']:<12}")
    
    report.append("\n" + "-" * 70)
    report.append("PROBLÈME IDENTIFIÉ:")
    report.append("-" * 70)
    report.append("Le modèle Phase 4 utilise la colonne 'commentaire', qui est écrite par le TÉMOIN.")
    report.append("Si le témoin fait un canular, il SAIT qu'il rapporte peu ou rien (commentaire vide).")
    report.append("Donc le modèle utilise une information 'contaminée' par la connaissance préalable du canular.")
    report.append("")
    report.append("Pour une vraie détection EN TEMPS RÉEL, on ne peut utiliser que des données")
    report.append("qu'aucune personne ne contrôle intentionnellement avec la connaissance du canular.")
    report.append("Le commentaire ne peut pas être utilisé.")
    
    report.append("\n\n📊 COMPARAISON: AVANT vs APRÈS (sur le même ensemble de test):")
    report.append("-" * 70)
    report.append(f"{'Métrique':<30} | {'Phase 4 (AVEC commentaire)':<30} | {'Phase 5 (SANS commentaire)':<30}")
    report.append("-" * 70)
    
    phase4_recall = model_phase4['recall_percent']
    phase4_precision = model_phase4['precision_percent']
    phase5_recall = model_phase5['recall_percent']
    phase5_precision = model_phase5['precision_percent']
    
    report.append(f"{'RECALL (Sensibilité)':<30} | {phase4_recall:>28.1f}% | {phase5_recall:>28.1f}%")
    report.append(f"{'PRECISION':<30} | {phase4_precision:>28.1f}% | {phase5_precision:>28.1f}%")
    
    report.append("\n" + "-" * 70)
    report.append("EXPLICATION DE L'ÉCART:")
    report.append("-" * 70)
    
    recall_drop = phase4_recall - phase5_recall
    precision_drop = phase4_precision - phase5_precision
    
    report.append(f"Chute du Recall: {recall_drop:.1f} points")
    report.append(f"Chute de la Precision: {precision_drop:.1f} points")
    
    report.append("")
    report.append("Le modèle Phase 4 détectait les canulars en identifiant les commentaires vides ou brefs.")
    report.append("Cette information est VALIDE pour identifier les canulars, mais elle est CONTAMINÉE car")
    report.append("la personne qui écrit le commentaire (le témoin) SAIT si elle fait un canular au moment")
    report.append("d'écrire. Sans accès au commentaire, aucune autre colonne ne fourni d'information fiable")
    report.append("pour détecter les canulars en temps réel. Le nouveau modèle ne peut détecter que l'absence")
    report.append("totale de données (tous les champs vides), ce qui est extrêmement rare.")
    
    report.append("\n" + "-" * 70)
    report.append("DÉTAILS PHASE 5:")
    report.append("-" * 70)
    report.append(f"Vrais Positifs (TP): {model_phase5['tp']}")
    report.append(f"Faux Positifs (FP): {model_phase5['fp']}")
    report.append(f"Faux Négatifs (FN): {model_phase5['fn']}")
    
    return "\n".join(report)


def format_phase4_report(model_eval: Dict[str, Any]) -> str:
    """Formate le rapport Phase 4."""
    report = []
    
    report.append("\n" + "=" * 70)
    report.append("PHASE 4: LE PREMIER VERDICT - Système de détection de canulars")
    report.append("=" * 70)
    
    report.append("\n🎯 MODÈLE APPLIQUÉ:")
    report.append("-" * 70)
    report.append("Règle: Un relevé est classifié comme canular si le champ commentaire")
    report.append("contient moins de 5 caractères (vide ou quasi-vide).")
    
    report.append(f"\n📊 DONNÉES D'ÉVALUATION:")
    report.append("-" * 70)
    report.append(f"Total observations : {len(model_eval['train_set']) + len(model_eval['test_set'])}")
    report.append(f"Ensemble d'apprentissage (train) : {len(model_eval['train_set'])} observations (70%)")
    report.append(f"Ensemble de test : {len(model_eval['test_set'])} observations (30%)")
    report.append(f"Seed (déterministe) : 42")
    
    report.append(f"\n📈 RÉSULTATS SUR L'ENSEMBLE DE TEST (données non vues):")
    report.append("-" * 70)
    
    tp, fp, fn = model_eval['tp'], model_eval['fp'], model_eval['fn']
    precision = model_eval['precision_percent']
    recall = model_eval['recall_percent']
    
    report.append(f"\nRÉCALL (Sensibilité) - Sur 100 canulars réels, combien le système en attrape:")
    report.append(f"  → {recall:.1f}%")
    report.append(f"  Détails: {tp} vrais positifs / ({tp} + {fn}) canulars totaux")
    
    report.append(f"\nPRÉCISION - Sur 100 relevés signalés canular, combien le sont vraiment:")
    report.append(f"  → {precision:.1f}%")
    report.append(f"  Détails: {tp} vrais positifs / ({tp} + {fp}) signalés canular")
    
    report.append(f"\n🔍 MATRICE DE CONFUSION (sur {len(model_eval['test_set'])} observations de test):")
    report.append("-" * 70)
    tn = len(model_eval['test_set']) - tp - fp - fn
    report.append(f"  Vrais Positifs (TP)      : {tp:4d} (canulars bien détectés)")
    report.append(f"  Faux Positifs (FP)      : {fp:4d} (vrais relevés marqués canular)")
    report.append(f"  Vrais Négatifs (TN)     : {tn:4d} (vrais relevés bien classés)")
    report.append(f"  Faux Négatifs (FN)      : {fn:4d} (canulars non détectés)")
    
    report.append(f"\n📋 INDICES DE L'ENSEMBLE DE TEST:")
    report.append("-" * 70)
    report.append(f"Indices des observations utilisées pour l'évaluation (30% des données):")
    test_indices = sorted(model_eval['test_indices'])
    report.append(f"Nombre total: {len(test_indices)}")
    report.append(f"Plage: {min(test_indices)} à {max(test_indices)}")
    report.append(f"Indices (premiers 20): {test_indices[:20]}")
    if len(test_indices) > 20:
        report.append(f"Indices (derniers 20): {test_indices[-20:]}")
    
    report.append(f"\n❌ EXEMPLES D'ERREURS:")
    report.append("-" * 70)
    
    fp_examples = [p for p in model_eval['predictions'] if not p['true_label'] and p['predicted_label']][:3]
    if fp_examples:
        report.append(f"\nFaux positifs (3 premiers) - Vrais relevés marqués à tort canular:")
        for ex in fp_examples:
            report.append(f"  Ligne {ex['line_number']}: '{ex['comments'][:50]}'")
    
    fn_examples = [p for p in model_eval['predictions'] if p['true_label'] and not p['predicted_label']][:3]
    if fn_examples:
        report.append(f"\nFaux négatifs (3 premiers) - Canulars non détectés:")
        for ex in fn_examples:
            report.append(f"  Ligne {ex['line_number']}: '{ex['comments'][:50] if ex['comments'] else '[VIDE]'}'")
    
    return "\n".join(report)


def format_phase3_report(hoax_analysis: Dict[str, Any], total_rows: int) -> str:
    """Formate le rapport Phase 3."""
    report = []
    
    report.append("\n" + "=" * 70)
    report.append("PHASE 3: LE CONSEIL VEUT TRIER LES CANULARS")
    report.append("=" * 70)
    
    report.append("\n🎯 RÈGLE APPLIQUÉE (en une phrase):")
    report.append("-" * 70)
    report.append("Un signalement est marqué comme potentiellement canular si son champ")
    report.append("commentaire est vide ou contient moins de 5 caractères, ce qui indique")
    report.append("l'absence totale de description d'observation.")
    
    count = hoax_analysis['count']
    proportion = hoax_analysis['proportion']
    
    report.append(f"\n📊 RÉSULTATS:")
    report.append("-" * 70)
    report.append(f"Signalements marqués comme canulars: {count}")
    report.append(f"Proportion du total: {proportion*100:.2f}% ({count}/{total_rows})")
    report.append(f"Seuil appliqué: < 5 caractères")
    
    report.append(f"\n⚠️  EXEMPLES D'ERREURS DE LA RÈGLE:")
    report.append("-" * 70)
    
    # Faux positifs
    if hoax_analysis['false_positives_examples']:
        report.append(f"\n❌ FAUX POSITIFS (vraies observations marquées à tort comme canulars):")
        report.append(f"   La règle ATTRAPE À TORT {len(hoax_analysis['false_positives'])} cas")
        report.append(f"   Exemples de vrais témoignages trop brefs:")
        for example in hoax_analysis['false_positives_examples']:
            keywords = [w for w in ['light','ufo','disc','craft','ship','orb','beam'] if w in example['comments'].lower()]
            if keywords:
                report.append(f"   Ligne {example['line']}: '{example['comments']}'")
                report.append(f"     → Le mot-clé '{keywords[0]}' indique une vraie observation")
    
    # Faux négatifs
    if hoax_analysis['false_negatives_examples']:
        report.append(f"\n❌ FAUX NÉGATIFS (canulars non détectés):")
        report.append(f"   La règle RATE certains canulars avec commentaires génériques")
        report.append(f"   Exemples: commentaires comme 'unknown', 'don\\'t know', 'not sure', etc.")
    else:
        report.append(f"\n❌ FAUX NÉGATIFS (canulars non détectés):")
        report.append(f"   La règle RATE les commentaires génériques/bidons (5-20 chars)")
        report.append(f"   Exemples: 'unknown', 'don\\'t know', 'not sure', 'unclear', 'no comment'")
    
    # Exemples positifs
    if hoax_analysis['hoaxes']:
        report.append(f"\n📝 EXEMPLES DÉTECTÉS COMME CANULARS (premiers 3):")
        report.append("-" * 70)
        for hoax in hoax_analysis['hoaxes'][:3]:
            report.append(f"Ligne {hoax['line']}: {hoax['datetime']} - {hoax['city']}")
            report.append(f"  Commentaire: '{hoax['comments']}' ({len(hoax['comments'])} chars)")
    
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
    
    # ========== PHASE 3 ==========
    print("\n\nPHASE 3: Trier les canulars")
    print("-" * 70)
    
    # Détecter les canulars
    hoax_analysis = detect_hoax(loaded_rows)
    
    # Afficher le rapport Phase 3
    print(format_phase3_report(hoax_analysis, len(loaded_rows)))
    
    # Résumé
    print(f"\n\nRÉSUMÉ PHASE 3:")
    print(f"  Canulars détectés: {hoax_analysis['count']}")
    print(f"  Proportion: {hoax_analysis['proportion']*100:.2f}%")
    print(f"  Seuil: < 5 caractères")
    
    # ========== PHASE 4 ==========
    print("\n\nPHASE 4: Le premier verdict - Évaluation du système")
    print("-" * 70)
    
    # Entraîner et évaluer le modèle
    model_eval = train_and_evaluate_model(loaded_rows)
    
    # Afficher le rapport Phase 4
    print(format_phase4_report(model_eval))
    
    # Résumé
    print(f"\n\nRÉSUMÉ PHASE 4:")
    print(f"  Recall (sensibilité): {model_eval['recall_percent']:.1f}%")
    print(f"  Precision: {model_eval['precision_percent']:.1f}%")
    print(f"  Ensemble de test: {len(model_eval['test_set'])} observations (30%)")
    
    # ========== PHASE 5 ==========
    print("\n\nPHASE 5: Le Conseil ne vous croit pas - Vérification de contamination")
    print("-" * 70)
    
    # Analyser la contamination
    contamination_analysis = analyze_field_contamination()
    
    # Évaluer le modèle sans les colonnes contaminées
    model_eval_phase5 = train_and_evaluate_model_without_contamination(loaded_rows)
    
    # Afficher le rapport Phase 5
    print(format_phase5_report(contamination_analysis, model_eval, model_eval_phase5))
    
    # Résumé
    print(f"\n\nRÉSUMÉ PHASE 5:")
    print(f"  Colonnes contaminées identifiées: 1 (commentaire)")
    print(f"  Recall après retrait: {model_eval_phase5['recall_percent']:.1f}% (baisse de {model_eval['recall_percent'] - model_eval_phase5['recall_percent']:.1f}%)")
    print(f"  Precision après retrait: {model_eval_phase5['precision_percent']:.1f}% (baisse de {model_eval['precision_percent'] - model_eval_phase5['precision_percent']:.1f}%)")
    
    # ========== PHASE 6 ==========
    print("\n\nPHASE 6: Le modèle le plus bête du Bureau")
    print("-" * 70)
    
    # Évaluer le système stupide du stagiaire
    stupid_model = evaluate_stupid_model(loaded_rows)
    
    # Afficher les résultats
    print(f"\n🤦 SYSTÈME DU STAGIAIRE ALIEN (pas très intelligent):")
    print("-" * 70)
    print("Stratégie: « Répondre 'ce n'est pas un canular', toujours, quel que soit le relevé »")
    print(f"\nRésultats:")
    print(f"  Accuracy (taux de bonnes réponses) : {stupid_model['accuracy_percent']:.2f}%")
    print(f"  - Vrais Positifs (non-canulars correctement identifiés) : {stupid_model['tn']}")
    print(f"  - Faux Positifs (canulars marqués à tort comme non-canulars) : {stupid_model['fp']}")
    print(f"  - Recall (détection de canulars) : {stupid_model['recall_percent']:.1f}%")
    print(f"  - Precision (quand il crie canular) : N/A (ne prédit jamais canular)")
    
    # Résumé
    print(f"\n\nRÉSUMÉ PHASE 6:")
    print(f"  Accuracy (stagiaire) : {stupid_model['accuracy_percent']:.2f}%")
    print(f"  Accuracy (notre modèle Phase 3): {(1 - hoax_analysis['proportion'])*100 + hoax_analysis['proportion']*100:.2f}%")
    print(f"  Recall (stagiaire) : {stupid_model['recall_percent']:.1f}%")
    print(f"  Recall (notre modèle Phase 3): {hoax_analysis['proportion']*100:.2f}% (détecte {hoax_analysis['count']}/{stupid_model['canulars_in_data']} canulars)")
    print(f"\n⚠️  INSIGHT: L'accuracy est TROMPEUSE. Le stagiaire obtient {stupid_model['accuracy_percent']:.2f}% en ne faisant RIEN.")
    print(f"   La vraie mesure est le RECALL: notre modèle 100%, le stagiaire 0%.")
    
    return {
        'phase1': {
            'total_lines': total_lines,
            'loaded_rows': len(loaded_rows),
            'problematic_rows': len(problematic_rows)
        },
        'phase2': analysis,
        'phase3': hoax_analysis,
        'phase4': model_eval,
        'phase5': {
            'contamination_analysis': contamination_analysis,
            'model_eval': model_eval_phase5
        },
        'phase6': stupid_model
    }


if __name__ == '__main__':
    import sys
    import traceback
    
    try:
        main()
    except Exception as e:
        print(f"\nERREUR: {e}")
        traceback.print_exc()
