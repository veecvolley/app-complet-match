import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State, ALL
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import json
import re
import copy
import time
import sys # Import manquant pour sys.argv

# --- CONFIGURATION & CONSTANTES ---

URL_IMAGE_TERRAIN = "https://github.com/takerusumida-lgtm/agent-stats-volley-veec/raw/d2e3108b9553552d0847008ecdea2c1b83987ab8/terrain_volleyball.jpg"

VEEC_POSITIONS_COORDS = {
    1: {"x": 22, "y": 29, "name": "P1 (Service)"}, 6: {"x": 22, "y": 49, "name": "P6"},
    5: {"x": 22, "y": 69, "name": "P5"}, 2: {"x": 39, "y": 29, "name": "P2"},
    3: {"x": 39, "y": 49, "name": "P3"}, 4: {"x": 39, "y": 69, "name": "P4"},
}

ADVERSE_POSITIONS_COORDS = {
    1: {"x": 80, "y": 69, "name": "P1 Adv (Service)"},
    6: {"x": 80, "y": 49, "name": "P6 Adv"},
    5: {"x": 80, "y": 29, "name": "P5 Adv"},
    2: {"x": 63, "y": 69, "name": "P2 Adv"},
    3: {"x": 63, "y": 49, "name": "P3 Adv"},
    4: {"x": 63, "y": 29, "name": "P4 Adv"},
}

LISTE_JOUEURS_PREDEFINIE = [
    {"numero": 1, "nom": "Nelson DE OLIVIEIRA"}, {"numero": 3, "nom": "Florian ROCHE"},
    {"numero": 6, "nom": "Hugo BARTHELMEBS"}, {"numero": 8, "nom": "Maxime CUGNOD"},
    {"numero": 9, "nom": "Takeru SUMIDA"}, {"numero": 11, "nom": "Medhi ZARHOUNI"},
    {"numero": 12, "nom": "Emrik LESREL"}, {"numero": 13, "nom": "Teddy BECARD"},
    {"numero": 15, "nom": "Ewen TINLOT"}, {"numero": 16, "nom": "Guilhem ROUSSELLE"},
    {"numero": 7, "nom": "Mathis VARIN"}
]

# Conversion de votre liste en un dictionnaire
JOUERS_VEEC_DICT = {
    joueur["numero"]: joueur for joueur in LISTE_JOUEURS_PREDEFINIE
}

# Assurez-vous d'avoir bien défini cette liste en constante dans votre code.

FORMATION_INITIALE = {}
for i, pos_num in enumerate(VEEC_POSITIONS_COORDS.keys()):
    FORMATION_INITIALE[pos_num] = LISTE_JOUEURS_PREDEFINIE[i].copy()

JOUEURS_BANC_INITIAL = {}
for i in range(6, len(LISTE_JOUEURS_PREDEFINIE)):
    JOUEURS_BANC_INITIAL[LISTE_JOUEURS_PREDEFINIE[i]["numero"]] = LISTE_JOUEURS_PREDEFINIE[i].copy()

FORMATION_ADVERSE_INITIALE = {}
adverse_keys_sorted = sorted(list(ADVERSE_POSITIONS_COORDS.keys()))
for i, pos_num in enumerate(adverse_keys_sorted):
    joueur_adverse = {"numero": i + 1, "nom": f"Adv {i + 1}"}
    FORMATION_ADVERSE_INITIALE[pos_num] = joueur_adverse
BANC_ADVERSE_INITIAL = {}

# Constantes Libero
LIBERO_PRINCIPAL_NUM = 7  # Basé sur A. Libero
LIBERO_RESERVE_NUM = 9    # Basé sur B. Libero 2
LIBERO_POSITIONS_AUTORISEES = [1, 5, 6] # Positions arrière où le Libero peut entrer

MAX_TIMEOUTS_PER_SET = 2
MAX_SUBS_PER_SET = 6
TIMEOUT_DURATION_SECONDS = 30
SHORT_BREAK_DURATION_SECONDS = 3 * 60
LONG_BREAK_DURATION_SECONDS = 5 * 60

VEEC_COLOR = "#007bff"
ADVERSE_COLOR = "#dc3545"

# --- UTILITIES & LOGIQUE DE ROTATION ---

def clean_formations(state):
    if 'formation_actuelle' in state and state['formation_actuelle']:
        state['formation_actuelle'] = { int(k): v for k, v in state['formation_actuelle'].items() }
    if 'formation_adverse_actuelle' in state and state['formation_adverse_actuelle']:
        state['formation_adverse_actuelle'] = { int(k): v for k, v in state['formation_adverse_actuelle'].items() }
    if 'joueurs_banc' in state and state['joueurs_banc']:
        state['joueurs_banc'] = { int(k): v for k, v in state['joueurs_banc'].items() }
    return state

def appliquer_rotation_veec(formation):
    new_formation = {}
    new_formation[1] = formation[2].copy()
    new_formation[2] = formation[3].copy()
    new_formation[3] = formation[4].copy()
    new_formation[4] = formation[5].copy()
    new_formation[5] = formation[6].copy()
    new_formation[6] = formation[1].copy()
    return new_formation

def swap_liberos_on_bench(current_state):
    """
    Gère l'échange du statut de Libero Actif (N°8) avec le Libero de Réserve (N°9)
    lorsque les deux sont sur le banc.
    Si le N°9 est activé, le N°8 ne peut plus jouer du set/match.
    """
    new_state = copy.deepcopy(current_state)
    liberos_status = new_state['liberos_veec']
    
    L8_num = liberos_status['actif_numero']  # 8
    L9_num = liberos_status['reserve_numero'] # 9
    
    # Condition de sécurité : La substitution n'est possible que si AUCUN Libero n'est sur le terrain.
    if liberos_status['is_on_court']:
        # Le Libero (N°8 ou N°9) est sur le terrain, l'échange est impossible.
        # Vous devez ajouter un feedback à l'utilisateur ici (via un Div ou un store Dash)
        return new_state, "Échange Libero-Libero impossible : Un Libero est sur le terrain."

    # L'échange de statut Libero n'est possible qu'une seule fois dans le set/match selon les règles standard
    # et a des implications majeures : si L9 entre, L8 est définitivement out.
    if liberos_status['is_reserve_used']:
        return new_state, "Le Libero de réserve a déjà été utilisé. L'échange est terminé."

    # ----------------------------------------------------
    # LOGIQUE D'ÉCHANGE L8 <-> L9
    # ----------------------------------------------------
    
    # 1. Mise à jour des numéros actif/réserve
    liberos_status['actif_numero'] = L9_num  # 9 devient l'Actif
    liberos_status['reserve_numero'] = L8_num # 8 devient le Libero de réserve (out)
    
    # 2. Flag le N°8 comme étant remplacé
    liberos_status['is_reserve_used'] = True 
    
    # 3. Mise à jour des joueurs sur le banc (leurs numéros de maillot/roles restent les mêmes,
    # mais il faut loguer l'échange et potentiellement l'afficher différemment)
    
    # 4. Enregistrement dans l'historique
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

def handle_libero_out(current_state):
    """
    Gère la sortie (OUT) du Libero Actif (N°8 ou N°9) par son joueur titulaire initial.
    """
    new_state = copy.deepcopy(current_state)
    liberos_status = new_state['liberos_veec']
    
    # ----------------------------------------------------
    # VÉRIFICATIONS PRÉ-ÉCHANGE
    # ----------------------------------------------------
    
    # 1. Vérifier si un Libero est sur le terrain
    if not liberos_status['is_on_court']:
        return new_state, "Échec: Aucun Libero n'est sur le terrain."

    # 2. Récupérer le numéro du joueur qui doit entrer (le titulaire initial)
    starter_num_to_enter = liberos_status['starter_numero_replaced']
    if starter_num_to_enter is None:
        # Erreur si l'état est incohérent, car le Libero doit toujours avoir un titulaire à remplacer.
        return new_state, "Erreur d'état: Le titulaire que le Libero remplaçait est inconnu."

    # 3. Le Libero qui sort et sa position
    libero_num_to_out = liberos_status['actif_numero']
    pos_sortie = liberos_status['current_pos_on_court'] # La position où le Libero se trouve
    
    # 4. Le titulaire (joueur entrant) doit être sur le banc
    joueur_titulaire = new_state['joueurs_banc'].get(starter_num_to_enter)
    if not joueur_titulaire:
        return new_state, f"Échec: Le titulaire N°{starter_num_to_enter} n'est pas disponible sur le banc."

    # ----------------------------------------------------
    # EFFECTUER L'ÉCHANGE LIBERO OUT
    # ----------------------------------------------------
    
    # 1. Mettre le titulaire (joueur entrant) sur le terrain à la place du Libero
    new_state['formation_actuelle'][pos_sortie] = joueur_titulaire
    
    # 2. Mettre le Libero (qui sort) sur le banc
    # On utilise le Libero ACTIF (N°8 ou N°9) pour le remettre sur le banc
    # On le récupère du dictionnaire des joueurs sur le banc (où il était avant d'entrer)
    libero_on_bench = current_state['joueurs_banc'].get(libero_num_to_out)
    
    # Si l'objet Libero a été supprimé du banc lors de l'entrée, on le recrée/met à jour ici.
    # Dans notre modèle, on le remet sur le banc avec son rôle initial (si besoin, on peut complexifier)
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

def appliquer_rotation_adverse(formation):
    new_formation = {}
    new_formation[1] = formation[2].copy()
    new_formation[2] = formation[3].copy()
    new_formation[3] = formation[4].copy()
    new_formation[4] = formation[5].copy()
    new_formation[5] = formation[6].copy()
    new_formation[6] = formation[1].copy()
    return new_formation
    
def create_historique_table(historique_stats):
    """Crée et retourne le Dash DataTable à partir de l'historique."""
    if not historique_stats:
        return html.Div("L'historique des actions est vide pour le moment.", style={'padding': '10px', 'color': '#666'})
        
    df_historique = pd.DataFrame(historique_stats)
    columns_config = [{"name": i.capitalize(), "id": i} for i in df_historique.columns]

    return dash_table.DataTable(
        id='datatable-historique',
        columns=columns_config,
        data=df_historique.head(50).to_dict('records'),
        style_table={'overflowX': 'auto', 'marginTop': '10px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
        ]
    )

def create_court_figure(formation_equipe, formation_adverse, service_actuel, liberos_veec):
    
    # Note: On suppose qu'un seul Libero adverse est géré, et qu'il a le numéro 1
    # Si l'adversaire a des Libéros dynamiques, il faudra ajuster.
    libero_adverse_num = 1 # Supposons que le Libero adverse est le N°1
    libero_adverse_is_on_court = True # On suppose qu'il est toujours sur le terrain pour la couleur (simplification)

    fig = go.Figure()
    layout_config = {'modeBarButtonsToRemove': ['zoom', 'pan', 'select', 'lasso2d', 'autoscale', 'zoomIn', 'zoomOut', 'resetscale'], 'scrollZoom': False}

    fig.add_layout_image(
        dict(source=URL_IMAGE_TERRAIN, xref="x", yref="y", x=0, y=100, sizex=100, sizey=100,
             sizing="stretch", opacity=1.0, layer="below"))

    veec_positions_list = sorted(list(VEEC_POSITIONS_COORDS.keys())) 
    veec_x = [VEEC_POSITIONS_COORDS[pos]["x"] for pos in veec_positions_list]
    veec_y = [VEEC_POSITIONS_COORDS[pos]["y"] for pos in veec_positions_list]
    veec_text = [str(formation_equipe.get(pos, {}).get('numero', '?')) for pos in veec_positions_list]
    veec_customdata = [pos for pos in veec_positions_list]
    veec_hovertext = [f"P{pos} - {formation_equipe.get(pos, {}).get('nom', 'N/A')}" for pos in veec_positions_list]

    # ----------------------------------------------------
    # LOGIQUE LIBERO CENTRALISÉE (Début de la fonction)
    # ----------------------------------------------------
    # L'argument liberos_veec est le dictionnaire de statut Libero
    libero_actif_num = liberos_veec.get('actif_numero')
    libero_reserve_num = liberos_veec.get('reserve_numero') 
    is_libero_on_court_status = liberos_veec.get('is_on_court')
    # ----------------------------------------------------
    
    veec_colors = []
    veec_line_colors = []
    veec_line_widths = [] # <--- NOUVELLE LISTE À AJOUTER

    # Suppression de la ligne précédente qui utilisait 'libero_numero' obsolète
    # et des initialisations redondantes.
    
    for pos in veec_positions_list:
        # 1. Récupérer les données du joueur à la position actuelle (P[pos])
     player_data = formation_equipe.get(pos, {})
     player_on_court_numero = player_data.get('numero') 
     # 2. VÉRIFICATION : Est-ce que le joueur actuel est le Libero ACTIF ou RESERVE ?
     is_libero_in_pos = is_libero_on_court_status and \
                             (player_on_court_numero == libero_actif_num or player_on_court_numero == libero_reserve_num)
     if is_libero_in_pos:
        # Style Libero : Bleu (Remplissage), Bleu (Bordure), Épais (3)
        veec_colors.append('#ADD8E6')        
        veec_line_colors.append('white')      # Bordue/contrastée
        veec_line_widths.append(3)          # Bordure épaisse pour l'identification
        # Si vous utilisez veec_text_colors, ajoutez 'black' ici.
     else:
        # Style standard VEEC
        veec_colors.append(VEEC_COLOR)
        veec_line_colors.append('white')    # Bordure par défaut
        veec_line_widths.append(1)          # Bordure fine
            
    # Le reste de la fonction (fig.add_trace, etc.) reste inchangé.

    fig.add_trace(go.Scatter(
        x=veec_x, y=veec_y, hoveron='points', connectgaps=False, mode="markers+text", name="VEEC",
        # MODIFIÉ: Utiliser les listes de couleurs calculées
        marker=dict(size=85, color=veec_colors, symbol="circle", line=dict(width=veec_line_widths, color=veec_line_colors)),
        text=veec_text, textposition="middle center",
        textfont=dict(color="white", size=18, weight="bold"),
        customdata=veec_customdata, hoverinfo='text',
        hovertext=veec_hovertext))

    adverse_positions_list = sorted(list(ADVERSE_POSITIONS_COORDS.keys())) 
    adverse_x = [ADVERSE_POSITIONS_COORDS[pos]["x"] for pos in adverse_positions_list]
    adverse_y = [ADVERSE_POSITIONS_COORDS[pos]["y"] for pos in adverse_positions_list]
    adverse_text = [str(formation_adverse.get(pos, {}).get('numero', '?')) for pos in adverse_positions_list]

    adverse_colors = []      # <--- NOUVEAU
    adverse_line_colors = [] # <--- NOUVEAU
    adverse_line_widths = [] # <--- NOUVEAU

    # ----------------------------------------------------
    # NOUVELLE LOGIQUE LIBERO ADVERSE
    # ----------------------------------------------------
    for pos in adverse_positions_list:
        player_data = formation_adverse.get(pos, {})
        player_on_court_numero = player_data.get('numero') 

        # VÉRIFICATION : Est-ce que le joueur actuel est le Libero Adverse ?
        is_libero_in_pos = player_on_court_numero == libero_adverse_num
        
        if is_libero_in_pos and libero_adverse_is_on_court:
            # Style Libero Adverse : Rouge, Bordure Rouge Épaisse
            adverse_colors.append('#F08080')
            adverse_line_colors.append('white')
            adverse_line_widths.append(3)
        else:
            # Style standard Adverse
            adverse_colors.append(ADVERSE_COLOR)
            adverse_line_colors.append('white')
            adverse_line_widths.append(1)

    fig.add_trace(go.Scatter(
        x=adverse_x, y=adverse_y, mode="markers+text", name="Adversaire",
        marker=dict(size=85, color=adverse_colors, symbol="circle", line=dict(width=adverse_line_widths, color=adverse_line_colors)),
        text=adverse_text, textposition="middle center",
        textfont=dict(color="white", size=18, weight="bold"), hoverinfo='none',
    ))

    service_coords = {}
    if service_actuel == 'VEEC':
        service_coords = VEEC_POSITIONS_COORDS[1]
        x_offset, y_offset = -8, -8 
    elif service_actuel == 'ADVERSAIRE':
        service_coords = ADVERSE_POSITIONS_COORDS[1]
        x_offset, y_offset = 8, 8 
    
    if service_coords:
        fig.add_trace(go.Scatter(
            x=[service_coords["x"] + x_offset],
            y=[service_coords["y"] + y_offset], 
            mode="text", name="Service Ball",
            text=["🏐"], textposition="middle center",
            textfont=dict(size=53), hoverinfo='none',
        ))

    fig.update_layout(
        xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, visible=False, fixedrange=True),
        yaxis=dict(range=[0, 100], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=0.5, fixedrange=True),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', dragmode=False,
        clickmode='event')
    
    return fig, layout_config

def create_player_card(player_data, is_selected=False, is_assigned=False):
    """Génère un bouton/carte pour un joueur disponible ou assigné."""
       
    num = player_data['numero']
    name = player_data['nom']
    
    VEEC_COLOR = '#007bff' # Ajustez si votre couleur est différente
    
    style = {
        'margin': '5px', 'padding': '10px', 'borderRadius': '5px',
        'border': f'2px solid #ccc',
        'backgroundColor': '#fff',
        'cursor': 'pointer',
        'width': '100px', 
        'fontWeight': 'normal',
        'textAlign': 'center'
    }
    
    # ✅ GESTION DU SURLIGNAGE
    if is_selected:
        style.update({'backgroundColor': VEEC_COLOR, 'color': 'white', 'fontWeight': 'bold', 'border': '3px solid black'})
    
    # ✅ GESTION DU JOUER ASSIGNÉ
    elif is_assigned:
        style.update({'backgroundColor': '#eee', 'border': f'2px dashed #666', 'cursor': 'not-allowed', 'opacity': 0.6})
        
    # Le bouton est désactivé s'il est déjà assigné ou s'il est sélectionné (pour éviter un second clic inutile)
    return html.Button(
        html.Div([
            html.B(f"N°{num}"), 
            html.Small(name.split()[0]) # Affiche seulement le prénom
        ]),
        id={'type': 'setup-player-select', 'index': str(num)},
        n_clicks=0,
        style=style,
        disabled=is_assigned
    )

def create_position_card(pos_num, assigned_player_data, selected_player_num):
    """Génère une carte pour une position sur le terrain (P1 à P6), avec un style conditionnel."""
    
    # 🚨 LIGNE DE DÉBOGAGE CRITIQUE : Utile pour vérifier la persistance des données
    print(f"DEBUG RENDER P{pos_num}: Player Data Received -> {assigned_player_data.get('numero') if assigned_player_data else 'NONE'}")
    
    # --- 1. Détermination de l'État et des Données ---
    
    num_display = "?"
    name_display = "VIDE"

    is_assigned = assigned_player_data is not None
    
    # --- 2. LOGIQUE D'AFFICHAGE ET DE STYLE ---

    if is_assigned:
        # Remplissage des données
        num = assigned_player_data.get('numero')
        name = assigned_player_data.get('nom', 'N/A')
        num_display = str(num)
        name_display = name.split()[0]
        
        # 🚨 CAS 1: Position assignée (ROUGE/Occupé permanent)
        style = {
            'border': '2px solid #CC0000',      # Rouge vif
            'backgroundColor': '#FFDADA',       # Fond Rose/Rouge très clair
            'color': '#CC0000',                 # Texte rouge
            'fontWeight': 'bold',
            'boxShadow': '0 0 5px rgba(204, 0, 0, 0.5)'
        }
        
    elif selected_player_num is not None:
         # 🚨 CAS 2: Position vide, mais un joueur est sélectionné (VERT/Cible temporaire)
        style = {
            'border': '2px solid #00AA00',      # Vert vif
            'backgroundColor': '#DAFFDA',       # Fond Vert très clair
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

    # --- 3. RETURN (Fusion des styles) ---
    
    # Styles de base (communs à tous les boutons)
    base_styles = {
        'margin': '5px', 'padding': '10px', 'borderRadius': '8px', 
        'width': '30%', 'height': '120px', 'textAlign': 'center',
        'cursor': 'pointer'
    }

    # Fusion des styles conditionnels ('style') avec les styles de base ('base_styles')
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


def create_pre_match_setup_modal(current_state):
    """Génère la modal de configuration pré-match. Filtre les joueurs assignés."""
    
    VEEC_COLOR = '#007bff' # Remplacez par votre couleur réelle
    ROSTER_VEEC = current_state.get('JOUERS_VEEC', {})
    
    # --- 1. GESTION DES TYPES ET DES NUMÉROS ASSIGNÉS ---
    
    # Les clés du ROSTER sont généralement des chaînes (str) dans Dash, nous convertissons tout en str pour la comparaison.
    
    libero_actif_num = current_state.get('liberos_veec', {}).get('actif_numero', 99)
    libero_reserve_num = current_state.get('liberos_veec', {}).get('reserve_numero', None)
    
    # On utilise un Set de CHAÎNES pour une recherche rapide et précise
    liberos_num_str = {str(libero_actif_num)}
    if libero_reserve_num: liberos_num_str.add(str(libero_reserve_num))
    
    temp_formation = current_state.get('temp_setup_formation_veec', {})
    
    # 🚨 CORRECTION : On récupère les numéros assignés (convertis en chaîne)
    assigned_nums_str = {str(p['numero']) for p in temp_formation.values()}
    
    # Récupération du joueur actuellement sélectionné (laissé en INT pour la comparaison facile)
    selected_num = current_state.get('temp_setup_selected_player_num')
    selected_num_str = str(selected_num) if selected_num is not None else None
    
    # --- 2. JOUERS DISPONIBLES (Filtrage) ---
    
    player_list_components = []
    
    # Tri par numéro (en forçant la conversion en int pour un tri correct 1, 2, 10 au lieu de 1, 10, 2)
    sorted_roster = sorted(ROSTER_VEEC.items(), key=lambda item: int(item[0]))
    
    for num_str, data in sorted_roster:
        
        is_assigned = num_str in assigned_nums_str # Vérifie si le joueur est sur le terrain
        is_libero = num_str in liberos_num_str     # Vérifie si c'est un libéro
        is_selected = num_str == selected_num_str  # Vérifie si le joueur est sélectionné
        
        # ✅ LOGIQUE DE FILTRAGE : Afficher s'il n'est PAS libéro ET n'est PAS assigné.
        if not is_libero and not is_assigned: 
            player_list_components.append(
                create_player_card(
                    data, 
                    is_selected=is_selected, 
                    is_assigned=False # Il ne peut pas être assigné s'il est filtré
                )
            )
            
    # --- 3. POSITIONS SUR LE TERRAIN (P1 à P6) ---
    
    # 🚨 CORRECTION : On s'assure de passer le numéro du joueur sélectionné à create_position_card
    position_list_components = [
        create_position_card(
            pos, 
            assigned_player_data=temp_formation.get(pos),
            selected_player_num=selected_num # Passe l'INT pour la comparaison avec l'index de position (1, 2, etc.)
        )
        for pos in range(1, 7)
    ]
    
    # --- 4. MESSAGE ET BOUTON ---
    
    is_ready = len(temp_formation) == 6
    feedback_msg = f"{len(temp_formation)}/6 positions assignées."
    if is_ready:
        feedback_msg = "✅ Formation de départ complète. Prêt à commencer le match !"
    
    style_confirm = {
        'padding': '15px 30px', 'backgroundColor': VEEC_COLOR if is_ready else '#aaa',
        'color': 'white', 'border': 'none', 'borderRadius': '8px', 'fontSize': '1.2em', 
        'cursor': 'pointer' if is_ready else 'not-allowed', 'marginTop': '20px'
    }

    # ... (Le retour de la modal reste inchangé)
    modal_content = html.Div(
        children=[
            # ... (Toute la structure HTML de votre modal)
            html.H2("Configuration de la Formation de Départ VEEC", style={'textAlign': 'center', 'color': VEEC_COLOR, 'marginBottom': '20px'}),
            html.Div(feedback_msg, id='setup-feedback', style={'textAlign': 'center', 'fontWeight': 'bold', 'marginBottom': '20px'}),
            
            html.H3("Positions de Départ (P1 - P6)", style={'borderBottom': '1px solid #ddd', 'paddingBottom': '10px'}),
            html.Div(position_list_components, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around'}),
            
            html.H3("Joueurs Disponibles (Sélectionnez pour assigner)", style={'borderBottom': '1px solid #ddd', 'padding': '20px 0 10px 0', 'marginTop': '20px'}),
            html.Div(player_list_components, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around'}),
            
            html.Div(
                html.Button("Démarrer le Match", id='btn-confirm-setup', n_clicks=0, disabled=not is_ready, style=style_confirm),
                style={'textAlign': 'center', 'marginTop': '30px'}
            )
        ],
        style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 'width': '90%', 'maxWidth': '800px', 'boxShadow': '0 10px 30px rgba(0,0,0,0.5)'}
    )
    
    return html.Div(children=modal_content, style={'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.9)', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'zIndex': 1000})
# --- INITIALISATION DE L'APPLICATION DASH ---

VIEWPORT_META = [
    {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1.0, user-scalable=no"}
]

app = dash.Dash(__name__, suppress_callback_exceptions=True, meta_tags=VIEWPORT_META)

initial_state = {
    'formation_actuelle': FORMATION_INITIALE,
    'joueurs_banc': JOUEURS_BANC_INITIAL,
    'formation_adverse_actuelle': FORMATION_ADVERSE_INITIALE,
    'joueurs_banc_adverse': BANC_ADVERSE_INITIAL,
    # 🚨 VÉRIFIEZ BIEN CES DEUX CLÉS
    'match_setup_completed': False, 
    'temp_setup_formation_veec': {}, 
    'temp_setup_selected_player_num': None,
    # Utilisez le dictionnaire converti
    'JOUERS_VEEC': JOUERS_VEEC_DICT,
    'service_actuel': 'VEEC', 
    'score_veec': 0, 'score_adverse': 0, 
    'sets_veec': 0, 'sets_adverse': 0,
    'current_set': 1,
    'match_ended': False,  # <-- NOUVEAU : Indicateur global de fin de match
    'match_winner': None,  # <-- NOUVEAU : Stocke le gagnant ('VEEC' ou 'ADVERSE')
    'timeouts_veec': 0, 'timeouts_adverse': 0,
    'sub_veec': 0, 'sub_adverse': 0,
    'rotation_count': 0, 
    'service_choisi': True, 
    'historique_stats': [],
    'start_time': time.time(),
    'timer_end_time': 0, 
    'timer_type': None,
    'sub_en_cours_team': None,
    # CORRECTION : Le feedback est maintenant DANS l'état temporaire
    'temp_sub_state': {'entrant': None, 'sortant_pos': None, 'feedback': ""},
    'liberos_veec': {
        # Statut du Libero Actif (N°8)
        'actif_numero': LIBERO_PRINCIPAL_NUM,      # Utilise la constante
        'is_on_court': False,                  
        'starter_numero_replaced': None,       
        'current_pos_on_court': None,          

        # Statut du Libero Remplaçant (N°9)
        'reserve_numero': LIBERO_RESERVE_NUM,     # Utilise la constante
        'is_reserve_used': False,              
        'reserve_can_swap_in': False,          
        
        # Le titulaire que le Libero remplace (N°6 M. Central)
        'libero_spot_starter_numero': 6,       
    },
}

# --- MISE EN PAGE (LAYOUT) ---

app.layout = html.Div(
    [
        dcc.Store(id='match-state', data=initial_state),
        dcc.Store(id='joueur-selectionne', data=None),
        dcc.Store(id='setup-refresh-trigger'), # 🚨 AJOUTEZ CETTE LIGNE
        dcc.Store(id='current-set', data=1), 
        dcc.Interval(id='interval-component', interval=1000, n_intervals=0), 
        dcc.Store(id='close-modal-trigger', data=0), 
        # 🚨 NOUVEAU : Conteneur de la modal de configuration (sera affiché ou masqué)
        html.Div(id='pre-match-setup-container'),
        html.Div(id='service-modal-container'), 
        html.Div(id='stat-modal-container'), 
        
        # CORRECTION : Suppression du 'sub-cancel-btn' statique
        # CORRECTION : Ajout du div de feedback statique
        #html.Div(id='sub-feedback-msg', children=None, style={'display': 'none'}),
        
        html.Div([
             html.Div([
             html.Span("VEEC", style={'fontSize': '1.8em', 'fontWeight': 'bold', 'fontFamily': 'sans-serif', 'color': '#333', 'marginRight': '15px'}),
             html.Div(
             html.Img(src='/assets/logo-simple.png', style={'height': '35px', 'width': '35px'}),
             style={
                'border': f'2px solid {VEEC_COLOR}',
                'borderRadius': '50%', 
                'padding': '2px',
                'display': 'flex', 
                'alignItems': 'center', 
                'justifyContent': 'center',
                'height': '45px', 'width': '45px',
                'boxShadow': '0 0 5px rgba(0,0,0,0.1)',
                'overflow': 'hidden',
                'backgroundColor': 'white'
             }),
             ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'width': '35%', 'paddingRight': '20px'}),
        
             html.Div([
                html.Span(id='sets-veec-display', children='0', style={'color': VEEC_COLOR, 'fontSize': '3em', 'fontWeight': '900', 'fontFamily': 'sans-serif'}),
                 html.Span(" : ", style={'fontSize': '3em', 'color': '#666', 'fontWeight': 'lighter', 'margin': '0 10px'}),
                html.Span(id='sets-adverse-display', children='0', style={'color': ADVERSE_COLOR, 'fontSize': '3em', 'fontWeight': '900', 'fontFamily': 'sans-serif'}),
                 ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'width': '30%', 'border': '2px solid #ddd', 'borderRadius': '10px', 'padding': '10px 0', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}),
        
                 html.Div([
                 html.Span("ADVERSAIRE", style={'fontSize': '1.8em', 'fontWeight': 'bold', 'fontFamily': 'sans-serif', 'color': '#333'}),
                 html.Div(style={'height': '35px', 'width': '35px', 'backgroundColor': ADVERSE_COLOR, 'borderRadius': '5px', 'marginLeft': '10px'}),
                 ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start', 'width': '35%', 'paddingLeft': '20px'}),
        
                     ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'padding': '20px 0', 'backgroundColor': '#fff', 'borderBottom': '1px solid #ccc', 'marginBottom': '10px'}),
        
        html.Hr(),

        html.Div(id='hidden-div-for-js', style={'display': 'none'}),

        dcc.Graph(
            id='terrain-graph-statique', 
            figure=create_court_figure(FORMATION_INITIALE, FORMATION_ADVERSE_INITIALE, initial_state['service_actuel'], initial_state['liberos_veec'])[0], 
            config={'displayModeBar': False, 'scrollZoom': False, 'doubleClick': False,
                    'modeBarButtonsToRemove': [
            'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'autoscale', 
            'zoomIn2d', 'zoomOut2d', 'resetScale2d', 'hoverClosestCartesian', 
            'hoverCompareCartesian', 'toggleSpikelines', 'sendDataToCloud'
        ]}, 
            style={'width': '100%', 'height': '50vh'} 
        ), 
        
        html.Hr(),

        html.Button('Sub. Libero', id='btn-sub-libero-veec', n_clicks=0,
            style={'backgroundColor': '#28a745', 'color': 'white', 'padding': '10px', 'borderRadius': '5px', 'marginRight': '10px'}),

        # Dans votre mise en page (app.layout ou une fonction d'éléments) :
        html.Button('Swap Libero N°9', id='btn-swap-libero-reserve', n_clicks=0, 
            style={'backgroundColor': 'orange', 'color': 'white', 'fontWeight': 'bold', 'margin': '5px'}),

        # Ajoutez quelque part dans votre layout pour afficher les messages du callback
        html.Div(id='feedback-output-libero', style={'color': 'orange', 'marginTop': '10px'}),
        
        html.Div([
            html.Button("Point VEEC ➕", id='btn-point-veec', n_clicks=0, 
                         style={'marginRight': '10px', 
            'backgroundColor': VEEC_COLOR, 
            'color': 'white',
            'fontSize': '1.8em',
            'padding': '15px 30px',
            'minHeight': '70px',
            'borderRadius': '8px',
            'fontWeight': 'bold'}),
            html.Button("Point ADVERSAIRE ➖", id='btn-point-adverse', n_clicks=0, 
                         style={'backgroundColor': ADVERSE_COLOR, 
            'color': 'white',
            'fontSize': '1.8em',
            'padding': '15px 30px',
            'minHeight': '70px',
            'borderRadius': '8px',
            'fontWeight': 'bold'}),
        ], style={'textAlign': 'center', 'marginBottom': '20px', 'marginTop': '10px'}),

        # Ajoutez ce Div dans votre layout, près de la modal de substitution ou sous la zone de score/contrôle.
        html.Div(
         id='feedback-sub-output',
         children=None, # Commence vide
         style={
             'color': 'red', 
             'fontWeight': 'bold', 
             'textAlign': 'center',
             'marginTop': '10px'
              }
            ),

        html.Div([
            html.Div([
                html.H4("Set ", style={'width': '20%', 'textAlign': 'left', 'fontSize': '1.5em', 'paddingLeft': '10px'}),
                html.Span("1", id='set-number-display', style={'fontSize': '1.5em', 'fontWeight': 'bold'}),
                html.Div(id='timer-progress-bar', style={'width': '70%', 'textAlign': 'right', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end'}), 
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '15px', 'paddingRight': '10px'}),

            html.Div([
                
                html.Div(
                    id='score-veec-container',
                    children=html.Div(id='score-veec-large', children='0', 
                                     style={'fontSize': '5em', 'fontWeight': '900', 'fontFamily': 'sans-serif', 'color': 'black'}), 
                    style={
                        'width': '30%', 'textAlign': 'center', 
                        'padding': '10px 0', 
                        'border': f'3px solid {VEEC_COLOR}', 
                        'borderRadius': '15px', 
                        'boxShadow': '0 4px 10px rgba(0,0,0,0.1)',
                        'backgroundColor': 'white'
                    }
                ),

                html.Div([
                    
                    html.Div([
                        html.Span(id='btn-sub-veec-center', children='0', style={'color': VEEC_COLOR, 'fontSize': '2em', 'fontWeight': 'bold', 'marginRight': '5px'}),
                        html.Button("Sub", id='btn-sub-veec', n_clicks=0, style={'color': '#666', 'fontSize': '1em', 'border': 'none', 'background': 'none', 'padding': '0 5px'}), 
                        html.Span("|", style={'margin': '0 15px', 'color': '#ddd'}),
                        html.Button("Sub", id='btn-sub-adverse', n_clicks=0, style={'color': '#666', 'fontSize': '1em', 'border': 'none', 'background': 'none', 'padding': '0 5px', 'marginRight': '5px'}),
                        html.Span(id='btn-sub-adverse-center', children='0', style={'color': ADVERSE_COLOR, 'fontSize': '2em', 'fontWeight': 'bold'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '10px'}),
                    
                    html.Div([
                        html.Span(id='btn-to-veec-center', children='0', style={'color': VEEC_COLOR, 'fontSize': '2em', 'fontWeight': 'bold', 'marginRight': '5px'}),
                        html.Button("TO", id='btn-to-veec', n_clicks=0, style={'color': '#666', 'fontSize': '1em', 'border': 'none', 'background': 'none', 'padding': '0 5px'}), 
                        html.Span("|", style={'margin': '0 15px', 'color': '#ddd'}),
                        html.Button("TO", id='btn-to-adverse', n_clicks=0, style={'color': '#666', 'fontSize': '1em', 'border': 'none', 'background': 'none', 'padding': '0 5px', 'marginRight': '5px'}), 
                        html.Span(id='btn-to-adverse-center', children='0', style={'color': ADVERSE_COLOR, 'fontSize': '2em', 'fontWeight': 'bold'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),
                    
                ], style={'width': '40%', 'textAlign': 'center', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center'}),
                
                html.Div(
                    id='score-adverse-container',
                    children=html.Div(id='score-adverse-large', children='0', 
                                     style={'fontSize': '5em', 'fontWeight': '900', 'fontFamily': 'sans-serif', 'color': 'black'}),
                    style={
                        'width': '30%', 'textAlign': 'center', 
                        'padding': '10px 0', 
                        'border': f'3px solid {ADVERSE_COLOR}', 
                        'borderRadius': '15px', 
                        'boxShadow': '0 4px 10px rgba(0,0,0,0.1)',
                        'backgroundColor': 'white'
                    }
                ),
                
            ], style={'display': 'flex', 'justifyContent': 'space-around', 'alignItems': 'center', 'marginTop': '15px', 'marginBottom': '15px'}),
            
        ], style={'padding': '20px', 'borderTop': '1px solid #ccc'}),
        
        html.Details([
            html.Summary("Historique des Actions (Détail)", style={'marginTop': '20px', 'fontWeight': 'bold'}),
            # CORRECTION : Initialisation du tableau
            html.Div(id='historique-output', children=create_historique_table(initial_state['historique_stats']))
        ], style={'padding': '10px'}),
    ],
    style={'padding': '0', 'margin': '0'}, 
)

# --- CALLBACKS (1 à 7) ---

# 0. Créez ce callback après votre définition d'app.layout
@app.callback(
    # Output principal : Mise à jour de l'état du match
    Output('match-state', 'data', allow_duplicate=True),
    # Output secondaire : Afficher un message de feedback à l'utilisateur
    Output('feedback-output-libero', 'children'), 
    
    Input('btn-swap-libero-reserve', 'n_clicks'),
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_libero_swap_ui(n_clicks, current_state):
    """
    Gère l'activation du Libero de réserve (N°9) par le bouton dédié.
    """
    if n_clicks is None or n_clicks == 0:
        raise dash.exceptions.PreventUpdate

    # La fonction swap_liberos_on_bench est appelée ici
    new_state, feedback_message = swap_liberos_on_bench(current_state)
    
    # new_state contient l'état mis à jour (ou non si échec)
    # feedback_message contient le résultat de l'opération
    return new_state, feedback_message


# 0.3 Gestion de la sélection Joueur/Position et Affichage de la Modal
@app.callback(
    Output('pre-match-setup-container', 'children'),
    Output('match-state', 'data', allow_duplicate=True),
    [
        Input({'type': 'setup-player-select', 'index': ALL}, 'n_clicks'),
        Input({'type': 'setup-position-assign', 'index': ALL}, 'n_clicks'),
        Input('match-state', 'data') 
    ],
    State('match-state', 'data'),
    prevent_initial_call='initial_duplicate' 
)
def handle_setup_selection(player_clicks, position_clicks, 
                           match_state_input, 
                           current_state_from_state):
    
    ctx = dash.callback_context
    triggered_prop_id = ctx.triggered[0]['prop_id'] if ctx.triggered else 'No trigger'
    
    # ----------------------------------------------------------------------
    # 🚨 BLOC CRITIQUE FINAL : TOUJOURS UTILISER L'INPUT FRAIS COMME BASE
    # ----------------------------------------------------------------------
    # Utiliser l'Input match_state_input (toujours la version la plus fraîche)
    state_to_use = match_state_input
    
    # Si l'Input est None (très rare, mais par sécurité), on utilise le State.
    if state_to_use is None:
        state_to_use = current_state_from_state
        
    new_state = copy.deepcopy(state_to_use)
    
    # Assurer que la formation est initialisée (avec des clés ENTRIES)
    if 'temp_setup_formation_veec' not in new_state:
        new_state['temp_setup_formation_veec'] = {}
    temp_formation = new_state['temp_setup_formation_veec'] 
    
    # ----------------------------------------------------------------------
    # A. GESTION DE L'AFFICHAGE INITIAL ET DU REFRESH 
    # ----------------------------------------------------------------------
    
    if not ctx.triggered or triggered_prop_id == 'match-state.data':
        if not state_to_use.get('match_setup_completed'):
            if triggered_prop_id == 'match-state.data' or not ctx.triggered:
                return create_pre_match_setup_modal(state_to_use), dash.no_update
        return None, dash.no_update
        
    # --- B. GESTION DES CLICS ---
    if not ctx.triggered[0]['value']:
         return dash.no_update, dash.no_update 
    
    player_num = new_state.get('temp_setup_selected_player_num')
    
    triggered_id = triggered_prop_id.replace(".n_clicks", "")
    
    try:
        triggered_dict = json.loads(re.sub(r"'", '"', triggered_id))
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"Erreur de parsing dans handle_setup_selection pour ID: {triggered_id} -> {e}")
        return dash.no_update, dash.no_update
    
    print(f"SETUP ACTION -> Type: {triggered_dict['type']}, Index: {triggered_dict['index']}, Joueur sélectionné (AVANT): {player_num}")
    
    # 1. Clic sur un joueur (setup-player-select)
    if triggered_dict['type'] == 'setup-player-select':
        num = int(triggered_dict['index'])
        new_selection = num if player_num != num else None
        new_state['temp_setup_selected_player_num'] = new_selection
        print(f"-> JOUER CLIC: Joueur N°{num} sélectionné. Nouvelle sélection: {new_selection}")

    # 2. Clic sur une position (setup-position-assign)
    elif triggered_dict['type'] == 'setup-position-assign':
        # 🚨 Utilisation de l'ENTIER
        pos = int(triggered_dict['index']) 
        
        # A. Désassigner
        if pos in temp_formation:
            player_to_unassign = temp_formation[pos]['numero']
            temp_formation.pop(pos)
            new_state['temp_setup_selected_player_num'] = None
            print(f"-> POSITION CLIC: P{pos} désassignée (Joueur {player_to_unassign} retiré).")
            
        # B. Assignation
        elif player_num is not None:
            ROSTER_VEEC = new_state.get('JOUERS_VEEC', {})
            
            player_data = ROSTER_VEEC.get(player_num)
            if player_data is None: 
                player_data = ROSTER_VEEC.get(str(player_num))
            
            if player_data:
                player_data['numero'] = int(player_num)
                # Utilisation de l'ENTIER 'pos' comme clé
                temp_formation[pos] = player_data 
                new_state['temp_setup_selected_player_num'] = None 
                print(f"-> POSITION CLIC: Joueur N°{player_num} assigné à P{pos}. Sélection réinitialisée.")
            else:
                print(f"-> ERREUR CRITIQUE: Données joueur non trouvées pour N°{player_num}.")
        else:
            print(f"-> POSITION CLIC: P{pos} cliquée, mais AUCUN joueur n'était sélectionné.")

    # --- D. MISE À JOUR VISUELLE (Après la logique de clic) ---
    updated_modal = create_pre_match_setup_modal(new_state)
    
    return updated_modal, new_state

# 0.4 Confirmation de la Formation et Démarrage du Match
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Output('historique-output', 'children', allow_duplicate=True),
    Input('btn-confirm-setup', 'n_clicks'),
    State('match-state', 'data'),
    prevent_initial_call=True
)
def confirm_setup_and_start_match(n_clicks, current_state):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update
    
    new_state = copy.deepcopy(current_state)
    temp_formation = new_state.get('temp_setup_formation_veec', {})
    
    if len(temp_formation) != 6:
        # Ceci ne devrait pas arriver si le bouton est désactivé
        return dash.no_update, dash.no_update 
    
    # 1. Mettre à jour la formation_actuelle
    new_state['formation_actuelle'] = temp_formation
    
    # 2. Définir le banc (tous les autres joueurs non titulaires)
    ROSTER_VEEC = new_state.get('JOUERS_VEEC', {})
    assigned_nums = [p['numero'] for p in temp_formation.values()]
    
    new_banc = {}
    for num, data in ROSTER_VEEC.items():
        # Inclure tous les joueurs non-titulaires (y compris les libéros) au banc
        if num not in assigned_nums:
            new_banc[num] = data
            
    new_state['joueurs_banc'] = new_banc

    # 3. Finaliser le setup et démarrer
    new_state['match_setup_completed'] = True
    new_state['temp_setup_formation_veec'] = {}
    new_state['temp_setup_selected_player_num'] = None
    
    # 4. Historique (Ajout de la ligne de démarrage)
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp, 'set': 1, 'score': '0-0',
        'position': 'SETUP', 'joueur_nom': 'MATCH', 'action_code': 'START', 'resultat': 'Formation Confirmée'
    }
    new_state['historique_stats'].insert(0, log_entry)
    historique_table = create_historique_table(new_state['historique_stats']) # Assurez-vous d'avoir cette fonction

    return new_state, historique_table

# 1. Gérer les points et les rotations
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Output('joueur-selectionne', 'data', allow_duplicate=True),
    Input('btn-point-veec', 'n_clicks'),
    Input('btn-point-adverse', 'n_clicks'),
    State('match-state', 'data'),
    prevent_initial_call=True,
)
def update_score_and_rotation(n_veec, n_adverse, current_state):
    new_state = copy.deepcopy(current_state)

    # 🚨 CLAUSE DE GARDE : Bloquer si le setup n'est pas terminé
    if not current_state.get('match_setup_completed'):
        # On assume que le retour d'Output('joueur-selectionne', 'data') peut être None ici
        return dash.no_update, None

    new_state = clean_formations(new_state)

    # 🚨 NOUVEAU : Bloquer le jeu si le match est terminé
    if new_state.get('match_ended'):
        return new_state, None
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return new_state, None

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    gagnant = None
    if button_id == 'btn-point-veec':
        gagnant = 'VEEC'
    elif button_id == 'btn-point-adverse':
        gagnant = 'ADVERSAIRE'
        
    if gagnant:
        service_avant = new_state['service_actuel']
        
        if gagnant == 'VEEC':
            new_state['score_veec'] += 1
            if service_avant == 'ADVERSAIRE':
                
                # Rotation VEEC (point gagné en réception)
                new_state['service_actuel'] = 'VEEC'
                new_state['formation_actuelle'] = appliquer_rotation_veec(new_state['formation_actuelle'])
                new_state['rotation_count'] += 1 
                
                # ----------------------------------------------------
                # LOGIQUE DE SORTIE FORCÉE DU LIBERO EN P4
                # ----------------------------------------------------
                liberos_status = new_state['liberos_veec']
                libero_num_to_enter = liberos_status['actif_numero'] # <--- Utilisez cette clé ! 
                
                if liberos_status['is_on_court']:
                    
                    player_in_p4 = new_state['formation_actuelle'][4]
                    libero_actif_num = liberos_status['actif_numero']
                    libero_reserve_num = liberos_status['reserve_numero']
                    
                    is_libero_in_p4 = player_in_p4['numero'] == libero_actif_num or player_in_p4['numero'] == libero_reserve_num
                    
                    if is_libero_in_p4:
                        
                        # --- Libero en P4 : Sortie Forcée ---
                        
                        pos_sortie = 4
                        starter_num = liberos_status['starter_numero_replaced']
                        joueur_libero = player_in_p4 
                        joueur_titulaire = new_state['joueurs_banc'].get(starter_num)
                        
                        if joueur_titulaire:
                            
                            # 1. Mettre le Libero sur le banc 
                            new_state['joueurs_banc'][joueur_libero['numero']] = joueur_libero
                            
                            # 2. Mettre le Titulaire sur le terrain en P4
                            new_state['formation_actuelle'][pos_sortie] = joueur_titulaire
                            
                            # 3. Retirer le Titulaire du banc
                            del new_state['joueurs_banc'][starter_num]
                            
                            # 4. Mettre à jour le statut Libero
                            liberos_status['is_on_court'] = False
                            liberos_status['starter_numero_replaced'] = None
                            liberos_status['current_pos_on_court'] = None 
                            
                            # 5. Enregistrement dans l'historique
                            log_entry = {
                                'timestamp': time.time(), 
                                'action_code': 'LIBERO_AUTO_OUT', 
                                'details': f"L{joueur_libero['numero']} OUT, N°{starter_num} IN P{pos_sortie}"
                            }
                            new_state['historique_stats'].insert(0, log_entry)
                        
                    # ----------------------------------------------------
                    # GESTION DE LA NOUVELLE POSITION DU LIBERO (s'il est resté)
                    # ----------------------------------------------------
                    
                    # Si le Libero est toujours sur le terrain après la rotation (il était en P1 ou P6)
                    if liberos_status['is_on_court']:
                        
                        # Le joueur en P6 (nouvelle position) était en P1 (ancienne position arrière)
                        if new_state['formation_actuelle'][6]['numero'] == libero_actif_num or new_state['formation_actuelle'][6]['numero'] == libero_reserve_num:
                            liberos_status['current_pos_on_court'] = 6
                        # Le joueur en P5 (nouvelle position) était en P6.
                        elif new_state['formation_actuelle'][5]['numero'] == libero_actif_num or new_state['formation_actuelle'][5]['numero'] == libero_reserve_num:
                            liberos_status['current_pos_on_court'] = 5
                    
                new_state['liberos_veec'] = liberos_status # Mettre à jour l'état final Libero
            
        elif gagnant == 'ADVERSAIRE':
            new_state['score_adverse'] += 1
            if service_avant == 'VEEC':
                new_state['service_actuel'] = 'ADVERSAIRE'
                new_state['formation_adverse_actuelle'] = appliquer_rotation_adverse(new_state['formation_adverse_actuelle'])
                new_state['rotation_count'] += 1 
                
    # ----------------------------------------------------
    # NOUVEAU BLOC CENTRALISÉ DE VÉRIFICATION DE FIN DE SET / FIN DE MATCH
    # ----------------------------------------------------
    
    set_ended = False
    match_winner = None
    
    # Déterminer le seuil de points (25 points pour sets 1-4, 15 points pour set 5)
    seuil_points = 15 if new_state['current_set'] == 5 else 25
    
    score_veec = new_state['score_veec']
    score_adverse = new_state['score_adverse']

    # Vérification de la fin du set (score >= seuil ET écart >= 2)
    if score_veec >= seuil_points and (score_veec - score_adverse) >= 2:
        match_winner = 'VEEC'
        set_ended = True
    elif score_adverse >= seuil_points and (score_adverse - score_veec) >= 2:
        match_winner = 'ADVERSAIRE'
        set_ended = True

    if set_ended:
        # Mise à jour des sets gagnés
        if match_winner == 'VEEC':
            new_state['sets_veec'] += 1
        else:
            new_state['sets_adverse'] += 1
        
        # 🚨 VÉRIFICATION DE LA FIN DU MATCH (3 sets gagnants)
        if new_state['sets_veec'] == 3 or new_state['sets_adverse'] == 3:
            new_state['match_ended'] = True
            new_state['match_winner'] = match_winner
            # Ajoutez ici une logique pour le minuteur (Ex: new_state['timer_type'] = 'MATCH_ENDED')
            
        else:
            # Préparation pour le prochain set
            new_state['score_veec'], new_state['score_adverse'] = 0, 0
            new_state['current_set'] += 1 
            
            # Réinitialisation des temps-morts et substitutions
            new_state['timeouts_veec'], new_state['timeouts_adverse'] = 0, 0
            new_state['sub_veec'], new_state['sub_adverse'] = 0, 0
            
            # Gestion de la minuterie de pause
            # Assurez-vous que LONG_BREAK_DURATION_SECONDS et SHORT_BREAK_DURATION_SECONDS sont accessibles
            duration = new_state.get('LONG_BREAK_DURATION_SECONDS', 300) if new_state['current_set'] == 5 else new_state.get('SHORT_BREAK_DURATION_SECONDS', 180) 
            
            # Note: Vous devez avoir 'import time' en tête de votre fichier
            new_state['timer_end_time'] = time.time() + duration
            new_state['timer_type'] = 'SET_BREAK'
            
    return new_state, None # <-- Votre retour de fonction


def create_libero_sub_modal(current_state):
    """Génère la modal pour l'échange du Libero."""
    
    libero_status = current_state['liberos_veec']
    is_on_court = libero_status['is_on_court']
    # CORRECTION : Utiliser le numéro du Libero ACTIF (qui peut être 8 ou 9)
    libero_num_actif = libero_status.get('actif_numero') 
    
    libero_data = current_state['joueurs_banc'].get(libero_num_actif)    

    # Si le Libero n'est pas sur le banc, il doit être sur le terrain (gestion défensive)
    if not libero_data:
        # Tenter de récupérer les données du Libero depuis la formation si la substitution est en cours
        libero_data = next((p for p in current_state['formation_actuelle'].values() if p.get('numero') == libero_num_actif), None)
        
    modal_title = f"Échange Libero (N°{libero_num_actif})"
    
    # Contenu de la modal
    if not is_on_court:
        # Le Libero (N°4) est sur le banc. Il doit entrer.
        # Lister les joueurs qui peuvent être remplacés (P1, P5, P6)
        positions_remplacables = []
        for pos in LIBERO_POSITIONS_AUTORISEES:
            player = current_state['formation_actuelle'].get(pos)
            if player:
                positions_remplacables.append(
                    html.Button(f"Remplacer P{pos} - N°{player['numero']} ({player['nom']})", 
                                id={'type': 'confirm-libero-in', 'pos': str(pos)}, n_clicks=0,
                                style={'margin': '5px', 'padding': '10px', 'backgroundColor': '#d4edda', 'border': '1px solid #155724', 'cursor': 'pointer'})
                )
        
        content = [
            html.H4(f"Entrée du Libero (N°{libero_num_actif})", style={'color': '#28a745'}),
            html.P("Le Libero peut remplacer n'importe quel joueur de la ligne arrière (P1, P5, P6) :"),
            html.Div(positions_remplacables, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),
        ]
        
    else:
        # Le Libero est sur le terrain. Il doit sortir.
        starter_numero = libero_status['starter_numero_replaced']
        starter_data = current_state['joueurs_banc'].get(starter_numero)
        current_pos = libero_status['current_pos_on_court']
        
        if starter_data:
            content = [
                html.H4(f"Sortie du Libero (N°{libero_num_actif})", style={'color': '#dc3545'}),
                html.P(f"Le Libero doit être remplacé par le joueur titulaire qu'il a remplacé :"),
                html.P(f"Joueur entrant : N°{starter_data['numero']} ({starter_data['nom']}) à la position P{current_pos}"),
                html.Button("Confirmer la sortie", id='btn-confirm-libero-out', n_clicks=0, 
                            style={'padding': '10px 20px', 'backgroundColor': '#dc3545', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'marginTop': '15px', 'cursor': 'pointer'})
            ]
        else:
             content = [html.P("Erreur: Impossible de trouver le joueur titulaire à remplacer par le Libero.")]

    # Construction de la modal
    return html.Div(
        children=[
            html.H3(modal_title, style={'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div(content, style={'textAlign': 'center', 'marginBottom': '20px'}),
            html.Button("Annuler", id='btn-cancel-libero-sub', n_clicks=0, 
                        style={'padding': '10px 20px', 'backgroundColor': '#6c757d', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'})
        ],
        style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 'width': '90%', 'maxWidth': '500px', 'boxShadow': '0 10px 30px rgba(0,0,0,0.5)', 'position': 'relative'}
    )


# 2. Sélection du joueur (pour la modal)
@app.callback(
    Output('joueur-selectionne', 'data', allow_duplicate=True),
    Input('terrain-graph-statique', 'clickData'), 
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_player_click_dash(clickData, current_state):
    current_state = clean_formations(current_state)
    
    if current_state.get('timer_end_time', 0) > time.time() or current_state.get('sub_en_cours_team'):
        return dash.no_update
    
    if clickData and 'points' in clickData and clickData['points']: 
        point = clickData['points'][0]
        if point.get('curveNumber') == 0 and 'customdata' in point:
            try:
                pos = int(point['customdata']) 
                joueur_data = current_state['formation_actuelle'].get(pos)
                if joueur_data:
                    return {'pos': pos, 'data': joueur_data, 'equipe': 'VEEC'}
            except (ValueError, TypeError):
                pass 
    return None 


# 3. Mise à jour de l'interface graphique
@app.callback(
    Output('terrain-graph-statique', 'figure'), 
    Output('terrain-graph-statique', 'config'), 
    Output('score-veec-large', 'children'),
    Output('score-adverse-large', 'children'),
    Output('sets-veec-display', 'children'), 
    Output('sets-adverse-display', 'children'), 
    Output('set-number-display', 'children'), 
    Output('btn-sub-veec-center', 'children'),
    Output('btn-to-veec-center', 'children'), 
    Output('btn-sub-adverse-center', 'children'),
    Output('btn-to-adverse-center', 'children'),
    Input('match-state', 'data'),
)
def update_ui_scores(current_state):
    current_state = clean_formations(current_state)
    
    fig, config = create_court_figure(current_state['formation_actuelle'], 
                                     current_state['formation_adverse_actuelle'], 
                                     current_state['service_actuel'],
                                     current_state['liberos_veec']) # <-- Clé changée à 'liberos_veec'
    
    score_veec_large = str(current_state['score_veec'])
    score_adverse_large = str(current_state['score_adverse'])
    sets_veec = str(current_state['sets_veec'])
    sets_adverse = str(current_state['sets_adverse'])
    set_number = str(current_state['current_set'])
    
    to_veec_count = str(current_state['timeouts_veec'])
    sub_veec_count = str(current_state['sub_veec'])
    to_adverse_count = str(current_state['timeouts_adverse'])
    sub_adverse_count = str(current_state['sub_adverse'])
    
    return (fig, config, score_veec_large, score_adverse_large, sets_veec, sets_adverse, 
            set_number,
            sub_veec_count, to_veec_count, sub_adverse_count, to_adverse_count)


# 4. Affichage du Timer (Mise à jour de l'affichage UNIQUEMENT)
@app.callback(
    Output('timer-progress-bar', 'children'),
    Input('interval-component', 'n_intervals'),
    State('match-state', 'data'),
    prevent_initial_call=True
)
def update_timer_display_only(n, current_state):
    
    timer_end_time = current_state.get('timer_end_time', 0)
    timer_type = current_state.get('timer_type')
    
    # Cas 1: Minuteur inactif (Affichage du temps de jeu écoulé)
    if timer_end_time == 0:
        elapsed_seconds = int(time.time() - current_state.get('start_time', time.time()))
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        time_str = f"Temps de jeu : {minutes:02d}:{seconds:02d}"
        return html.Div(time_str, style={'textAlign': 'right', 'fontSize': '1.1em', 'fontWeight': 'bold', 'color': '#333'})

    remaining_seconds = int(timer_end_time - time.time())
    
    # Cas 2: Minuteur expiré (Affichage du message de fin)
    if remaining_seconds <= 0:
        time_str = "REPRISE DU JEU !"
        return html.Div(time_str, style={'textAlign': 'center', 'color': 'red', 'fontWeight': 'bold', 'fontSize': '1.1em'})
        
    # Cas 3: Minuteur actif (Affichage de la barre de progression)
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    
    title = ""
    duration = 1 # Durée par défaut, sera écrasée
    
    if timer_type == 'TIMEOUT':
        title = "TEMPS MORT"
        color = '#ffc107' 
        # Assurez-vous que TIMEOUT_DURATION_SECONDS est défini quelque part dans votre script
        duration = TIMEOUT_DURATION_SECONDS 
    elif timer_type == 'SET_BREAK':
        title = "PAUSE SET"
        color = '#333'
        # Assurez-vous que LONG/SHORT_BREAK_DURATION_SECONDS sont définis
        duration = LONG_BREAK_DURATION_SECONDS if current_state['current_set'] == 5 else SHORT_BREAK_DURATION_SECONDS
        
    time_str = f"{title}: {minutes:02d}:{seconds:02d}"
    
    elapsed_for_bar = duration - remaining_seconds
    progress_percent = max(0, min(100, (elapsed_for_bar / duration) * 100))
    
    progress_bar = html.Div([
        html.Div(style={
            'height': '10px', 'backgroundColor': '#ddd', 'borderRadius': '5px', 'width': '100%'
        }),
        html.Div(style={
            'height': '10px', 'backgroundColor': color, 'borderRadius': '5px', 'width': f'{progress_percent}%',
            'marginTop': '-10px', 'transition': 'width 1s linear'
        })
    ], style={'width': '100%'})

    return html.Div([
        html.Div(time_str, style={'textAlign': 'center', 'fontWeight': 'bold', 'color': color, 'marginBottom': '5px'}),
        progress_bar 
    ], style={'width': '100%', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})

# 4.2 Gestion de l'Expiration du Minuteur (Met à jour le match-state)
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Input('interval-component', 'n_intervals'),
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_timer_expiration(n, current_state):
    
    # 🚨 CLAUSE DE GARDE : Bloquer si le setup n'est pas terminé
    if not current_state.get('match_setup_completed', False):
        return dash.no_update # C'est le seul Output, donc retour simple

    timer_end_time = current_state.get('timer_end_time', 0)
    
    # N'agit que si un minuteur est en cours
    if timer_end_time > 0 and time.time() >= timer_end_time:
        
        new_state = copy.deepcopy(current_state)
        
        # Réinitialiser l'état du minuteur
        print(f"DEBUG: Minuteur ({new_state.get('timer_type')}) expiré. Réinitialisation de l'état.")
        new_state['timer_end_time'] = 0
        new_state['timer_type'] = None
        
        # L'état est mis à jour ici
        return new_state
        
    return dash.no_update # Ne rien faire si le minuteur est actif ou inactif


# 5. Gérer l'enregistrement des statistiques et fermeture de la modale
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Output('joueur-selectionne', 'data', allow_duplicate=True),
    Output('historique-output', 'children', allow_duplicate=True), 
    Input({'type': 'stat-btn', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input('btn-close-modal-static', 'n_clicks'),
    State('match-state', 'data'),
    State('joueur-selectionne', 'data'),
    prevent_initial_call=True
)
def handle_stat_log_and_close(n_clicks, close_clicks, current_state, joueur_sel):
    ctx = dash.callback_context
    if not ctx.triggered or not ctx.triggered[0]['value']:
        return dash.no_update, dash.no_update, dash.no_update
    
    # 🚨 CLAUSE DE GARDE : Bloquer si le setup n'est pas terminé
    if not current_state.get('match_setup_completed', False):
        return dash.no_update, dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]['prop_id']
    new_state = copy.deepcopy(current_state) 
    
    reset_selection = False
    stat_enregistree_avec_succes = False
    
    # ----------------------------------------------------
    # 1. Gérer le bouton de Fermeture
    # ----------------------------------------------------
    if triggered_id == 'btn-close-modal-static.n_clicks':
        reset_selection = True
    
    # ----------------------------------------------------
    # 2. Gérer les clics sur les boutons de STAT (ID dynamique)
    # ----------------------------------------------------
    elif 'stat-btn' in triggered_id: 
        if not joueur_sel:
            # Même si le joueur-selectionne est None, on force la fermeture
            reset_selection = True
            
        try:
            # Parsing de l'ID dynamique
            id_str = triggered_id.replace(".n_clicks", "")
            id_str_clean = re.sub(r"'", '"', id_str) 
            triggered_dict = json.loads(id_str_clean) 
            stat_index = triggered_dict.get('index', '') 
            
            # --- 💡 Logique d'enregistrement ---
            stat_info = stat_index.split('_')
            
            if len(stat_info) != 3:
                raise IndexError(f"Format d'ID incorrect: '{stat_index}'.")

            pos, action_code, resultat = int(stat_info[0]), stat_info[1], stat_info[2]
            
            # Récupération des données du joueur (potentiellement la source de KeyError)
            if joueur_sel and joueur_sel['pos'] == pos: 
                joueur_data = new_state['formation_actuelle'][pos]
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_entry = {
                    'timestamp': timestamp, 'set': new_state['current_set'], 
                    'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
                    'position': pos, 'joueur_nom': joueur_data['nom'],
                    'action_code': action_code, 'resultat': resultat
                }
                new_state['historique_stats'].insert(0, log_entry)

                # Mise à jour du score
                if resultat in ['KILL', 'ACE', 'GAIN']:
                    new_state['score_veec'] += 1
                    
                stat_enregistree_avec_succes = True # Stat enregistrée
                
        except (KeyError, json.JSONDecodeError, ValueError, IndexError) as e:
            # Si une erreur survient, on l'affiche mais on n'interrompt pas la fermeture
            print(f"Erreur lors de l'enregistrement de la stat: {e}")
        
        # On doit toujours réinitialiser la sélection après un clic sur un bouton de stat
        reset_selection = True
    
    # ----------------------------------------------------
    # 3. Retour et Fermeture de la Modale
    # ----------------------------------------------------
    
    historique_table = create_historique_table(new_state['historique_stats'])
    
    if reset_selection:
        # En retournant None pour 'joueur-selectionne', on force la fermeture de la modal via le Callback 6.
        return new_state, None, historique_table
    
    return dash.no_update, dash.no_update, dash.no_update


# 6. Afficher/Calculer la Modal de Stat
@app.callback(
    Output('stat-modal-container', 'children', allow_duplicate=True),
    Input('joueur-selectionne', 'data'),
    State('match-state', 'data'),
    prevent_initial_call=True
)
def display_stat_modal(joueur_selectionne, current_state):
    if not joueur_selectionne or not current_state.get('service_choisi', False) or current_state.get('timer_end_time', 0) > time.time() or current_state.get('sub_en_cours_team'):
        return None
    
    joueur_sel = joueur_selectionne
    
    modal_style = {
        'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
        'backgroundColor': 'rgba(0,0,0,0.7)', 'display': 'flex', 'justifyContent': 'center', 
        'alignItems': 'center', 'zIndex': 1001 
    }
    content_style = {
        'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'width': '90%', 
        'maxWidth': '800px', 'boxShadow': '0 8px 16px rgba(0,0,0,0.4)', 'maxHeight': '90vh', 'overflowY': 'auto',
        'position': 'relative', 'zIndex': 1002 
    }

    stat_categories = [
        ("Service", "SVC", [("🎯 Ace", "ACE", "primary"), ("🔄 Service OK", "OK", "secondary"), ("💥 Faute", "FAUTE", "danger")]),
        ("Réception", "REC", [("✅ Parfaite", "PERF", "primary"), ("👐 Réception OK", "OK", "secondary"), ("💔 Manquée", "FAUTE", "danger")]),
        ("Attaque", "ATK", [("💥 Kill (Gagnant)", "KILL", "primary"), ("👐 Manusiée", "MANU", "secondary"), ("❌ Faute/Dehors", "FAUTE", "danger")]),
        ("Bloc", "BLK", [("🛡️ Block Gagnant", "GAIN", "primary"), ("🚫 Block Touché", "TOUCH", "secondary"), ("⛔ Block Faute", "FAUTE", "danger")]),
    ]

    cols = []
    for title, code_base, buttons in stat_categories:
        button_elements = []
        for label, code_result, type_class in buttons:
            btn_id = {'type': 'stat-btn', 'index': f"{joueur_sel['pos']}_{code_base}_{code_result}"}
            bg_color = {'primary': VEEC_COLOR, 'secondary': '#6c757d', 'danger': ADVERSE_COLOR}.get(type_class, '#007bff')

            button_elements.append(
                html.Button(label, id=btn_id, n_clicks=0,
                    style={'width': '100%', 'marginBottom': '5px', 'backgroundColor': bg_color, 'color': 'white', 'border': 'none', 'padding': '12px 0', 'borderRadius': '5px', 'fontSize': '1.1em'}
                ))
        
        cols.append(
            html.Div([
                html.H4(title, style={'textAlign': 'center', 'fontSize': '1.3em', 'marginBottom': '15px'}),
                *button_elements
            ], style={'width': '23%', 'display': 'inline-block', 'padding': '0 1%', 'verticalAlign': 'top'}))
    
    modal_content = html.Div(
        children=[
            html.Div([
                html.H3(f"Saisie Stat : N°{joueur_sel['data']['numero']} ({joueur_sel['data']['nom']}) - P{joueur_sel['pos']}", style={'textAlign': 'center', 'color': '#333'}),
                
                html.Button("✕ Fermer", id='btn-close-modal-static', n_clicks=0, 
                    style={'position': 'absolute', 'top': '10px', 'right': '10px', 'backgroundColor': 'transparent', 'border': 'none', 'fontSize': '1.2em', 'cursor': 'pointer'})
            ], style={'position': 'relative', 'marginBottom': '20px'}),
            
            html.Div(cols, style={'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap'})
        ], style=content_style
    )
    
    return html.Div(children=modal_content, style=modal_style)
    
    
# 7. Gérer les Temps Morts (Time Out)
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Output('stat-modal-container', 'children', allow_duplicate=True),
    Input('btn-to-veec', 'n_clicks'),
    Input('btn-to-adverse', 'n_clicks'),
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_timeouts(n_veec, n_adverse, current_state):
    # (Logique inchangée)
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    # 🚨 CLAUSE DE GARDE : Bloquer si le setup n'est pas terminé
    if not current_state.get('match_setup_completed', False):
        return dash.no_update, dash.no_update

    new_state = copy.deepcopy(current_state)
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    team = None
    if button_id == 'btn-to-veec':
        team = 'VEEC'
        count = new_state['timeouts_veec']
    elif button_id == 'btn-to-adverse':
        team = 'ADVERSAIRE'
        count = new_state['timeouts_adverse']
    else:
        return dash.no_update, dash.no_update
    
    if new_state.get('timer_end_time', 0) > time.time():
        return dash.no_update, dash.no_update

    if count >= MAX_TIMEOUTS_PER_SET:
        return dash.no_update, dash.no_update

    if team == 'VEEC':
        new_state['timeouts_veec'] += 1
    else:
        new_state['timeouts_adverse'] += 1

    new_state['timer_end_time'] = time.time() + TIMEOUT_DURATION_SECONDS
    new_state['timer_type'] = 'TIMEOUT'
    
    return new_state, None # None ferme la modale de stat si elle était ouverte

# --- NOUVELLES FONCTIONS D'AFFICHAGE DE MODAL (CORRIGÉES) ---

def create_simple_adverse_sub_modal(new_state, feedback_msg):
    """Génère la modal de confirmation pour la sub adverse (simplifiée)."""
    team = "ADVERSAIRE"
    count = new_state['sub_adverse']
    color = ADVERSE_COLOR
    
    modal_sub_content = html.Div(
        [
            html.H4(f"Substitution {team} : {count + 1}/{MAX_SUBS_PER_SET}", 
                    style={'padding': '10px', 'textAlign': 'center', 'color': color}),
            
            # ID 'sub-feedback-msg' est REQUIS pour le Callback 9
            html.Div(id='sub-feedback-msg', children=feedback_msg, style={'color': ADVERSE_COLOR, 'fontWeight': 'bold', 'marginBottom': '20px'}),
            
            # CORRECTION : Standardisation des ID dynamiques (type/index)
            html.Button("Confirmer Substitution Adverse", id={'type': 'confirm-sub-adverse', 'index': team}, n_clicks=0,
                        style={'margin': '10px', 'backgroundColor': color, 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '5px'}),
            html.Button("Annuler", id={'type': 'cancel-sub', 'index': team}, n_clicks=0, 
                        style={'margin': '10px', 'backgroundColor': '#aaa', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '5px'})
        ],
        style={'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 
               'backgroundColor': 'white', 'padding': '30px', 'borderRadius': '10px', 'zIndex': 1005, 'boxShadow': '0 0 20px rgba(0,0,0,0.5)'}
    )
    # Le conteneur parent (Div) est essentiel pour Dash
    return html.Div(children=modal_sub_content, style={'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 'backgroundColor': 'rgba(0,0,0,0.7)', 'zIndex': 1001})

def create_veec_sub_modal(new_state, temp_state, feedback_msg):
    """Génère la modal de substitution VEEC avec gestion de la surbrillance."""
    
    formation = new_state['formation_actuelle']
    banc = new_state['joueurs_banc']
    count = new_state['sub_veec']
    team = 'VEEC'
    color = VEEC_COLOR
    
    modal_style = {
        'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
        'backgroundColor': 'rgba(0,0,0,0.8)', 'display': 'flex', 'justifyContent': 'center', 
        'alignItems': 'center', 'zIndex': 1001 
    }
    content_style = {
        'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 'width': '95%', 
        'maxWidth': '600px', 'boxShadow': '0 10px 30px rgba(0,0,0,0.5)', 'maxHeight': '90vh', 'overflowY': 'auto',
        'position': 'relative', 'zIndex': 1002 
    }

    # Style pour les joueurs sortants
    joueurs_sur_terrain = []
    formation_cleaned = {int(k): v for k, v in formation.items()}
    pos_keys = sorted(formation_cleaned.keys())
    
    for pos in pos_keys:
        data = formation_cleaned[pos]
        # CORRECTION : Assurer la comparaison entre entiers
        is_selected_out = temp_state.get('sortant_pos') == pos 
        style_out = {
            'width': '48%', 'margin': '1%', 'padding': '10px', 'borderRadius': '5px',
            'border': f'2px solid {ADVERSE_COLOR}', 'fontWeight': 'normal'
        }
        if is_selected_out:
            style_out.update({'backgroundColor': ADVERSE_COLOR, 'color': 'white', 'fontWeight': 'bold', 'border': '3px solid black'})
        else:
            style_out.update({'backgroundColor': '#f8d7da', 'color': '#721c24'})
            
        joueurs_sur_terrain.append(
            html.Button(f"P{pos} - N°{data['numero']} ({data['nom']})", 
                        id={'type': 'sub-player-btn', 'role': 'sortant', 'index': str(pos)}, n_clicks=0, 
                        style=style_out)
        )

    # Style pour les joueurs entrants
    joueurs_sur_banc = []
    banc_cleaned = {int(k): v for k, v in banc.items()}
    num_keys = sorted(banc_cleaned.keys())
    
    for num in num_keys:
        data = banc_cleaned[num]
        is_selected_in = temp_state.get('entrant') and temp_state.get('entrant')['numero'] == num
        style_in = {
            'width': '48%', 'margin': '1%', 'padding': '10px', 'borderRadius': '5px',
            'border': f'2px solid {VEEC_COLOR}', 'fontWeight': 'normal'
        }
        if is_selected_in:
            style_in.update({'backgroundColor': VEEC_COLOR, 'color': 'white', 'fontWeight': 'bold', 'border': '3px solid black'})
        else:
            style_in.update({'backgroundColor': '#d4edda', 'color': '#155724'})
            
        joueurs_sur_banc.append(
            # NOUVEL ID : Utiliser 'sub-player-btn' avec role 'entrant' (comme le sortant)
            html.Button(f"N°{data['numero']} ({data['nom']})", 
                        id={'type': 'sub-player-btn', 'role': 'entrant', 'index': str(num)}, n_clicks=0, # <-- NOUVEL ID
                        style=style_in)
        )

    is_ready = temp_state.get('entrant') is not None and temp_state.get('sortant_pos') is not None
    
    # CORRECTION : Le style du curseur est maintenant dynamique
    style_confirm = {
        'padding': '10px 20px', 'backgroundColor': '#007bff', 'color': 'white', 
        'border': 'none', 'borderRadius': '5px', 'fontSize': '1.1em', 'cursor': 'pointer'
    }
    if not is_ready:
        style_confirm.update({'backgroundColor': '#aaa', 'cursor': 'not-allowed'})

    modal_content = html.Div(
        children=[
            html.H3(f"Substitution {team} ({count + 1}/{MAX_SUBS_PER_SET})", style={'textAlign': 'center', 'marginBottom': '20px', 'color': color}),
            
            # L'ID 'sub-feedback-msg' est REQUIS
            html.Div(id='sub-feedback-msg', children=feedback_msg, style={'color': 'blue', 'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '15px'}),
            
            html.P("1. Joueur Sortant (Terrain) :", style={'fontWeight': 'bold', 'marginTop': '10px'}),
            html.Div(joueurs_sur_terrain, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'marginBottom': '20px'}),
            
            html.P("2. Joueur Entrant (Banc) :", style={'fontWeight': 'bold'}),
            html.Div(joueurs_sur_banc, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'marginBottom': '30px'}),
            
            # ID dynamique pour l'annulation VEEC
            html.Button("✕ Annuler", id={'type': 'cancel-sub', 'index': team}, n_clicks=0, 
                        style={'marginRight': '20px', 'padding': '10px 20px', 'backgroundColor': '#6c757d', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'fontSize': '1.1em', 'cursor': 'pointer'}),
            
            html.Button("✅ Confirmation des changements", id='btn-confirm-sub', n_clicks=0, 
                        disabled=not is_ready,
                        style=style_confirm), # Style dynamique (curseur)
            
        ],
        style=content_style
    )
    
    return html.Div(children=modal_content, style=modal_style)

# 8. Gérer le déclenchement de la Modal de Substitution (Affichage simple)
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Output('service-modal-container', 'children', allow_duplicate=True), # ✅ MODIFIÉ    Input('btn-sub-veec', 'n_clicks'),
    Input('btn-sub-adverse', 'n_clicks'),
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_sub_init(n_veec, n_adverse, current_state):
    # Ce callback OUVRE la modale et initialise l'état temporaire
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    # 🚨 CLAUSE DE GARDE : Bloquer si le setup n'est pas terminé
    if not current_state.get('match_setup_completed', False):
        return dash.no_update, dash.no_update # Deux Outputs

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    new_state = copy.deepcopy(current_state)
    new_state = clean_formations(new_state)
    
    # Bloquer si un timer est en cours ou si une sub est déjà ouverte
    if new_state.get('timer_end_time', 0) > time.time() or new_state.get('sub_en_cours_team'):
        return dash.no_update, dash.no_update

    team = None
    if button_id == 'btn-sub-veec':
        if new_state['sub_veec'] >= MAX_SUBS_PER_SET:
            return dash.no_update, None # Optionnel: Gérer un message d'erreur ici
        team = 'VEEC'
    elif button_id == 'btn-sub-adverse':
        if new_state['sub_adverse'] >= MAX_SUBS_PER_SET:
            return dash.no_update, None
        team = 'ADVERSAIRE'

    if team:
        new_state['sub_en_cours_team'] = team
        # Initialiser l'état temporaire avec le feedback
        new_state['temp_sub_state'] = {'entrant': None, 'sortant_pos': None, 'feedback': "Sélectionnez le joueur sortant puis le joueur entrant."}
        
        # Le Callback 10 va maintenant voir ce changement et afficher la modale
        return new_state, dash.no_update

    return dash.no_update, dash.no_update


# 9. Gérer la SÉLECTION des joueurs (Logique)
# Met à jour l'état (match-state) basé sur les clics DANS la modale
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    [
        # OK: Écoute les sortants
        Input({'type': 'sub-player-btn', 'role': 'sortant', 'index': dash.dependencies.ALL}, 'n_clicks'),
        # CORRECTION : Écoute les entrants (Nouveaux IDs)
        Input({'type': 'sub-player-btn', 'role': 'entrant', 'index': dash.dependencies.ALL}, 'n_clicks') 
    ],
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_sub_selection(n_sortants, n_entrants, current_state):
    # 🚨 CLAUSE DE GARDE : Bloquer si le setup n'est pas terminé
    if not current_state.get('match_setup_completed', False):
        return dash.no_update
    
    new_state = copy.deepcopy(current_state)
    new_state = clean_formations(new_state)

    # N'agir que si une substitution VEEC est en cours
    if not new_state.get('sub_en_cours_team') or new_state.get('sub_en_cours_team') != 'VEEC':
        return dash.no_update

    ctx = dash.callback_context
    triggered_clicks = [c for c in ctx.triggered if c and c.get('value', 0) > 0]
    if not triggered_clicks:
        return dash.no_update
    
    triggered_id = triggered_clicks[0]['prop_id'].replace(".n_clicks", "")
    triggered_dict = json.loads(re.sub(r"'", '"', triggered_id)) 
    
    role = triggered_dict.get('role') # Utiliser .get pour éviter une erreur si 'role' n'existe pas
    team = new_state['sub_en_cours_team']
    temp_state = new_state.get('temp_sub_state', {})
    
    # 1. Mise à jour de l'état temporaire
    if role == 'sortant':
        pos_sortant = int(triggered_dict['index'])
        
        if temp_state.get('sortant_pos') == pos_sortant:
             temp_state.pop('sortant_pos', None)
        else:
            temp_state['sortant_pos'] = pos_sortant
    
    elif role == 'entrant':
        num_entrant = int(triggered_dict['index'])
        joueur_entrant = new_state['joueurs_banc'][num_entrant]
        
        if temp_state.get('entrant') and temp_state.get('entrant').get('numero') == num_entrant:
            temp_state.pop('entrant', None)
        else:
            temp_state['entrant'] = joueur_entrant

    # 2. Vérification de la validation et mise à jour du message de feedback
    is_ready = temp_state.get('entrant') is not None and temp_state.get('sortant_pos') is not None
    
    default_msg = "Sélectionnez le joueur sortant sur le terrain, puis le joueur entrant sur le banc."
    
    if is_ready:
        sortant_pos = temp_state['sortant_pos']
        formation = new_state['formation_actuelle']
        joueur_sortant_nom = formation.get(sortant_pos, {}).get('nom', 'N/A')
        joueur_entrant_nom = temp_state['entrant'].get('nom', 'N/A')
        temp_state['feedback'] = f"Prêt à confirmer : **{joueur_sortant_nom}** (P{sortant_pos}) sort, remplacé par **{joueur_entrant_nom}**."
    elif temp_state.get('sortant_pos') is not None:
        sortant_pos = temp_state['sortant_pos']
        formation = new_state['formation_actuelle']
        joueur_sortant_nom = formation.get(sortant_pos, {}).get('nom', 'N/A')
        temp_state['feedback'] = f"Joueur sortant sélectionné: **{joueur_sortant_nom}** (P{sortant_pos}). Sélectionnez maintenant l'entrant sur le banc."
    elif temp_state.get('entrant') is not None:
        joueur_entrant_nom = temp_state['entrant'].get('nom', 'N/A')
        temp_state['feedback'] = f"Joueur entrant sélectionné: **{joueur_entrant_nom}**. Sélectionnez maintenant le joueur sortant sur le terrain."
    else:
        temp_state['feedback'] = default_msg
        
    new_state['temp_sub_state'] = temp_state
    
    # Renvoyer l'état mis à jour
    return new_state


# 10. AFFICHAGE (Callback 10) et CONFIRMATION/ANNULATION (Callback 11)
# Nous devons séparer l'affichage de la confirmation pour éviter les erreurs "A nonexistent object..."

# 10. AFFICHAGE de la Modale (Basé sur l'état)
@app.callback(
    Output('service-modal-container', 'children', allow_duplicate=True),
    Input('match-state', 'data'), # Écoute tous les changements d'état
    prevent_initial_call=True
)
def display_sub_modal_on_state_change(current_state):
    
    sub_team = current_state.get('sub_en_cours_team')
    
    # Si aucune substitution n'est en cours, fermer la modal.
    if sub_team is None:
        return None

    temp_state = current_state.get('temp_sub_state', {})
    feedback_message = temp_state.get('feedback', "")
    
    if sub_team == 'VEEC':
        modal = create_veec_sub_modal(current_state, temp_state, feedback_message)
        return modal

    elif sub_team == 'ADVERSAIRE':
        modal = create_adverse_sub_modal(current_state, feedback_message)
        return modal
    
    elif sub_team == 'LIBERO_VEEC': # <-- AJOUTER CE CAS
        temp_state = current_state.get('temp_sub_state', {})
        return create_libero_sub_modal(current_state)
        
    return None # Fermer si pas de sub_team

# 11. CONFIRMATION et ANNULATION (Actions de fermeture)
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Output('historique-output', 'children', allow_duplicate=True),
    Output('feedback-sub-output', 'children'),
    [
        Input('btn-confirm-sub', 'n_clicks'),
        Input({'type': 'cancel-sub', 'index': dash.dependencies.ALL}, 'n_clicks'),
        Input({'type': 'confirm-sub-adverse', 'index': dash.dependencies.ALL}, 'n_clicks'), 
    ],
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_sub_confirm_cancel(confirm_clicks, cancel_clicks, confirm_adverse_clicks, current_state):
    
    ctx = dash.callback_context
    triggered_inputs = [c for c in ctx.triggered if c and c.get('value', 0) > 0]
    if not triggered_inputs:
        return dash.no_update, dash.no_update, dash.no_update

    triggered_prop_id = triggered_inputs[0]['prop_id']
    new_state = copy.deepcopy(current_state)
    new_state = clean_formations(new_state)

    # Déterminer quel bouton a été cliqué
    try:
        # Tenter de charger l'ID dynamique (si ce n'est pas 'btn-confirm-sub')
        triggered_id_str = triggered_prop_id.replace(".n_clicks", "")
        if triggered_id_str != 'btn-confirm-sub':
            triggered_dict = json.loads(re.sub(r"'", '"', triggered_id_str))
            triggered_type = triggered_dict.get('type')
        else:
            triggered_type = 'btn-confirm-sub'
    except Exception:
        # Si la chaîne n'est pas JSON (ex: 'btn-confirm-sub'), on traite comme tel
        triggered_type = triggered_prop_id.split('.')[0] 

    # --- 1. Logique d'annulation (VEEC ou ADVERSE) ---
    if triggered_type == 'cancel-sub':
        print("DEBUG : Annulation (Clic). Fermeture de la modale.")
        new_state['sub_en_cours_team'] = None
        new_state['temp_sub_state'] = {}
        return new_state, dash.no_update, ""

    # --- 2. Logique de confirmation de SUB ADVERSE ---
    if triggered_type == 'confirm-sub-adverse':
        print("DEBUG : Confirmation de la substitution ADVERSE. Fermeture de la modale.")
        new_state['sub_adverse'] += 1
        new_state['sub_en_cours_team'] = None
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp, 'set': new_state['current_set'], 'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
            'position': 'Adv Bench', 'joueur_nom': f"Adversaire Sub",
            'action_code': 'SUB', 'resultat': 'ADVERSE_CONFIRMED'
        }
        new_state['historique_stats'].insert(0, log_entry)
        
        historique_table = create_historique_table(new_state['historique_stats'])
        return new_state, historique_table, ""

    # --- 3. Logique de confirmation de SUB VEEC ---
    if triggered_type == 'btn-confirm-sub' and current_state.get('sub_en_cours_team') == 'VEEC':
        # ... (Logique de confirmation VEEC inchangée) ...
        team = new_state['sub_en_cours_team']
        temp_state = new_state.get('temp_sub_state', {})
        
        sortant_pos = temp_state.get('sortant_pos')
        joueur_entrant_data = temp_state.get('entrant')

        if not team or not sortant_pos or not joueur_entrant_data:
            print("DEBUG: ERREUR - Données de substitution manquantes à la confirmation.")
            return dash.no_update, dash.no_update, "ERREUR : Le Libero ne peut pas être impliqué dans une substitution régulière." # ✅ Correction
        
        joueur_entrant = joueur_entrant_data
        
        print(f"DEBUG: Confirmation SUB {team}. Sortant Pos: {sortant_pos}, Entrant Num: {joueur_entrant.get('numero')}")

        if team == 'VEEC':
            # Récupérer les numéros des joueurs impliqués dans cette SUB régulière
            veec_sortant_num = new_state['formation_actuelle'][sortant_pos]['numero']
            veec_entrant_num = joueur_entrant_data['numero']
            
            # ----------------------------------------------------
            # NOUVELLE VALIDATION LIBERO (Bloc Inséré ici)
            # ----------------------------------------------------
            libero_status = new_state['liberos_veec']
            starter_bloque = libero_status.get('starter_numero_replaced')
            libero_est_sur_terrain = libero_status.get('is_on_court')
            libero_actif_num = libero_status.get('actif_numero')

            # Règle 1 : Interdire la substitution du Libero
            if veec_sortant_num == libero_actif_num or veec_entrant_num == libero_actif_num:
                 # Le message d'erreur est affiché via le 'print' (à logguer dans votre interface si possible)
                 print(f"ERREUR SUB : Le Libero (L{libero_actif_num}) ne peut pas être impliqué dans une substitution régulière.")
                 # Annuler la substitution en fermant la modale sans appliquer de changements d'état/historique.
                 new_state['sub_en_cours_team'] = None
                 new_state['temp_sub_state'] = {}
                 # On renvoie l'état actuel et on ne met pas à jour l'historique
                 return new_state, dash.no_update, f"ERREUR : Le joueur N°{starter_bloque} est bloqué et doit revenir via l'échange Libero." # ✅ Correction

            # Règle 2 : Interdire l'entrée du joueur titulaire bloqué tant que le Libero est sur le terrain
            if libero_est_sur_terrain and starter_bloque is not None:
                if veec_entrant_num == starter_bloque:
                    print(f"ERREUR SUB : Le joueur N°{starter_bloque} doit revenir via l'échange Libero-OUT.")
                    # Annuler la substitution
                    new_state['sub_en_cours_team'] = None
                    new_state['temp_sub_state'] = {}
                    return new_state, dash.no_update
            
            # ----------------------------------------------------
            # FIN VALIDATION LIBERO
            # ----------------------------------------------------
            
            joueur_sortant = new_state['formation_actuelle'][sortant_pos]
            new_state['joueurs_banc'][joueur_sortant['numero']] = joueur_sortant 
            new_state['formation_actuelle'][sortant_pos] = joueur_entrant 
            del new_state['joueurs_banc'][joueur_entrant['numero']]
            new_state['sub_veec'] += 1
            print(f"DEBUG: VEEC - {joueur_sortant['nom']} sort de P{sortant_pos}. {joueur_entrant['nom']} entre.")
    
        # Enregistrement et réinitialisation
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp, 'set': new_state['current_set'], 'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
            'position': sortant_pos, 'joueur_nom': f"{joueur_sortant['nom']} (SORT)",
            'action_code': 'SUB', 'resultat': f"ENTRE: {joueur_entrant['nom']}"
        }
        new_state['historique_stats'].insert(0, log_entry)

        new_state['sub_en_cours_team'] = None
        new_state['temp_sub_state'] = {}
        print("DEBUG: Substitution appliquée et état réinitialisé. Fermeture de la modale.")

        historique_table = create_historique_table(new_state['historique_stats'])
        
        return new_state, historique_table, ""

    return new_state, dash.no_update, "Votre message d'erreur"

# 12. Gérer le déclenchement de la Modal du Libero
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Output('stat-modal-container', 'children', allow_duplicate=True), 
    Input('btn-sub-libero-veec', 'n_clicks'),
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_libero_init(n_clicks, current_state):
    # Blocage si un autre timer/sub est en cours
    if not n_clicks or current_state.get('timer_end_time', 0) > time.time() or current_state.get('sub_en_cours_team'):
        return dash.no_update, dash.no_update
        
    new_state = copy.deepcopy(current_state)
    
    # Déclencher l'affichage du type de modal Libero
    new_state['sub_en_cours_team'] = 'LIBERO_VEEC' 
    
    modal = create_libero_sub_modal(new_state)
    
    return new_state, modal


# 13. Gérer la confirmation de la substitution Libero
@app.callback(
    Output('match-state', 'data', allow_duplicate=True),
    Output('historique-output', 'children', allow_duplicate=True),
    Output('stat-modal-container', 'children', allow_duplicate=True), # Fermer la modal
    [
        Input('btn-confirm-libero-out', 'n_clicks'),
        Input('btn-cancel-libero-sub', 'n_clicks'),
        Input({'type': 'confirm-libero-in', 'pos': dash.dependencies.ALL}, 'n_clicks'),
    ],
    State('match-state', 'data'),
    prevent_initial_call=True
)
def handle_libero_swap(out_clicks, cancel_clicks, in_clicks, current_state):
    ctx = dash.callback_context
    triggered_inputs = [c for c in ctx.triggered if c and c.get('value', 0) > 0]
    if not triggered_inputs:
        return dash.no_update, dash.no_update, dash.no_update
    
    triggered_prop_id = triggered_inputs[0]['prop_id']
    new_state = copy.deepcopy(current_state)
    libero_status = new_state['liberos_veec']
    historique_output = dash.no_update

    # --- 1. Annulation ---
    if triggered_prop_id == 'btn-cancel-libero-sub.n_clicks':
        new_state['sub_en_cours_team'] = None
        return new_state, dash.no_update, None

    # --- 2. Sortie du Libero (Libero -> Titulaire) ---
    if triggered_prop_id == 'btn-confirm-libero-out.n_clicks':
        if not libero_status['is_on_court'] or libero_status.get('starter_numero_replaced') is None: # Vérification renforcée
            print("ERREUR: Tente de sortir le Libero alors qu'il n'est pas censé être là ou pas de titulaire enregistré.")
            return new_state, dash.no_update, dash.no_update
            
        starter_num = libero_status['starter_numero_replaced']
        current_pos = libero_status['current_pos_on_court']
        
        # CORRECTION : Utiliser le Libero ACTIF
        libero_num_actif = libero_status['actif_numero']

        # 1. Échange Libero (P4) -> Titulaire (P1)
        new_state['joueurs_banc'][libero_num_actif] = new_state['formation_actuelle'][current_pos] # Libero sur le banc
        new_state['formation_actuelle'][current_pos] = new_state['joueurs_banc'][starter_num] # Titulaire sur le terrain
        del new_state['joueurs_banc'][starter_num] # Titulaire retiré du banc

        # 2. Mise à jour du statut Libero
        libero_status['is_on_court'] = False
        libero_status['current_pos_on_court'] = None
        new_state['sub_en_cours_team'] = None
        
        # 3. Historique
        log_entry = {'timestamp': datetime.now().strftime("%H:%M:%S"), 'set': new_state['current_set'], 'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
                     'position': current_pos, 'joueur_nom': f"L{libero_num_actif} (SORT)", 'action_code': 'LIBERO_OUT', 'resultat': f"ENTRE: N°{starter_num}"}
        new_state['historique_stats'].insert(0, log_entry)
        historique_output = create_historique_table(new_state['historique_stats'])
        
        return new_state, historique_output, None

    # --- 3. Entrée du Libero (Titulaire -> Libero) ---
    if triggered_prop_id.startswith('{"type":"confirm-libero-in"'):
        if libero_status['is_on_court']:
            print("ERREUR: Tente d'entrer le Libero alors qu'il est déjà sur le terrain.")
            return new_state, dash.no_update, dash.no_update
            
        triggered_dict = json.loads(re.sub(r"'", '"', triggered_prop_id.replace(".n_clicks", "")))
        pos_sortant = int(triggered_dict['pos'])
        libero_num_actif = libero_status['actif_numero']

        # Vérification finale (Libero doit être sur le banc)
        if libero_num_actif not in new_state['joueurs_banc']:
            print("ERREUR: Libero non trouvé sur le banc.")
            return new_state, dash.no_update, dash.no_update
            
        joueur_sortant = new_state['formation_actuelle'][pos_sortant]
        
        # 1. Échange Titulaire (P1) -> Libero (P4)
        new_state['joueurs_banc'][joueur_sortant['numero']] = joueur_sortant # Titulaire sur le banc
        new_state['formation_actuelle'][pos_sortant] = new_state['joueurs_banc'][libero_num_actif] # Libero sur le terrain
        del new_state['joueurs_banc'][libero_num_actif] # Libero retiré du banc

        # 2. Mise à jour du statut Libero
        libero_status['is_on_court'] = True
        libero_status['starter_numero_replaced'] = joueur_sortant['numero']
        libero_status['current_pos_on_court'] = pos_sortant
        new_state['sub_en_cours_team'] = None
        
        # 3. Historique
        log_entry = {'timestamp': datetime.now().strftime("%H:%M:%S"), 'set': new_state['current_set'], 'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
                     'position': pos_sortant, 'joueur_nom': f"N°{joueur_sortant['numero']} (SORT)", 'action_code': 'LIBERO_IN', 'resultat': f"ENTRE: L{libero_num_actif}"}
        new_state['historique_stats'].insert(0, log_entry)
        historique_output = create_historique_table(new_state['historique_stats'])
        
        return new_state, historique_output, None

    return dash.no_update, dash.no_update, dash.no_update

# --- DÉMARRAGE DE L'APPLICATION ---
if __name__ == '__main__':
    app.run(debug=True, port=8051)
