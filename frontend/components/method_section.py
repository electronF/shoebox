"""
Entry method selection component (upload file vs manual entry).
"""

from dash import html
from frontend.theme import (
    COLORS, FONTS, SPACE,
    CARD, BTN_SECONDARY, SECTION_TITLE,
)
from frontend.views.upload._doc_types import DOC_TYPES


def method_section(selected_type: str) -> html.Div:
    """
    Renders the upload / manual entry button pair.

    Args:
        selected_type: Currently selected doc type ID.

    Returns:
        Card with two action buttons and a format hint.
    """
    doc = next((d for d in DOC_TYPES if d["id"] == selected_type), DOC_TYPES[0])

    return html.Div(
        [
            html.Div("Méthode d'ajout", style=SECTION_TITLE),

            html.Div(
                [
                    html.Button(
                        [
                            html.I(
                                className="fa-solid fa-folder-open",
                                style={"marginRight": "8px", "color": COLORS["muted"]}), 
                            "Charger un fichier"
                        ],
                        id="btn-open-upload",
                        n_clicks=0,
                        style={
                            **BTN_SECONDARY,
                            "flex": "1", "height": "44px",
                            "display": "flex", "alignItems": "center",
                            "justifyContent": "center",
                        },
                    ),
                    html.Button(
                        [html.Span("⌨️", style={"marginRight": "8px"}), "Saisir manuellement"],
                        id="btn-manual-entry",
                        n_clicks=0,
                        style={
                            **BTN_SECONDARY,
                            "flex": "1", "height": "44px",
                            "display": "flex", "alignItems": "center",
                            "justifyContent": "center",
                        },
                    ),
                ],
                style={"display": "flex", "gap": f"{SPACE['sm']}px"},
            ),

            # Format hint line
            html.Div(
                [
                    html.Span("Formats acceptés : ", style={
                        "fontFamily": FONTS["sans"],
                        "fontSize":   "12px",
                        "color":      COLORS["muted"],
                    }),
                    html.Span(doc["formats"], style={
                        "fontFamily": FONTS["mono"],
                        "fontSize":   "12px",
                        "fontWeight": "600",
                        "color":      COLORS["ink"],
                    }),
                    html.Span(
                        " · Plusieurs fichiers" if doc["multi"] else " · Fichier unique",
                        style={
                            "fontFamily": FONTS["sans"],
                            "fontSize":   "12px",
                            "color":      COLORS["muted"],
                        },
                    ),
                ],
                style={"marginTop": f"{SPACE['sm']}px"},
            ),
        ],
        style=CARD,
    )