"""
Composants de modales pour l'application
"""
from dash import html
from typing import Dict, Any
from config.settings import (
    LIBERO_POSITIONS_AUTORISEES,
    VEEC_COLOR,
    ADVERSE_COLOR,
    MAX_SUBS_PER_SET
)


def create_libero_sub_modal(current_state: Dict[str, Any]) -> html.Div:
    """Génère la modal pour l'échange du Libero."""

    libero_status = current_state['liberos_veec']
    is_on_court = libero_status['is_on_court']
    libero_num_actif = libero_status.get('actif_numero')

    libero_data = current_state['joueurs_banc'].get(libero_num_actif)

    # Si le Libero n'est pas sur le banc, le récupérer de la formation
    if not libero_data:
        libero_data = next(
            (p for p in current_state['formation_actuelle'].values()
             if p.get('numero') == libero_num_actif),
            None
        )

    modal_title = f"Échange Libero (N°{libero_num_actif})"

    # Contenu de la modal
    if not is_on_court:
        # Le Libero est sur le banc - Entrée
        positions_remplacables = []
        for pos in LIBERO_POSITIONS_AUTORISEES:
            player = current_state['formation_actuelle'].get(pos)
            if player:
                positions_remplacables.append(
                    html.Button(
                        f"Remplacer P{pos} - N°{player['numero']} ({player['nom']})",
                        id={'type': 'confirm-libero-in', 'pos': str(pos)},
                        n_clicks=0,
                        style={
                            'margin': '5px',
                            'padding': '10px',
                            'backgroundColor': '#d4edda',
                            'border': '1px solid #155724',
                            'cursor': 'pointer'
                        }
                    )
                )

        content = [
            html.H4(f"Entrée du Libero (N°{libero_num_actif})", style={'color': '#28a745'}),
            html.P("Le Libero peut remplacer n'importe quel joueur de la ligne arrière (P1, P5, P6) :"),
            html.Div(positions_remplacables, style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'justifyContent': 'center'
            }),
        ]

    else:
        # Le Libero est sur le terrain - Sortie
        starter_numero = libero_status['starter_numero_replaced']
        starter_data = current_state['joueurs_banc'].get(starter_numero)
        current_pos = libero_status['current_pos_on_court']

        if starter_data:
            content = [
                html.H4(f"Sortie du Libero (N°{libero_num_actif})", style={'color': '#dc3545'}),
                html.P("Le Libero doit être remplacé par le joueur titulaire qu'il a remplacé :"),
                html.P(f"Joueur entrant : N°{starter_data['numero']} ({starter_data['nom']}) à la position P{current_pos}"),
                html.Button(
                    "Confirmer la sortie",
                    id='btn-confirm-libero-out',
                    n_clicks=0,
                    style={
                        'padding': '10px 20px',
                        'backgroundColor': '#dc3545',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '5px',
                        'marginTop': '15px',
                        'cursor': 'pointer'
                    }
                )
            ]
        else:
            content = [html.P("Erreur: Impossible de trouver le joueur titulaire à remplacer par le Libero.")]

    # Construction de la modal
    return html.Div(
        children=[
            html.H3(modal_title, style={'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div(content, style={'textAlign': 'center', 'marginBottom': '20px'}),
            html.Button(
                "Annuler",
                id='btn-cancel-libero-sub',
                n_clicks=0,
                style={
                    'padding': '10px 20px',
                    'backgroundColor': '#6c757d',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                }
            )
        ],
        style={
            'backgroundColor': 'white',
            'padding': '25px',
            'borderRadius': '12px',
            'width': '90%',
            'maxWidth': '500px',
            'boxShadow': '0 10px 30px rgba(0,0,0,0.5)',
            'position': 'relative'
        }
    )


def create_simple_adverse_sub_modal(new_state: Dict[str, Any], feedback_msg: str) -> html.Div:
    """Génère la modal de confirmation pour la substitution adverse."""
    team = "ADVERSAIRE"
    count = new_state['sub_adverse']
    color = ADVERSE_COLOR

    modal_sub_content = html.Div(
        [
            html.H4(
                f"Substitution {team} : {count + 1}/{MAX_SUBS_PER_SET}",
                style={'padding': '10px', 'textAlign': 'center', 'color': color}
            ),
            html.Div(
                id='sub-feedback-msg',
                children=feedback_msg,
                style={'color': ADVERSE_COLOR, 'fontWeight': 'bold', 'marginBottom': '20px'}
            ),
            html.Button(
                "Confirmer Substitution Adverse",
                id={'type': 'confirm-sub-adverse', 'index': team},
                n_clicks=0,
                style={
                    'margin': '10px',
                    'backgroundColor': color,
                    'color': 'white',
                    'padding': '10px 20px',
                    'border': 'none',
                    'borderRadius': '5px'
                }
            ),
            html.Button(
                "Annuler",
                id={'type': 'cancel-sub', 'index': team},
                n_clicks=0,
                style={
                    'margin': '10px',
                    'backgroundColor': '#aaa',
                    'color': 'white',
                    'padding': '10px 20px',
                    'border': 'none',
                    'borderRadius': '5px'
                }
            )
        ],
        style={
            'position': 'fixed',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'backgroundColor': 'white',
            'padding': '30px',
            'borderRadius': '10px',
            'zIndex': 1005,
            'boxShadow': '0 0 20px rgba(0,0,0,0.5)'
        }
    )

    return html.Div(
        children=modal_sub_content,
        style={
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.7)',
            'zIndex': 1001
        }
    )


def create_veec_sub_modal(new_state: Dict[str, Any], temp_state: Dict[str, Any], feedback_msg: str) -> html.Div:
    """Génère la modal de substitution VEEC avec gestion de la surbrillance."""

    formation = new_state['formation_actuelle']
    banc = new_state['joueurs_banc']
    count = new_state['sub_veec']
    team = 'VEEC'
    color = VEEC_COLOR

    modal_style = {
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'width': '100%',
        'height': '100%',
        'backgroundColor': 'rgba(0,0,0,0.8)',
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'zIndex': 1001
    }

    content_style = {
        'backgroundColor': 'white',
        'padding': '25px',
        'borderRadius': '12px',
        'width': '95%',
        'maxWidth': '600px',
        'boxShadow': '0 10px 30px rgba(0,0,0,0.5)',
        'maxHeight': '90vh',
        'overflowY': 'auto',
        'position': 'relative',
        'zIndex': 1002
    }

    # Joueurs sortants (terrain)
    joueurs_sur_terrain = []
    formation_cleaned = {int(k): v for k, v in formation.items()}
    pos_keys = sorted(formation_cleaned.keys())

    for pos in pos_keys:
        data = formation_cleaned[pos]
        is_selected_out = temp_state.get('sortant_pos') == pos

        style_out = {
            'width': '48%',
            'margin': '1%',
            'padding': '10px',
            'borderRadius': '5px',
            'border': f'2px solid {ADVERSE_COLOR}',
            'fontWeight': 'normal'
        }

        if is_selected_out:
            style_out.update({
                'backgroundColor': ADVERSE_COLOR,
                'color': 'white',
                'fontWeight': 'bold',
                'border': '3px solid black'
            })
        else:
            style_out.update({
                'backgroundColor': '#f8d7da',
                'color': '#721c24'
            })

        joueurs_sur_terrain.append(
            html.Button(
                f"P{pos} - N°{data['numero']} ({data['nom']})",
                id={'type': 'sub-player-btn', 'role': 'sortant', 'index': str(pos)},
                n_clicks=0,
                style=style_out
            )
        )

    # Joueurs entrants (banc)
    joueurs_sur_banc = []
    banc_cleaned = {int(k): v for k, v in banc.items()}
    num_keys = sorted(banc_cleaned.keys())

    for num in num_keys:
        data = banc_cleaned[num]
        is_selected_in = temp_state.get('entrant') and temp_state.get('entrant')['numero'] == num

        style_in = {
            'width': '48%',
            'margin': '1%',
            'padding': '10px',
            'borderRadius': '5px',
            'border': f'2px solid {VEEC_COLOR}',
            'fontWeight': 'normal'
        }

        if is_selected_in:
            style_in.update({
                'backgroundColor': VEEC_COLOR,
                'color': 'white',
                'fontWeight': 'bold',
                'border': '3px solid black'
            })
        else:
            style_in.update({
                'backgroundColor': '#d4edda',
                'color': '#155724'
            })

        joueurs_sur_banc.append(
            html.Button(
                f"N°{data['numero']} ({data['nom']})",
                id={'type': 'sub-player-btn', 'role': 'entrant', 'index': str(num)},
                n_clicks=0,
                style=style_in
            )
        )

    is_ready = temp_state.get('entrant') is not None and temp_state.get('sortant_pos') is not None

    style_confirm = {
        'padding': '10px 20px',
        'backgroundColor': '#007bff',
        'color': 'white',
        'border': 'none',
        'borderRadius': '5px',
        'fontSize': '1.1em',
        'cursor': 'pointer'
    }

    if not is_ready:
        style_confirm.update({'backgroundColor': '#aaa', 'cursor': 'not-allowed'})

    modal_content = html.Div(
        children=[
            html.H3(
                f"Substitution {team} ({count + 1}/{MAX_SUBS_PER_SET})",
                style={'textAlign': 'center', 'marginBottom': '20px', 'color': color}
            ),
            html.Div(
                id='sub-feedback-msg',
                children=feedback_msg,
                style={
                    'color': 'blue',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'marginBottom': '15px'
                }
            ),
            html.P("1. Joueur Sortant (Terrain) :", style={'fontWeight': 'bold', 'marginTop': '10px'}),
            html.Div(
                joueurs_sur_terrain,
                style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'justifyContent': 'space-around',
                    'marginBottom': '20px'
                }
            ),
            html.P("2. Joueur Entrant (Banc) :", style={'fontWeight': 'bold'}),
            html.Div(
                joueurs_sur_banc,
                style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'justifyContent': 'space-around',
                    'marginBottom': '30px'
                }
            ),
            html.Button(
                "✕ Annuler",
                id={'type': 'cancel-sub', 'index': team},
                n_clicks=0,
                style={
                    'marginRight': '20px',
                    'padding': '10px 20px',
                    'backgroundColor': '#6c757d',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '5px',
                    'fontSize': '1.1em',
                    'cursor': 'pointer'
                }
            ),
            html.Button(
                "✅ Confirmation des changements",
                id='btn-confirm-sub',
                n_clicks=0,
                disabled=not is_ready,
                style=style_confirm
            ),
        ],
        style=content_style
    )

    return html.Div(children=modal_content, style=modal_style)


def create_pre_match_setup_modal(current_state: Dict[str, Any]) -> html.Div:
    """Génère la modal de configuration pré-match."""
    from src.components.cards import create_player_card, create_position_card
    from config.settings import VEEC_COLOR

    ROSTER_VEEC = current_state.get('JOUERS_VEEC', {})

    libero_actif_num = current_state.get('liberos_veec', {}).get('actif_numero', 99)
    libero_reserve_num = current_state.get('liberos_veec', {}).get('reserve_numero', None)

    liberos_num_str = {str(libero_actif_num)}
    if libero_reserve_num:
        liberos_num_str.add(str(libero_reserve_num))

    temp_formation = current_state.get('temp_setup_formation_veec', {})
    assigned_nums_str = {str(p['numero']) for p in temp_formation.values()}

    selected_num = current_state.get('temp_setup_selected_player_num')
    selected_num_str = str(selected_num) if selected_num is not None else None

    # Joueurs disponibles
    player_list_components = []
    sorted_roster = sorted(ROSTER_VEEC.items(), key=lambda item: int(item[0]))

    for num_str, data in sorted_roster:
        is_assigned = num_str in assigned_nums_str
        is_libero = num_str in liberos_num_str
        is_selected = num_str == selected_num_str

        if not is_libero and not is_assigned:
            player_list_components.append(
                create_player_card(data, is_selected=is_selected, is_assigned=False)
            )

    # Positions sur le terrain
    position_list_components = [
        create_position_card(pos, temp_formation.get(pos), selected_num)
        for pos in range(1, 7)
    ]

    # Message et bouton
    is_ready = len(temp_formation) == 6
    feedback_msg = f"{len(temp_formation)}/6 positions assignées."
    if is_ready:
        feedback_msg = "✅ Formation de départ complète. Prêt à commencer le match !"

    style_confirm = {
        'padding': '15px 30px',
        'backgroundColor': VEEC_COLOR if is_ready else '#aaa',
        'color': 'white',
        'border': 'none',
        'borderRadius': '8px',
        'fontSize': '1.2em',
        'cursor': 'pointer' if is_ready else 'not-allowed',
        'marginTop': '20px'
    }

    modal_content = html.Div(
        children=[
            html.H2("Configuration de la Formation de Départ VEEC", style={
                'textAlign': 'center',
                'color': VEEC_COLOR,
                'marginBottom': '20px'
            }),
            html.Div(feedback_msg, id='setup-feedback', style={
                'textAlign': 'center',
                'fontWeight': 'bold',
                'marginBottom': '20px'
            }),

            html.H3("Positions de Départ (P1 - P6)", style={
                'borderBottom': '1px solid #ddd',
                'paddingBottom': '10px'
            }),
            html.Div(position_list_components, style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'justifyContent': 'space-around'
            }),

            html.H3("Joueurs Disponibles (Sélectionnez pour assigner)", style={
                'borderBottom': '1px solid #ddd',
                'padding': '20px 0 10px 0',
                'marginTop': '20px'
            }),
            html.Div(player_list_components, style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'justifyContent': 'space-around'
            }),

            html.Div(
                html.Button("Démarrer le Match", id='btn-confirm-setup', n_clicks=0, disabled=not is_ready, style=style_confirm),
                style={'textAlign': 'center', 'marginTop': '30px'}
            )
        ],
        style={
            'backgroundColor': 'white',
            'padding': '25px',
            'borderRadius': '12px',
            'width': '90%',
            'maxWidth': '800px',
            'boxShadow': '0 10px 30px rgba(0,0,0,0.5)'
        }
    )

    return html.Div(
        children=modal_content,
        style={
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.9)',
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center',
            'zIndex': 1000
        }
    )
