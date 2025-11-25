"""
Tous les callbacks de l'application VEEC Scorer
Organisés par catégorie fonctionnelle
"""
import dash
from dash import Input, Output, State, ALL, html
from datetime import datetime
import json
import re
import copy
import time

from src.utils.helpers import clean_formations
from src.utils.rotation import appliquer_rotation_veec, appliquer_rotation_adverse
from src.utils.libero import swap_liberos_on_bench
from src.components.court import create_court_figure
from src.components.tables import create_historique_table
from src.components.modals import (
    create_libero_sub_modal,
    create_simple_adverse_sub_modal,
    create_veec_sub_modal,
    create_pre_match_setup_modal
)
from config.settings import (
    VEEC_COLOR, ADVERSE_COLOR,
    MAX_TIMEOUTS_PER_SET, MAX_SUBS_PER_SET,
    TIMEOUT_DURATION_SECONDS, SHORT_BREAK_DURATION_SECONDS, LONG_BREAK_DURATION_SECONDS
)


def register_callbacks(app):
    """
    Enregistre tous les callbacks de l'application

    Args:
        app: Instance de l'application Dash
    """

    # =================================================================
    # CALLBACKS LIBERO
    # =================================================================

    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('feedback-output-libero', 'children'),
        Input('btn-swap-libero-reserve', 'n_clicks'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_libero_swap_ui(n_clicks, current_state):
        """Gère l'activation du Libero de réserve (N°9)"""
        if n_clicks is None or n_clicks == 0:
            raise dash.exceptions.PreventUpdate

        new_state, feedback_message = swap_liberos_on_bench(current_state)
        return new_state, feedback_message


    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('stat-modal-container', 'children', allow_duplicate=True),
        Input('btn-sub-libero-veec', 'n_clicks'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_libero_init(n_clicks, current_state):
        """Ouvre la modal de substitution Libero"""
        if not n_clicks or current_state.get('timer_end_time', 0) > time.time() or current_state.get('sub_en_cours_team'):
            return dash.no_update, dash.no_update

        new_state = copy.deepcopy(current_state)
        new_state['sub_en_cours_team'] = 'LIBERO_VEEC'
        modal = create_libero_sub_modal(new_state)

        return new_state, modal


    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('historique-output', 'children', allow_duplicate=True),
        Output('stat-modal-container', 'children', allow_duplicate=True),
        [
            Input('btn-confirm-libero-out', 'n_clicks'),
            Input('btn-cancel-libero-sub', 'n_clicks'),
            Input({'type': 'confirm-libero-in', 'pos': ALL}, 'n_clicks'),
        ],
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_libero_swap(out_clicks, cancel_clicks, in_clicks, current_state):
        """Gère la confirmation de substitution Libero"""
        ctx = dash.callback_context
        triggered_inputs = [c for c in ctx.triggered if c and c.get('value', 0) > 0]
        if not triggered_inputs:
            return dash.no_update, dash.no_update, dash.no_update

        triggered_prop_id = triggered_inputs[0]['prop_id']
        new_state = copy.deepcopy(current_state)
        libero_status = new_state['liberos_veec']
        historique_output = dash.no_update

        # Annulation
        if triggered_prop_id == 'btn-cancel-libero-sub.n_clicks':
            new_state['sub_en_cours_team'] = None
            return new_state, dash.no_update, None

        # Sortie du Libero
        if triggered_prop_id == 'btn-confirm-libero-out.n_clicks':
            if not libero_status['is_on_court'] or libero_status.get('starter_numero_replaced') is None:
                return new_state, dash.no_update, dash.no_update

            starter_num = libero_status['starter_numero_replaced']
            current_pos = libero_status['current_pos_on_court']
            libero_num_actif = libero_status['actif_numero']

            # Échange
            new_state['joueurs_banc'][libero_num_actif] = new_state['formation_actuelle'][current_pos]
            new_state['formation_actuelle'][current_pos] = new_state['joueurs_banc'][starter_num]
            del new_state['joueurs_banc'][starter_num]

            libero_status['is_on_court'] = False
            libero_status['current_pos_on_court'] = None
            new_state['sub_en_cours_team'] = None

            # Historique
            log_entry = {
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'set': new_state['current_set'],
                'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
                'position': current_pos,
                'joueur_nom': f"L{libero_num_actif} (SORT)",
                'action_code': 'LIBERO_OUT',
                'resultat': f"ENTRE: N°{starter_num}"
            }
            new_state['historique_stats'].insert(0, log_entry)
            historique_output = create_historique_table(new_state['historique_stats'])

            return new_state, historique_output, None

        # Entrée du Libero
        if triggered_prop_id.startswith('{"type":"confirm-libero-in"'):
            if libero_status['is_on_court']:
                return new_state, dash.no_update, dash.no_update

            triggered_dict = json.loads(re.sub(r"'", '"', triggered_prop_id.replace(".n_clicks", "")))
            pos_sortant = int(triggered_dict['pos'])
            libero_num_actif = libero_status['actif_numero']

            if libero_num_actif not in new_state['joueurs_banc']:
                return new_state, dash.no_update, dash.no_update

            joueur_sortant = new_state['formation_actuelle'][pos_sortant]

            # Échange
            new_state['joueurs_banc'][joueur_sortant['numero']] = joueur_sortant
            new_state['formation_actuelle'][pos_sortant] = new_state['joueurs_banc'][libero_num_actif]
            del new_state['joueurs_banc'][libero_num_actif]

            libero_status['is_on_court'] = True
            libero_status['starter_numero_replaced'] = joueur_sortant['numero']
            libero_status['current_pos_on_court'] = pos_sortant
            new_state['sub_en_cours_team'] = None

            # Historique
            log_entry = {
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'set': new_state['current_set'],
                'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
                'position': pos_sortant,
                'joueur_nom': f"N°{joueur_sortant['numero']} (SORT)",
                'action_code': 'LIBERO_IN',
                'resultat': f"ENTRE: L{libero_num_actif}"
            }
            new_state['historique_stats'].insert(0, log_entry)
            historique_output = create_historique_table(new_state['historique_stats'])

            return new_state, historique_output, None

        return dash.no_update, dash.no_update, dash.no_update


    # =================================================================
    # CALLBACKS SCORE ET ROTATION
    # =================================================================

    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('joueur-selectionne', 'data', allow_duplicate=True),
        Input('btn-point-veec', 'n_clicks'),
        Input('btn-point-adverse', 'n_clicks'),
        State('match-state', 'data'),
        prevent_initial_call=True,
    )
    def update_score_and_rotation(n_veec, n_adverse, current_state):
        """Gère les points et les rotations"""
        new_state = copy.deepcopy(current_state)

        if not current_state.get('match_setup_completed'):
            return dash.no_update, None

        new_state = clean_formations(new_state)

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
                    new_state['service_actuel'] = 'VEEC'
                    new_state['formation_actuelle'] = appliquer_rotation_veec(new_state['formation_actuelle'])
                    new_state['rotation_count'] += 1

                    # Logique de sortie forcée du Libero en P4
                    liberos_status = new_state['liberos_veec']
                    if liberos_status['is_on_court']:
                        player_in_p4 = new_state['formation_actuelle'][4]
                        libero_actif_num = liberos_status['actif_numero']
                        libero_reserve_num = liberos_status['reserve_numero']

                        is_libero_in_p4 = player_in_p4['numero'] == libero_actif_num or player_in_p4['numero'] == libero_reserve_num

                        if is_libero_in_p4:
                            pos_sortie = 4
                            starter_num = liberos_status['starter_numero_replaced']
                            joueur_libero = player_in_p4
                            joueur_titulaire = new_state['joueurs_banc'].get(starter_num)

                            if joueur_titulaire:
                                new_state['joueurs_banc'][joueur_libero['numero']] = joueur_libero
                                new_state['formation_actuelle'][pos_sortie] = joueur_titulaire
                                del new_state['joueurs_banc'][starter_num]

                                liberos_status['is_on_court'] = False
                                liberos_status['starter_numero_replaced'] = None
                                liberos_status['current_pos_on_court'] = None

                                log_entry = {
                                    'timestamp': time.time(),
                                    'action_code': 'LIBERO_AUTO_OUT',
                                    'details': f"L{joueur_libero['numero']} OUT, N°{starter_num} IN P{pos_sortie}"
                                }
                                new_state['historique_stats'].insert(0, log_entry)

                        # Mise à jour position Libero
                        if liberos_status['is_on_court']:
                            if new_state['formation_actuelle'][6]['numero'] == libero_actif_num or new_state['formation_actuelle'][6]['numero'] == libero_reserve_num:
                                liberos_status['current_pos_on_court'] = 6
                            elif new_state['formation_actuelle'][5]['numero'] == libero_actif_num or new_state['formation_actuelle'][5]['numero'] == libero_reserve_num:
                                liberos_status['current_pos_on_court'] = 5

                    new_state['liberos_veec'] = liberos_status

            elif gagnant == 'ADVERSAIRE':
                new_state['score_adverse'] += 1
                if service_avant == 'VEEC':
                    new_state['service_actuel'] = 'ADVERSAIRE'
                    new_state['formation_adverse_actuelle'] = appliquer_rotation_adverse(new_state['formation_adverse_actuelle'])
                    new_state['rotation_count'] += 1

        # Vérification fin de set/match
        set_ended = False
        match_winner = None
        seuil_points = 15 if new_state['current_set'] == 5 else 25
        score_veec = new_state['score_veec']
        score_adverse = new_state['score_adverse']

        if score_veec >= seuil_points and (score_veec - score_adverse) >= 2:
            match_winner = 'VEEC'
            set_ended = True
        elif score_adverse >= seuil_points and (score_adverse - score_veec) >= 2:
            match_winner = 'ADVERSAIRE'
            set_ended = True

        if set_ended:
            if match_winner == 'VEEC':
                new_state['sets_veec'] += 1
            else:
                new_state['sets_adverse'] += 1

            if new_state['sets_veec'] == 3 or new_state['sets_adverse'] == 3:
                new_state['match_ended'] = True
                new_state['match_winner'] = match_winner
            else:
                new_state['score_veec'], new_state['score_adverse'] = 0, 0
                new_state['current_set'] += 1
                new_state['timeouts_veec'], new_state['timeouts_adverse'] = 0, 0
                new_state['sub_veec'], new_state['sub_adverse'] = 0, 0

                duration = LONG_BREAK_DURATION_SECONDS if new_state['current_set'] == 5 else SHORT_BREAK_DURATION_SECONDS
                new_state['timer_end_time'] = time.time() + duration
                new_state['timer_type'] = 'SET_BREAK'

        return new_state, None


    # =================================================================
    # CALLBACKS UI
    # =================================================================

    @app.callback(
        Output('joueur-selectionne', 'data', allow_duplicate=True),
        Input('terrain-graph-statique', 'clickData'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_player_click_dash(clickData, current_state):
        """Gère les clics sur les joueurs du terrain"""
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
        """Mise à jour complète de l'interface"""
        current_state = clean_formations(current_state)

        fig, config = create_court_figure(
            current_state['formation_actuelle'],
            current_state['formation_adverse_actuelle'],
            current_state['service_actuel'],
            current_state['liberos_veec']
        )

        return (
            fig, config,
            str(current_state['score_veec']),
            str(current_state['score_adverse']),
            str(current_state['sets_veec']),
            str(current_state['sets_adverse']),
            str(current_state['current_set']),
            str(current_state['sub_veec']),
            str(current_state['timeouts_veec']),
            str(current_state['sub_adverse']),
            str(current_state['timeouts_adverse'])
        )


    # =================================================================
    # CALLBACKS TIMER
    # =================================================================

    @app.callback(
        Output('timer-progress-bar', 'children'),
        Input('interval-component', 'n_intervals'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def update_timer_display_only(n, current_state):
        """Affichage du timer"""
        timer_end_time = current_state.get('timer_end_time', 0)
        timer_type = current_state.get('timer_type')

        if timer_end_time == 0:
            elapsed_seconds = int(time.time() - current_state.get('start_time', time.time()))
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            time_str = f"Temps de jeu : {minutes:02d}:{seconds:02d}"
            return html.Div(time_str, style={'textAlign': 'right', 'fontSize': '1.1em', 'fontWeight': 'bold', 'color': '#333'})

        remaining_seconds = int(timer_end_time - time.time())

        if remaining_seconds <= 0:
            return html.Div("REPRISE DU JEU !", style={'textAlign': 'center', 'color': 'red', 'fontWeight': 'bold', 'fontSize': '1.1em'})

        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        if timer_type == 'TIMEOUT':
            title = "TEMPS MORT"
            color = '#ffc107'
            duration = TIMEOUT_DURATION_SECONDS
        elif timer_type == 'SET_BREAK':
            title = "PAUSE SET"
            color = '#333'
            duration = LONG_BREAK_DURATION_SECONDS if current_state['current_set'] == 5 else SHORT_BREAK_DURATION_SECONDS
        else:
            duration = 1
            title = ""
            color = '#333'

        time_str = f"{title}: {minutes:02d}:{seconds:02d}"
        elapsed_for_bar = duration - remaining_seconds
        progress_percent = max(0, min(100, (elapsed_for_bar / duration) * 100))

        progress_bar = html.Div([
            html.Div(style={'height': '10px', 'backgroundColor': '#ddd', 'borderRadius': '5px', 'width': '100%'}),
            html.Div(style={'height': '10px', 'backgroundColor': color, 'borderRadius': '5px', 'width': f'{progress_percent}%', 'marginTop': '-10px', 'transition': 'width 1s linear'})
        ], style={'width': '100%'})

        return html.Div([
            html.Div(time_str, style={'textAlign': 'center', 'fontWeight': 'bold', 'color': color, 'marginBottom': '5px'}),
            progress_bar
        ], style={'width': '100%', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})


    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Input('interval-component', 'n_intervals'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_timer_expiration(n, current_state):
        """Gestion de l'expiration du timer"""
        if not current_state.get('match_setup_completed', False):
            return dash.no_update

        timer_end_time = current_state.get('timer_end_time', 0)

        if timer_end_time > 0 and time.time() >= timer_end_time:
            new_state = copy.deepcopy(current_state)
            new_state['timer_end_time'] = 0
            new_state['timer_type'] = None
            return new_state

        return dash.no_update


    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('stat-modal-container', 'children', allow_duplicate=True),
        Input('btn-to-veec', 'n_clicks'),
        Input('btn-to-adverse', 'n_clicks'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_timeouts(n_veec, n_adverse, current_state):
        """Gère les temps morts"""
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update

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

        return new_state, None


    # =================================================================
    # CALLBACKS STATISTIQUES
    # =================================================================

    @app.callback(
        Output('stat-modal-container', 'children', allow_duplicate=True),
        Input('joueur-selectionne', 'data'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def display_stat_modal(joueur_selectionne, current_state):
        """Affiche la modal de statistiques"""
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


    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('joueur-selectionne', 'data', allow_duplicate=True),
        Output('historique-output', 'children', allow_duplicate=True),
        Input({'type': 'stat-btn', 'index': ALL}, 'n_clicks'),
        Input('btn-close-modal-static', 'n_clicks'),
        State('match-state', 'data'),
        State('joueur-selectionne', 'data'),
        prevent_initial_call=True
    )
    def handle_stat_log_and_close(n_clicks, close_clicks, current_state, joueur_sel):
        """Gère l'enregistrement des statistiques"""
        ctx = dash.callback_context
        if not ctx.triggered or not ctx.triggered[0]['value']:
            return dash.no_update, dash.no_update, dash.no_update

        if not current_state.get('match_setup_completed', False):
            return dash.no_update, dash.no_update, dash.no_update

        triggered_id = ctx.triggered[0]['prop_id']
        new_state = copy.deepcopy(current_state)

        reset_selection = False

        if triggered_id == 'btn-close-modal-static.n_clicks':
            reset_selection = True

        elif 'stat-btn' in triggered_id:
            if not joueur_sel:
                reset_selection = True
            else:
                try:
                    id_str = triggered_id.replace(".n_clicks", "")
                    id_str_clean = re.sub(r"'", '"', id_str)
                    triggered_dict = json.loads(id_str_clean)
                    stat_index = triggered_dict.get('index', '')

                    stat_info = stat_index.split('_')

                    if len(stat_info) == 3:
                        pos, action_code, resultat = int(stat_info[0]), stat_info[1], stat_info[2]

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

                            if resultat in ['KILL', 'ACE', 'GAIN']:
                                new_state['score_veec'] += 1

                except (KeyError, json.JSONDecodeError, ValueError, IndexError) as e:
                    print(f"Erreur lors de l'enregistrement de la stat: {e}")

                reset_selection = True

        historique_table = create_historique_table(new_state['historique_stats'])

        if reset_selection:
            return new_state, None, historique_table

        return dash.no_update, dash.no_update, dash.no_update


    # =================================================================
    # CALLBACKS SUBSTITUTION
    # =================================================================

    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('service-modal-container', 'children', allow_duplicate=True),
        Input('btn-sub-veec', 'n_clicks'),
        Input('btn-sub-adverse', 'n_clicks'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_sub_init(n_veec, n_adverse, current_state):
        """Ouvre la modale de substitution"""
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update

        if not current_state.get('match_setup_completed', False):
            return dash.no_update, dash.no_update

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        new_state = copy.deepcopy(current_state)
        new_state = clean_formations(new_state)

        if new_state.get('timer_end_time', 0) > time.time() or new_state.get('sub_en_cours_team'):
            return dash.no_update, dash.no_update

        team = None
        if button_id == 'btn-sub-veec':
            if new_state['sub_veec'] >= MAX_SUBS_PER_SET:
                return dash.no_update, None
            team = 'VEEC'
        elif button_id == 'btn-sub-adverse':
            if new_state['sub_adverse'] >= MAX_SUBS_PER_SET:
                return dash.no_update, None
            team = 'ADVERSAIRE'

        if team:
            new_state['sub_en_cours_team'] = team
            new_state['temp_sub_state'] = {
                'entrant': None,
                'sortant_pos': None,
                'feedback': "Sélectionnez le joueur sortant puis le joueur entrant."
            }
            return new_state, dash.no_update

        return dash.no_update, dash.no_update


    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        [
            Input({'type': 'sub-player-btn', 'role': 'sortant', 'index': ALL}, 'n_clicks'),
            Input({'type': 'sub-player-btn', 'role': 'entrant', 'index': ALL}, 'n_clicks')
        ],
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_sub_selection(n_sortants, n_entrants, current_state):
        """Gère la sélection des joueurs pour substitution VEEC"""
        if not current_state.get('match_setup_completed', False):
            return dash.no_update

        new_state = copy.deepcopy(current_state)
        new_state = clean_formations(new_state)

        if not new_state.get('sub_en_cours_team') or new_state.get('sub_en_cours_team') != 'VEEC':
            return dash.no_update

        ctx = dash.callback_context
        triggered_clicks = [c for c in ctx.triggered if c and c.get('value', 0) > 0]
        if not triggered_clicks:
            return dash.no_update

        triggered_id = triggered_clicks[0]['prop_id'].replace(".n_clicks", "")
        triggered_dict = json.loads(re.sub(r"'", '"', triggered_id))

        role = triggered_dict.get('role')
        temp_state = new_state.get('temp_sub_state', {})

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

        # Mise à jour du feedback
        is_ready = temp_state.get('entrant') is not None and temp_state.get('sortant_pos') is not None

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
            temp_state['feedback'] = "Sélectionnez le joueur sortant sur le terrain, puis le joueur entrant sur le banc."

        new_state['temp_sub_state'] = temp_state
        return new_state


    @app.callback(
        Output('service-modal-container', 'children', allow_duplicate=True),
        Input('match-state', 'data'),
        prevent_initial_call=True
    )
    def display_sub_modal_on_state_change(current_state):
        """Affiche la modal de substitution selon l'état"""
        sub_team = current_state.get('sub_en_cours_team')

        if sub_team is None:
            return None

        temp_state = current_state.get('temp_sub_state', {})
        feedback_message = temp_state.get('feedback', "")

        if sub_team == 'VEEC':
            return create_veec_sub_modal(current_state, temp_state, feedback_message)
        elif sub_team == 'ADVERSAIRE':
            return create_simple_adverse_sub_modal(current_state, feedback_message)
        elif sub_team == 'LIBERO_VEEC':
            return create_libero_sub_modal(current_state)

        return None


    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('historique-output', 'children', allow_duplicate=True),
        Output('feedback-sub-output', 'children'),
        [
            Input('btn-confirm-sub', 'n_clicks'),
            Input({'type': 'cancel-sub', 'index': ALL}, 'n_clicks'),
            Input({'type': 'confirm-sub-adverse', 'index': ALL}, 'n_clicks'),
        ],
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def handle_sub_confirm_cancel(confirm_clicks, cancel_clicks, confirm_adverse_clicks, current_state):
        """Gère la confirmation et l'annulation des substitutions"""
        ctx = dash.callback_context
        triggered_inputs = [c for c in ctx.triggered if c and c.get('value', 0) > 0]
        if not triggered_inputs:
            return dash.no_update, dash.no_update, dash.no_update

        triggered_prop_id = triggered_inputs[0]['prop_id']
        new_state = copy.deepcopy(current_state)
        new_state = clean_formations(new_state)

        # Déterminer quel bouton a été cliqué
        try:
            triggered_id_str = triggered_prop_id.replace(".n_clicks", "")
            if triggered_id_str != 'btn-confirm-sub':
                triggered_dict = json.loads(re.sub(r"'", '"', triggered_id_str))
                triggered_type = triggered_dict.get('type')
            else:
                triggered_type = 'btn-confirm-sub'
        except Exception:
            triggered_type = triggered_prop_id.split('.')[0]

        # Annulation
        if triggered_type == 'cancel-sub':
            new_state['sub_en_cours_team'] = None
            new_state['temp_sub_state'] = {}
            return new_state, dash.no_update, ""

        # Confirmation substitution adverse
        if triggered_type == 'confirm-sub-adverse':
            new_state['sub_adverse'] += 1
            new_state['sub_en_cours_team'] = None

            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = {
                'timestamp': timestamp,
                'set': new_state['current_set'],
                'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
                'position': 'Adv Bench',
                'joueur_nom': 'Adversaire Sub',
                'action_code': 'SUB',
                'resultat': 'ADVERSE_CONFIRMED'
            }
            new_state['historique_stats'].insert(0, log_entry)
            historique_table = create_historique_table(new_state['historique_stats'])
            return new_state, historique_table, ""

        # Confirmation substitution VEEC
        if triggered_type == 'btn-confirm-sub' and current_state.get('sub_en_cours_team') == 'VEEC':
            temp_state = new_state.get('temp_sub_state', {})

            sortant_pos = temp_state.get('sortant_pos')
            joueur_entrant_data = temp_state.get('entrant')

            if not sortant_pos or not joueur_entrant_data:
                return dash.no_update, dash.no_update, "ERREUR : Données de substitution manquantes."

            # Validation Libero
            libero_status = new_state['liberos_veec']
            starter_bloque = libero_status.get('starter_numero_replaced')
            libero_est_sur_terrain = libero_status.get('is_on_court')
            libero_actif_num = libero_status.get('actif_numero')

            veec_sortant_num = new_state['formation_actuelle'][sortant_pos]['numero']
            veec_entrant_num = joueur_entrant_data['numero']

            # Règle 1 : Interdire la substitution du Libero
            if veec_sortant_num == libero_actif_num or veec_entrant_num == libero_actif_num:
                new_state['sub_en_cours_team'] = None
                new_state['temp_sub_state'] = {}
                return new_state, dash.no_update, "ERREUR : Le Libero ne peut pas être impliqué dans une substitution régulière."

            # Règle 2 : Interdire l'entrée du joueur titulaire bloqué
            if libero_est_sur_terrain and starter_bloque is not None:
                if veec_entrant_num == starter_bloque:
                    new_state['sub_en_cours_team'] = None
                    new_state['temp_sub_state'] = {}
                    return new_state, dash.no_update, f"ERREUR : Le joueur N°{starter_bloque} est bloqué et doit revenir via l'échange Libero."

            # Effectuer la substitution
            joueur_sortant = new_state['formation_actuelle'][sortant_pos]
            new_state['joueurs_banc'][joueur_sortant['numero']] = joueur_sortant
            new_state['formation_actuelle'][sortant_pos] = joueur_entrant_data
            del new_state['joueurs_banc'][joueur_entrant_data['numero']]
            new_state['sub_veec'] += 1

            # Enregistrement
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = {
                'timestamp': timestamp,
                'set': new_state['current_set'],
                'score': f"{new_state['score_veec']}-{new_state['score_adverse']}",
                'position': sortant_pos,
                'joueur_nom': f"{joueur_sortant['nom']} (SORT)",
                'action_code': 'SUB',
                'resultat': f"ENTRE: {joueur_entrant_data['nom']}"
            }
            new_state['historique_stats'].insert(0, log_entry)

            new_state['sub_en_cours_team'] = None
            new_state['temp_sub_state'] = {}

            historique_table = create_historique_table(new_state['historique_stats'])
            return new_state, historique_table, ""

        return new_state, dash.no_update, ""


    # =================================================================
    # CALLBACKS SETUP PRÉ-MATCH
    # =================================================================

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
    def handle_setup_selection(player_clicks, position_clicks, match_state_input, current_state_from_state):
        """Gère la sélection des joueurs et positions pour le setup pré-match"""
        ctx = dash.callback_context
        triggered_prop_id = ctx.triggered[0]['prop_id'] if ctx.triggered else 'No trigger'

        # Utiliser l'Input frais
        state_to_use = match_state_input if match_state_input is not None else current_state_from_state
        new_state = copy.deepcopy(state_to_use)

        # Initialiser la formation temporaire
        if 'temp_setup_formation_veec' not in new_state:
            new_state['temp_setup_formation_veec'] = {}

        temp_formation = new_state['temp_setup_formation_veec']

        # Affichage initial
        if not ctx.triggered or triggered_prop_id == 'match-state.data':
            if not state_to_use.get('match_setup_completed'):
                return create_pre_match_setup_modal(state_to_use), dash.no_update
            return None, dash.no_update

        # Gestion des clics
        if not ctx.triggered[0]['value']:
            return dash.no_update, dash.no_update

        player_num = new_state.get('temp_setup_selected_player_num')
        triggered_id = triggered_prop_id.replace(".n_clicks", "")

        try:
            triggered_dict = json.loads(re.sub(r"'", '"', triggered_id))
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            return dash.no_update, dash.no_update

        # Clic sur un joueur
        if triggered_dict['type'] == 'setup-player-select':
            num = int(triggered_dict['index'])
            new_selection = num if player_num != num else None
            new_state['temp_setup_selected_player_num'] = new_selection

        # Clic sur une position
        elif triggered_dict['type'] == 'setup-position-assign':
            pos = int(triggered_dict['index'])

            # Désassigner
            if pos in temp_formation:
                temp_formation.pop(pos)
                new_state['temp_setup_selected_player_num'] = None

            # Assigner
            elif player_num is not None:
                ROSTER_VEEC = new_state.get('JOUERS_VEEC', {})
                player_data = ROSTER_VEEC.get(player_num) or ROSTER_VEEC.get(str(player_num))

                if player_data:
                    player_data['numero'] = int(player_num)
                    temp_formation[pos] = player_data
                    new_state['temp_setup_selected_player_num'] = None

        updated_modal = create_pre_match_setup_modal(new_state)
        return updated_modal, new_state


    @app.callback(
        Output('match-state', 'data', allow_duplicate=True),
        Output('historique-output', 'children', allow_duplicate=True),
        Input('btn-confirm-setup', 'n_clicks'),
        State('match-state', 'data'),
        prevent_initial_call=True
    )
    def confirm_setup_and_start_match(n_clicks, current_state):
        """Confirme la formation et démarre le match"""
        if n_clicks is None or n_clicks == 0:
            return dash.no_update, dash.no_update

        new_state = copy.deepcopy(current_state)
        temp_formation = new_state.get('temp_setup_formation_veec', {})

        if len(temp_formation) != 6:
            return dash.no_update, dash.no_update

        # Mettre à jour la formation actuelle
        new_state['formation_actuelle'] = temp_formation

        # Définir le banc
        ROSTER_VEEC = new_state.get('JOUERS_VEEC', {})
        assigned_nums = [p['numero'] for p in temp_formation.values()]

        new_banc = {}
        for num, data in ROSTER_VEEC.items():
            if num not in assigned_nums:
                new_banc[num] = data

        new_state['joueurs_banc'] = new_banc

        # Finaliser le setup
        new_state['match_setup_completed'] = True
        new_state['temp_setup_formation_veec'] = {}
        new_state['temp_setup_selected_player_num'] = None

        # Historique
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'set': 1,
            'score': '0-0',
            'position': 'SETUP',
            'joueur_nom': 'MATCH',
            'action_code': 'START',
            'resultat': 'Formation Confirmée'
        }
        new_state['historique_stats'].insert(0, log_entry)
        historique_table = create_historique_table(new_state['historique_stats'])

        return new_state, historique_table


    print("✅ Tous les callbacks ont été enregistrés")
