"""
Step 4 — Form validation page layout.

All components targeting forms-container, forms-summary-banner,
and the inline add-file panel are defined here and exist only
on this page, so callbacks can safely reference them.
"""

from dash import dcc, html

import frontend.views.upload.step4_callbacks  # noqa: F401 — registers callbacks

from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS, SHADOW,
    BTN_PRIMARY, BTN_SECONDARY,
    PAGE_TITLE, PAGE_SUBTITLE, SECTION_TITLE,
    DROPZONE,
)
from frontend.components.step_bar import step_bar


def _add_file_panel() -> html.Div:
    """
    Inline upload panel shown when the user chooses "Charger un fichier"
    from the add-section menu on Step 4.

    Hidden by default (display:none). Toggled by callbacks.
    Always in the DOM so Dash never throws a ReferenceError on its outputs.

    Returns:
        Styled div with dcc.Upload, file list, errors, and action buttons.
    """
    return html.Div(
        [
            html.Div(
                [
                    html.Span("Charger un fichier supplémentaire", style={
                        "fontFamily": FONTS["sans"],
                        "fontSize":   "14px",
                        "fontWeight": "600",
                        "color":      COLORS["ink"],
                    }),
                    html.Button(
                        "✕",
                        id="btn-cancel-s4",
                        n_clicks=0,
                        style={
                            "background": "none",
                            "border":     "none",
                            "cursor":     "pointer",
                            "color":      COLORS["muted"],
                            "fontSize":   "18px",
                            "fontWeight": "600",
                            "padding":    "0",
                            "lineHeight": "1",
                        },
                    ),
                ],
                style={
                    "display":        "flex",
                    "justifyContent": "space-between",
                    "alignItems":     "center",
                    "marginBottom":   f"{SPACE['md']}px",
                },
            ),

            dcc.Upload(
                id="dcc-upload-s4",
                children=html.Div(
                    [
                        html.Div("☁️", style={"fontSize": "24px", "marginBottom": "6px"}),
                        html.Div("Glisser-déposer ici", style={
                            "fontFamily": FONTS["sans"],
                            "fontSize":   "12px",
                            "fontWeight": "600",
                            "color":      COLORS["ink"],
                            "marginBottom": "3px",
                        }),
                        html.Div("ou cliquer pour parcourir", style={
                            "fontFamily": FONTS["sans"],
                            "fontSize":   "11px",
                            "color":      COLORS["muted"],
                        }),
                    ],
                    style={"textAlign": "center"},
                ),
                style=DROPZONE,
                multiple=True,
            ),

            html.Div(id="upload-file-list-s4"),
            html.Div(id="upload-errors-s4"),

            html.Div(
                [
                    html.Button(
                        "Annuler",
                        id="btn-cancel2-s4",
                        n_clicks=0,
                        style=BTN_SECONDARY,
                    ),
                    html.Button(
                        "Ajouter au formulaire →",
                        id="btn-confirm-s4",
                        n_clicks=0,
                        disabled=True,
                        style={**BTN_PRIMARY, "opacity": "0.5"},
                    ),
                ],
                style={
                    "display":        "flex",
                    "justifyContent": "flex-end",
                    "gap":            f"{SPACE['sm']}px",
                    "marginTop":      f"{SPACE['md']}px",
                },
            ),
        ],
        id="upload-panel-s4",
        style={
            "display":         "none",
            "backgroundColor": COLORS["white"],
            "border":          f"1px solid {COLORS['border']}",
            "borderRadius":    RADIUS["lg"],
            "padding":         f"{SPACE['lg']}px",
            "marginBottom":    f"{SPACE['md']}px",
            "boxShadow":       SHADOW["sm"],
        },
    )


def layout() -> html.Div:
    """Renders the Step 4 page."""
    return html.Div(
        [
            # Fires once after mount to trigger form generation
            dcc.Interval(
                id="step4-mount-trigger",
                interval=150,
                n_intervals=0,
                max_intervals=1,
            ),

            step_bar(current=4),

            html.H1("Formulaires & validation", style=PAGE_TITLE),
            html.P(
                "Vérifiez et corrigez les champs extraits avant de soumettre.",
                style=PAGE_SUBTITLE,
            ),

            # Active document type label — populated by generate_forms callback
            html.Div(id="step4-doc-type-label",
                     style={"marginBottom": f"{SPACE['sm']}px"}),

            # Summary line — updated by generate_forms and add callbacks
            html.Div(id="forms-summary-banner"),

            # Add-file inline panel — always in DOM, shown/hidden by callback
            _add_file_panel(),

            # Form sections — populated by generate_forms callback
            html.Div(id="forms-container", children=[]),

            # Add-section button + dropdown menu
            html.Div(
                [
                    html.Button(
                        [
                            html.I(
                                className="fa-solid fa-plus",
                                style={"marginRight": "8px"},
                            ),
                            "Ajouter une section",
                        ],
                        id="btn-add-section",
                        n_clicks=0,
                        style=BTN_SECONDARY,
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fa-solid fa-cloud-arrow-up",
                                        style={"marginRight": "8px", "color": COLORS["muted"]},
                                    ),
                                    "Charger un fichier",
                                ],
                                id="btn-add-from-file",
                                n_clicks=0,
                                style={
                                    "padding":      f"{SPACE['sm']}px {SPACE['md']}px",
                                    "fontSize":     "13px",
                                    "cursor":       "pointer",
                                    "fontFamily":   FONTS["sans"],
                                    "color":        COLORS["ink"],
                                    "borderRadius": "6px",
                                    "display":      "flex",
                                    "alignItems":   "center",
                                },
                            ),
                            html.Div(
                                [
                                    html.I(
                                        className="fa-solid fa-keyboard",
                                        style={"marginRight": "8px", "color": COLORS["muted"]},
                                    ),
                                    "Entrer manuellement",
                                ],
                                id="btn-add-manual",
                                n_clicks=0,
                                style={
                                    "padding":      f"{SPACE['sm']}px {SPACE['md']}px",
                                    "fontSize":     "13px",
                                    "cursor":       "pointer",
                                    "fontFamily":   FONTS["sans"],
                                    "color":        COLORS["ink"],
                                    "borderRadius": "6px",
                                    "display":      "flex",
                                    "alignItems":   "center",
                                },
                            ),
                        ],
                        id="add-section-menu",
                        style={
                            "display":         "none",
                            "position":        "absolute",
                            "backgroundColor": COLORS["white"],
                            "border":          f"1px solid {COLORS['border']}",
                            "borderRadius":    "10px",
                            "padding":         "6px",
                            "boxShadow":       "0 4px 12px rgba(0,0,0,0.08)",
                            "zIndex":          "100",
                            "minWidth":        "190px",
                            "marginTop":       "4px",
                        },
                    ),
                ],
                style={
                    "position":     "relative",
                    "marginTop":    f"{SPACE['md']}px",
                    "marginBottom": f"{SPACE['md']}px",
                },
            ),

            # Bottom action bar
            html.Div(
                [
                    html.Button(
                        [
                            html.I(
                                className="fa-solid fa-arrow-left",
                                style={"marginRight": "8px"},
                            ),
                            "Retour",
                        ],
                        id="btn-step4-back",
                        n_clicks=0,
                        style=BTN_SECONDARY,
                    ),
                    html.Button(
                        [
                            "Soumettre",
                            html.I(
                                className="fa-solid fa-arrow-right",
                                style={"marginLeft": "8px"},
                            ),
                        ],
                        id="btn-step4-submit",
                        n_clicks=0,
                        style=BTN_PRIMARY,
                    ),
                ],
                style={
                    "display":        "flex",
                    "justifyContent": "space-between",
                    "marginTop":      f"{SPACE['lg']}px",
                },
            ),
        ],
        style={"maxWidth": "900px"},
    )
