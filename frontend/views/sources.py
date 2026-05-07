"""
Sources — expense breakdown by payment source with clickable filter chips.

Chip filter updates the transaction table and highlights active chip
via sources_callbacks.py.
"""

from dash import dcc, html
import plotly.graph_objects as go

import frontend.api_client as api
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS,
    CARD, SECTION_TITLE, PAGE_TITLE, PAGE_SUBTITLE,
    TABLE_HEADER_CELL, TABLE_CELL,
)

_SRC_COLORS = ["#1a4d3e", "#185fa5", "#c8a84b", "#854f0b", "#3c3489"]
_SRC_ICONS  = {
    "credit_card": "fa-solid fa-credit-card",
    "cash":        "fa-solid fa-money-bill-wave",
    "personal":    "fa-solid fa-user",
}

_CHIP_BASE = {
    "display": "inline-flex", "alignItems": "center", "gap": "8px",
    "padding": f"{SPACE['sm']}px {SPACE['md']}px",
    "borderRadius": RADIUS["pill"], "cursor": "pointer",
    "marginRight": f"{SPACE['sm']}px", "marginBottom": f"{SPACE['sm']}px",
}
_CHIP_ON  = {**_CHIP_BASE, "backgroundColor": COLORS["accent_light"],
             "border": f"2px solid {COLORS['accent']}"}
_CHIP_OFF = {**_CHIP_BASE, "backgroundColor": COLORS["white"],
             "border": f"1px solid {COLORS['border']}"}


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


def _make_chip(label: str, amount: float, source_id: str,
               color: str, active: bool) -> html.Div:
    """One source filter chip with optional active highlight.

    Args:
        label:     Display label. amount: Total for this source.
        source_id: Pattern-matching index ("all" or source ID).
        color:     Dot colour. active: Whether this chip is currently selected.

    Returns:
        html.Div: Styled clickable chip.
    """
    return html.Div([
        html.Span(style={"width": "8px", "height": "8px", "borderRadius": "50%",
                         "backgroundColor": color, "flexShrink": "0"}),
        html.Span(label, style={"fontFamily": FONTS["sans"], "fontSize": "13px",
                                "fontWeight": "600" if active else "500",
                                "color": COLORS["accent"] if active else COLORS["ink"]}),
        html.Span(f"${amount:,.2f}", style={"fontFamily": FONTS["mono"], "fontSize": "12px",
                                             "color": COLORS["accent"] if active else COLORS["muted"],
                                             "marginLeft": "4px"}),
    ], id={"type": "src-chip", "index": source_id}, n_clicks=0,
       style=_CHIP_ON if active else _CHIP_OFF)


def make_chips(sources: list, by_src: dict, total: float, active_id: str) -> list:
    """Builds the full chip list with active state applied.

    Args:
        sources:   Source dicts from the API.
        by_src:    Dict mapping source label to total amount.
        total:     Grand total for the "Toutes sources" chip.
        active_id: Currently selected source ID (or "all").

    Returns:
        list: Chip components ready to render.
    """
    all_chip = _make_chip("Toutes sources", total, "all",
                          COLORS["muted"], active_id == "all")
    src_chips = [
        _make_chip(s.get("label", "?"), by_src.get(s.get("label", ""), 0),
                   s.get("id", ""), _SRC_COLORS[i % len(_SRC_COLORS)],
                   active_id == s.get("id", ""))
        for i, s in enumerate(sources)
    ]
    return [all_chip, *src_chips]


def _donut(by_src: dict) -> dcc.Graph:
    """Donut chart showing expense share per source.

    Args:
        by_src: Dict mapping source label to total amount.

    Returns:
        dcc.Graph: Plotly donut chart component.
    """
    labels = list(by_src.keys())
    values = list(by_src.values())
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker={"colors": _SRC_COLORS[:len(labels)]},
        textinfo="label+percent",
        textfont={"family": FONTS["sans"], "size": 11},
        hovertemplate="%{label}: $%{value:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=COLORS["white"],
        margin={"l": 0, "r": 0, "t": 8, "b": 8},
        height=260,
        showlegend=False,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False},
                     style={"height": "260px"})


def _src_bars(by_src: dict) -> html.Div:
    """Horizontal proportion bars — one per source.

    Args:
        by_src: Dict mapping source label to total amount.

    Returns:
        html.Div: Stacked bar rows sorted descending by amount.
    """
    if not by_src:
        return html.Div("Aucune donnée.", style={"color": COLORS["muted"],
                                                  "fontFamily": FONTS["sans"], "fontSize": "13px"})
    grand = sum(by_src.values()) or 1
    rows  = []
    for i, (label, amt) in enumerate(sorted(by_src.items(), key=lambda x: -x[1])):
        color = _SRC_COLORS[i % len(_SRC_COLORS)]
        pct   = amt / grand * 100
        rows.append(html.Div([
            html.Div(label, style={"fontFamily": FONTS["sans"], "fontSize": "12px",
                                   "color": COLORS["ink"], "width": "160px", "flexShrink": "0",
                                   "overflow": "hidden", "textOverflow": "ellipsis",
                                   "whiteSpace": "nowrap"}),
            html.Div(html.Div(style={
                "height": "6px", "borderRadius": "3px", "backgroundColor": color,
                "width": f"{pct:.0f}%", "minWidth": "4px",
            }), style={"flex": "1", "backgroundColor": COLORS["border_light"],
                       "borderRadius": "3px", "height": "6px", "overflow": "hidden"}),
            html.Div(f"${amt:,.2f}", style={"fontFamily": FONTS["mono"], "fontSize": "12px",
                                             "color": COLORS["ink"], "width": "80px",
                                             "textAlign": "right", "flexShrink": "0"}),
            html.Div(f"{pct:.0f}%", style={"fontFamily": FONTS["mono"], "fontSize": "11px",
                                             "color": COLORS["muted"], "width": "36px",
                                             "textAlign": "right", "flexShrink": "0"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "12px",
                  "marginBottom": f"{SPACE['sm']}px"}))
    return html.Div(rows)


def _build_tx_table(txs: list, source_map: dict) -> html.Div:
    """Transaction table filterable by source.

    Args:
        txs:        Transaction dicts from the API.
        source_map: Dict mapping source_id → source dict (with label, source_type).

    Returns:
        html.Div: Scrollable transaction table or empty-state message.
    """
    def _row(tx: dict, idx: int) -> html.Tr:
        bg      = COLORS["white"] if idx % 2 == 0 else COLORS["paper"]
        src     = source_map.get(tx.get("source_id", ""), {})
        src_lbl = src.get("label", tx.get("source_id", "—"))
        src_i   = next((
            _SRC_COLORS[i % len(_SRC_COLORS)]
            for i, sid in enumerate(source_map.keys())
            if sid == tx.get("source_id")
        ), COLORS["muted"])
        personal = tx.get("is_personal", False)
        amt      = tx.get("amount", 0)
        cat_badge = html.Span(
            (tx.get("category") or "—")[:18],
            style={"fontFamily": FONTS["mono"], "fontSize": "10px",
                   "color": COLORS["muted"], "backgroundColor": COLORS["cream"],
                   "borderRadius": RADIUS["pill"], "padding": "2px 8px"},
        )
        return html.Tr([
            html.Td(str(tx.get("date", "—"))[:10], style={
                **TABLE_CELL, "backgroundColor": bg,
                "fontFamily": FONTS["mono"], "fontSize": "12px", "color": COLORS["muted"],
            }),
            html.Td((tx.get("description") or "—")[:50], style={**TABLE_CELL, "backgroundColor": bg}),
            html.Td(cat_badge, style={**TABLE_CELL, "backgroundColor": bg}),
            html.Td(html.Div([
                html.Span(style={"width": "8px", "height": "8px", "borderRadius": "50%",
                                 "backgroundColor": src_i, "flexShrink": "0"}),
                html.Span(src_lbl, style={"fontFamily": FONTS["sans"], "fontSize": "12px",
                                          "color": COLORS["ink"]}),
            ], style={"display": "flex", "alignItems": "center", "gap": "6px"}),
                style={**TABLE_CELL, "backgroundColor": bg}),
            html.Td(f"${amt:,.2f}", style={
                **TABLE_CELL, "backgroundColor": bg,
                "fontFamily": FONTS["mono"], "fontSize": "13px", "textAlign": "right",
                "color": COLORS["error"] if personal else (COLORS["ok"] if amt < 0 else COLORS["ink"]),
            }),
        ])

    if not txs:
        return html.Div("Aucune transaction.", style={"color": COLORS["muted"],
                                                      "fontFamily": FONTS["sans"], "fontSize": "13px"})
    return html.Div(
        html.Table([
            html.Thead(html.Tr([html.Th(h, style=TABLE_HEADER_CELL)
                                for h in ["Date", "Description", "Catégorie", "Source", "Montant"]])),
            html.Tbody([_row(tx, i) for i, tx in enumerate(txs)]),
        ], style={"width": "100%", "borderCollapse": "collapse"}),
        style={"overflowX": "auto", "maxHeight": "480px", "overflow": "auto"},
    )


def layout() -> html.Div:
    """Renders the payment sources breakdown page.

    Returns:
        html.Div: Full page with KPIs, filter chips, donut+bars, and transaction table.
    """
    sources    = api.get_sources()
    by_src     = api.get_by_source()
    tx_data    = api.get_transactions(size=200)
    txs        = tx_data.get("items", []) if isinstance(tx_data, dict) else []
    total      = sum(by_src.values())
    source_map = {s.get("id", ""): s for s in sources}

    kpi_row = html.Div([
        _kpi_card("fa-solid fa-wallet", str(len(sources)), "sources de paiement",
                  COLORS["accent"], COLORS["accent_light"]),
        _kpi_card("fa-solid fa-dollar-sign", f"${total:,.2f}", "total toutes sources",
                  COLORS["gold"], COLORS["gold_light"]),
        _kpi_card("fa-solid fa-list", str(len(txs)), "transactions affichées",
                  COLORS["info"], COLORS["info_bg"]),
    ], style={"display": "flex", "gap": f"{SPACE['md']}px", "marginBottom": f"{SPACE['xl']}px"})

    chip_bar = html.Div([
        html.Div("FILTRER PAR SOURCE", style={
            "fontFamily": FONTS["mono"], "fontSize": "10px", "letterSpacing": "0.1em",
            "color": COLORS["muted"], "textTransform": "uppercase",
            "marginBottom": f"{SPACE['xs']}px",
        }),
        html.Div(
            id="sources-chip-bar",
            children=make_chips(sources, by_src, total, "all"),
        ),
    ], style={"marginBottom": f"{SPACE['lg']}px"})

    donut_card = html.Div([
        html.Div("Répartition par source", style=SECTION_TITLE),
        _donut(by_src) if by_src else html.Div("Aucune donnée.", style={
            "color": COLORS["muted"], "fontFamily": FONTS["sans"], "fontSize": "13px",
        }),
    ], style={**CARD, "flex": "1", "minWidth": "260px"})

    bars_card = html.Div([
        html.Div("Dépenses par source", style=SECTION_TITLE),
        _src_bars(by_src),
    ], style={**CARD, "flex": "2", "minWidth": "300px"})

    viz_row = html.Div(
        [donut_card, bars_card],
        style={"display": "flex", "gap": f"{SPACE['md']}px",
               "flexWrap": "wrap", "marginBottom": f"{SPACE['md']}px"},
    )

    tx_card = html.Div([
        html.Div("Transactions par source", style=SECTION_TITLE),
        html.Div(id="sources-tx-content", children=_build_tx_table(txs, source_map)),
    ], style=CARD)

    return html.Div([
        html.Div([
            html.H1("Sources de paiement", style=PAGE_TITLE),
            html.P("Répartition des dépenses par source.", style=PAGE_SUBTITLE),
        ], style={"marginBottom": f"{SPACE['xl']}px"}),
        kpi_row,
        chip_bar,
        viz_row,
        tx_card,
    ], style={"maxWidth": "1100px"})
