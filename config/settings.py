"""
Configuration et constantes pour l'application VEEC Scorer
"""
import os
from typing import Dict, List, Any

# --- Configuration Serveur ---
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8051'))

# --- URLs et Assets ---
URL_IMAGE_TERRAIN = "/assets/terrain_volleyball.jpg"

# --- Coordonnées des Positions ---
VEEC_POSITIONS_COORDS: Dict[int, Dict[str, Any]] = {
    1: {"x": 22, "y": 29, "name": "P1 (Service)"},
    6: {"x": 22, "y": 49, "name": "P6"},
    5: {"x": 22, "y": 69, "name": "P5"},
    2: {"x": 39, "y": 29, "name": "P2"},
    3: {"x": 39, "y": 49, "name": "P3"},
    4: {"x": 39, "y": 69, "name": "P4"},
}

ADVERSE_POSITIONS_COORDS: Dict[int, Dict[str, Any]] = {
    1: {"x": 80, "y": 69, "name": "P1 Adv (Service)"},
    6: {"x": 80, "y": 49, "name": "P6 Adv"},
    5: {"x": 80, "y": 29, "name": "P5 Adv"},
    2: {"x": 63, "y": 69, "name": "P2 Adv"},
    3: {"x": 63, "y": 49, "name": "P3 Adv"},
    4: {"x": 63, "y": 29, "name": "P4 Adv"},
}

# --- Joueurs VEEC ---
LISTE_JOUEURS_PREDEFINIE: List[Dict[str, Any]] = [
    {"numero": 1, "nom": "Nelson DE OLIVIEIRA"},
    {"numero": 3, "nom": "Florian ROCHE"},
    {"numero": 6, "nom": "Hugo BARTHELMEBS"},
    {"numero": 8, "nom": "Maxime CUGNOD"},
    {"numero": 9, "nom": "Takeru SUMIDA"},
    {"numero": 11, "nom": "Medhi ZARHOUNI"},
    {"numero": 12, "nom": "Emrik LESREL"},
    {"numero": 13, "nom": "Teddy BECARD"},
    {"numero": 15, "nom": "Ewen TINLOT"},
    {"numero": 16, "nom": "Guilhem ROUSSELLE"},
    {"numero": 7, "nom": "Mathis VARIN"}
]

JOUERS_VEEC_DICT: Dict[int, Dict[str, Any]] = {
    joueur["numero"]: joueur for joueur in LISTE_JOUEURS_PREDEFINIE
}

# --- Formations Initiales ---
def get_formation_initiale() -> Dict[int, Dict[str, Any]]:
    """Retourne la formation initiale de l'équipe VEEC"""
    formation = {}
    for i, pos_num in enumerate(VEEC_POSITIONS_COORDS.keys()):
        formation[pos_num] = LISTE_JOUEURS_PREDEFINIE[i].copy()
    return formation

def get_joueurs_banc_initial() -> Dict[int, Dict[str, Any]]:
    """Retourne les joueurs initialement sur le banc"""
    banc = {}
    for i in range(6, len(LISTE_JOUEURS_PREDEFINIE)):
        banc[LISTE_JOUEURS_PREDEFINIE[i]["numero"]] = LISTE_JOUEURS_PREDEFINIE[i].copy()
    return banc

def get_formation_adverse_initiale() -> Dict[int, Dict[str, Any]]:
    """Retourne la formation initiale de l'équipe adverse"""
    formation = {}
    adverse_keys_sorted = sorted(list(ADVERSE_POSITIONS_COORDS.keys()))
    for i, pos_num in enumerate(adverse_keys_sorted):
        joueur_adverse = {"numero": i + 1, "nom": f"Adv {i + 1}"}
        formation[pos_num] = joueur_adverse
    return formation

BANC_ADVERSE_INITIAL: Dict[int, Dict[str, Any]] = {}

# --- Constantes Libero ---
LIBERO_PRINCIPAL_NUM = 7
LIBERO_RESERVE_NUM = 9
LIBERO_POSITIONS_AUTORISEES = [1, 5, 6]  # Positions arrière uniquement

# --- Règles du Match ---
MAX_TIMEOUTS_PER_SET = 2
MAX_SUBS_PER_SET = 6
TIMEOUT_DURATION_SECONDS = 30
SHORT_BREAK_DURATION_SECONDS = 3 * 60
LONG_BREAK_DURATION_SECONDS = 5 * 60

# --- Couleurs UI ---
VEEC_COLOR = "#007bff"
ADVERSE_COLOR = "#dc3545"
LIBERO_COLOR = "#ffc107"  # Jaune pour le Libero

# --- Configuration Match ---
POINTS_TO_WIN_SET = 25
POINTS_TO_WIN_SET_5 = 15
MIN_POINT_DIFF = 2
