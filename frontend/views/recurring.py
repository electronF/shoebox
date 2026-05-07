"""
Recurring — detected patterns with month breakdown, Q forecast detail, and trend chart.
"""

from dash import dcc, html
import plotly.graph_objects as go

import frontend.api_client as api
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS,
    CARD, SECTION_TITLE, PAGE_TITLE, PAGE_SUBTITLE,
    TABLE_HEADER_CELL, TABLE_CELL,
)

_MONTHS_FR = {
    "01": "JAN", "02": "FÉV", "03": "MAR", "04": "AVR",
    "05": "MAI", "06": "JUI", "07": "JUL", "08": "AOÛ",
    "09": "SEP", "10": "OCT", "11": "NOV", "12": "DÉC",
}


def _kpi_card(value: str, label: str, sub: str, color: str = COLORS["ink"]) -> html.Div:
    """KPI tile: uppercase label, large value, small sub-label.

    Args:
        value: Formatted display value. label: Uppercase heading. sub: Sub-label. color: Value colour.

    Returns:
        html.Div: Styled KPI tile.
    """
    return html.Div([
        html.Div(label, style={"fontFamily": FONTS["mono"], "fontSize": "10px",
                               "letterSpacing": "0.08em", "color": COLORS["muted"],
                               "textTransform": "uppercase", "marginBottom": "6px"}),
        html.Div(value, style={"fontFamily": FONTS["serif"], "fontSize": "26px",
                               "fontWeight": "700", "color": color, "lineHeight": "1"}),
        html.Div(sub, style={"fontFamily": FONTS["sans"], "fontSize": "11px",
                             "color": COLORS["muted"], "marginTop": "4px"}),
    ], style={**CARD, "flex": "1"})


def _freq_badge(freq: str) -> html.Span:
    """Frequency pill badge.

    Args:
        freq: Pattern frequency string.

    Returns:
        html.Span: Coloured badge.
    """
    is_fixed = freq == "monthly"
    return html.Span("Mensuel" if is_fixed else "Variable", style={
        "fontFamily": FONTS["mono"], "fontSize": "10px",
        "color": COLORS["ok"] if is_fixed else COLORS["warning"],
        "backgroundColor": COLORS["ok_bg"] if is_fixed else COLORS["warning_bg"],
        "borderRadius": RADIUS["pill"], "padding": "3px 8px",
    })


def _verdict(p: dict) -> tuple:
    """Compute verdict (label, color, bg) for a pattern.

    Args:
        p: Pattern dict from the API.

    Returns:
        Tuple of (label, text_color, bg_color).
    """
    freq, conf = p.get("frequency", ""), p.get("confidence", 0)
    if freq == "monthly" and conf >= 0.75:
        return "Garder",   COLORS["ok"],      COLORS["ok_bg"]
    if freq == "monthly":
        return "Évaluer",  COLORS["warning"],  COLORS["warning_bg"]
    if conf >= 0.5:
        return "Vérifier", COLORS["gold"],     COLORS["gold_light"]
    return "Déplacer",     COLORS["error"],    COLORS["error_bg"]


def _pattern_row(p: dict, show_months: list, idx: int) -> html.Tr:
    """Month-by-month pattern row with verdict badge.

    Args:
        p: Pattern dict. show_months: Ordered "YYYY-MM" keys to display. idx: Row index.

    Returns:
        html.Tr: Styled table row.
    """
    bg, ma = COLORS["white"] if idx % 2 == 0 else COLORS["paper"], p.get("monthly_amounts", {})
    vlbl, vcol, vbg = _verdict(p)
    month_cells = [html.Td(
        f"${ma[m]:,.2f}" if m in ma else "—",
        style={**TABLE_CELL, "backgroundColor": bg, "fontFamily": FONTS["mono"],
               "fontSize": "13px", "fontWeight": "600" if m in ma else "400",
               "color": COLORS["ink"] if m in ma else COLORS["placeholder"]},
    ) for m in show_months]
    return html.Tr([
        html.Td(p.get("display_name", "—")[:32], style={**TABLE_CELL, "backgroundColor": bg}),
        html.Td(_freq_badge(p.get("frequency", "")), style={**TABLE_CELL, "backgroundColor": bg}),
        *month_cells,
        html.Td(f"${p.get('avg_amount', 0):,.2f}", style={
            **TABLE_CELL, "backgroundColor": bg,
            "fontFamily": FONTS["mono"], "fontSize": "13px", "fontWeight": "600"}),
        html.Td(html.Span(vlbl, style={
            "fontFamily": FONTS["mono"], "fontSize": "10px", "color": vcol,
            "backgroundColor": vbg, "borderRadius": RADIUS["pill"], "padding": "3px 10px",
        }), style={**TABLE_CELL, "backgroundColor": bg}),
    ])


def _forecast_mini(month_key: str, entries: list) -> html.Div:
    """Mini forecast card for one month.

    Args:
        month_key: "YYYY-MM" string. entries: Forecast entries for that month.

    Returns:
        html.Div: Styled mini card.
    """
    total = sum(e.get("predicted_amt", 0) for e in entries)
    lbl   = _MONTHS_FR.get(month_key[5:], month_key[5:]) if len(month_key) >= 7 else month_key
    return html.Div([
        html.Div(f"{lbl} (Prévu)", style={"fontFamily": FONTS["mono"], "fontSize": "10px",
                                          "color": COLORS["muted"], "letterSpacing": "0.08em",
                                          "textTransform": "uppercase", "marginBottom": "4px"}),
        html.Div(f"${total:,.0f}", style={"fontFamily": FONTS["serif"], "fontSize": "26px",
                                          "fontWeight": "700", "color": COLORS["ink"]}),
        html.Div(f"{len(entries)} postes", style={"fontFamily": FONTS["sans"],
                                                   "fontSize": "11px", "color": COLORS["muted"],
                                                   "marginTop": "2px"}),
    ], style={**CARD, "flex": "1", "textAlign": "center"})


def _forecast_detail(forecast: list, patterns: list, fc_months: list) -> html.Div:
    """Per-pattern forecast table with confidence dots and monthly totals row.

    Args:
        forecast: Forecast entry dicts. patterns: Pattern dicts for confidence lookup.
        fc_months: Ordered "YYYY-MM" forecast month keys.

    Returns:
        html.Div: Forecast detail table.
    """
    by_name: dict = {}
    for e in forecast:
        by_name.setdefault(e.get("display_name", ""), {})[e.get("month", "")] = e.get("predicted_amt", 0)
    conf_map = {p.get("display_name", ""): p.get("confidence", 0) for p in patterns}
    month_labels = [_MONTHS_FR.get(m[5:], m[5:]) for m in fc_months]

    def _dot(name: str) -> html.Div:
        c = conf_map.get(name, 0)
        col = COLORS["ok"] if c >= 0.75 else (COLORS["warning"] if c >= 0.5 else COLORS["error"])
        lbl = "Confiance élevée" if c >= 0.75 else ("Confiance moyenne" if c >= 0.5 else "Incertain")
        return html.Div([
            html.Span(style={"display": "inline-block", "width": "7px", "height": "7px",
                             "borderRadius": "50%", "backgroundColor": col, "marginRight": "5px",
                             "flexShrink": "0"}),
            html.Span(lbl, style={"fontFamily": FONTS["sans"], "fontSize": "11px",
                                  "color": COLORS["muted"]}),
        ], style={"display": "flex", "alignItems": "center"})

    rows, totals = [], {m: 0.0 for m in fc_months}
    for name, amounts in by_name.items():
        for m, v in amounts.items():
            if m in totals:
                totals[m] += v
        rows.append(html.Tr([
            html.Td(name[:22], style={**TABLE_CELL, "fontFamily": FONTS["sans"],
                                      "fontSize": "13px", "fontWeight": "600"}),
            html.Td(_dot(name), style=TABLE_CELL),
            *[html.Td(f"${amounts.get(m, 0):,.2f}" if amounts.get(m) else "—",
                      style={**TABLE_CELL, "fontFamily": FONTS["mono"], "fontSize": "13px",
                             "color": COLORS["ink"] if amounts.get(m) else COLORS["placeholder"]},
                      ) for m in fc_months],
        ]))
    rows.append(html.Tr([
        html.Td("Total prévu", style={**TABLE_CELL, "fontFamily": FONTS["mono"], "fontWeight": "700"}),
        html.Td("", style=TABLE_CELL),
        *[html.Td(f"${totals[m]:,.0f}", style={**TABLE_CELL, "fontFamily": FONTS["mono"],
                                                "fontWeight": "700", "color": COLORS["accent"]},
                  ) for m in fc_months],
    ], style={"borderTop": f"2px solid {COLORS['border']}"}))

    return html.Div(html.Table([
        html.Thead(html.Tr([html.Th(h, style=TABLE_HEADER_CELL) for h in ["Poste", ""] + month_labels])),
        html.Tbody(rows),
    ], style={"width": "100%", "borderCollapse": "collapse"}), style={"overflowX": "auto"})


def _trend_chart(by_month: dict, forecast: list, patterns: list) -> dcc.Graph:
    """Line chart: actual monthly total, forecast projection, and fixed-only baseline.

    Args:
        by_month: "YYYY-MM" → amount dict. forecast: Forecast entries. patterns: Detected patterns.

    Returns:
        dcc.Graph: Plotly multi-line chart.
    """
    hist  = sorted(by_month.keys())
    hvals = [by_month[m] for m in hist]
    fc: dict = {}
    for e in forecast:
        m = e.get("month", "")
        fc[m] = fc.get(m, 0) + e.get("predicted_amt", 0)
    fc_months = sorted(fc.keys())
    fixed = sum(p.get("avg_amount", 0) for p in patterns if p.get("frequency") == "monthly")
    all_m = hist + [m for m in fc_months if m not in hist]
    lbl = lambda ms: [_MONTHS_FR.get(m[5:], m[5:]) for m in ms]
    fig = go.Figure([
        go.Scatter(x=lbl(hist), y=hvals, name="Dépenses réelles",
                   mode="lines+markers", line={"color": COLORS["accent"], "width": 2},
                   marker={"size": 6}),
        go.Scatter(x=lbl(fc_months), y=[fc[m] for m in fc_months], name="Prévision",
                   mode="lines+markers", line={"color": COLORS["info"], "width": 2, "dash": "dash"},
                   marker={"size": 7, "symbol": "circle-open"}),
        go.Scatter(x=lbl(all_m), y=[fixed] * len(all_m), name="Fixes seulement",
                   mode="lines", line={"color": COLORS["ok"], "width": 1.5, "dash": "dot"}),
    ])
    fig.update_layout(
        plot_bgcolor=COLORS["white"], paper_bgcolor=COLORS["white"],
        margin={"l": 40, "r": 16, "t": 8, "b": 48}, height=230,
        font={"family": FONTS["sans"], "size": 11, "color": COLORS["muted"]},
        xaxis={"showgrid": False, "type": "category"},
        yaxis={"showgrid": True, "gridcolor": COLORS["border_light"],
               "tickprefix": "$", "tickfont": {"size": 10}},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.35,
                "font": {"family": FONTS["mono"], "size": 10}},
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "270px"})


def layout() -> html.Div:
    """Renders the recurring expense detection and forecast page.

    Returns:
        html.Div: Full page with KPIs, month-by-month table, forecast detail, and trend chart.
    """
    data     = api.get_recurring()
    patterns = data.get("patterns", [])
    forecast = data.get("forecast", [])
    by_month = api.get_by_month()

    fixed_total = sum(p.get("avg_amount", 0) for p in patterns if p.get("frequency") == "monthly")
    var_total   = sum(p.get("avg_amount", 0) for p in patterns if p.get("frequency") != "monthly")
    to_cut      = [p for p in patterns if _verdict(p)[0] in ("Évaluer", "Vérifier", "Déplacer")]
    fc_total    = sum(e.get("predicted_amt", 0) for e in forecast)
    cut_names   = " + ".join(p.get("display_name", "?")[:12] for p in to_cut[:2])

    kpi_row = html.Div([
        _kpi_card(f"${fixed_total:,.2f}", "Charges fixes/mois",
                  f"{len(patterns)} abonnements détectés"),
        _kpi_card(f"${var_total:,.2f}", "Charges variables moy.", "Moyenne Q1"),
        _kpi_card(f"${fc_total:,.0f}", "Projection Q total",
                  "Basé sur tendance Q1", COLORS["info"]),
        _kpi_card(f"${sum(p.get('avg_amount',0)*12 for p in to_cut):,.0f}/an",
                  "Économies si coupes", cut_names or "—", COLORS["ok"]),
    ], style={"display": "flex", "gap": f"{SPACE['md']}px", "marginBottom": f"{SPACE['xl']}px"})

    all_months  = sorted({m for p in patterns for m in p.get("monthly_amounts", {})})
    show_months = all_months[-3:] if len(all_months) >= 3 else all_months
    headers = (["Service", "Fréq."] +
               [_MONTHS_FR.get(m[5:], m[5:]) for m in show_months] +
               ["Moy/mois", "Statut"])
    body = ([_pattern_row(p, show_months, i) for i, p in enumerate(patterns)] if patterns else [
        html.Tr(html.Td(
            "Aucun pattern détecté. Importez plusieurs relevés pour que l'analyse fonctionne.",
            colSpan=len(headers),
            style={**TABLE_CELL, "textAlign": "center", "color": COLORS["muted"], "padding": "32px"},
        ))
    ])
    patterns_card = html.Div([
        html.Div("Abonnements récurrents détectés — présence mensuelle confirmée",
                 style=SECTION_TITLE),
        html.Div(html.Table([
            html.Thead(html.Tr([html.Th(h, style=TABLE_HEADER_CELL) for h in headers])),
            html.Tbody(body),
        ], style={"width": "100%", "borderCollapse": "collapse"}), style={"overflowX": "auto"}),
    ], style={**CARD, "marginBottom": f"{SPACE['md']}px"})

    fc_by_month: dict = {}
    for e in forecast:
        fc_by_month.setdefault(e.get("month", ""), []).append(e)
    fc_sorted = sorted(fc_by_month.keys())
    fc_mini   = [_forecast_mini(m, fc_by_month[m]) for m in fc_sorted[:3]]
    fc_card = html.Div([
        html.Div("Prévision des dépenses — 3 prochains mois", style=SECTION_TITLE),
        html.Div(fc_mini if fc_mini else [html.Div("Aucune prévision.", style={
            "color": COLORS["muted"], "fontFamily": FONTS["sans"], "fontSize": "13px"})],
                 style={"display": "flex", "gap": f"{SPACE['md']}px",
                        "marginBottom": f"{SPACE['md']}px"}),
        _forecast_detail(forecast, patterns, fc_sorted[:3]) if forecast else None,
    ], style={**CARD, "marginBottom": f"{SPACE['md']}px"})

    chart_card = html.Div([
        html.Div("Tendance réelle vs prévision", style=SECTION_TITLE),
        _trend_chart(by_month, forecast, patterns) if (by_month or forecast) else html.Div(
            "Aucune donnée.", style={"color": COLORS["muted"],
                                    "fontFamily": FONTS["sans"], "fontSize": "13px"}),
    ], style=CARD)

    return html.Div([
        html.Div([html.H1("Récurrences", style=PAGE_TITLE),
                  html.P("Patterns détectés et prévisions à 3 mois.", style=PAGE_SUBTITLE)],
                 style={"marginBottom": f"{SPACE['xl']}px"}),
        kpi_row, patterns_card, fc_card, chart_card,
    ], style={"maxWidth": "960px"})
