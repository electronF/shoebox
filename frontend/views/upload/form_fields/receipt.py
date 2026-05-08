"""
Form fields for receipt document type (REC).

Covers both official printed receipts and informal/handwritten ones.
All fields are editable regardless of OCR confidence.
"""

from dash import html, dcc
from frontend.theme import SPACE, COLORS, FONTS, RADIUS, BTN_SECONDARY
from frontend.components.form_field import form_field


def receipt_form(form_id: str, data: dict, status: str = "ok") -> html.Div:
    """
    Renders receipt form fields.

    Args:
        form_id: Unique form instance identifier.
        data:    Pre-filled values from OCR extraction.
        status:  Overall form status for default field states.
    """
    merchant_status = "ok" if data.get("merchant") else (
        "error" if status != "informal" else "neutral"
    )
    date_status  = "ok" if data.get("date")  else "error"
    total_status = "ok" if data.get("total") else "error"

    payment_value = data.get("payment_method", "") or None

    return html.Div([
        html.Div(
            [
                form_field("MARCHAND",      form_id, "merchant",
                           value=data.get("merchant", ""),
                           required=True, field_status=merchant_status,
                           placeholder="ex: Bureau en Gros"),

                form_field("DATE",          form_id, "date",
                           value=data.get("date", ""),
                           required=True, field_status=date_status,
                           input_type="date"),

                form_field("DESCRIPTION",   form_id, "description",
                           value=data.get("description", ""),
                           placeholder="ex: Fournitures de bureau"),

                form_field("SOUS-TOTAL",    form_id, "subtotal",
                           value=data.get("subtotal", ""),
                           required=True,
                           hint="Montant hors taxes",
                           placeholder="$0.00"),

                form_field("TOTAL TTC",     form_id, "total",
                           value=data.get("total", ""),
                           required=True,
                           hint="Montant final incluant les taxes",
                           field_status=total_status,
                           placeholder="$0.00"),

                form_field("TPS (5%)",      form_id, "tps",
                           value=data.get("tps", ""),
                           hint="Taxe fédérale",
                           placeholder="$0.00"),

                form_field("TVQ (9.975%)",  form_id, "tvq",
                           value=data.get("tvq", ""),
                           hint="Taxe provinciale",
                           placeholder="$0.00"),

                # MODE DE PAIEMENT — dropdown with pattern-matching id
                html.Div(
                    [
                        html.Div(
                            [html.Span("MODE DE PAIEMENT", className="field-label")],
                            style={"marginBottom": "5px"},
                        ),
                        dcc.Dropdown(
                            id={"type": "form-field", "form": form_id, "field": "payment_method"},
                            options=[
                                {"label": "Comptant", "value": "cash"},
                                {"label": "Carte",    "value": "card"},
                                {"label": "Virement", "value": "transfer"},
                            ],
                            value=payment_value,
                            placeholder="Sélectionner…",
                            clearable=True,
                            style={
                                "fontFamily": FONTS["sans"],
                                "fontSize":   "13px",
                                "borderRadius": RADIUS["sm"],
                            },
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column"},
                ),

                form_field("N° TRANSACTION", form_id, "ref",
                           value=data.get("ref", ""),
                           hint="Présent sur les reçus officiels imprimés",
                           placeholder="ex: 20250122-0312-0947"),
            ],
            className="field-group",
        ),

        # Informal receipt toggle
        html.Button(
            [
                html.I(className="fa-solid fa-pen",
                       style={"marginRight": "6px"}),
                "Marquer comme reçu informel (sans taxes)",
            ],
            id={"type": "btn-mark-informal", "form": form_id},
            n_clicks=0,
            style={
                **BTN_SECONDARY,
                "fontSize":  "11px",
                "padding":   "4px 10px",
                "marginTop": f"{SPACE['sm']}px",
            },
        ),
    ])
