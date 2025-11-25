"""
Composants de tables (historique, statistiques)
"""
from dash import html, dash_table
import pandas as pd
from typing import List, Dict, Any, Union


def create_historique_table(historique_stats: List[Dict[str, Any]]) -> Union[dash_table.DataTable, html.Div]:
    """
    Crée le DataTable Dash pour afficher l'historique des actions du match.

    Args:
        historique_stats: Liste des entrées d'historique

    Returns:
        DataTable ou Div si l'historique est vide
    """
    if not historique_stats:
        return html.Div(
            "L'historique des actions est vide pour le moment.",
            style={'padding': '10px', 'color': '#666'}
        )

    df_historique = pd.DataFrame(historique_stats)
    columns_config = [
        {"name": i.capitalize(), "id": i}
        for i in df_historique.columns
    ]

    return dash_table.DataTable(
        id='datatable-historique',
        columns=columns_config,
        data=df_historique.head(50).to_dict('records'),
        style_table={'overflowX': 'auto', 'marginTop': '10px'},
        style_header={
            'backgroundColor': 'lightgrey',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ]
    )
