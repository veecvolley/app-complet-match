"""
Logique de gestion des Liberos (Principal et Réserve)
"""
from typing import Dict, Any, Tuple
import copy
import time


def swap_liberos_on_bench(current_state: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Gère l'échange du statut de Libero Actif avec le Libero de Réserve
    lorsque les deux sont sur le banc.

    Règle: Si le Libero de Réserve (N°9) est activé, le Libero Principal (N°8)
    ne peut plus jouer du set/match.

    Args:
        current_state: État actuel de l'application

    Returns:
        Tuple (new_state, message)
    """
    new_state = copy.deepcopy(current_state)
    liberos_status = new_state['liberos_veec']

    L8_num = liberos_status['actif_numero']  # 8
    L9_num = liberos_status['reserve_numero']  # 9

    # Condition de sécurité : Aucun Libero ne doit être sur le terrain
    if liberos_status['is_on_court']:
        return new_state, "Échange Libero-Libero impossible : Un Libero est sur le terrain."

    # L'échange n'est possible qu'une seule fois dans le set/match
    if liberos_status['is_reserve_used']:
        return new_state, "Le Libero de réserve a déjà été utilisé. L'échange est terminé."

    # --- LOGIQUE D'ÉCHANGE L8 <-> L9 ---

    # 1. Mise à jour des numéros actif/réserve
    liberos_status['actif_numero'] = L9_num  # 9 devient l'Actif
    liberos_status['reserve_numero'] = L8_num  # 8 devient le Libero de réserve (out)

    # 2. Flag le N°8 comme étant remplacé
    liberos_status['is_reserve_used'] = True

    # 3. Enregistrement dans l'historique
    log_entry = {
        'timestamp': time.time(),
        'set': new_state['current_set'],
        'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
        'position': 'BANC',
        'joueur_nom': f"L{L8_num} OUT (Règle)",
        'action_code': 'LIBERO_SWAP_RESERVE',
        'resultat': f"L{L9_num} devient ACTIF"
    }
    new_state['historique_stats'].insert(0, log_entry)

    new_state['liberos_veec'] = liberos_status
    return new_state, f"L{L9_num} est désormais le Libero ACTIF. L{L8_num} ne peut plus rejouer."


def handle_libero_out(current_state: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Gère la sortie (OUT) du Libero Actif par son joueur titulaire initial.

    Args:
        current_state: État actuel de l'application

    Returns:
        Tuple (new_state, message)
    """
    new_state = copy.deepcopy(current_state)
    liberos_status = new_state['liberos_veec']

    # --- VÉRIFICATIONS PRÉ-ÉCHANGE ---

    # 1. Vérifier si un Libero est sur le terrain
    if not liberos_status['is_on_court']:
        return new_state, "Échec: Aucun Libero n'est sur le terrain."

    # 2. Récupérer le numéro du joueur qui doit entrer (le titulaire initial)
    starter_num_to_enter = liberos_status['starter_numero_replaced']
    if starter_num_to_enter is None:
        return new_state, "Erreur d'état: Le titulaire que le Libero remplaçait est inconnu."

    # 3. Le Libero qui sort et sa position
    libero_num_to_out = liberos_status['actif_numero']
    pos_sortie = liberos_status['current_pos_on_court']

    # 4. Le titulaire (joueur entrant) doit être sur le banc
    joueur_titulaire = new_state['joueurs_banc'].get(starter_num_to_enter)
    if not joueur_titulaire:
        return new_state, f"Échec: Le titulaire N°{starter_num_to_enter} n'est pas disponible sur le banc."

    # --- EFFECTUER L'ÉCHANGE LIBERO OUT ---

    # 1. Mettre le titulaire sur le terrain à la place du Libero
    new_state['formation_actuelle'][pos_sortie] = joueur_titulaire

    # 2. Mettre le Libero sur le banc
    new_state['joueurs_banc'][libero_num_to_out] = {
        'numero': libero_num_to_out,
        'nom': f"Libero L{libero_num_to_out}",
        'role': 'LIBERO',
        'statut': 'BANC'
    }

    # 3. Retirer le titulaire du banc (il est maintenant sur le terrain)
    del new_state['joueurs_banc'][starter_num_to_enter]

    # 4. Mettre à jour l'état du Libero (OUT)
    liberos_status['is_on_court'] = False
    liberos_status['current_pos_on_court'] = None

    # 5. Enregistrement dans l'historique
    log_entry = {
        'timestamp': time.time(),
        'set': new_state['current_set'],
        'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
        'action_code': 'LIBERO_OUT',
        'details': f"L{libero_num_to_out} OUT P{pos_sortie} pour N°{starter_num_to_enter} (Titulaire)"
    }
    new_state['historique_stats'].insert(0, log_entry)

    new_state['liberos_veec'] = liberos_status

    return new_state, f"Libero N°{libero_num_to_out} sorti. Titulaire N°{starter_num_to_enter} entré en P{pos_sortie}."
