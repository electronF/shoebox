"""
Files — registry of all ingested files with per-file stats and category breakdown.
"""

from dash import html
import frontend.api_client as api
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS,
    CARD, SECTION_TITLE, PAGE_TITLE, PAGE_SUBTITLE,
    TABLE_HEADER_CELL, TABLE_CELL,
)

_FILE_TYPE_CFG = {
    "pdf":   (COLORS["info"],    COLORS["info_bg"],    "PDF"),
    "xlsx":  (COLORS["ok"],      COLORS["ok_bg"],      "XLSX"),
    "txt":   (COLORS["muted"],   COLORS["cream"],      "TXT"),
    "image": (COLORS["gold"],    COLORS["gold_light"], "Image"),
}
_BAR_COLORS = ["#1a4d3e", "#185fa5", "#c8a84b", "#2e6b3e", "#3c3489", "#854f0b", "#b5361c"]


def _kpi_card(icon: str, value: str, label: str, color: str, bg: str) -> html.Div:
    """Compact KPI tile.

    Args:
        icon: Font Awesome class. value: Display value. label: Description.
        color: Icon colour. bg: Background.

    Returns:
        html.Div: Styled KPI card.
    """
    return html.Div([
        html.Div(html.I(className=icon, style={"fontSize": "18px", "color": color}), style={
            "width": "40px", "height": "40px", "borderRadius": RADIUS["md"],
            "backgroundColor": bg, "display": "flex", "alignItems": "center",
            "justifyContent": "center", "marginBottom": f"{SPACE['sm']}px",
        }),
        html.Div(value, style={"fontFamily": FONTS["serif"], "fontSize": "26px",
                               "fontWeight": "700", "color": COLORS["ink"], "lineHeight": "1"}),
        html.Div(label, style={"fontFamily": FONTS["sans"], "fontSize": "12px",
                               "color": COLORS["muted"], "marginTop": "4px"}),
    ], style={**CARD, "flex": "1"})


def _type_badge(file_type: str) -> html.Span:
    """Pill badge for file type.

    Args:
        file_type: One of "pdf", "xlsx", "txt", "image".

    Returns:
        html.Span: Coloured type badge.
    """
    color, bg, label = _FILE_TYPE_CFG.get(file_type, (COLORS["muted"], COLORS["cream"], file_type.upper()))
    return html.Span(label, style={
        "fontFamily": FONTS["mono"], "fontSize": "10px", "fontWeight": "500",
        "color": color, "backgroundColor": bg,
        "borderRadius": RADIUS["sm"], "padding": "3px 8px",
    })


def _ocr_badge(attempted: bool, success: bool) -> html.Span:
    """Status badge derived from OCR flags.

    Args:
        attempted: Whether OCR was run. success: Whether OCR succeeded.

    Returns:
        html.Span: Coloured status badge.
    """
    if not attempted:
        color, bg, label = COLORS["muted"],   COLORS["cream"],      "Non-OCR"
    elif success:
        color, bg, label = COLORS["ok"],      COLORS["ok_bg"],      "OK"
    else:
        color, bg, label = COLORS["error"],   COLORS["error_bg"],   "Erreur"
    return html.Span(label, style={
        "fontFamily": FONTS["mono"], "fontSize": "10px",
        "color": color, "backgroundColor": bg,
        "borderRadius": RADIUS["pill"], "padding": "3px 8px",
    })


def _file_row(f: dict, source_map: dict, idx: int) -> html.Tr:
    """One row in the file registry table.

    Args:
        f:          File dict from the API. source_map: id → label dict. idx: Row index.

    Returns:
        html.Tr: Styled table row.
    """
    bg      = COLORS["white"] if idx % 2 == 0 else COLORS["paper"]
    tx_cnt  = f.get("tx_count", 0)
    amt     = f.get("total_amount", 0)
    src_lbl = source_map.get(f.get("source_id", ""), "—")
    date_s  = str(f.get("uploaded_at", ""))[:10] or "—"
    return html.Tr([
        html.Td(html.Div([
            html.I(className="fa-solid fa-file",
                   style={"color": COLORS["muted"], "marginRight": "8px", "fontSize": "12px"}),
            html.Span(f.get("filename", "—"), style={
                "fontFamily": FONTS["sans"], "fontSize": "13px", "color": COLORS["ink"],
            }),
        ], style={"display": "flex", "alignItems": "center"}), style={**TABLE_CELL, "backgroundColor": bg}),
        html.Td(_type_badge(f.get("file_type", "")), style={**TABLE_CELL, "backgroundColor": bg}),
        html.Td(src_lbl, style={**TABLE_CELL, "backgroundColor": bg,
                                "fontFamily": FONTS["sans"], "fontSize": "13px",
                                "color": COLORS["muted"]}),
        html.Td(
            html.Span(f"{tx_cnt} tx", style={"fontFamily": FONTS["mono"], "fontSize": "12px",
                                              "color": COLORS["accent"]}) if tx_cnt
            else html.Span("—", style={"color": COLORS["placeholder"]}),
            style={**TABLE_CELL, "backgroundColor": bg},
        ),
        html.Td(
            f"${amt:,.2f}" if amt else "—",
            style={**TABLE_CELL, "backgroundColor": bg,
                   "fontFamily": FONTS["mono"], "fontSize": "12px", "color": COLORS["ink"]},
        ),
        html.Td(date_s, style={**TABLE_CELL, "backgroundColor": bg,
                               "fontFamily": FONTS["mono"], "fontSize": "12px",
                               "color": COLORS["muted"]}),
        html.Td(_ocr_badge(f.get("ocr_attempted", False), f.get("ocr_success", False)),
                style={**TABLE_CELL, "backgroundColor": bg, "textAlign": "center"}),
    ])


def _amount_bars(files: list, source_map: dict) -> html.Div:
    """Horizontal bars showing total amount extracted per file.

    Args:
        files:      File dicts from the API.
        source_map: Source id → label dict.

    Returns:
        html.Div: Bar rows, one per file with non-zero amount.
    """
    valued = [(f.get("filename", "?"), f.get("total_amount", 0))
              for f in files if f.get("total_amount", 0) > 0]
    if not valued:
        return html.Div("Aucun montant extrait.", style={
            "color": COLORS["muted"], "fontFamily": FONTS["sans"], "fontSize": "13px",
        })
    max_amt = max(amt for _, amt in valued) or 1
    rows = []
    for i, (name, amt) in enumerate(sorted(valued, key=lambda x: -x[1])):
        color = _BAR_COLORS[i % len(_BAR_COLORS)]
        rows.append(html.Div([
            html.Div(name[:30], style={"fontFamily": FONTS["sans"], "fontSize": "12px",
                                       "color": COLORS["ink"], "width": "180px", "flexShrink": "0",
                                       "overflow": "hidden", "textOverflow": "ellipsis",
                                       "whiteSpace": "nowrap"}),
            html.Div(html.Div(style={
                "height": "6px", "borderRadius": "3px", "backgroundColor": color,
                "width": f"{amt/max_amt*100:.0f}%", "minWidth": "4px",
            }), style={"flex": "1", "backgroundColor": COLORS["border_light"],
                       "borderRadius": "3px", "height": "6px", "overflow": "hidden"}),
            html.Div(f"${amt:,.2f}", style={"fontFamily": FONTS["mono"], "fontSize": "12px",
                                             "color": COLORS["ink"], "width": "80px",
                                             "textAlign": "right", "flexShrink": "0"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "12px",
                  "marginBottom": f"{SPACE['sm']}px"}))
    return html.Div(rows)


def _cat_badges(cats: list) -> html.Div:
    """Inline badge list for unique categories.

    Args:
        cats: List of category name strings.

    Returns:
        html.Div: Wrapping flex row of pill badges.
    """
    return html.Div([
        html.Span(c[:20], style={
            "fontFamily": FONTS["mono"], "fontSize": "10px",
            "color": COLORS["info"], "backgroundColor": COLORS["info_bg"],
            "borderRadius": RADIUS["pill"], "padding": "2px 8px",
            "marginRight": "4px", "marginBottom": "4px",
        })
        for c in cats[:5]
    ], style={"display": "flex", "flexWrap": "wrap"})


def layout() -> html.Div:
    """Renders the file registry page.

    Returns:
        html.Div: Full page layout with KPIs, file table, amount bars, and category breakdown.
    """
    files      = api.get_files()
    sources    = api.get_sources()
    tx_data    = api.get_transactions(size=200)
    txs        = tx_data.get("items", []) if isinstance(tx_data, dict) else []
    source_map = {s.get("id", ""): s.get("label", "?") for s in sources}

    total_files = len(files)
    total_txs   = sum(f.get("tx_count", 0) for f in files)
    total_amt   = sum(f.get("total_amount", 0) for f in files)

    kpi_row = html.Div([
        _kpi_card("fa-solid fa-folder-open", str(total_files), "fichiers traités",
                  COLORS["info"], COLORS["info_bg"]),
        _kpi_card("fa-solid fa-list", str(total_txs), "transactions extraites",
                  COLORS["accent"], COLORS["accent_light"]),
        _kpi_card("fa-solid fa-dollar-sign", f"${total_amt:,.2f}", "montant total extrait",
                  COLORS["gold"], COLORS["gold_light"]),
    ], style={"display": "flex", "gap": f"{SPACE['md']}px", "marginBottom": f"{SPACE['xl']}px"})

    rows = ([_file_row(f, source_map, i) for i, f in enumerate(files)] if files else [
        html.Tr(html.Td(
            "Aucun fichier enregistré. Utilisez l'import pour commencer.",
            colSpan=7,
            style={**TABLE_CELL, "textAlign": "center", "color": COLORS["muted"], "padding": "32px"},
        ))
    ])
    registry_card = html.Div([
        html.Div("Registre des fichiers reçus", style=SECTION_TITLE),
        html.Div(html.Table([
            html.Thead(html.Tr([html.Th(h, style=TABLE_HEADER_CELL)
                                for h in ["Fichier", "Type", "Source", "Txns",
                                           "Montant", "Date", "OCR"]])),
            html.Tbody(rows),
        ], style={"width": "100%", "borderCollapse": "collapse"}), style={"overflowX": "auto"}),
    ], style={**CARD, "marginBottom": f"{SPACE['md']}px"})

    bars_card = html.Div([
        html.Div("Dépenses par fichier source — montant extrait", style=SECTION_TITLE),
        _amount_bars(files, source_map),
    ], style={**CARD, "marginBottom": f"{SPACE['md']}px"})

    # Per-file categories from transactions
    cats_by_file: dict[str, set] = {}
    for tx in txs:
        fid = tx.get("file_id")
        cat = tx.get("category")
        if fid and cat:
            cats_by_file.setdefault(fid, set()).add(cat)

    cat_rows = []
    for i, f in enumerate(files):
        bg   = COLORS["white"] if i % 2 == 0 else COLORS["paper"]
        cats = sorted(cats_by_file.get(f.get("id", ""), set()))
        cat_rows.append(html.Tr([
            html.Td(f.get("filename", "—")[:35], style={**TABLE_CELL, "backgroundColor": bg}),
            html.Td(_cat_badges(cats) if cats else html.Span(
                "—", style={"color": COLORS["placeholder"]}),
                style={**TABLE_CELL, "backgroundColor": bg}),
            html.Td(f"${f.get('total_amount', 0):,.2f}", style={
                **TABLE_CELL, "backgroundColor": bg,
                "fontFamily": FONTS["mono"], "fontSize": "12px", "textAlign": "right",
            }),
        ]))

    cats_card = html.Div([
        html.Div("Catégories par fichier", style=SECTION_TITLE),
        html.Div(html.Table([
            html.Thead(html.Tr([html.Th(h, style=TABLE_HEADER_CELL)
                                for h in ["Fichier", "Catégories détectées", "Total extrait"]])),
            html.Tbody(cat_rows or [html.Tr(html.Td(
                "Aucune donnée.", colSpan=3,
                style={**TABLE_CELL, "textAlign": "center", "color": COLORS["muted"], "padding": "32px"},
            ))]),
        ], style={"width": "100%", "borderCollapse": "collapse"}), style={"overflowX": "auto"}),
    ], style=CARD)

    return html.Div([
        html.Div([
            html.H1("Fichiers", style=PAGE_TITLE),
            html.P("Registre de tous les fichiers importés.", style=PAGE_SUBTITLE),
        ], style={"marginBottom": f"{SPACE['xl']}px"}),
        kpi_row, registry_card, bars_card, cats_card,
    ], style={"maxWidth": "1100px"})
