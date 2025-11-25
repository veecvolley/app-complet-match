"""
Composant de visualisation du terrain de volleyball
"""
import plotly.graph_objects as go
from typing import Dict, Any, Tuple
from config.settings import (
    URL_IMAGE_TERRAIN,
    VEEC_POSITIONS_COORDS,
    ADVERSE_POSITIONS_COORDS,
    VEEC_COLOR,
    ADVERSE_COLOR
)


def create_court_figure(
    formation_equipe: Dict[int, Dict[str, Any]],
    formation_adverse: Dict[int, Dict[str, Any]],
    service_actuel: str,
    liberos_veec: Dict[str, Any]
) -> Tuple[go.Figure, Dict[str, Any]]:
    """
    Crée la figure Plotly représentant le terrain de volleyball
    avec les formations des deux équipes et l'indication du service.

    Args:
        formation_equipe: Formation VEEC {position: joueur_data}
        formation_adverse: Formation adverse {position: joueur_data}
        service_actuel: 'VEEC' ou 'ADVERSAIRE'
        liberos_veec: État des liberos VEEC

    Returns:
        Tuple (figure, layout_config)
    """
    # Note: Libero adverse simplifié (numéro 1)
    libero_adverse_num = 1
    libero_adverse_is_on_court = True

    fig = go.Figure()
    layout_config = {
        'modeBarButtonsToRemove': [
            'zoom', 'pan', 'select', 'lasso2d', 'autoscale',
            'zoomIn', 'zoomOut', 'resetscale'
        ],
        'scrollZoom': False
    }

    # Image de fond du terrain
    fig.add_layout_image(
        dict(
            source=URL_IMAGE_TERRAIN,
            xref="x", yref="y",
            x=0, y=100,
            sizex=100, sizey=100,
            sizing="stretch",
            opacity=1.0,
            layer="below"
        )
    )

    # --- ÉQUIPE VEEC ---
    veec_positions_list = sorted(list(VEEC_POSITIONS_COORDS.keys()))
    veec_x = [VEEC_POSITIONS_COORDS[pos]["x"] for pos in veec_positions_list]
    veec_y = [VEEC_POSITIONS_COORDS[pos]["y"] for pos in veec_positions_list]
    veec_text = [str(formation_equipe.get(pos, {}).get('numero', '?')) for pos in veec_positions_list]
    veec_customdata = [pos for pos in veec_positions_list]
    veec_hovertext = [
        f"P{pos} - {formation_equipe.get(pos, {}).get('nom', 'N/A')}"
        for pos in veec_positions_list
    ]

    # Logique Libero pour coloration
    libero_actif_num = liberos_veec.get('actif_numero')
    libero_reserve_num = liberos_veec.get('reserve_numero')
    is_libero_on_court_status = liberos_veec.get('is_on_court')

    veec_colors = []
    veec_line_colors = []
    veec_line_widths = []

    for pos in veec_positions_list:
        player_data = formation_equipe.get(pos, {})
        player_on_court_numero = player_data.get('numero')

        # Vérifier si le joueur actuel est le Libero ACTIF ou RESERVE
        is_libero_in_pos = is_libero_on_court_status and \
                          (player_on_court_numero == libero_actif_num or
                           player_on_court_numero == libero_reserve_num)

        if is_libero_in_pos:
            # Style Libero : Bleu clair, bordure blanche épaisse
            veec_colors.append('#ADD8E6')
            veec_line_colors.append('white')
            veec_line_widths.append(3)
        else:
            # Style standard VEEC
            veec_colors.append(VEEC_COLOR)
            veec_line_colors.append('white')
            veec_line_widths.append(1)

    fig.add_trace(go.Scatter(
        x=veec_x, y=veec_y,
        hoveron='points',
        connectgaps=False,
        mode="markers+text",
        name="VEEC",
        marker=dict(
            size=85,
            color=veec_colors,
            symbol="circle",
            line=dict(width=veec_line_widths, color=veec_line_colors)
        ),
        text=veec_text,
        textposition="middle center",
        textfont=dict(color="white", size=18, weight="bold"),
        customdata=veec_customdata,
        hoverinfo='text',
        hovertext=veec_hovertext
    ))

    # --- ÉQUIPE ADVERSE ---
    adverse_positions_list = sorted(list(ADVERSE_POSITIONS_COORDS.keys()))
    adverse_x = [ADVERSE_POSITIONS_COORDS[pos]["x"] for pos in adverse_positions_list]
    adverse_y = [ADVERSE_POSITIONS_COORDS[pos]["y"] for pos in adverse_positions_list]
    adverse_text = [
        str(formation_adverse.get(pos, {}).get('numero', '?'))
        for pos in adverse_positions_list
    ]

    adverse_colors = []
    adverse_line_colors = []
    adverse_line_widths = []

    # Logique Libero Adverse
    for pos in adverse_positions_list:
        player_data = formation_adverse.get(pos, {})
        player_on_court_numero = player_data.get('numero')

        is_libero_in_pos = player_on_court_numero == libero_adverse_num

        if is_libero_in_pos and libero_adverse_is_on_court:
            # Style Libero Adverse : Rouge clair, bordure blanche épaisse
            adverse_colors.append('#F08080')
            adverse_line_colors.append('white')
            adverse_line_widths.append(3)
        else:
            # Style standard Adverse
            adverse_colors.append(ADVERSE_COLOR)
            adverse_line_colors.append('white')
            adverse_line_widths.append(1)

    fig.add_trace(go.Scatter(
        x=adverse_x, y=adverse_y,
        mode="markers+text",
        name="Adversaire",
        marker=dict(
            size=85,
            color=adverse_colors,
            symbol="circle",
            line=dict(width=adverse_line_widths, color=adverse_line_colors)
        ),
        text=adverse_text,
        textposition="middle center",
        textfont=dict(color="white", size=18, weight="bold"),
        hoverinfo='none'
    ))

    # --- INDICATEUR DE SERVICE (Ballon) ---
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
            mode="text",
            name="Service Ball",
            text=["🏐"],
            textposition="middle center",
            textfont=dict(size=53),
            hoverinfo='none'
        ))

    # --- LAYOUT FINAL ---
    fig.update_layout(
        xaxis=dict(
            range=[0, 100],
            showgrid=False,
            zeroline=False,
            visible=False,
            fixedrange=True
        ),
        yaxis=dict(
            range=[0, 100],
            showgrid=False,
            zeroline=False,
            visible=False,
            scaleanchor="x",
            scaleratio=0.5,
            fixedrange=True
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        dragmode=False,
        clickmode='event'
    )

    return fig, layout_config
