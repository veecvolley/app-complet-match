"""
Logique de rotation des joueurs sur le terrain
"""
from typing import Dict, Any
import copy


def appliquer_rotation_veec(formation: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Applique la rotation horaire pour l'équipe VEEC.

    Rotation: P1 ← P2 ← P3 ← P4 ← P5 ← P6 ← P1

    Args:
        formation: Formation actuelle {position: joueur_data}

    Returns:
        Nouvelle formation après rotation
    """
    new_formation = {}
    new_formation[1] = formation[2].copy()
    new_formation[2] = formation[3].copy()
    new_formation[3] = formation[4].copy()
    new_formation[4] = formation[5].copy()
    new_formation[5] = formation[6].copy()
    new_formation[6] = formation[1].copy()
    return new_formation


def appliquer_rotation_adverse(formation: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Applique la rotation horaire pour l'équipe adverse.

    Rotation: P1 ← P2 ← P3 ← P4 ← P5 ← P6 ← P1

    Args:
        formation: Formation actuelle {position: joueur_data}

    Returns:
        Nouvelle formation après rotation
    """
    new_formation = {}
    new_formation[1] = formation[2].copy()
    new_formation[2] = formation[3].copy()
    new_formation[3] = formation[4].copy()
    new_formation[4] = formation[5].copy()
    new_formation[5] = formation[6].copy()
    new_formation[6] = formation[1].copy()
    return new_formation
