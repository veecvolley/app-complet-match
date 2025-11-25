"""
Définition de l'état initial de l'application
"""
import time
from typing import Dict, Any
from config.settings import (
    get_formation_initiale,
    get_joueurs_banc_initial,
    get_formation_adverse_initiale,
    BANC_ADVERSE_INITIAL,
    JOUERS_VEEC_DICT,
    LIBERO_PRINCIPAL_NUM,
    LIBERO_RESERVE_NUM
)


def get_initial_state() -> Dict[str, Any]:
    """
    Retourne l'état initial de l'application.

    Returns:
        Dictionnaire contenant tout l'état initial du match
    """
    return {
        # Formations
        'formation_actuelle': get_formation_initiale(),
        'joueurs_banc': get_joueurs_banc_initial(),
        'formation_adverse_actuelle': get_formation_adverse_initiale(),
        'joueurs_banc_adverse': BANC_ADVERSE_INITIAL,

        # Configuration pré-match
        'match_setup_completed': False,
        'temp_setup_formation_veec': {},
        'temp_setup_selected_player_num': None,
        'JOUERS_VEEC': JOUERS_VEEC_DICT,

        # Score et service
        'service_actuel': 'VEEC',
        'score_veec': 0,
        'score_adverse': 0,
        'sets_veec': 0,
        'sets_adverse': 0,
        'current_set': 1,

        # Fin de match
        'match_ended': False,
        'match_winner': None,

        # Timeouts et substitutions
        'timeouts_veec': 0,
        'timeouts_adverse': 0,
        'sub_veec': 0,
        'sub_adverse': 0,

        # Rotation et timing
        'rotation_count': 0,
        'service_choisi': True,
        'start_time': time.time(),
        'timer_end_time': 0,
        'timer_type': None,

        # Substitution en cours
        'sub_en_cours_team': None,
        'temp_sub_state': {
            'entrant': None,
            'sortant_pos': None,
            'feedback': ""
        },

        # Historique
        'historique_stats': [],

        # État des Liberos
        'liberos_veec': {
            # Libero Actif (Principal)
            'actif_numero': LIBERO_PRINCIPAL_NUM,
            'is_on_court': False,
            'starter_numero_replaced': None,
            'current_pos_on_court': None,

            # Libero Réserve
            'reserve_numero': LIBERO_RESERVE_NUM,
            'is_reserve_used': False,
            'reserve_can_swap_in': False,

            # Le titulaire que le Libero remplace (N°6 Milieu Central)
            'libero_spot_starter_numero': 6,
        },
    }
