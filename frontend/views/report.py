"""
Tax deduction report — deductible business expenses by category and transaction.
"""

from dash import html

import frontend.api_client as api
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS,
    CARD, SECTION_TITLE, PAGE_TITLE, PAGE_SUBTITLE,
    TABLE_HEADER_CELL, TABLE_CELL,
)


def _kpi_card(icon: str, value: str, label: str, color: str, bg: str) -> html.Div:
    """Compact KPI tile.

    Args:
        icon:  Font Awesome class string.
        value: Formatted display value.
        label: Descriptive label.
        color: Icon colour.
        bg:    Icon background colour.

    Returns:
        html.Div: Styled KPI card.
    """
    return html.Div([
        html.Div(
            html.I(className=icon, style={"fontSize": "18px", "color": color}),
            style={
                "width": "40px", "height": "40px", "borderRadius": RADIUS["md"],
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
    ], style={**CARD, "flex": "1"})


def _category_row(cat: str, amount: float, total: float, idx: int) -> html.Tr:
    """One row in the category breakdown table with a proportion bar.

    Args:
        cat:    Category name string.
        amount: Total amount for this category.
        total:  Grand total (for percentage calculation).
        idx:    Row index for alternating background.

    Returns:
        html.Tr: Styled table row with proportion bar.
    """
    bg  = COLORS["white"] if idx % 2 == 0 else COLORS["paper"]
    pct = (amount / total * 100) if total else 0
    bar = html.Div(
        html.Div(style={"height": "6px", "borderRadius": "3px",
                        "width": f"{pct:.0f}%", "backgroundColor": COLORS["accent"]}),
        style={"width": "120px", "height": "6px", "backgroundColor": COLORS["border_light"],
               "borderRadius": "3px", "overflow": "hidden"},
    )
    return html.Tr([
        html.Td(cat, style={**TABLE_CELL, "backgroundColor": bg, "fontWeight": "500"}),
        html.Td(
            f"${amount:,.2f}",
            style={**TABLE_CELL, "backgroundColor": bg,
                   "fontFamily": FONTS["mono"], "fontSize": "13px"},
        ),
        html.Td(
            html.Div(
                [bar, html.Span(
                    f"{pct:.0f}%",
                    style={"fontFamily": FONTS["mono"], "fontSize": "11px",
                           "color": COLORS["muted"], "marginLeft": "8px"},
                )],
                style={"display": "flex", "alignItems": "center"},
            ),
            style={**TABLE_CELL, "backgroundColor": bg},
        ),
    ])


def _tx_row(tx: dict, idx: int) -> html.Tr:
    """One row in the deductible transaction table.

    Args:
        tx:  Transaction dict from the API.
        idx: Row index for alternating background.

    Returns:
        html.Tr: Styled table row.
    """
    bg = COLORS["white"] if idx % 2 == 0 else COLORS["paper"]
    return html.Tr([
        html.Td(
            str(tx.get("date", "—"))[:10],
            style={**TABLE_CELL, "backgroundColor": bg,
                   "fontFamily": FONTS["mono"], "fontSize": "12px", "color": COLORS["muted"]},
        ),
        html.Td(tx.get("description", "—")[:55], style={**TABLE_CELL, "backgroundColor": bg}),
        html.Td(
            tx.get("category", "—"),
            style={**TABLE_CELL, "backgroundColor": bg,
                   "fontFamily": FONTS["mono"], "fontSize": "11px", "color": COLORS["muted"]},
        ),
        html.Td(
            f"${tx.get('amount', 0):,.2f}",
            style={**TABLE_CELL, "backgroundColor": bg,
                   "fontFamily": FONTS["mono"], "fontSize": "13px", "textAlign": "right"},
        ),
    ])


def _cat_section(cat: str, txs: list) -> html.Div:
    """Expandable section showing transactions for one category.

    Args:
        cat: Category name string.
        txs: Transaction dicts belonging to this category.

    Returns:
        html.Div: Card with title bar (total) and compact transaction rows.
    """
    total = sum(t.get("amount", 0) for t in txs)
    rows = [html.Div([
        html.Div(str(t.get("date", ""))[:10], style={
            "fontFamily": FONTS["mono"], "fontSize": "11px", "color": COLORS["muted"],
            "flexShrink": "0", "width": "80px",
        }),
        html.Div((t.get("description") or "—")[:50], style={
            "fontFamily": FONTS["sans"], "fontSize": "12px", "color": COLORS["ink"], "flex": "1",
        }),
        html.Div(f"${t.get('amount', 0):,.2f}", style={
            "fontFamily": FONTS["mono"], "fontSize": "12px", "color": COLORS["accent"],
            "fontWeight": "500", "flexShrink": "0",
        }),
    ], style={
        "display": "flex", "alignItems": "center", "gap": "12px",
        "padding": f"{SPACE['xs']}px 0",
        "borderBottom": f"1px solid {COLORS['border_light']}",
    }) for t in txs]
    return html.Div([
        html.Div([
            html.Span(cat, style={
                "fontFamily": FONTS["mono"], "fontSize": "11px", "fontWeight": "500",
                "textTransform": "uppercase", "letterSpacing": "0.06em", "color": COLORS["accent"],
            }),
            html.Span(f"${total:,.2f}", style={
                "fontFamily": FONTS["mono"], "fontSize": "13px",
                "fontWeight": "700", "color": COLORS["ink"],
            }),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "marginBottom": f"{SPACE['sm']}px"}),
        *rows,
    ], style={**CARD, "marginBottom": f"{SPACE['sm']}px",
              "borderLeft": f"3px solid {COLORS['accent']}"})


def layout() -> html.Div:
    """Renders the tax deduction report page.

    Returns:
        html.Div: Full page layout with KPIs, category breakdown, and grouped transaction sections.
    """
    by_cat   = api.get_by_category()
    tx_data  = api.get_transactions(exclude_personal=True, size=200)
    txs      = tx_data.get("items", []) if isinstance(tx_data, dict) else []
    total    = sum(by_cat.values())

    kpi_row = html.Div([
        _kpi_card("fa-solid fa-file-lines", f"${total:,.2f}", "total déductible",
                  COLORS["info"], COLORS["info_bg"]),
        _kpi_card("fa-solid fa-list", str(len(txs)), "transactions d'affaires",
                  COLORS["accent"], COLORS["accent_light"]),
        _kpi_card("fa-solid fa-layer-group", str(len(by_cat)), "catégories actives",
                  COLORS["gold"], COLORS["gold_light"]),
    ], style={"display": "flex", "gap": f"{SPACE['md']}px", "marginBottom": f"{SPACE['xl']}px"})

    cat_rows = [
        _category_row(cat, amt, total, i)
        for i, (cat, amt) in enumerate(by_cat.items())
    ] if by_cat else [
        html.Tr(html.Td(
            "Aucune catégorie disponible.",
            colSpan=3,
            style={**TABLE_CELL, "textAlign": "center", "color": COLORS["muted"], "padding": "32px"},
        ))
    ]
    cat_card = html.Div([
        html.Div("Déductions par catégorie", style=SECTION_TITLE),
        html.Div(
            html.Table([
                html.Thead(html.Tr([
                    html.Th(h, style=TABLE_HEADER_CELL)
                    for h in ["Catégorie", "Montant", "Part du total"]
                ])),
                html.Tbody(cat_rows),
            ], style={"width": "100%", "borderCollapse": "collapse"}),
            style={"overflowX": "auto"},
        ),
    ], style={**CARD, "marginBottom": f"{SPACE['md']}px"})

    tx_rows = [_tx_row(tx, i) for i, tx in enumerate(txs)] if txs else [
        html.Tr(html.Td(
            "Aucune transaction déductible.",
            colSpan=4,
            style={**TABLE_CELL, "textAlign": "center", "color": COLORS["muted"], "padding": "32px"},
        ))
    ]
    tx_card = html.Div([
        html.Div("Détail des transactions déductibles", style=SECTION_TITLE),
        html.Div(
            html.Table([
                html.Thead(html.Tr([
                    html.Th(h, style=TABLE_HEADER_CELL)
                    for h in ["Date", "Description", "Catégorie", "Montant"]
                ])),
                html.Tbody(tx_rows),
            ], style={"width": "100%", "borderCollapse": "collapse"}),
            style={"overflowX": "auto", "maxHeight": "420px", "overflow": "auto"},
        ),
    ], style=CARD)

    # Per-category transaction sections
    txs_by_cat: dict[str, list] = {}
    for tx in txs:
        c = tx.get("category", "Autre")
        txs_by_cat.setdefault(c, []).append(tx)
    cat_sections = [_cat_section(cat, txs_by_cat[cat])
                    for cat in by_cat if cat in txs_by_cat] if by_cat else []

    return html.Div([
        html.Div([
            html.H1("Rapport fiscal", style=PAGE_TITLE),
            html.P("Dépenses déductibles d'impôts — vue comptable.", style=PAGE_SUBTITLE),
        ], style={"marginBottom": f"{SPACE['xl']}px"}),
        kpi_row,
        cat_card,
        html.Div("Détail par catégorie", style={**SECTION_TITLE, "marginBottom": f"{SPACE['md']}px",
                                                 "marginTop": f"{SPACE['xl']}px"}),
        *cat_sections,
        tx_card,
    ], style={"maxWidth": "960px"})
