"""
Step 3 — Document type selection and file upload.

No popup. The dcc.Upload zone is always visible inline.

Layout trick: the right side is its own flex column with three children:
  1. right-column      (dynamic — upload card, rebuilt on tile click)
  2. btn-manual-entry  (STATIC — never inside a dynamic container)
  3. fields-col        (dynamic — fields preview, rebuilt on tile click)

btn-manual-entry must stay outside any callback-updated container so Dash
always tracks its n_clicks reliably without losing state on tile changes.
"""

from dash import html, dcc

from frontend.theme import (
    COLORS, FONTS, SPACE,
    CARD, PAGE_TITLE, PAGE_SUBTITLE, SECTION_TITLE,
    BTN_PRIMARY, BTN_SECONDARY, DROPZONE,
)
from frontend.components.step_bar       import step_bar
from frontend.components.doc_tile       import doc_tile
from frontend.components.fields_preview import fields_preview
from frontend.views.upload._doc_types   import DOC_TYPES, ACCEPT_MIME


def _upload_card(doc_type: str) -> html.Div:
    """
    Builds the upload zone card for a given document type.

    Contains dcc.Upload, file list, error alerts, and the centered
    confirm button. Does NOT contain btn-manual-entry.

    Args:
        doc_type: Currently selected document type ID.

    Returns:
        Card div with upload zone and confirm button.
    """
    doc    = next((d for d in DOC_TYPES if d["id"] == doc_type), DOC_TYPES[0])
    accept = ACCEPT_MIME.get(doc_type, "*")

    return html.Div(
        [
            html.Div("Importer des fichiers", style=SECTION_TITLE),

            dcc.Upload(
                id="dcc-upload",
                children=html.Div(
                    [
                        html.Div("☁️", style={"fontSize": "28px", "marginBottom": "8px"}),
                        html.Div("Glisser-déposer ici", style={
                            "fontFamily":   FONTS["sans"],
                            "fontSize":     "13px",
                            "fontWeight":   "600",
                            "color":        COLORS["ink"],
                            "marginBottom": "4px",
                        }),
                        html.Div("ou cliquer pour parcourir", style={
                            "fontFamily": FONTS["sans"],
                            "fontSize":   "12px",
                            "color":      COLORS["muted"],
                        }),
                        html.Div(
                            [
                                html.Span("Formats : ", style={
                                    "fontFamily": FONTS["sans"],
                                    "fontSize":   "11px",
                                    "color":      COLORS["muted"],
                                }),
                                html.Span(doc["formats"], style={
                                    "fontFamily": FONTS["mono"],
                                    "fontSize":   "11px",
                                    "fontWeight": "600",
                                    "color":      COLORS["ink"],
                                }),
                            ],
                            style={"marginTop": "8px"},
                        ),
                    ],
                    style={"textAlign": "center"},
                ),
                style=DROPZONE,
                multiple=doc["multi"],
                accept=accept,
            ),

            html.Div(id="upload-file-list"),
            html.Div(id="upload-errors"),

            # Confirm button — centered
            html.Div(
                html.Button(
                    "Extraire et créer les formulaires →",
                    id="btn-confirm-upload",
                    n_clicks=0,
                    disabled=True,
                    style={**BTN_PRIMARY, "opacity": "0.5"},
                ),
                style={"textAlign": "center", "marginTop": f"{SPACE['md']}px"},
            ),
        ],
        style=CARD,
    )


def _fields_card(doc_type: str) -> html.Div:
    """
    Builds the fields preview card for a given document type.

    Args:
        doc_type: Currently selected document type ID.

    Returns:
        Card div with the fields preview list.
    """
    return html.Div(
        [
            html.Div("Champs extraits pour ce type", style=SECTION_TITLE),
            fields_preview(doc_type),
        ],
        style=CARD,
    )


def layout() -> html.Div:
    """Renders the Step 3 page."""
    return html.Div(
        [
            step_bar(current=3),

            html.H1("Ajouter une entrée", style=PAGE_TITLE),
            html.P(
                "Choisissez le type de document, puis la méthode d'ajout.",
                style=PAGE_SUBTITLE,
            ),

            html.Div(
                [
                    # Left — type selection tiles (static)
                    html.Div(
                        [
                            html.Div("Type de document", style=SECTION_TITLE),
                            html.Div(
                                [doc_tile(d, d["id"] == "REC") for d in DOC_TYPES],
                                id="doc-tiles-container",
                            ),
                        ],
                        style={**CARD, "flex": "1", "minWidth": "0"},
                    ),

                    # Right side — flex column with upload card / static button / fields preview
                    html.Div(
                        [
                            # 1. Upload card — rebuilt by select_doc_type callback
                            html.Div(
                                id="right-column",
                                children=[_upload_card("REC")],
                            ),

                            # 2. "Saisir manuellement" — STATIC, never replaced by any callback
                            html.Div(
                                html.Button(
                                    [
                                        html.Span("⌨️", style={"marginRight": "8px"}),
                                        "Saisir manuellement",
                                    ],
                                    id="btn-manual-entry",
                                    n_clicks=0,
                                    style={**BTN_SECONDARY, "width": "100%"},
                                ),
                                style={"marginTop": f"{SPACE['sm']}px"},
                            ),

                            # 3. Fields preview — rebuilt by select_doc_type callback
                            html.Div(
                                id="fields-col",
                                children=[_fields_card("REC")],
                                style={"marginTop": f"{SPACE['md']}px"},
                            ),
                        ],
                        style={
                            "flex":          "1",
                            "minWidth":      "0",
                            "display":       "flex",
                            "flexDirection": "column",
                        },
                    ),
                ],
                style={
                    "display":    "flex",
                    "gap":        f"{SPACE['lg']}px",
                    "alignItems": "flex-start",
                },
            ),
        ],
        style={"maxWidth": "1100px"},
    )
