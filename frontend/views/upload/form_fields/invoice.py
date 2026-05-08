"""
Form fields for issued invoice document type (INV).

Supports two modes:
- Multi-row (xlsx): editable table, one row per invoice line.
- Single (pdf/other): full form with all fields including tax breakdown.
"""

from dash import html, dcc
from frontend.theme import COLORS, FONTS, SPACE, RADIUS
from frontend.components.form_field import form_field

_STATUS_OPTIONS = [
    {"label": "Payée",      "value": "paid"},
    {"label": "En attente", "value": "unpaid"},
    {"label": "Impayée",    "value": "overdue"},
    {"label": "Annulée",    "value": "void"},
]


def invoice_form(form_id: str, data: dict) -> html.Div:
    """
    Renders invoice form fields.

    Delegates to the multi-row table when data contains "rows" (xlsx source),
    otherwise renders the single-invoice form.

    Args:
        form_id: Unique form instance identifier.
        data:    Pre-filled values from parser. May contain a "rows" list
                 (xlsx) or flat fields (single invoice).
    """
    if data.get("rows"):
        return _invoice_rows_form(form_id, data["rows"])
    return _invoice_single_form(form_id, data)


def _invoice_single_form(form_id: str, data: dict) -> html.Div:
    """
    Full single-invoice form with all fields including tax breakdown.

    Args:
        form_id: Unique form identifier.
        data:    Pre-filled values.
    """
    client_status = "ok" if data.get("client") else "error"
    amount_status = "ok" if data.get("amount") else "error"

    return html.Div([
        html.Div(
            [
                form_field("N° FACTURE",       form_id, "invoice_number",
                           value=data.get("invoice_number", ""),
                           placeholder="ex: INV-2025-001"),

                form_field("CLIENT",            form_id, "client",
                           value=data.get("client", ""),
                           required=True, field_status=client_status,
                           placeholder="ex: BrightPath Marketing"),

                form_field("DESCRIPTION",       form_id, "description",
                           value=data.get("description", ""),
                           placeholder="ex: Social media graphics — March"),

                form_field("MONTANT HT",        form_id, "amount",
                           value=data.get("amount", ""),
                           required=True,
                           hint="Montant hors taxes en CAD",
                           field_status=amount_status,
                           placeholder="$0.00"),

                form_field("SOUS-TOTAL",        form_id, "subtotal",
                           value=data.get("subtotal", ""),
                           hint="Avant taxes",
                           placeholder="$0.00"),

                form_field("TOTAL TTC",         form_id, "total",
                           value=data.get("total", ""),
                           hint="Montant final incluant les taxes",
                           placeholder="$0.00"),

                form_field("TPS",               form_id, "tps",
                           value=data.get("tps", ""),
                           hint="Taxe fédérale (taux variable)",
                           placeholder="$0.00"),

                form_field("TVQ",               form_id, "tvq",
                           value=data.get("tvq", ""),
                           hint="Taxe provinciale (taux variable)",
                           placeholder="$0.00"),

                form_field("N° TRANSACTION",    form_id, "ref",
                           value=data.get("ref", ""),
                           placeholder="ex: TXN-2025-001"),

                form_field("DATE D'ENVOI",      form_id, "date_sent",
                           value=data.get("date_sent", ""),
                           input_type="date"),

                form_field("DATE PAIEMENT",     form_id, "date_paid",
                           value=data.get("date_paid", ""),
                           hint="Laisser vide si non encore payée",
                           input_type="date"),

                # Status dropdown
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("STATUT", className="field-label-required"),
                                html.Span(" *", className="required-star"),
                            ],
                            style={"display": "flex", "alignItems": "center",
                                   "marginBottom": "5px"},
                        ),
                        dcc.Dropdown(
                            id={"type": "form-field", "form": form_id, "field": "status"},
                            options=_STATUS_OPTIONS,
                            value=data.get("status", "unpaid"),
                            clearable=False,
                            className="dash-dropdown",
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column"},
                ),
            ],
            className="field-group",
        ),
    ])


def _invoice_rows_form(form_id: str, rows: list[dict]) -> html.Div:
    """
    Renders an editable multi-row table for xlsx invoice files.

    Each row maps to five inputs: client, description, amount, date_sent,
    date_paid. Uses the same tx_{i}_field pattern as statement rows.

    Args:
        form_id: Unique form identifier.
        rows:    List of row dicts from extract_rows().
    """
    return html.Div([
        html.Div(
            [
                html.Div(
                    "Factures extraites",
                    style={
                        "fontFamily":    FONTS["sans"],
                        "fontSize":      "11px",
                        "fontWeight":    "700",
                        "letterSpacing": "0.06em",
                        "textTransform": "uppercase",
                        "color":         COLORS["muted"],
                        "marginBottom":  f"{SPACE['sm']}px",
                        "paddingBottom": f"{SPACE['xs']}px",
                        "borderBottom":  f"1px solid {COLORS['border_light']}",
                    },
                ),

                # Column headers
                html.Div(
                    [
                        html.Span("Client",      style=_hdr("120px")),
                        html.Span("Description", style=_hdr("1")),
                        html.Span("Montant",     style=_hdr("76px")),
                        html.Span("Envoyée",     style=_hdr("92px")),
                        html.Span("Payée",       style=_hdr("92px")),
                    ],
                    style={"display": "flex", "gap": "6px",
                           "marginBottom": "4px", "padding": "0 4px"},
                ),

                html.Div(
                    [_inv_row(form_id, i, row) for i, row in enumerate(rows)]
                    if rows else [html.Div(
                        "Aucune ligne extraite.",
                        style={"fontFamily": FONTS["sans"], "fontSize": "12px",
                               "color": COLORS["muted"], "padding": f"{SPACE['sm']}px"},
                    )],
                    style={"maxHeight": "400px", "overflowY": "auto", "paddingRight": "4px"},
                ),

                html.Div(
                    f"{len(rows)} facture(s) à réviser",
                    style={
                        "fontFamily": FONTS["sans"],
                        "fontSize":   "11px",
                        "color":      COLORS["ok"] if rows else COLORS["muted"],
                        "marginTop":  f"{SPACE['sm']}px",
                        "textAlign":  "right",
                    },
                ) if rows else None,
            ],
            style={
                "padding":         f"{SPACE['md']}px",
                "backgroundColor": COLORS["cream"],
                "borderRadius":    RADIUS["md"],
                "border":          f"1px solid {COLORS['border_light']}",
            },
        ),
    ])


def _hdr(flex_or_width: str) -> dict:
    base = {
        "fontFamily":    FONTS["mono"],
        "fontSize":      "10px",
        "fontWeight":    "600",
        "color":         COLORS["muted"],
        "textTransform": "uppercase",
        "letterSpacing": "0.05em",
    }
    if flex_or_width == "1":
        base["flex"] = "1"
    else:
        base["width"]      = flex_or_width
        base["flexShrink"] = "0"
    return base


def _inv_row(form_id: str, index: int, row: dict) -> html.Div:
    """
    Renders one editable invoice row.

    Args:
        form_id: Parent form identifier.
        index:   Row index.
        row:     Dict with client, description, amount, date_sent, date_paid.
    """
    _s = {
        "fontFamily":    FONTS["mono"],
        "fontSize":      "12px",
        "border":        f"1px solid {COLORS['border_light']}",
        "borderRadius":  RADIUS["sm"],
        "padding":       "4px 6px",
        "backgroundColor": COLORS["white"],
        "color":         COLORS["ink"],
        "width":         "100%",
        "boxSizing":     "border-box",
    }
    paid = row.get("date_paid", "")
    amount_color = COLORS["ok"] if paid else COLORS["ink"]

    return html.Div(
        [
            dcc.Input(
                id={"type": "form-field", "form": form_id, "field": f"tx_{index}_client"},
                type="text", value=row.get("client", ""), placeholder="Client",
                style={**_s, "width": "120px", "flexShrink": "0"},
                debounce=True,
            ),
            dcc.Input(
                id={"type": "form-field", "form": form_id, "field": f"tx_{index}_desc"},
                type="text", value=row.get("description", ""), placeholder="Description",
                style={**_s, "flex": "1", "minWidth": "0"},
                debounce=True,
            ),
            dcc.Input(
                id={"type": "form-field", "form": form_id, "field": f"tx_{index}_amount"},
                type="text", value=row.get("amount", ""), placeholder="0.00",
                style={**_s, "width": "76px", "flexShrink": "0",
                       "textAlign": "right", "color": amount_color, "fontWeight": "600"},
                debounce=True,
            ),
            html.Div(
                dcc.DatePickerSingle(
                    id={"type": "form-date", "form": form_id, "field": f"tx_{index}_date_sent"},
                    date=row.get("date_sent", "") or None,
                    display_format="DD/MM/YY",
                    placeholder="JJ/MM/AA",
                    with_portal=True,
                    style={"width": "100%"},
                ),
                style={"width": "92px", "flexShrink": "0", "overflow": "hidden"},
            ),
            html.Div(
                dcc.DatePickerSingle(
                    id={"type": "form-date", "form": form_id, "field": f"tx_{index}_date_paid"},
                    date=row.get("date_paid", "") or None,
                    display_format="DD/MM/YY",
                    placeholder="JJ/MM/AA",
                    with_portal=True,
                    style={"width": "100%"},
                ),
                style={"width": "92px", "flexShrink": "0", "overflow": "hidden"},
            ),
        ],
        style={
            "display": "flex", "gap": "6px",
            "marginBottom": "4px", "alignItems": "center",
        },
    )
