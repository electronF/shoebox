"""
Subscriptions — recurring expense audit: detail cards, overlap insights, and cost donut.
"""

from dash import dcc, html
import plotly.graph_objects as go

import frontend.api_client as api
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS, CARD, SECTION_TITLE, PAGE_TITLE, PAGE_SUBTITLE,
    TABLE_HEADER_CELL, TABLE_CELL,
)

_SHADES = ["#185fa5", "#2e7d5e", "#c8a84b", "#b5361c", "#1a4d3e", "#854f0b", "#3c3489", "#6b6557"]


def _kpi_tile(label: str, value: str, color: str = COLORS["ink"]) -> html.Div:
    """Compact KPI tile — label above, large value below.

    Args:
        label: Description. value: Formatted value. color: Value colour.

    Returns:
        html.Div: Styled tile.
    """
    return html.Div([
        html.Div(label, style={"fontFamily": FONTS["sans"], "fontSize": "11px",
                               "color": COLORS["muted"], "marginBottom": "6px"}),
        html.Div(value, style={"fontFamily": FONTS["serif"], "fontSize": "26px",
                               "fontWeight": "700", "color": color, "lineHeight": "1"}),
    ], style={**CARD, "flex": "1"})


def _icon(name: str) -> str:
    """Map service display name to a Font Awesome class.

    Args:
        name: Service display name.

    Returns:
        str: Font Awesome CSS class.
    """
    n = name.lower()
    for kw, cls in [("adobe", "fa-solid fa-a"), ("shopify", "fa-brands fa-shopify"),
                    ("canva", "fa-solid fa-pen-nib"), ("google", "fa-brands fa-google"),
                    ("netflix", "fa-solid fa-film"), ("amazon", "fa-brands fa-amazon"),
                    ("postes", "fa-solid fa-envelope"), ("vrbo", "fa-solid fa-building"),
                    ("slack", "fa-brands fa-slack"), ("zoom", "fa-solid fa-video")]:
        if kw in n:
            return cls
    return "fa-solid fa-globe"


def _verdict(p: dict) -> tuple:
    """Compute verdict (label, color, bg) for a pattern.

    Args:
        p: Pattern dict from the API.

    Returns:
        Tuple of (label, text_color, bg_color).
    """
    freq, conf = p.get("frequency", ""), p.get("confidence", 0)
    if freq == "monthly" and conf >= 0.75:
        return "Garder",    COLORS["ok"],      COLORS["ok_bg"]
    if freq == "monthly":
        return "À évaluer", COLORS["warning"],  COLORS["warning_bg"]
    if conf >= 0.5:
        return "Vérifier",  COLORS["gold"],     COLORS["gold_light"]
    return "Vérifier",      COLORS["error"],    COLORS["error_bg"]


def _auto_desc(p: dict) -> str:
    """One-line description generated from pattern data.

    Args:
        p: Pattern dict from the API.

    Returns:
        str: Human-readable description.
    """
    avg, ma = p.get("avg_amount", 0), p.get("monthly_amounts", {})
    if p.get("frequency") == "monthly":
        return f"${avg:.2f}/mois récurrent. Présence mensuelle confirmée."
    if ma:
        lo, hi = min(ma.values()), max(ma.values())
        if hi > avg * 1.4:
            return f"Variable : ${lo:.2f}–${hi:.2f}. Pic de ${hi:.2f} — doublon possible."
        return f"Variable : ${lo:.2f}–${hi:.2f}. Moy. ${avg:.2f}/mois."
    return f"Moy. ${avg:.2f}/mois."


def _sub_row(p: dict, idx: int, max_amt: float, color: str) -> html.Tr:
    """One subscription row: icon + name + description + bar, then amount columns.

    Args:
        p: Pattern dict. idx: Row index. max_amt: Max avg for bar scaling. color: Accent colour.

    Returns:
        html.Tr: Styled table row.
    """
    bg, avg = COLORS["white"] if idx % 2 == 0 else COLORS["paper"], p.get("avg_amount", 0)
    pct = int(avg / max_amt * 100) if max_amt else 0
    vlbl, vcol, vbg = _verdict(p)
    service_cell = html.Div([
        html.Div([
            html.I(className=_icon(p.get("display_name", "")),
                   style={"color": color, "fontSize": "14px", "width": "20px",
                          "marginRight": "10px", "flexShrink": "0"}),
            html.Span(p.get("display_name", "—")[:35], style={
                "fontFamily": FONTS["sans"], "fontSize": "13px",
                "fontWeight": "600", "color": COLORS["ink"],
            }),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "3px"}),
        html.Div(_auto_desc(p), style={"fontFamily": FONTS["sans"], "fontSize": "11px",
                                        "color": COLORS["muted"], "marginLeft": "30px",
                                        "marginBottom": "6px", "fontStyle": "italic"}),
        html.Div(html.Div(style={"height": "3px", "borderRadius": "2px",
                                  "backgroundColor": color, "width": f"{pct}%"}),
                 style={"marginLeft": "30px", "height": "3px", "borderRadius": "2px",
                        "backgroundColor": COLORS["border_light"], "overflow": "hidden"}),
    ])
    return html.Tr([
        html.Td(service_cell, style={**TABLE_CELL, "backgroundColor": bg,
                                      "paddingTop": "12px", "paddingBottom": "12px"}),
        html.Td(f"${avg:,.2f}", style={**TABLE_CELL, "backgroundColor": bg,
                                        "fontFamily": FONTS["mono"], "fontSize": "14px",
                                        "fontWeight": "600", "textAlign": "right",
                                        "whiteSpace": "nowrap"}),
        html.Td(f"${avg*12:,.0f}", style={**TABLE_CELL, "backgroundColor": bg,
                                           "fontFamily": FONTS["mono"], "fontSize": "12px",
                                           "color": COLORS["muted"], "textAlign": "right",
                                           "whiteSpace": "nowrap"}),
        html.Td(html.Span(vlbl, style={"fontFamily": FONTS["mono"], "fontSize": "10px",
                                        "color": vcol, "backgroundColor": vbg,
                                        "borderRadius": RADIUS["pill"], "padding": "4px 12px"}),
                style={**TABLE_CELL, "backgroundColor": bg, "textAlign": "right"}),
    ])


def _insight_card(title: str, body: str, cta: str, warn: bool = True) -> html.Div:
    """Recommendation card for overlap or clarification alerts.

    Args:
        title: Card heading. body: Explanation text. cta: Call-to-action line. warn: Warning vs info style.

    Returns:
        html.Div: Styled insight card.
    """
    col = COLORS["warning"] if warn else COLORS["info"]
    bg  = COLORS["warning_bg"] if warn else COLORS["info_bg"]
    return html.Div([
        html.Div(title, style={"fontFamily": FONTS["mono"], "fontSize": "10px",
                               "letterSpacing": "0.1em", "color": COLORS["muted"],
                               "textTransform": "uppercase", "marginBottom": "10px"}),
        html.P(body, style={"fontFamily": FONTS["sans"], "fontSize": "13px",
                             "color": COLORS["ink"], "lineHeight": "1.55", "marginBottom": "12px"}),
        html.Div([
            html.I(className="fa-solid fa-scissors" if warn else "fa-solid fa-circle-question",
                   style={"marginRight": "6px", "fontSize": "11px"}),
            html.Span(cta, style={"fontFamily": FONTS["mono"], "fontSize": "11px"}),
        ], style={"color": col, "backgroundColor": bg, "borderRadius": RADIUS["sm"],
                  "padding": f"{SPACE['xs']}px {SPACE['sm']}px",
                  "display": "inline-flex", "alignItems": "center"}),
    ], style={**CARD, "flex": "1", "minWidth": "280px"})


def _donut(patterns: list) -> dcc.Graph:
    """Donut chart of annual cost share per subscription.

    Args:
        patterns: Pattern dicts from the API.

    Returns:
        dcc.Graph: Plotly donut chart.
    """
    fig = go.Figure(go.Pie(
        labels=[p.get("display_name", "?")[:20] for p in patterns],
        values=[p.get("avg_amount", 0) * 12 for p in patterns],
        hole=0.5, marker={"colors": _SHADES[:len(patterns)]},
        textinfo="label+percent", textfont={"family": FONTS["sans"], "size": 10},
        hovertemplate="%{label}: $%{value:,.0f}/an<extra></extra>",
    ))
    fig.update_layout(paper_bgcolor=COLORS["white"],
                      margin={"l": 0, "r": 0, "t": 8, "b": 120}, height=340,
                      legend={"font": {"family": FONTS["mono"], "size": 10},
                              "orientation": "h", "yanchor": "bottom", "y": -0.45})
    return dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "480px"})


def layout() -> html.Div:
    """Renders the subscription audit page.

    Returns:
        html.Div: Full page with KPIs, detail table, insight cards, and cost donut.
    """
    patterns  = api.get_recurring().get("patterns", [])
    total_moy = sum(p.get("avg_amount", 0) for p in patterns)
    to_act    = [p for p in patterns if _verdict(p)[0] in ("Vérifier", "À évaluer")]

    kpi_row = html.Div([
        _kpi_tile("Total abonnements / mois (moy.)", f"${total_moy:,.2f}"),
        _kpi_tile("Coût annualisé", f"${total_moy * 12:,.0f}"),
        _kpi_tile("Économies potentielles / an",
                  f"${sum(p.get('avg_amount',0)*12 for p in to_act):,.0f}", COLORS["ok"]),
        _kpi_tile("Abonnements à vérifier", str(len(to_act)), COLORS["error"]),
    ], style={"display": "flex", "gap": f"{SPACE['md']}px", "marginBottom": f"{SPACE['xl']}px"})

    max_amt = max((p.get("avg_amount", 0) for p in patterns), default=1)
    rows = ([_sub_row(p, i, max_amt, _SHADES[i % len(_SHADES)]) for i, p in enumerate(patterns)]
            if patterns else [html.Tr(html.Td(
                "Aucun abonnement détecté. Importez des relevés pour l'analyse.", colSpan=4,
                style={**TABLE_CELL, "textAlign": "center", "color": COLORS["muted"], "padding": "32px"},
            ))])
    detail_card = html.Div([
        html.Div("Détail par abonnement", style=SECTION_TITLE),
        html.Div(html.Table([
            html.Thead(html.Tr([
                html.Th("Service", style=TABLE_HEADER_CELL),
                html.Th("/ mois", style={**TABLE_HEADER_CELL, "textAlign": "right"}),
                html.Th("/ an",   style={**TABLE_HEADER_CELL, "textAlign": "right"}),
                html.Th("Verdict", style={**TABLE_HEADER_CELL, "textAlign": "right"}),
            ])),
            html.Tbody(rows),
        ], style={"width": "100%", "borderCollapse": "collapse"}), style={"overflowX": "auto"}),
    ], style={**CARD, "marginBottom": f"{SPACE['md']}px"})

    by_cat: dict = {}
    for p in patterns:
        by_cat.setdefault(p.get("category", "autre"), []).append(p)
    insight_cards = []
    for cat, ps in by_cat.items():
        if len(insight_cards) >= 2:
            break
        if len(ps) >= 2:
            names = " et ".join(p.get("display_name", "?")[:15] for p in ps[:2])
            insight_cards.append(_insight_card(
                f"{ps[0].get('display_name','?')[:15]} — Chevauchement".upper(),
                f"Tu paies pour {names} dans la même catégorie ({cat}). "
                "Vérifie si les deux sont nécessaires.",
                f"Économies potentielles : ${sum(p.get('avg_amount',0)*12 for p in ps[:2]):,.0f}/an",
            ))
    for p in patterns:
        if len(insight_cards) >= 2:
            break
        ma = p.get("monthly_amounts", {})
        if ma and max(ma.values()) > p.get("avg_amount", 0) * 1.4:
            hi = max(ma.values())
            insight_cards.append(_insight_card(
                f"{p.get('display_name','?')[:18]} — À clarifier".upper(),
                f"Pic de ${hi:.2f} détecté (moy. ${p.get('avg_amount',0):.2f}/mois). "
                "Doublon ou upgrade ? Vérifie si l'abonnement est toujours actif.",
                f"Si inactif : couper = ${p.get('avg_amount',0)*12:,.0f}/an d'économies.",
                warn=False,
            ))

    donut_card = html.Div([
        html.Div("Répartition du coût annuel", style=SECTION_TITLE),
        _donut(patterns) if patterns else html.Div("Aucune donnée.", style={
            "color": COLORS["muted"], "fontFamily": FONTS["sans"], "fontSize": "13px"}),
    ], style=CARD)

    children = [
        html.Div([html.H1("Abonnements", style=PAGE_TITLE),
                  html.P("Audit des dépenses récurrentes détectées.", style=PAGE_SUBTITLE)],
                 style={"marginBottom": f"{SPACE['xl']}px"}),
        kpi_row, detail_card,
    ]
    if insight_cards:
        children.append(html.Div(insight_cards, style={
            "display": "flex", "gap": f"{SPACE['md']}px",
            "flexWrap": "wrap", "marginBottom": f"{SPACE['md']}px",
        }))
    children.append(donut_card)
    return html.Div(children, style={"maxWidth": "900px"})
