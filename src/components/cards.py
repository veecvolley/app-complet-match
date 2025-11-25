"""
Composants de cartes pour joueurs et positions
"""
from dash import html
from typing import Dict, Any, Optional
from config.settings import VEEC_COLOR


def create_player_card(
    player_data: Dict[str, Any],
    is_selected: bool = False,
    is_assigned: bool = False
) -> html.Button:
    """
    Génère un bouton/carte pour un joueur disponible ou assigné.

    Args:
        player_data: Données du joueur {'numero': int, 'nom': str}
        is_selected: True si le joueur est actuellement sélectionné
        is_assigned: True si le joueur est déjà assigné à une position

    Returns:
        Bouton HTML représentant le joueur
    """
    num = player_data['numero']
    name = player_data['nom']

    style = {
        'margin': '5px',
        'padding': '10px',
        'borderRadius': '5px',
        'border': '2px solid #ccc',
        'backgroundColor': '#fff',
        'cursor': 'pointer',
        'width': '100px',
        'fontWeight': 'normal',
        'textAlign': 'center'
    }

    # Gestion du surlignage
    if is_selected:
        style.update({
            'backgroundColor': VEEC_COLOR,
            'color': 'white',
            'fontWeight': 'bold',
            'border': '3px solid black'
        })
    # Gestion du joueur assigné
    elif is_assigned:
        style.update({
            'backgroundColor': '#eee',
            'border': '2px dashed #666',
            'cursor': 'not-allowed',
            'opacity': 0.6
        })

    return html.Button(
        html.Div([
            html.B(f"N°{num}"),
            html.Small(name.split()[0])  # Affiche seulement le prénom
        ]),
        id={'type': 'setup-player-select', 'index': str(num)},
        n_clicks=0,
        style=style,
        disabled=is_assigned
    )


def create_position_card(
    pos_num: int,
    assigned_player_data: Optional[Dict[str, Any]],
    selected_player_num: Optional[int]
) -> html.Button:
    """
    Génère une carte pour une position sur le terrain (P1 à P6),
    avec un style conditionnel.

    Args:
        pos_num: Numéro de position (1-6)
        assigned_player_data: Données du joueur assigné (None si vide)
        selected_player_num: Numéro du joueur sélectionné (None si aucun)

    Returns:
        Bouton HTML représentant la position
    """
    # Debug (peut être retiré en production)
    print(f"DEBUG RENDER P{pos_num}: Player Data Received -> "
          f"{assigned_player_data.get('numero') if assigned_player_data else 'NONE'}")

    # --- Détermination de l'état et des données ---
    num_display = "?"
    name_display = "VIDE"
    is_assigned = assigned_player_data is not None

    # --- Logique d'affichage et de style ---
    if is_assigned:
        # Remplissage des données
        num = assigned_player_data.get('numero')
        name = assigned_player_data.get('nom', 'N/A')
        num_display = str(num)
        name_display = name.split()[0]

        # CAS 1: Position assignée (ROUGE/Occupé permanent)
        style = {
            'border': '2px solid #CC0000',
            'backgroundColor': '#FFDADA',
            'color': '#CC0000',
            'fontWeight': 'bold',
            'boxShadow': '0 0 5px rgba(204, 0, 0, 0.5)'
        }

    elif selected_player_num is not None:
        # CAS 2: Position vide, mais un joueur est sélectionné (VERT/Cible temporaire)
        style = {
            'border': '2px solid #00AA00',
            'backgroundColor': '#DAFFDA',
            'color': '#00AA00',
            'fontWeight': 'bold',
            'boxShadow': '0 0 5px rgba(0, 170, 0, 0.5)'
        }

    else:
        # CAS 3: Position vide et aucun joueur sélectionné (GRIS/Défaut)
        style = {
            'border': '1px solid #ddd',
            'backgroundColor': '#f2f2f2',
            'color': '#888888',
            'fontWeight': 'normal',
            'boxShadow': '0 0 2px rgba(0, 0, 0, 0.1)'
        }

    # --- Styles de base (communs à tous les boutons) ---
    base_styles = {
        'margin': '5px',
        'padding': '10px',
        'borderRadius': '8px',
        'width': '30%',
        'height': '120px',
        'textAlign': 'center',
        'cursor': 'pointer'
    }

    # Fusion des styles
    final_style = {**base_styles, **style}

    return html.Button(
        html.Div([
            html.B(f"P{pos_num}", style={'fontSize': '1.2em'}),
            html.Div(f"N°{num_display}", style={'fontSize': '1.8em', 'fontWeight': 'bold'}),
            html.Small(name_display)
        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}),
        id={'type': 'setup-position-assign', 'index': str(pos_num)},
        n_clicks=0,
        style=final_style
    )
