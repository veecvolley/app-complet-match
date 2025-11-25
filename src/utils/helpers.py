"""
Fonctions utilitaires générales pour l'application VEEC Scorer
"""
from typing import Dict, Any


def clean_formations(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les clés de positions de string vers int après désérialisation JSON.

    Le composant dcc.Store sérialise en JSON, ce qui convertit les clés numériques
    de dictionnaires en chaînes de caractères. Cette fonction les reconvertit en int.

    Args:
        state: État de l'application (dict)

    Returns:
        État avec les clés de positions converties en int
    """
    if 'formation_actuelle' in state and state['formation_actuelle']:
        state['formation_actuelle'] = {
            int(k): v for k, v in state['formation_actuelle'].items()
        }

    if 'formation_adverse_actuelle' in state and state['formation_adverse_actuelle']:
        state['formation_adverse_actuelle'] = {
            int(k): v for k, v in state['formation_adverse_actuelle'].items()
        }

    if 'joueurs_banc' in state and state['joueurs_banc']:
        state['joueurs_banc'] = {
            int(k): v for k, v in state['joueurs_banc'].items()
        }

    return state
