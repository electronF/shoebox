"""
Application shell — sidebar, persistent stores, and page container.
forms-container and forms-summary-banner live here so they are
always in the DOM regardless of the current page.
"""

from dash import dcc, html
from frontend.theme import (
    COLORS, FONTS, SPACE, SIDEBAR, NAV_ITEM,
)
from frontend.theme import ICONS

_NAV_ITEMS = [
    ("nav-overview",      "/",              ICONS["chart"],     "Vue d'ensemble"),
    ("nav-upload",        "/upload",        ICONS["import"],    "Importer"),
    ("nav-invoices",      "/invoices",      ICONS["invoice"],   "Factures émises"),
    ("nav-subscriptions", "/subscriptions", ICONS["recurring"], "Abonnements"),
    ("nav-report",        "/report",        ICONS["report"],    "Rapport fiscal"),
    ("nav-recurring",     "/recurring",     ICONS["recurring"], "Récurrents"),
    ("nav-sources",       "/sources",       ICONS["wallet"],    "Sources & cartes"),
    ("nav-files",         "/files",         ICONS["folder"],    "Fichiers"),
]


def build_sidebar() -> html.Div:
    """Builds the persistent left navigation sidebar."""
    logo = html.Div(
        [
            html.Div(
                [
                    html.Span("Sh", style={
                        "fontFamily": FONTS["serif"], "fontSize": "20px",
                        "fontWeight": "700", "color": COLORS["white"],
                    }),
                    html.Span("o", style={
                        "fontFamily": FONTS["serif"], "fontSize": "20px",
                        "fontWeight": "700", "color": COLORS["white"],
                    }),
                    html.Span("eBox", style={
                        "fontFamily": FONTS["serif"], "fontSize": "20px",
                        "fontWeight": "700", "color": COLORS["white"],
                    }),
                ],
                style={"display": "flex", "alignItems": "baseline"},
            ),
            html.Div("FINANCES FREELANCE", style={
                "fontFamily": FONTS["mono"], "fontSize": "9px",
                "letterSpacing": "0.12em", "color": COLORS["gold"],
                "marginTop": "2px",
            }),
        ],
        style={
            "backgroundColor": COLORS["accent"],
            "padding": f"{SPACE['md']}px {SPACE['lg']}px",
            "marginBottom": f"{SPACE['md']}px",
        },
    )

    nav_label = html.Div("NAVIGATION", style={
        "fontFamily": FONTS["mono"], "fontSize": "9px",
        "letterSpacing": "0.12em", "color": COLORS["placeholder"],
        "padding": f"0 {SPACE['lg']}px",
        "marginBottom": f"{SPACE['xs']}px",
    })

    nav_items = [
        dcc.Link(
            html.Div(
                [
                    html.I(className=icon, style={
                        "fontSize": "14px", "width": "18px",
                        "textAlign": "center", "flexShrink": "0",
                    }),
                    html.Span(label, style={"fontFamily": FONTS["sans"]}),
                ],
                id=nav_id,
                style=NAV_ITEM,
            ),
            href=path,
            style={"textDecoration": "none"},
        )
        for nav_id, path, icon, label in _NAV_ITEMS
    ]

    period_badge = html.Div(
        [
            html.Div("PÉRIODE ACTIVE", style={
                "fontFamily": FONTS["mono"], "fontSize": "9px",
                "letterSpacing": "0.1em", "color": COLORS["placeholder"],
                "marginBottom": "4px",
            }),
            html.Div("Q1 2025", style={
                "fontFamily": FONTS["sans"], "fontSize": "13px",
                "fontWeight": "600", "color": COLORS["accent"],
            }),
        ],
        style={
            "padding": f"{SPACE['md']}px {SPACE['lg']}px",
            "borderTop": f"1px solid {COLORS['border']}",
            "marginTop": "auto",
        },
    )

    return html.Div(
        [logo, nav_label, *nav_items, period_badge],
        style=SIDEBAR,
    )


def build_shell() -> html.Div:
    """
    Builds the full application shell.

    All persistent stores and shared containers live here.
    forms-container is placed here (hidden) so callbacks targeting
    it always find it in the DOM, regardless of current page.
    """
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),

            # ── Persistent stores ─────────────────────────────────────────
            dcc.Store(id="selected-doc-type",    data="REC",
                      storage_type="session"),
            dcc.Store(id="uploaded-files-store", data=[],
                      storage_type="session"),
            dcc.Store(id="popup-open",           data=False),
            dcc.Store(id="forms-data-store",     data=[]),
            dcc.Store(id="step4-doc-type",       data="REC",
                      storage_type="session"),

            # Validation popup — fixed position, always in DOM
            html.Div(id="validation-popup", style={"display": "none"}),

            # ─────────────────────────────────────────────────────────────
            html.Div(
                [
                    build_sidebar(),
                    html.Div(
                        html.Div(
                            id="page-content",
                            style={
                                "flex":            "1",
                                "padding":         f"{SPACE['2xl']}px",
                                "overflowY":       "auto",
                                "backgroundColor": COLORS["paper"],
                                "minHeight":       "100vh",
                            },
                        ),
                        style={
                            "flex":          "1",
                            "display":       "flex",
                            "flexDirection": "column",
                            "overflow":      "hidden",
                        },
                    ),
                ],
                style={
                    "display":         "flex",
                    "height":          "100vh",
                    "overflow":        "hidden",
                    "backgroundColor": COLORS["paper"],
                },
            ),
        ]
    )