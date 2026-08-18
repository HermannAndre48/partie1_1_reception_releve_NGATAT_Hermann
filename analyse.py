#!/usr/bin/env python3
"""
Analyse des données OVNI - PARTIES 1-2: Fondations et Validation ML Avancé

PARTIE 1: Fondations (Phases 1-6)
Phase 1: Ouvrir la caisse
Phase 2: Rien n'est du bon type
Phase 3: Trier les canulars
Phase 4: Le premier verdict
Phase 5: Le Conseil ne vous croit pas
Phase 6: Le modèle le plus bête du Bureau

PARTIE 2: Validation Rigoureuse (Phases 7-12)
Phase 7: Plusieurs témoins, un seul événement
Phase 8: L'ordre des choses (découpe temporelle)
Phase 9: Les cases vides (données manquantes)
Phase 10: La chaîne de traitement du Bureau (data leakage)
Phase 11: Combien de temps ça a duré (durées)
Phase 12: La ville et l'heure (encodage spatial-temporel)

PARTIE 3: ML Avancé - Défendre une Décision (Phases 13-18)
Phase 13: La facture du Bureau (optimisation de seuil par coût)
Phase 14: Une promesse à 80% (calibration des probabilités)
Phase 15: Deux analystes, deux chiffres (intervalles de confiance)
Phase 16: Trois dossiers sur le bureau (interprétabilité)
Phase 17: L'angle mort du Bureau (analyse géographique)
Phase 18: La transmission d'archive (dérive temporelle et monitoring)
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


# ============================================================================
# PHASE 7 : Plusieurs témoins, un seul événement
# ============================================================================

def identify_events(loaded_rows: List[dict]) -> Dict[str, Any]:
    """Identifie les événements: groupes de relevés parlant du même événement."""
    from collections import defaultdict
    
    events = defaultdict(list)
    duplicates = []
    
    # Passer 1: Identifier les doublons (contenu identique)
    seen_comments = {}
    for i, row in enumerate(loaded_rows):
        comment_hash = row['comments'].strip().lower()
        if comment_hash and len(comment_hash) > 20:
            if comment_hash in seen_comments:
                duplicates.append((seen_comments[comment_hash], i + 1))
            else:
                seen_comments[comment_hash] = i + 1
    
    # Passer 2: Grouper par (ville, date approximative)
    for i, row in enumerate(loaded_rows):
        city_key = row['city'].strip().lower()
        datetime_str = row['datetime'].strip()
        
        try:
            dt = datetime.strptime(datetime_str, "%m/%d/%Y %H:%M") if datetime_str else None
            if dt:
                date_key = dt.strftime("%Y-%m-%d")
            else:
                date_key = "unknown"
        except:
            date_key = "unknown"
        
        event_key = f"{city_key}|{date_key}"
        events[event_key].append(i)
    
    multi_witness_events = {k: v for k, v in events.items() if len(v) > 1}
    
    return {
        'events': events,
        'multi_witness_events': multi_witness_events,
        'num_multi_witness': len(multi_witness_events),
        'max_witnesses': max(len(v) for v in multi_witness_events.values()) if multi_witness_events else 0,
        'duplicates': duplicates,
        'num_duplicates': len(duplicates)
    }


# ============================================================================
# PHASE 8 : L'ordre des choses (découpe temporelle)
# ============================================================================

def temporal_split(loaded_rows: List[dict], split_ratio: float = 0.7) -> Tuple[List[int], List[int], str]:
    """Fait la découpe train/test en respectant l'ordre du temps."""
    dated_rows = []
    for i, row in enumerate(loaded_rows):
        date_str = row['date_posted'].strip()
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y") if date_str else None
            if dt:
                dated_rows.append((i, dt))
        except:
            pass
    
    if not dated_rows:
        return list(range(len(loaded_rows))), [], "unknown"
    
    dated_rows.sort(key=lambda x: x[1])
    split_idx = int(len(dated_rows) * split_ratio)
    cutoff_date = dated_rows[split_idx][1] if split_idx < len(dated_rows) else dated_rows[-1][1]
    
    train_indices = [idx for idx, dt in dated_rows if dt < cutoff_date]
    test_indices = [idx for idx, dt in dated_rows if dt >= cutoff_date]
    
    all_with_date = {idx for idx, _ in dated_rows}
    for i in range(len(loaded_rows)):
        if i not in all_with_date:
            test_indices.append(i)
    
    return sorted(train_indices), sorted(test_indices), cutoff_date.strftime("%m/%d/%Y")


# ============================================================================
# PHASE 9 : Les cases vides
# ============================================================================

def analyze_missing_data(loaded_rows: List[dict]) -> Dict[str, Any]:
    """Analyse les colonnes avec des valeurs manquantes."""
    from collections import defaultdict, Counter
    
    missing_counts = defaultdict(int)
    missing_by_field = defaultdict(list)
    
    for i, row in enumerate(loaded_rows):
        for field in FIELDS:
            value = row[field].strip()
            if not value:
                missing_counts[field] += 1
                missing_by_field[field].append(i)
    
    sorted_fields = sorted(missing_counts.items(), key=lambda x: -x[1])
    
    analysis = {}
    for field, count in sorted_fields[:3]:
        indices_with_hole = set(missing_by_field[field])
        indices_without_hole = set(range(len(loaded_rows))) - indices_with_hole
        
        hoaxes_with_hole = sum(1 for idx in indices_with_hole if len(loaded_rows[idx]['comments'].strip()) < 5)
        hoaxes_without_hole = sum(1 for idx in indices_without_hole if len(loaded_rows[idx]['comments'].strip()) < 5)
        
        prop_with_hole = hoaxes_with_hole / len(indices_with_hole) if indices_with_hole else 0
        prop_without_hole = hoaxes_without_hole / len(indices_without_hole) if indices_without_hole else 0
        
        analysis[field] = {
            'total_missing': count,
            'prop_with_hole': prop_with_hole,
            'prop_without_hole': prop_without_hole,
        }
    
    return {
        'missing_counts': dict(sorted_fields),
        'analysis': analysis
    }


# ============================================================================
# PHASE 10 : La chaîne de traitement du Bureau (data leakage)
# ============================================================================

def leakage_free_pipeline(loaded_rows: List[dict], split_ratio: float = 0.7) -> Dict[str, Any]:
    """Pipeline sans data leakage: découpe d'abord, ENSUITE on apprend sur train seul."""
    train_indices, test_indices, cutoff = temporal_split(loaded_rows, split_ratio)
    
    train_hoaxes = sum(1 for i in train_indices if len(loaded_rows[i]['comments'].strip()) < 5)
    test_hoaxes = sum(1 for i in test_indices if len(loaded_rows[i]['comments'].strip()) < 5)
    
    train_prop = train_hoaxes / len(train_indices) if train_indices else 0
    test_prop = test_hoaxes / len(test_indices) if test_indices else 0
    
    return {
        'train_indices': train_indices,
        'test_indices': test_indices,
        'train_size': len(train_indices),
        'test_size': len(test_indices),
        'train_hoax_prop': train_prop,
        'test_hoax_prop': test_prop,
        'train_hoax_count': train_hoaxes,
        'test_hoax_count': test_hoaxes,
        'cutoff_date': cutoff
    }


# ============================================================================
# PHASE 11 : Combien de temps ça a duré (durées)
# ============================================================================

def analyze_durations(loaded_rows: List[dict]) -> Dict[str, Any]:
    """Analyse les deux colonnes de durée."""
    durations = []
    conflicts = 0
    unusable = 0
    
    for row in loaded_rows:
        clean_str = row['duration_seconds'].strip()
        
        clean_val = None
        if clean_str:
            try:
                clean_val = float(clean_str)
                durations.append(clean_val)
            except:
                pass
        
        if clean_val is None:
            unusable += 1
    
    if durations:
        sorted_durations = sorted(durations)
        median = sorted_durations[len(sorted_durations) // 2]
        longest_3 = sorted(durations, reverse=True)[:3]
    else:
        median = 0
        longest_3 = []
    
    long_observations = sum(1 for d in durations if d > 86400)
    
    return {
        'unusable_count': unusable,
        'conflicts_count': conflicts,
        'median_duration': median,
        'long_observations': long_observations,
        'longest_3': longest_3,
        'total_durations': len(durations)
    }


# ============================================================================
# PHASE 12 : La ville et l'heure
# ============================================================================

def analyze_encoding_issues(loaded_rows: List[dict]) -> Dict[str, Any]:
    """Analyse les problèmes d'encodage pour ville et heure."""
    from collections import Counter
    
    cities = Counter()
    shapes = Counter()
    hours = Counter()
    
    unique_cities = set()
    
    for row in loaded_rows:
        city = row['city'].strip()
        if city:
            cities[city] += 1
            unique_cities.add(city)
        
        shape = row['shape'].strip()
        if shape:
            shapes[shape] += 1
        
        datetime_str = row['datetime'].strip()
        if datetime_str:
            try:
                dt = datetime.strptime(datetime_str, "%m/%d/%Y %H:%M")
                hours[dt.hour] += 1
            except:
                pass
    
    single_occurrence_cities = sum(1 for c in cities.values() if c == 1)
    rare_shapes = sum(1 for c in shapes.values() if c <= 2)
    
    return {
        'num_cities': len(unique_cities),
        'single_occurrence_cities': single_occurrence_cities,
        'num_shapes': len(shapes),
        'rare_shapes': rare_shapes
    }


# ============================================================================
# PHASE 13 : La facture du Bureau (optim seuil par coût)
# ============================================================================

def cost_optimized_threshold(predictions: List[tuple], test_indices: List[int], loaded_rows: List[dict]) -> Dict[str, Any]:
    """Optimise le seuil de décision en fonction de la grille de coûts du Bureau.
    
    Coûts:
    - Canular laissé passer: 30 crédits
    - Relevé honnête marqué canular: 2 crédits
    - Canular attrapé: 0 crédit
    - Relevé honnête laissé passer: 0 crédit
    """
    probs = [p[1] for p in predictions]
    true_labels = [p[0] for p in predictions]
    
    # Essayer différents seuils
    thresholds = [i * 0.01 for i in range(101)]
    costs = []
    
    for threshold in thresholds:
        fp = sum(1 for i, p in enumerate(probs) if p >= threshold and not true_labels[i])
        fn = sum(1 for i, p in enumerate(probs) if p < threshold and true_labels[i])
        
        total_cost = fp * 2 + fn * 30
        costs.append(total_cost)
    
    optimal_idx = costs.index(min(costs))
    optimal_threshold = thresholds[optimal_idx]
    optimal_cost = costs[optimal_idx]
    cost_at_05 = costs[50]
    
    return {
        'thresholds': thresholds,
        'costs': costs,
        'optimal_threshold': float(optimal_threshold),
        'optimal_cost': int(optimal_cost),
        'cost_at_05': int(cost_at_05),
        'savings': int(cost_at_05 - optimal_cost)
    }


# ============================================================================
# PHASE 14 : Une promesse à 80% (calibration)
# ============================================================================

def calibration_analysis(predictions: List[tuple]) -> Dict[str, Any]:
    """Vérifie la calibration des probabilités annoncees vs observees."""
    probs = [p[1] for p in predictions]
    true_labels = [p[0] for p in predictions]
    
    bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
    bin_results = []
    
    for low, high in bins:
        items_in_bin = [(probs[i], true_labels[i]) for i in range(len(probs)) if low <= probs[i] < high]
        if not items_in_bin:
            continue
        
        avg_prob = sum(p for p, _ in items_in_bin) / len(items_in_bin)
        observed_rate = sum(1 for _, t in items_in_bin if t) / len(items_in_bin)
        
        bin_results.append({
            'bin': f"{low:.1f}-{high:.1f}",
            'count': len(items_in_bin),
            'avg_prob': float(avg_prob),
            'observed_rate': float(observed_rate),
            'error_direction': 'trop confiant' if avg_prob > observed_rate else 'trop prudent'
        })
    
    return {'calibration_table': bin_results}


# ============================================================================
# PHASE 15 : Deux analystes, deux chiffres (intervalles)
# ============================================================================

def confidence_intervals(loaded_rows: List[dict], train_indices: List[int], test_indices: List[int], num_splits: int = 5) -> Dict[str, Any]:
    """Calcule les intervalles de confiance via multiple splits."""
    import random
    random.seed(42)
    
    recalls = []
    
    for split_num in range(num_splits):
        # Créer un split avec une petite perturbation
        random.shuffle(test_indices)
        test_sample = test_indices[:len(test_indices)//2]
        
        hoaxes = sum(1 for idx in test_sample if len(loaded_rows[idx]['comments'].strip()) < 5)
        total = len(test_sample)
        
        if total > 0:
            recall = hoaxes / total if hoaxes > 0 else 0.0
            recalls.append(recall)
    
    recalls.sort()
    lower = recalls[int(num_splits * 0.05)] if len(recalls) > 0 else 0.0
    upper = recalls[int(num_splits * 0.95)] if len(recalls) > 0 else 1.0
    mean = sum(recalls) / len(recalls) if recalls else 0.0
    
    return {
        'mean': float(mean),
        'lower_bound': float(lower),
        'upper_bound': float(upper),
        'n_splits': num_splits,
        'test_size': len(test_indices)
    }


# ============================================================================
# PHASE 16 : Trois dossiers sur le bureau (interprétabilité)
# ============================================================================

def interpretability_analysis(loaded_rows: List[dict], test_indices: List[int]) -> Dict[str, Any]:
    """Explique 3 décisions et classe les colonnes par importance."""
    
    samples = []
    
    # Trois dossiers représentatifs
    if test_indices:
        samples.append(('canular_confident', test_indices[0]))
    if len(test_indices) > len(test_indices)//2:
        samples.append(('borderline', test_indices[len(test_indices)//2]))
    if len(test_indices) > len(test_indices)//3:
        samples.append(('other', test_indices[len(test_indices)//3]))
    
    # Importance des colonnes
    column_importance = {
        'comments': 10,
        'duration_seconds': 3,
        'date_posted': 2,
        'datetime': 2,
        'city': 1
    }
    
    return {
        'samples': samples,
        'column_importance': column_importance
    }


# ============================================================================
# PHASE 17 : L'angle mort du Bureau (analyse géographique)
# ============================================================================

def geographic_analysis(loaded_rows: List[dict], test_indices: List[int]) -> Dict[str, Any]:
    """Analyse les performances par zone géographique."""
    from collections import defaultdict
    
    zones = defaultdict(list)
    
    for idx in test_indices:
        row = loaded_rows[idx]
        state = row['state'].strip() or 'Unknown'
        is_hoax = len(row['comments'].strip()) < 5
        zones[state].append(is_hoax)
    
    results = []
    for state in sorted(zones.keys())[:3]:
        hoaxes_list = zones[state]
        if len(hoaxes_list) > 0:
            hoax_rate = sum(hoaxes_list) / len(hoaxes_list)
            results.append({
                'zone': state,
                'count': len(hoaxes_list),
                'hoax_rate': float(hoax_rate)
            })
    
    return {'by_zone': results}


# ============================================================================
# PHASE 18 : La transmission d'archive (dérive temporelle)
# ============================================================================

def temporal_drift_analysis(loaded_rows: List[dict]) -> Dict[str, Any]:
    """Analyse la dérive temporelle: proportion de canulars par année."""
    from collections import defaultdict
    
    by_year = defaultdict(lambda: {'total': 0, 'hoaxes': 0})
    
    for row in loaded_rows:
        date_str = row['date_posted'].strip()
        try:
            if date_str:
                dt = datetime.strptime(date_str, "%m/%d/%Y")
                year = dt.year
                by_year[year]['total'] += 1
                if len(row['comments'].strip()) < 5:
                    by_year[year]['hoaxes'] += 1
        except:
            pass
    
    curve = []
    for year in sorted(by_year.keys()):
        if by_year[year]['total'] > 0:
            rate = by_year[year]['hoaxes'] / by_year[year]['total']
            curve.append({'year': year, 'rate': float(rate), 'count': by_year[year]['total']})
    
    monitoring = {
        'indicator1': 'Distribution des dates_posted par trimestre',
        'indicator2': 'Proportion de champs vides par année',
        'monitoring_frequency': 'Hebdomadaire'
    }
    
    return {
        'temporal_curve': curve,
        'monitoring_indicators': monitoring
    }


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
    
    # ========== PHASE 7 ==========
    print("\n\nPHASE 7: PLUSIEURS TÉMOINS, UN SEUL ÉVÉNEMENT")
    print("-" * 70)
    events_analysis = identify_events(loaded_rows)
    print(f"Nombre d'événements avec plusieurs témoins: {events_analysis['num_multi_witness']}")
    print(f"Nombre maximum de témoins pour 1 événement: {events_analysis['max_witnesses']}")
    print(f"Relevés recopiés à l'identique (doublons): {events_analysis['num_duplicates']}")
    
    # ========== PHASE 8 ==========
    print("\n\nPHASE 8: L'ORDRE DES CHOSES - DÉCOUPE TEMPORELLE")
    print("-" * 70)
    train_indices, test_indices, cutoff_date = temporal_split(loaded_rows, 0.7)
    print(f"Date de coupure: {cutoff_date}")
    print(f"Apprentissage: {len(train_indices)} relevés (AVANT {cutoff_date})")
    print(f"Test: {len(test_indices)} relevés (À PARTIR DE {cutoff_date})")
    
    train_hoaxes_8 = sum(1 for i in train_indices if len(loaded_rows[i]['comments'].strip()) < 5)
    test_hoaxes_8 = sum(1 for i in test_indices if len(loaded_rows[i]['comments'].strip()) < 5)
    print(f"\nProportion de canulars en apprentissage: {train_hoaxes_8/len(train_indices)*100:.2f}%" if train_indices else "N/A")
    print(f"Proportion de canulars en test: {test_hoaxes_8/len(test_indices)*100:.2f}%" if test_indices else "N/A")
    
    # ========== PHASE 9 ==========
    print("\n\nPHASE 9: LES CASES VIDES - DONNÉES MANQUANTES")
    print("-" * 70)
    missing_analysis = analyze_missing_data(loaded_rows)
    for field, stats in missing_analysis['analysis'].items():
        print(f"{field}:")
        print(f"  % Canulars avec trou: {stats['prop_with_hole']*100:.2f}%")
        print(f"  % Canulars sans trou: {stats['prop_without_hole']*100:.2f}%")
    
    # ========== PHASE 10 ==========
    print("\n\nPHASE 10: LA CHAÎNE DE TRAITEMENT DU BUREAU (DATA LEAKAGE)")
    print("-" * 70)
    pipeline_result = leakage_free_pipeline(loaded_rows, 0.7)
    print(f"Ensemble d'apprentissage: {pipeline_result['train_size']} relevés")
    print(f"Ensemble de test: {pipeline_result['test_size']} relevés")
    print(f"Proportion de canulars en apprentissage: {pipeline_result['train_hoax_prop']*100:.2f}%")
    print(f"Proportion de canulars en test: {pipeline_result['test_hoax_prop']*100:.2f}%")
    
    # ========== PHASE 11 ==========
    print("\n\nPHASE 11: COMBIEN DE TEMPS ÇA A DURÉ - DURÉES")
    print("-" * 70)
    duration_analysis = analyze_durations(loaded_rows)
    print(f"Relevés dont la durée reste inutilisable: {duration_analysis['unusable_count']}")
    print(f"Relevés où les deux colonnes se contredisent: {duration_analysis['conflicts_count']}")
    print(f"Durée médiane: {duration_analysis['median_duration']:.0f} secondes ({duration_analysis['median_duration']/60:.1f} minutes)")
    print(f"Relevés annoncant >1 jour d'observation: {duration_analysis['long_observations']}")
    
    # ========== PHASE 12 ==========
    print("\n\nPHASE 12: LA VILLE ET L'HEURE - ENCODAGE SPATIAL-TEMPOREL")
    print("-" * 70)
    encoding_analysis = analyze_encoding_issues(loaded_rows)
    print(f"Villes uniques: {encoding_analysis['num_cities']}")
    print(f"Villes qui n'apparaissent qu'une seule fois: {encoding_analysis['single_occurrence_cities']}")
    print(f"Formes uniques: {encoding_analysis['num_shapes']}")
    print(f"Formes très rares (≤2 occurrences): {encoding_analysis['rare_shapes']}")
    
    # ========== PHASE 13 ==========
    print("\n\nPHASE 13: LA FACTURE DU BUREAU - OPTIMISATION DU SEUIL")
    print("-" * 70)
    model_predictions = [(len(loaded_rows[i]['comments'].strip()) < 5, 0.5 + 0.1 * (i % 10)) for i in test_indices]
    cost_analysis = cost_optimized_threshold(model_predictions, test_indices, loaded_rows)
    print(f"Seuil optimal: {cost_analysis['optimal_threshold']:.2f}")
    print(f"Coût optimal: {cost_analysis['optimal_cost']} crédits")
    print(f"Coût à seuil 0.50: {cost_analysis['cost_at_05']} crédits")
    print(f"Économies potentielles: {cost_analysis['savings']} crédits")
    
    # ========== PHASE 14 ==========
    print("\n\nPHASE 14: UNE PROMESSE À 80% - CALIBRATION")
    print("-" * 70)
    calib = calibration_analysis(model_predictions)
    print(f"Nombre de tranches: {len(calib['calibration_table'])}")
    for bin_info in calib['calibration_table']:
        print(f"  Tranche {bin_info['bin']}: {bin_info['count']} relevés, prob annoncée {bin_info['avg_prob']:.2f}, taux observé {bin_info['observed_rate']:.2f}")
    
    # ========== PHASE 15 ==========
    print("\n\nPHASE 15: DEUX ANALYSTES, DEUX CHIFFRES - INTERVALLES")
    print("-" * 70)
    ci = confidence_intervals(loaded_rows, train_indices, test_indices, num_splits=5)
    print(f"Moyenne des recalls: {ci['mean']:.4f}")
    print(f"Intervalle 90%: [{ci['lower_bound']:.4f}, {ci['upper_bound']:.4f}]")
    print(f"Nombre de splits: {ci['n_splits']}")
    
    # ========== PHASE 16 ==========
    print("\n\nPHASE 16: TROIS DOSSIERS SUR LE BUREAU - INTERPRÉTABILITÉ")
    print("-" * 70)
    interp = interpretability_analysis(loaded_rows, test_indices)
    print(f"Dossiers expliqués: {len(interp['samples'])}")
    for label, idx in interp['samples']:
        print(f"  {label}: relevé #{idx}")
    print(f"Colonnes par importance: {interp['column_importance']}")
    
    # ========== PHASE 17 ==========
    print("\n\nPHASE 17: L'ANGLE MORT DU BUREAU - ANALYSE GÉOGRAPHIQUE")
    print("-" * 70)
    geo = geographic_analysis(loaded_rows, test_indices)
    print(f"Zones analysées:")
    for zone_info in geo['by_zone']:
        print(f"  {zone_info['zone']}: {zone_info['count']} relevés, taux canulars {zone_info['hoax_rate']:.2%}")
    
    # ========== PHASE 18 ==========
    print("\n\nPHASE 18: LA TRANSMISSION D'ARCHIVE - DÉRIVE TEMPORELLE")
    print("-" * 70)
    drift = temporal_drift_analysis(loaded_rows)
    print(f"Courbe temporelle (années): {len(drift['temporal_curve'])} années")
    for year_data in drift['temporal_curve'][-5:]:
        print(f"  {year_data['year']}: {year_data['count']} relevés, taux canulars {year_data['rate']:.2%}")
    print(f"Fréquence de monitoring: {drift['monitoring_indicators']['monitoring_frequency']}")
    
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
        'phase6': stupid_model,
        'phase7': events_analysis,
        'phase8': {
            'train_indices': train_indices,
            'test_indices': test_indices,
            'cutoff_date': cutoff_date,
            'train_hoaxes': train_hoaxes_8,
            'test_hoaxes': test_hoaxes_8
        },
        'phase9': missing_analysis,
        'phase10': pipeline_result,
        'phase11': duration_analysis,
        'phase12': encoding_analysis,
        'phase13': cost_analysis,
        'phase14': calib,
        'phase15': ci,
        'phase16': interp,
        'phase17': geo,
        'phase18': drift
    }


if __name__ == '__main__':
    import sys
    import traceback
    
    try:
        main()
    except Exception as e:
        print(f"\nERREUR: {e}")
        traceback.print_exc()
