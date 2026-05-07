"""
Document type selection tile component.

Renders a clickable tile for one document type, with
icon, label, description, format info, and selection state.
"""

from dash import html
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS,
    DOC_TILE, DOC_TILE_ACTIVE, DOC_TILE_ICON,
)


def doc_tile(doc: dict, selected: bool) -> html.Div:
    """
    Renders a single document type tile.

    Args:
        doc:      Document type definition from DOC_TYPES.
        selected: Whether this tile is currently active.

    Returns:
        Clickable tile with visual selection state.
    """
    tile_style = {
        **(DOC_TILE_ACTIVE if selected else DOC_TILE),
        "cursor": "pointer",
        "userSelect": "none",   # ← empêche la sélection de texte au clic
    }

    return html.Div(
        [
            # Icon bubble
            html.Div(
                doc["icon"],
                style={**DOC_TILE_ICON, "backgroundColor": doc["icon_bg"]},
            ),

            # Text block
            html.Div(
                [
                    # Title row
                    html.Div([
                        html.Span(doc["label"], style={
                            "fontFamily": FONTS["sans"],
                            "fontSize":   "14px",
                            "fontWeight": "600" if selected else "500",
                            "color": COLORS["accent"] if selected else COLORS["ink"],
                        }),
                        html.Span(doc["sublabel"], style={
                            "fontFamily":   FONTS["mono"],
                            "fontSize":     "10px",
                            "color":        COLORS["muted"],
                            "marginLeft":   "8px",
                            "letterSpacing": "0.04em",
                        }),
                    ], style={"marginBottom": "3px"}),

                    # Description
                    html.Div(doc["description"], style={
                        "fontFamily": FONTS["sans"],
                        "fontSize":   "12px",
                        "color":      COLORS["muted"],
                        "lineHeight": "1.5",
                    }),

                    # Format info
                    html.Div([
                        html.Span("Formats : ", style={
                            "fontFamily": FONTS["mono"],
                            "fontSize":   "10px",
                            "color":      COLORS["muted"],
                        }),
                        html.Span(doc["formats"], style={
                            "fontFamily": FONTS["mono"],
                            "fontSize":   "10px",
                            "fontWeight": "600",
                            "color": COLORS["accent"] if selected else COLORS["ink"],
                        }),
                        html.Span(
                            " · Plusieurs fichiers" if doc["multi"] else " · Fichier unique",
                            style={
                                "fontFamily": FONTS["mono"],
                                "fontSize":   "10px",
                                "color":      COLORS["muted"],
                            },
                        ),
                    ], style={"marginTop": "5px"}),
                ],
                style={"flex": "1"},
            ),

            # Selection checkmark
            html.Div(
                "✓" if selected else "",
                style={
                    "width":           "22px",
                    "height":          "22px",
                    "borderRadius":    "50%",
                    "backgroundColor": COLORS["accent"] if selected else "transparent",
                    "border": f"1.5px solid {COLORS['accent'] if selected else COLORS['border']}",
                    "color":           COLORS["white"],
                    "display":         "flex",
                    "alignItems":      "center",
                    "justifyContent":  "center",
                    "fontSize":        "12px",
                    "fontWeight":      "600",
                    "flexShrink":      "0",
                },
            ),
        ],
        id=f"tile-{doc['id']}",
        n_clicks=0,
        # style={**tile_style, "cursor": "pointer"},
        style=tile_style,
    )