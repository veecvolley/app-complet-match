"""
Application VEEC Scorer - Entry Point
Application de suivi de match de volleyball en temps réel

Structure restructurée pour une meilleure maintenabilité et déploiement en production.
"""
import dash
from dash import dcc, html, Input, Output, State, ALL
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports des modules applicatifs
from config.settings import (
    DEBUG, HOST, PORT,
    VEEC_COLOR, ADVERSE_COLOR
)
from src.models.state import get_initial_state
from src.utils.helpers import clean_formations
from src.utils.rotation import appliquer_rotation_veec, appliquer_rotation_adverse
from src.utils.libero import swap_liberos_on_bench, handle_libero_out
from src.components.court import create_court_figure
from src.components.tables import create_historique_table
from src.components.cards import create_player_card, create_position_card

# --- INITIALISATION DE L'APPLICATION ---

VIEWPORT_META = [
    {
        "name": "viewport",
        "content": "width=device-width, initial-scale=1, maximum-scale=1.0, user-scalable=no"
    }
]

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=VIEWPORT_META
)

# État initial
initial_state = get_initial_state()

# --- LAYOUT PRINCIPAL ---

app.layout = html.Div([
    # Stores pour la gestion d'état
    dcc.Store(id='match-state', data=initial_state),
    dcc.Store(id='joueur-selectionne', data=None),
    dcc.Store(id='setup-refresh-trigger'),
    dcc.Store(id='current-set', data=1),
    dcc.Store(id='close-modal-trigger', data=0),

    # Conteneurs de modals
    html.Div(id='pre-match-setup-container'),
    html.Div(id='service-modal-container'),
    html.Div(id='stat-modal-container'),

    # Interval pour le timer
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),

    # Div caché pour JS
    html.Div(id='hidden-div-for-js', style={'display': 'none'}),

    # --- EN-TÊTE ---
    html.Div([
        # VEEC
        html.Div([
            html.Span("VEEC", style={
                'fontSize': '1.8em',
                'fontWeight': 'bold',
                'fontFamily': 'sans-serif',
                'color': '#333',
                'marginRight': '15px'
            }),
            html.Div(
                html.Img(src='/assets/logo-simple.png', style={
                    'height': '35px',
                    'width': '35px'
                }),
                style={
                    'border': f'2px solid {VEEC_COLOR}',
                    'borderRadius': '50%',
                    'padding': '2px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'height': '45px',
                    'width': '45px',
                    'boxShadow': '0 0 5px rgba(0,0,0,0.1)',
                    'overflow': 'hidden',
                    'backgroundColor': 'white'
                }
            ),
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'flex-end',
            'width': '35%',
            'paddingRight': '20px'
        }),

        # Score Sets
        html.Div([
            html.Span(id='sets-veec-display', children='0', style={
                'color': VEEC_COLOR,
                'fontSize': '3em',
                'fontWeight': '900',
                'fontFamily': 'sans-serif'
            }),
            html.Span(" : ", style={
                'fontSize': '3em',
                'color': '#666',
                'fontWeight': 'lighter',
                'margin': '0 10px'
            }),
            html.Span(id='sets-adverse-display', children='0', style={
                'color': ADVERSE_COLOR,
                'fontSize': '3em',
                'fontWeight': '900',
                'fontFamily': 'sans-serif'
            }),
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'width': '30%',
            'border': '2px solid #ddd',
            'borderRadius': '10px',
            'padding': '10px 0',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }),

        # Adversaire
        html.Div([
            html.Span("ADVERSAIRE", style={
                'fontSize': '1.8em',
                'fontWeight': 'bold',
                'fontFamily': 'sans-serif',
                'color': '#333'
            }),
            html.Div(style={
                'height': '35px',
                'width': '35px',
                'backgroundColor': ADVERSE_COLOR,
                'borderRadius': '5px',
                'marginLeft': '10px'
            }),
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'flex-start',
            'width': '35%',
            'paddingLeft': '20px'
        }),
    ], style={
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'center',
        'padding': '20px 0',
        'backgroundColor': '#fff',
        'borderBottom': '1px solid #ccc',
        'marginBottom': '10px'
    }),

    html.Hr(),

    # --- TERRAIN DE JEU ---
    dcc.Graph(
        id='terrain-graph-statique',
        figure=create_court_figure(
            initial_state['formation_actuelle'],
            initial_state['formation_adverse_actuelle'],
            initial_state['service_actuel'],
            initial_state['liberos_veec']
        )[0],
        config={
            'displayModeBar': False,
            'scrollZoom': False,
            'doubleClick': False
        },
        style={'width': '100%', 'height': '50vh'}
    ),

    html.Hr(),

    # --- CONTRÔLES LIBERO ---
    html.Div([
        html.Button(
            'Sub. Libero',
            id='btn-sub-libero-veec',
            n_clicks=0,
            style={
                'backgroundColor': '#28a745',
                'color': 'white',
                'padding': '10px',
                'borderRadius': '5px',
                'marginRight': '10px'
            }
        ),
        html.Button(
            'Swap Libero N°9',
            id='btn-swap-libero-reserve',
            n_clicks=0,
            style={
                'backgroundColor': 'orange',
                'color': 'white',
                'fontWeight': 'bold',
                'margin': '5px'
            }
        ),
    ], style={'marginBottom': '10px'}),

    html.Div(id='feedback-output-libero', style={
        'color': 'orange',
        'marginTop': '10px'
    }),

    # --- BOUTONS DE SCORE ---
    html.Div([
        html.Button(
            "Point VEEC ➕",
            id='btn-point-veec',
            n_clicks=0,
            style={
                'marginRight': '10px',
                'backgroundColor': VEEC_COLOR,
                'color': 'white',
                'fontSize': '1.8em',
                'padding': '15px 30px',
                'minHeight': '70px',
                'borderRadius': '8px',
                'fontWeight': 'bold'
            }
        ),
        html.Button(
            "Point ADVERSAIRE ➖",
            id='btn-point-adverse',
            n_clicks=0,
            style={
                'backgroundColor': ADVERSE_COLOR,
                'color': 'white',
                'fontSize': '1.8em',
                'padding': '15px 30px',
                'minHeight': '70px',
                'borderRadius': '8px',
                'fontWeight': 'bold'
            }
        ),
    ], style={
        'textAlign': 'center',
        'marginBottom': '20px',
        'marginTop': '10px'
    }),

    # Feedback substitution
    html.Div(
        id='feedback-sub-output',
        children=None,
        style={
            'color': 'red',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'marginTop': '10px'
        }
    ),

    # --- TABLEAU DE BORD ---
    html.Div([
        html.Div([
            html.H4("Set ", style={
                'width': '20%',
                'textAlign': 'left',
                'fontSize': '1.5em',
                'paddingLeft': '10px'
            }),
            html.Span("1", id='set-number-display', style={
                'fontSize': '1.5em',
                'fontWeight': 'bold'
            }),
            html.Div(id='timer-progress-bar', style={
                'width': '70%',
                'textAlign': 'right',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'flex-end'
            }),
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'marginBottom': '15px',
            'paddingRight': '10px'
        }),

        html.Div([
            # Score VEEC
            html.Div(
                id='score-veec-container',
                children=html.Div(
                    id='score-veec-large',
                    children='0',
                    style={
                        'fontSize': '5em',
                        'fontWeight': '900',
                        'fontFamily': 'sans-serif',
                        'color': 'black'
                    }
                ),
                style={
                    'width': '30%',
                    'textAlign': 'center',
                    'padding': '10px 0',
                    'border': f'3px solid {VEEC_COLOR}',
                    'borderRadius': '15px',
                    'boxShadow': '0 4px 10px rgba(0,0,0,0.1)',
                    'backgroundColor': 'white'
                }
            ),

            # Contrôles centre (Subs et Timeouts)
            html.Div([
                # Substitutions
                html.Div([
                    html.Span(id='btn-sub-veec-center', children='0', style={
                        'color': VEEC_COLOR,
                        'fontSize': '2em',
                        'fontWeight': 'bold',
                        'marginRight': '5px'
                    }),
                    html.Button("Sub", id='btn-sub-veec', n_clicks=0, style={
                        'color': '#666',
                        'fontSize': '1em',
                        'border': 'none',
                        'background': 'none',
                        'padding': '0 5px'
                    }),
                    html.Span("|", style={'margin': '0 15px', 'color': '#ddd'}),
                    html.Button("Sub", id='btn-sub-adverse', n_clicks=0, style={
                        'color': '#666',
                        'fontSize': '1em',
                        'border': 'none',
                        'background': 'none',
                        'padding': '0 5px',
                        'marginRight': '5px'
                    }),
                    html.Span(id='btn-sub-adverse-center', children='0', style={
                        'color': ADVERSE_COLOR,
                        'fontSize': '2em',
                        'fontWeight': 'bold'
                    }),
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'marginBottom': '10px'
                }),

                # Timeouts
                html.Div([
                    html.Span(id='btn-to-veec-center', children='0', style={
                        'color': VEEC_COLOR,
                        'fontSize': '2em',
                        'fontWeight': 'bold',
                        'marginRight': '5px'
                    }),
                    html.Button("TO", id='btn-to-veec', n_clicks=0, style={
                        'color': '#666',
                        'fontSize': '1em',
                        'border': 'none',
                        'background': 'none',
                        'padding': '0 5px'
                    }),
                    html.Span("|", style={'margin': '0 15px', 'color': '#ddd'}),
                    html.Button("TO", id='btn-to-adverse', n_clicks=0, style={
                        'color': '#666',
                        'fontSize': '1em',
                        'border': 'none',
                        'background': 'none',
                        'padding': '0 5px',
                        'marginRight': '5px'
                    }),
                    html.Span(id='btn-to-adverse-center', children='0', style={
                        'color': ADVERSE_COLOR,
                        'fontSize': '2em',
                        'fontWeight': 'bold'
                    }),
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                }),
            ], style={
                'width': '40%',
                'textAlign': 'center',
                'display': 'flex',
                'flexDirection': 'column',
                'justifyContent': 'center'
            }),

            # Score Adverse
            html.Div(
                id='score-adverse-container',
                children=html.Div(
                    id='score-adverse-large',
                    children='0',
                    style={
                        'fontSize': '5em',
                        'fontWeight': '900',
                        'fontFamily': 'sans-serif',
                        'color': 'black'
                    }
                ),
                style={
                    'width': '30%',
                    'textAlign': 'center',
                    'padding': '10px 0',
                    'border': f'3px solid {ADVERSE_COLOR}',
                    'borderRadius': '15px',
                    'boxShadow': '0 4px 10px rgba(0,0,0,0.1)',
                    'backgroundColor': 'white'
                }
            ),
        ], style={
            'display': 'flex',
            'justifyContent': 'space-around',
            'alignItems': 'center',
            'marginTop': '15px',
            'marginBottom': '15px'
        }),
    ], style={'padding': '20px', 'borderTop': '1px solid #ccc'}),

    # --- HISTORIQUE ---
    html.Details([
        html.Summary("Historique des Actions (Détail)", style={
            'marginTop': '20px',
            'fontWeight': 'bold'
        }),
        html.Div(
            id='historique-output',
            children=create_historique_table(initial_state['historique_stats'])
        )
    ], style={'padding': '10px'}),

], style={'padding': '0', 'margin': '0'})


# --- CALLBACKS ---
# Import et enregistrement de tous les callbacks depuis le module centralisé
from src.callbacks.all_callbacks import register_callbacks

# Enregistrer tous les callbacks
register_callbacks(app)

print("✅ Callbacks enregistrés et application prête")


# --- POINT D'ENTRÉE ---
if __name__ == '__main__':
    app.run(
        debug=DEBUG,
        host=HOST,
        port=PORT
    )
