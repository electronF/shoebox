"""
Invoices — issued invoice tracking and collections dashboard.

Shows KPI summary, 12-month grouped bar chart, filter tabs, and
an inline mark-as-paid action per row.
"""

from datetime import date, timedelta

import plotly.graph_objects as go
from dash import dcc, html

import frontend.api_client as api
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS,
    CARD, PAGE_TITLE, PAGE_SUBTITLE, SECTION_TITLE,
    TABLE_HEADER_CELL, TABLE_CELL, BTN_PRIMARY,
)

_STATUS_CFG = {
    "paid":    ("Payée",      COLORS["ok"],      COLORS["ok_bg"]),
    "unpaid":  ("En attente", COLORS["warning"], COLORS["warning_bg"]),
    "overdue": ("Impayée",    COLORS["error"],   COLORS["error_bg"]),
    "void":    ("Annulée",    COLORS["muted"],   COLORS["cream"]),
}

_FILTER_OPTIONS = [
    ("all",     "Toutes"),
    ("unpaid",  "À encaisser"),
    ("paid",    "Payées"),
    ("overdue", "Impayées"),
]

_MONTHS_FR = {
    "01": "Jan", "02": "Fév", "03": "Mar", "04": "Avr",
    "05": "Mai", "06": "Juin", "07": "Juil", "08": "Août",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Déc",
}


def _last_12_months() -> list[str]:
    """Returns the last 12 month strings in YYYY-MM order."""
    today = date.today().replace(day=1)
    months = []
    for i in range(11, -1, -1):
        m = (today - timedelta(days=i * 30)).replace(day=1)
        months.append(m.strftime("%Y-%m"))
    return months


def _status_badge(status: str) -> html.Span:
    label, color, bg = _STATUS_CFG.get(status, ("—", COLORS["muted"], COLORS["cream"]))
    return html.Span(label, style={
        "fontFamily":      FONTS["mono"],
        "fontSize":        "10px",
        "fontWeight":      "600",
        "color":           color,
        "backgroundColor": bg,
        "borderRadius":    RADIUS["sm"],
        "padding":         "3px 10px",
        "whiteSpace":      "nowrap",
    })


def _kpi_card(icon: str, value: str, label: str, color: str, bg: str) -> html.Div:
    return html.Div([
        html.Div(
            html.I(className=icon, style={"fontSize": "16px", "color": color}),
            style={
                "width": "36px", "height": "36px", "borderRadius": RADIUS["md"],
                "backgroundColor": bg, "display": "flex",
                "alignItems": "center", "justifyContent": "center",
                "marginBottom": f"{SPACE['sm']}px",
            },
        ),
        html.Div(value, style={
            "fontFamily": FONTS["serif"], "fontSize": "24px",
            "fontWeight": "700", "color": COLORS["ink"], "lineHeight": "1",
        }),
        html.Div(label, style={
            "fontFamily": FONTS["sans"], "fontSize": "12px",
            "color": COLORS["muted"], "marginTop": "4px",
        }),
    ], style={**CARD, "flex": "1", "minWidth": "140px"})


def _monthly_chart(invoices: list) -> dcc.Graph:
    """12-month grouped bar chart: Payées / En attente / Impayées.

    Args:
        invoices: Full invoice list from the API.

    Returns:
        dcc.Graph: Plotly grouped bar chart.
    """
    months = _last_12_months()
    labels = [_MONTHS_FR.get(m[5:], m[5:]) for m in months]

    paid_amt    = {m: 0.0 for m in months}
    unpaid_amt  = {m: 0.0 for m in months}
    overdue_amt = {m: 0.0 for m in months}

    for inv in invoices:
        month  = (inv.get("date_sent") or "")[:7]
        amount = inv.get("amount", 0)
        status = inv.get("status", "unpaid")
        if month not in paid_amt:
            continue
        if status == "paid":
            paid_amt[month] += amount
        elif status == "overdue":
            overdue_amt[month] += amount
        else:
            unpaid_amt[month] += amount

    fig = go.Figure([
        go.Bar(name="Payées",      x=labels,
               y=[paid_amt[m]    for m in months],
               marker_color=COLORS["ok"],      marker_line_width=0),
        go.Bar(name="En attente", x=labels,
               y=[unpaid_amt[m]  for m in months],
               marker_color=COLORS["warning"], marker_line_width=0),
        go.Bar(name="Impayées",   x=labels,
               y=[overdue_amt[m] for m in months],
               marker_color=COLORS["error"],   marker_line_width=0),
    ])
    fig.update_layout(
        barmode="group",
        plot_bgcolor=COLORS["white"],
        paper_bgcolor=COLORS["white"],
        margin={"l": 40, "r": 16, "t": 8, "b": 60},
        height=240,
        font={"family": FONTS["sans"], "size": 11, "color": COLORS["muted"]},
        xaxis={"showgrid": False, "type": "category"},
        yaxis={
            "showgrid": True, "gridcolor": COLORS["border_light"],
            "tickprefix": "$", "tickfont": {"size": 10},
        },
        legend={
            "orientation": "h", "yanchor": "top", "y": -0.25,
            "font": {"family": FONTS["mono"], "size": 9},
        },
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False},
                     style={"height": "280px"})


def _invoice_row(inv: dict) -> html.Tr:
    """One table row for an invoice."""
    status    = inv.get("status", "unpaid")
    inv_id    = inv.get("id", "")
    can_pay   = status in ("unpaid", "overdue")
    date_sent = (inv.get("date_sent") or "")[:10]
    date_paid = (inv.get("date_paid") or "")[:10]
    amount    = inv.get("amount", 0)

    action = html.Button(
        [html.I(className="fa-solid fa-check", style={"marginRight": "6px"}),
         "Marquer payée"],
        id={"type": "btn-mark-paid", "invoice_id": inv_id},
        n_clicks=0,
        style={**BTN_PRIMARY, "fontSize": "11px", "padding": "4px 10px"},
    ) if can_pay else html.Span("—", style={
        "fontFamily": FONTS["mono"], "fontSize": "12px", "color": COLORS["muted"],
    })

    _cell = {**TABLE_CELL, "padding": f"10px {SPACE['md']}px"}

    return html.Tr([
        html.Td(inv.get("client", "—"),
                style={**_cell, "fontWeight": "600"}),
        html.Td(
            html.Span((inv.get("description") or "—")[:48],
                      style={"fontFamily": FONTS["sans"], "fontSize": "12px",
                             "color": COLORS["muted"]}),
            style=_cell,
        ),
        html.Td(f"${amount:,.2f}",
                style={**_cell, "fontFamily": FONTS["mono"], "fontWeight": "700",
                       "color": COLORS["ok"] if status == "paid" else COLORS["ink"]}),
        html.Td(date_sent or "—",
                style={**_cell, "fontFamily": FONTS["mono"], "fontSize": "12px",
                       "color": COLORS["muted"]}),
        html.Td(date_paid or "—",
                style={**_cell, "fontFamily": FONTS["mono"], "fontSize": "12px",
                       "color": COLORS["ok"] if date_paid else COLORS["muted"]}),
        html.Td(_status_badge(status), style=_cell),
        html.Td(action, style=_cell),
    ])


def _invoices_table(invoices: list) -> html.Div:
    """Full invoice table with header, or empty-state message."""
    if not invoices:
        return html.Div(
            "Aucune facture dans cette catégorie.",
            style={
                **CARD,
                "fontFamily": FONTS["sans"],
                "fontSize":   "13px",
                "color":      COLORS["muted"],
                "textAlign":  "center",
                "padding":    f"{SPACE['2xl']}px",
            },
        )

    _hdr = {**TABLE_HEADER_CELL, "padding": f"10px {SPACE['md']}px"}
    header = html.Tr([
        html.Th("Client",      style=_hdr),
        html.Th("Description", style=_hdr),
        html.Th("Montant",     style=_hdr),
        html.Th("Envoyée",     style=_hdr),
        html.Th("Payée",       style=_hdr),
        html.Th("Statut",      style=_hdr),
        html.Th("",            style=_hdr),
    ])
    return html.Div(
        html.Table(
            [html.Thead(header),
             html.Tbody([_invoice_row(inv) for inv in invoices])],
            style={"width": "100%", "borderCollapse": "collapse"},
        ),
        style={**CARD, "padding": "0", "overflowX": "auto"},
    )


def layout() -> html.Div:
    """Renders the invoices page."""
    all_invoices = api.get_invoices()

    unpaid  = [i for i in all_invoices if i.get("status") in ("unpaid", "overdue")]
    paid    = [i for i in all_invoices if i.get("status") == "paid"]
    overdue = [i for i in all_invoices if i.get("status") == "overdue"]

    total_to_collect = sum(i.get("amount", 0) for i in unpaid)
    total_collected  = sum(i.get("amount", 0) for i in paid)

    kpi_row = html.Div([
        _kpi_card("fa-solid fa-clock",
                  f"${total_to_collect:,.2f}", "À encaisser",
                  COLORS["warning"], COLORS["warning_bg"]),
        _kpi_card("fa-solid fa-circle-check",
                  f"${total_collected:,.2f}", "Encaissé",
                  COLORS["ok"], COLORS["ok_bg"]),
        _kpi_card("fa-solid fa-triangle-exclamation",
                  str(len(overdue)), "Impayées",
                  COLORS["error"], COLORS["error_bg"]),
        _kpi_card("fa-solid fa-file-invoice-dollar",
                  str(len(all_invoices)), "Total factures",
                  COLORS["accent"], COLORS["accent_light"]),
    ], style={
        "display": "flex", "gap": f"{SPACE['md']}px",
        "marginBottom": f"{SPACE['xl']}px",
    })

    chart_card = html.Div([
        html.Div("Évolution mensuelle — 12 derniers mois", style=SECTION_TITLE),
        _monthly_chart(all_invoices) if all_invoices else html.Div(
            "Importez des factures pour voir le graphique.",
            style={"fontFamily": FONTS["sans"], "fontSize": "12px",
                   "color": COLORS["muted"], "padding": f"{SPACE['md']}px 0"},
        ),
    ], style={**CARD, "marginBottom": f"{SPACE['xl']}px"})

    filter_tabs = html.Div([
        html.Div(
            html.Span(label, style={
                "fontFamily": FONTS["sans"], "fontSize": "12px", "fontWeight": "600",
            }),
            id={"type": "invoice-filter-tab", "value": value},
            n_clicks=0,
            style={
                "padding":         "6px 16px",
                "borderRadius":    RADIUS["sm"],
                "cursor":          "pointer",
                "backgroundColor": COLORS["accent"] if value == "all" else "transparent",
                "color":           COLORS["white"]  if value == "all" else COLORS["muted"],
                "border":          f"1px solid {COLORS['border']}",
            },
        )
        for value, label in _FILTER_OPTIONS
    ], style={
        "display": "flex", "gap": "6px",
        "marginBottom": f"{SPACE['md']}px",
    })

    return html.Div([
        html.H1("Factures émises", style=PAGE_TITLE),
        html.P("Suivi des encaissements clients", style=PAGE_SUBTITLE),
        kpi_row,
        chart_card,
        filter_tabs,
        html.Div(_invoices_table(all_invoices), id="invoices-table-container"),
    ], style={"maxWidth": "1100px"})
