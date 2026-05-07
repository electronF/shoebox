"""
Step 5 — Upload history / ingestion results.

Shows a success banner, KPI summary for the full file registry,
and a table of every ingested file. Navigated to automatically
after a successful submit from Step 4.
"""

from dash import dcc, html

import frontend.api_client as api
from frontend.components.step_bar import step_bar
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS,
    CARD, BTN_PRIMARY, BTN_SECONDARY,
    TABLE_HEADER_CELL, TABLE_CELL,
    SECTION_TITLE, PAGE_TITLE, PAGE_SUBTITLE,
)


def _status_badge(status: str) -> html.Span:
    """Build a colour-coded pill badge for OCR processing status.

    Args:
        status: One of 'ok', 'warning', or 'error'.

    Returns:
        html.Span: Styled inline badge element.
    """
    cfg = {
        "ok":      (COLORS["ok"],      COLORS["ok_bg"],      "fa-solid fa-check",                 "Traité"),
        "warning": (COLORS["warning"], COLORS["warning_bg"], "fa-solid fa-triangle-exclamation",  "Avertissement"),
        "error":   (COLORS["error"],   COLORS["error_bg"],   "fa-solid fa-xmark",                 "Erreur"),
    }.get(status, (COLORS["muted"], COLORS["cream"], "fa-solid fa-circle", status))
    color, bg, icon, label = cfg
    return html.Span(
        [html.I(className=icon, style={"marginRight": "5px", "fontSize": "10px"}), label],
        style={
            "display":         "inline-flex",
            "alignItems":      "center",
            "fontFamily":      FONTS["mono"],
            "fontSize":        "10px",
            "fontWeight":      "500",
            "textTransform":   "uppercase",
            "letterSpacing":   "0.05em",
            "color":           color,
            "backgroundColor": bg,
            "borderRadius":    RADIUS["pill"],
            "padding":         "3px 8px",
        },
    )


def _doc_type_badge(doc_type: str) -> html.Span:
    """Build a small blue pill badge for the document type.

    Args:
        doc_type: One of 'REC', 'STMT', 'INV', or 'NOTE'.

    Returns:
        html.Span: Styled inline badge element.
    """
    labels = {"REC": "Reçu", "STMT": "Relevé", "INV": "Facture", "NOTE": "Note"}
    return html.Span(
        labels.get(doc_type, doc_type),
        style={
            "fontFamily":      FONTS["mono"],
            "fontSize":        "10px",
            "color":           COLORS["info"],
            "backgroundColor": COLORS["info_bg"],
            "borderRadius":    RADIUS["pill"],
            "padding":         "3px 8px",
        },
    )


def _file_row(file_data: dict, idx: int) -> html.Tr:
    """Build a single table row for one ingested file.

    Args:
        file_data: File record dict from the API (UploadedFileRead schema).
        idx:       Row index used to alternate row background colours.

    Returns:
        html.Tr: Fully styled table row.
    """
    bg       = COLORS["white"] if idx % 2 == 0 else COLORS["paper"]
    tx_count = file_data.get("transaction_count", 0)

    name_cell = html.Td(
        html.Div(
            [
                html.I(
                    className="fa-solid fa-file",
                    style={"color": COLORS["muted"], "marginRight": "8px", "fontSize": "12px"},
                ),
                html.Span(
                    file_data.get("original_filename", "—"),
                    style={"fontFamily": FONTS["sans"], "fontSize": "13px", "color": COLORS["ink"]},
                ),
            ],
            style={"display": "flex", "alignItems": "center"},
        ),
        style={**TABLE_CELL, "backgroundColor": bg},
    )

    tx_display = (
        html.Span(
            f"{tx_count} transaction{'s' if tx_count != 1 else ''}",
            style={"fontFamily": FONTS["mono"], "fontSize": "12px", "color": COLORS["accent"]},
        )
        if tx_count
        else html.Span("—", style={"color": COLORS["placeholder"]})
    )

    date_str = (file_data.get("uploaded_at", "") or "")[:10] or "—"

    return html.Tr([
        name_cell,
        html.Td(_doc_type_badge(file_data.get("doc_type", "")),
                style={**TABLE_CELL, "backgroundColor": bg}),
        html.Td(file_data.get("source_label", "—"),
                style={**TABLE_CELL, "backgroundColor": bg,
                       "fontFamily": FONTS["sans"], "fontSize": "13px", "color": COLORS["muted"]}),
        html.Td(tx_display,  style={**TABLE_CELL, "backgroundColor": bg}),
        html.Td(date_str,
                style={**TABLE_CELL, "backgroundColor": bg,
                       "fontFamily": FONTS["mono"], "fontSize": "12px", "color": COLORS["muted"]}),
        html.Td(_status_badge(file_data.get("ocr_status", "ok")),
                style={**TABLE_CELL, "backgroundColor": bg, "textAlign": "center"}),
    ])


def _files_table(files: list) -> html.Div:
    """Build the complete file registry table.

    Args:
        files: List of file record dicts from the API.

    Returns:
        html.Div: Scrollable table container.
    """
    headers  = ["Fichier", "Type", "Source", "Transactions", "Date", "Statut"]
    header_row = html.Tr([html.Th(h, style=TABLE_HEADER_CELL) for h in headers])

    if files:
        body_rows = [_file_row(f, i) for i, f in enumerate(files)]
    else:
        body_rows = [html.Tr(html.Td(
            "Aucun fichier enregistré.",
            colSpan=6,
            style={**TABLE_CELL, "textAlign": "center", "color": COLORS["muted"], "padding": "32px"},
        ))]

    return html.Div(
        html.Table(
            [html.Thead(header_row), html.Tbody(body_rows)],
            style={"width": "100%", "borderCollapse": "collapse"},
        ),
        style={"overflowX": "auto"},
    )


def _kpi_row(files: list) -> html.Div:
    """Build the four summary KPI cards from the file list.

    Args:
        files: List of file record dicts from the API.

    Returns:
        html.Div: Flex row of four KPI cards.
    """
    total   = len(files)
    tx_sum  = sum(f.get("transaction_count", 0) for f in files)
    ok_cnt  = sum(1 for f in files if f.get("ocr_status") in ("ok", None, ""))
    err_cnt = total - ok_cnt

    kpis = [
        ("fa-solid fa-folder-open",  str(total),   "fichiers importés",      COLORS["info"],    COLORS["info_bg"]),
        ("fa-solid fa-list",         str(tx_sum),  "transactions extraites", COLORS["accent"],  COLORS["accent_light"]),
        ("fa-solid fa-check-circle", str(ok_cnt),  "traités avec succès",    COLORS["ok"],      COLORS["ok_bg"]),
        ("fa-solid fa-xmark-circle", str(err_cnt), "avec avertissements",    COLORS["error"],   COLORS["error_bg"]),
    ]

    cards = [
        html.Div(
            [
                html.Div(
                    html.I(className=icon, style={"fontSize": "20px", "color": color}),
                    style={
                        "width": "44px", "height": "44px", "borderRadius": RADIUS["md"],
                        "backgroundColor": bg,
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "marginBottom": f"{SPACE['sm']}px",
                    },
                ),
                html.Div(value, style={
                    "fontFamily": FONTS["serif"], "fontSize": "28px",
                    "fontWeight": "700", "color": COLORS["ink"], "lineHeight": "1",
                }),
                html.Div(label, style={
                    "fontFamily": FONTS["sans"], "fontSize": "12px",
                    "color": COLORS["muted"], "marginTop": "4px",
                }),
            ],
            style={**CARD, "flex": "1", "minWidth": "140px"},
        )
        for icon, value, label, color, bg in kpis
    ]

    return html.Div(
        cards,
        style={"display": "flex", "gap": f"{SPACE['md']}px", "marginBottom": f"{SPACE['xl']}px"},
    )


def layout() -> html.Div:
    """Render the upload history page (Step 5).

    Fetches the full file registry from the API and renders:
    - Step progress bar
    - Success banner
    - KPI summary row
    - File registry table
    - Navigation buttons

    Returns:
        html.Div: Complete page layout component.
    """
    files = api.get_files()

    success_banner = html.Div(
        [
            html.I(
                className="fa-solid fa-circle-check",
                style={"fontSize": "16px", "color": COLORS["ok"], "marginRight": "10px"},
            ),
            html.Span(
                "Soumission réussie — vos fichiers ont été traités.",
                style={"fontFamily": FONTS["sans"], "fontSize": "13px",
                       "fontWeight": "500", "color": COLORS["ok"]},
            ),
        ],
        style={
            "display":         "flex",
            "alignItems":      "center",
            "backgroundColor": COLORS["ok_bg"],
            "border":          f"1px solid {COLORS['ok']}",
            "borderRadius":    RADIUS["lg"],
            "padding":         f"{SPACE['md']}px {SPACE['lg']}px",
            "marginBottom":    f"{SPACE['xl']}px",
        },
    )

    nav_buttons = html.Div(
        [
            dcc.Link(
                html.Button(
                    [html.I(className="fa-solid fa-cloud-arrow-up", style={"marginRight": "8px"}),
                     "Importer d'autres fichiers"],
                    style=BTN_SECONDARY,
                ),
                href="/upload", style={"textDecoration": "none"},
            ),
            dcc.Link(
                html.Button(
                    [html.I(className="fa-solid fa-chart-bar", style={"marginRight": "8px"}),
                     "Voir le tableau de bord"],
                    style=BTN_PRIMARY,
                ),
                href="/", style={"textDecoration": "none"},
            ),
        ],
        style={"display": "flex", "gap": f"{SPACE['md']}px",
               "marginTop": f"{SPACE['xl']}px", "justifyContent": "flex-end"},
    )

    return html.Div(
        [
            step_bar(current=5),
            html.Div(
                [
                    html.H1("Historique des imports", style=PAGE_TITLE),
                    html.P("Fichiers ingérés et transactions extraites.", style=PAGE_SUBTITLE),
                ],
                style={"marginBottom": f"{SPACE['xl']}px"},
            ),
            success_banner,
            _kpi_row(files),
            html.Div(
                [
                    html.Div("Registre des fichiers", style=SECTION_TITLE),
                    _files_table(files),
                ],
                style=CARD,
            ),
            nav_buttons,
        ],
        style={"maxWidth": "960px"},
    )
