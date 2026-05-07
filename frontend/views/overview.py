"""
Overview dashboard — top-level financial summary.

KPI row, horizontal category breakdown, receipts panel,
monthly chart, and three-column action/alert section.
"""

from collections import Counter

from dash import dcc, html
import plotly.graph_objects as go

import frontend.api_client as api
from frontend.theme import COLORS, FONTS, SPACE, RADIUS, CARD, SECTION_TITLE, PAGE_TITLE, PAGE_SUBTITLE

_CAT_COLORS = ["#1a4d3e", "#c8a84b", "#185fa5", "#854f0b", "#3c3489", "#2e6b3e", "#b5361c", "#6b6557"]

_MONTHS_FR = {
    "01": "Jan", "02": "Fév", "03": "Mar", "04": "Avr",
    "05": "Mai", "06": "Juin", "07": "Juil", "08": "Août",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Déc",
}

_ROW    = {"display": "flex", "alignItems": "center", "justifyContent": "space-between"}
_MONO_SM = {"fontFamily": FONTS["mono"], "fontSize": "12px", "color": COLORS["ink"], "fontWeight": "500"}
_BODY_SM = {"fontFamily": FONTS["sans"], "fontSize": "12px", "color": COLORS["ink"]}
_PILL   = {
    "borderRadius": RADIUS["pill"], "padding": "2px 8px",
    "fontSize": "10px", "fontWeight": "600", "fontFamily": FONTS["mono"],
    "whiteSpace": "nowrap", "flexShrink": "0",
}


def _kpi_card(icon: str, value: str, label: str, sub: str = "",
              color: str = COLORS["accent"], bg: str = COLORS["accent_light"]) -> html.Div:
    """Compact KPI tile.

    Args:
        icon: Font Awesome class. value: Display value. label: Description.
        sub: Optional annotation. color: Icon colour. bg: Icon background.

    Returns:
        html.Div: Styled KPI card.
    """
    return html.Div([
        html.Div(html.I(className=icon, style={"fontSize": "16px", "color": color}), style={
            "width": "36px", "height": "36px", "borderRadius": RADIUS["md"], "backgroundColor": bg,
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "marginBottom": f"{SPACE['sm']}px",
        }),
        html.Div(value, style={"fontFamily": FONTS["serif"], "fontSize": "24px", "fontWeight": "700",
                               "color": COLORS["ink"], "lineHeight": "1"}),
        html.Div(label, style={"fontFamily": FONTS["sans"], "fontSize": "12px",
                               "color": COLORS["muted"], "marginTop": "4px"}),
        html.Div(sub, style={"fontFamily": FONTS["mono"], "fontSize": "10px",
                             "color": COLORS["placeholder"], "marginTop": "3px"}) if sub else None,
    ], style={**CARD, "flex": "1", "minWidth": "140px"})


def _category_bars(by_category: dict) -> html.Div:
    """Horizontal proportion bars per expense category.

    Args:
        by_category: Dict mapping category name to total amount, sorted descending.

    Returns:
        html.Div: Stacked bars with labels and amounts.
    """
    if not by_category:
        return html.Div("Aucune donnée.", style={**_BODY_SM, "color": COLORS["muted"]})
    max_val = max(by_category.values())
    rows = []
    for i, (cat, amt) in enumerate(list(by_category.items())[:8]):
        color = _CAT_COLORS[i % len(_CAT_COLORS)]
        rows.append(html.Div([
            html.Div([
                html.Div(cat, style={**_BODY_SM, "marginBottom": "4px", "whiteSpace": "nowrap",
                                     "overflow": "hidden", "textOverflow": "ellipsis", "maxWidth": "160px"}),
                html.Div(html.Div(style={
                    "height": "6px", "borderRadius": "3px", "backgroundColor": color,
                    "width": f"{(amt/max_val)*100:.0f}%", "minWidth": "4px",
                }), style={"backgroundColor": COLORS["border_light"], "borderRadius": "3px",
                           "height": "6px", "overflow": "hidden"}),
            ], style={"flex": "1"}),
            html.Div(f"${amt:,.0f}", style={**_MONO_SM, "marginLeft": "12px", "whiteSpace": "nowrap"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "8px",
                  "marginBottom": f"{SPACE['sm']}px"}))
    return html.Div(rows)


def _receipts_panel(transactions: list) -> html.Div:
    """Itemised list of informal (cash) transactions with a total footer.

    Args:
        transactions: Transaction dicts from the API.

    Returns:
        html.Div: Transaction list with total, or empty-state message.
    """
    items = [t for t in transactions if t.get("is_informal") and not t.get("is_personal")][:6]
    if not items:
        return html.Div("Aucun reçu comptant enregistré.",
                        style={**_BODY_SM, "color": COLORS["muted"]})
    sep = {"borderBottom": f"1px solid {COLORS['border_light']}"}
    rows = [html.Div([
        html.Div((t.get("description") or "—")[:32], style={**_BODY_SM, "flex": "1"}),
        html.Div(f"${t.get('amount', 0):,.2f}", style={**_MONO_SM, "color": COLORS["accent"]}),
    ], style={**_ROW, "padding": f"{SPACE['xs']}px 0", **sep}) for t in items]
    total = sum(t.get("amount", 0) for t in items)
    rows.append(html.Div([
        html.Div("Total", style={"fontFamily": FONTS["mono"], "fontSize": "11px",
                                 "textTransform": "uppercase", "color": COLORS["muted"]}),
        html.Div(f"${total:,.2f}", style={**_MONO_SM, "fontSize": "13px", "fontWeight": "700"}),
    ], style={**_ROW, "paddingTop": f"{SPACE['sm']}px", "marginTop": f"{SPACE['xs']}px"}))
    return html.Div(rows)


def _monthly_chart(transactions: list) -> dcc.Graph:
    """Stacked bar chart of monthly expenses broken down by category.

    Args:
        transactions: Transaction dicts from the API.

    Returns:
        dcc.Graph: Plotly stacked bar chart, one bar per month, one segment per category.
    """
    cat_month: dict[str, dict[str, float]] = {}
    for tx in transactions:
        month = (tx.get("date") or "")[:7]
        cat   = tx.get("category") or "Autre"
        amt   = tx.get("amount", 0)
        if month and amt > 0:
            cat_month.setdefault(cat, {})
            cat_month[cat][month] = cat_month[cat].get(month, 0) + amt

    months  = sorted({m for totals in cat_month.values() for m in totals})
    labels  = [_MONTHS_FR.get(m[5:], m[5:]) for m in months]
    cat_tot = {cat: sum(v.values()) for cat, v in cat_month.items()}
    top     = sorted(cat_tot, key=cat_tot.get, reverse=True)[:7]

    traces = [
        go.Bar(
            name=cat, x=labels,
            y=[cat_month[cat].get(m, 0) for m in months],
            marker_color=_CAT_COLORS[i % len(_CAT_COLORS)], marker_line_width=0,
        )
        for i, cat in enumerate(top)
    ]
    fig = go.Figure(traces)
    fig.update_layout(
        barmode="stack",
        plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"],
        margin={"l": 40, "r": 16, "t": 8, "b": 60}, height=240,
        font={"family": FONTS["sans"], "size": 11, "color": COLORS["muted"]},
        xaxis={"showgrid": False, "type": "category"},
        yaxis={"showgrid": True, "gridcolor": COLORS["border_light"],
               "tickprefix": "$", "tickfont": {"size": 10}},
        legend={"orientation": "h", "yanchor": "top", "y": -0.25,
                "font": {"family": FONTS["mono"], "size": 9}},
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "280px"})


def _badge(label: str, color: str, bg: str) -> html.Span:
    return html.Span(label, style={**_PILL, "color": color, "backgroundColor": bg})


def _item_row(badge: html.Span, text: str) -> html.Div:
    return html.Div(
        [badge, html.Span(text[:54], style={**_BODY_SM, "flex": "1", "overflow": "hidden",
                                            "textOverflow": "ellipsis", "whiteSpace": "nowrap"})],
        style={"display": "flex", "alignItems": "center", "gap": "8px",
               "padding": f"{SPACE['xs']}px 0",
               "borderBottom": f"1px solid {COLORS['border_light']}"},
    )


def layout() -> html.Div:
    """Renders the overview dashboard.

    Returns:
        html.Div: Full page layout with KPIs, charts, and action panels.
    """
    summary      = api.get_analytics_summary()
    by_category  = api.get_by_category()
    actions      = api.get_actions()
    sources      = api.get_sources()
    tx_data      = api.get_transactions(size=200)
    transactions = tx_data.get("items", []) if isinstance(tx_data, dict) else []
    all_invoices = api.get_invoices()

    total_biz = summary.get("total_business", 0)
    total_per = summary.get("total_personal", 0)
    refunds   = summary.get("total_refunds", 0)
    tx_count  = summary.get("tx_count", 0)
    flagged   = summary.get("flagged_count", 0)
    pending   = [a for a in actions if a.get("status") != "done"]

    source_chips = [html.Span(s.get("label", "?"), style={
        "fontFamily": FONTS["mono"], "fontSize": "10px", "backgroundColor": COLORS["accent_light"],
        "color": COLORS["accent"], "borderRadius": RADIUS["pill"], "padding": "3px 10px",
    }) for s in sources[:4]]

    header = html.Div([
        html.Div([html.H1("Vue d'ensemble", style=PAGE_TITLE),
                  html.P("Résumé financier · Q1 2025", style=PAGE_SUBTITLE)], style={"flex": "1"}),
        html.Div([
            *source_chips,
            html.Span([html.I(className="fa-solid fa-circle-exclamation",
                              style={"marginRight": "5px"}), f"{len(pending)} à faire"],
                      style={"fontFamily": FONTS["mono"], "fontSize": "10px",
                             "backgroundColor": COLORS["warning_bg"], "color": COLORS["warning"],
                             "borderRadius": RADIUS["pill"], "padding": "3px 10px",
                      }) if pending else None,
        ], style={"display": "flex", "gap": "8px", "alignItems": "center", "flexWrap": "wrap"}),
    ], style={**_ROW, "alignItems": "flex-start", "marginBottom": f"{SPACE['xl']}px"})

    kpi_row = html.Div([
        _kpi_card("fa-solid fa-briefcase", f"${total_biz:,.2f}", "Dépenses pro",
                  sub=f"{tx_count} transactions", color=COLORS["accent"], bg=COLORS["accent_light"]),
        _kpi_card("fa-solid fa-user", f"${total_per:,.2f}", "Dépenses perso",
                  sub="exclues du rapport", color=COLORS["info"], bg=COLORS["info_bg"]),
        _kpi_card("fa-solid fa-rotate-left", f"${refunds:,.2f}", "Remboursements",
                  sub="crédits reçus", color=COLORS["ok"], bg=COLORS["ok_bg"]),
        _kpi_card("fa-solid fa-triangle-exclamation", str(flagged), "À vérifier",
                  sub="transactions signalées", color=COLORS["warning"], bg=COLORS["warning_bg"]),
    ], style={"display": "flex", "gap": f"{SPACE['md']}px", "marginBottom": f"{SPACE['xl']}px"})

    two_col = html.Div([
        html.Div([html.Div("Dépenses par catégorie", style=SECTION_TITLE),
                  _category_bars(by_category)], style={**CARD, "flex": "2"}),
        html.Div([
            html.Div("Reçus comptant", style={**SECTION_TITLE, "marginBottom": "4px", "borderBottom": "none"}),
            html.Div("SHOEBOX", style={"fontFamily": FONTS["mono"], "fontSize": "9px",
                                       "letterSpacing": "0.12em", "color": COLORS["gold"],
                                       "marginBottom": f"{SPACE['md']}px",
                                       "borderBottom": f"1px solid {COLORS['border_light']}",
                                       "paddingBottom": f"{SPACE['xs']}px"}),
            _receipts_panel(transactions),
        ], style={**CARD, "flex": "1"}),
    ], style={"display": "flex", "gap": f"{SPACE['md']}px", "marginBottom": f"{SPACE['md']}px"})

    chart_card = html.Div([
        html.Div("Évolution mensuelle des dépenses", style=SECTION_TITLE),
        _monthly_chart(transactions) if transactions else html.Div("Aucune donnée.", style=_BODY_SM),
    ], style={**CARD, "marginBottom": f"{SPACE['md']}px"})

    # ── ALERTES & ANOMALIES ───────────────────────────────────────────────────
    personal_txs = [t for t in transactions if t.get("is_personal")]
    tx_keys      = [(t.get("date", "")[:10], round(t.get("amount", 0), 2)) for t in transactions]
    dup_keys     = {k for k, cnt in Counter(tx_keys).items() if cnt > 1 and k[0]}
    dup_txs      = [t for t in transactions
                    if (t.get("date", "")[:10], round(t.get("amount", 0), 2)) in dup_keys]

    alert_rows = []
    for t in personal_txs[:3]:
        alert_rows.append(_item_row(
            _badge("Personnel", COLORS["error"], COLORS["error_bg"]),
            (t.get("description") or t.get("ref") or "—"),
        ))
    seen_dups: set = set()
    for t in dup_txs:
        dk = (t.get("date", "")[:10], t.get("amount", 0))
        if dk not in seen_dups and len(seen_dups) < 3:
            seen_dups.add(dk)
            alert_rows.append(_item_row(
                _badge("Doublon?", COLORS["warning"], COLORS["warning_bg"]),
                f"{dk[0]} · ${dk[1]:,.2f}",
            ))

    if not alert_rows:
        alert_rows = [html.Div("Aucune anomalie détectée.",
                               style={**_BODY_SM, "color": COLORS["muted"]})]

    alerts_col = html.Div(
        [html.Div("Alertes & Anomalies", style=SECTION_TITLE), *alert_rows],
        style={**CARD, "flex": "1"},
    )

    # ── À FAIRE — SUIVI FACTURES ──────────────────────────────────────────────
    open_actions = [a for a in actions if a.get("status") == "open"]
    unpaid_invs  = [i for i in all_invoices if i.get("status") in ("unpaid", "overdue")]

    todo_rows = []
    for a in open_actions[:3]:
        todo_rows.append(_item_row(
            _badge("À faire", COLORS["info"], COLORS["info_bg"]),
            a.get("text") or "—",
        ))
    for inv in unpaid_invs[:3]:
        is_late   = inv.get("status") == "overdue"
        inv_color = COLORS["error"]   if is_late else COLORS["warning"]
        inv_bg    = COLORS["error_bg"] if is_late else COLORS["warning_bg"]
        inv_lbl   = "Impayée" if is_late else "En attente"
        todo_rows.append(_item_row(
            _badge(inv_lbl, inv_color, inv_bg),
            f"{inv.get('client', '—')} · ${inv.get('amount', 0):,.0f}",
        ))
    if not todo_rows:
        todo_rows = [html.Div("Aucun élément en attente.",
                              style={**_BODY_SM, "color": COLORS["muted"]})]

    todo_col = html.Div(
        [html.Div("À faire — Suivi factures", style=SECTION_TITLE), *todo_rows],
        style={**CARD, "flex": "1"},
    )

    # ── OPPORTUNITÉS BUSINESS ─────────────────────────────────────────────────
    _OPP = [
        ("upsell",   ["upsell", "motion graphic"],             COLORS["ok"],           COLORS["ok_bg"],           "Upsell"),
        ("prospect", ["prospect", "signage", "nonna"],         COLORS["info"],         COLORS["info_bg"],         "Prospect"),
        ("deduct",   ["deduct", "déduct", "home office"],      COLORS["accent"],       COLORS["accent_light"],    "Déduction"),
        ("optim",    ["netflix", "petco", "personnel", "perso"], COLORS["badge_purple"], COLORS["badge_purple_bg"], "Optimisation"),
    ]

    opp_rows = []
    for action in open_actions:
        txt_low = (action.get("text") or "").lower()
        for _key, kws, color, bg, lbl in _OPP:
            if any(kw in txt_low for kw in kws):
                opp_rows.append(_item_row(_badge(lbl, color, bg), action.get("text") or "—"))
                break

    if total_per > 0:
        opp_rows.append(_item_row(
            _badge("Optimisation", COLORS["badge_purple"], COLORS["badge_purple_bg"]),
            f"${total_per:,.2f} de dépenses perso sur carte pro",
        ))
    if not opp_rows:
        opp_rows = [html.Div("Importez des notes pour obtenir des insights.",
                             style={**_BODY_SM, "color": COLORS["muted"]})]

    opp_col = html.Div(
        [html.Div("Opportunités business", style=SECTION_TITLE), *opp_rows[:5]],
        style={**CARD, "flex": "1"},
    )

    return html.Div([
        header, kpi_row, two_col, chart_card,
        html.Div([alerts_col, todo_col, opp_col],
                 style={"display": "flex", "gap": f"{SPACE['md']}px"}),
    ], style={"maxWidth": "1100px"})
