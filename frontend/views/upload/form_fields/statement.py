"""
Form fields for bank/card statement document type (STMT).

A statement produces N transactions. The form shows statement metadata
at the top and a fully editable row for each extracted transaction so the
user can correct any OCR errors before submission.
"""

from dash import html, dcc
from frontend.theme import COLORS, FONTS, SPACE, RADIUS
from frontend.components.form_field import form_field


def statement_form(form_id: str, data: dict) -> html.Div:
    """
    Renders statement metadata fields followed by editable transaction rows.

    Args:
        form_id: Unique form instance identifier.
        data:    Pre-filled values from parser (holder, last_four, period_from,
                 period_to, source_label, and a list under "transactions").
    """
    holder_status = "ok" if data.get("holder")    else "error"
    card_status   = "ok" if data.get("last_four") else "error"

    transactions: list[dict] = data.get("transactions", [])

    return html.Div([

        # ── Statement metadata ────────────────────────────────────────────────
        html.Div(
            [
                form_field("TITULAIRE",        form_id, "holder",
                           value=data.get("holder", ""),
                           required=True, field_status=holder_status,
                           placeholder="ex: Claude E. Shannon"),

                form_field("NUMÉRO DE CARTE",  form_id, "last_four",
                           value=data.get("last_four", ""),
                           required=True,
                           hint="4 derniers chiffres",
                           field_status=card_status,
                           placeholder="ex: 4829"),

                form_field("PÉRIODE DU",       form_id, "period_from",
                           value=data.get("period_from", ""),
                           required=True,
                           hint="Date de début du relevé",
                           input_type="date"),

                form_field("PÉRIODE AU",       form_id, "period_to",
                           value=data.get("period_to", ""),
                           required=True,
                           hint="Date de fin du relevé",
                           input_type="date"),

                form_field("SOURCE DE PAIEMENT", form_id, "source_label",
                           value=data.get("source_label", ""),
                           required=True,
                           hint="Label affiché dans l'app",
                           placeholder="ex: Visa *4829"),
            ],
            className="field-group",
        ),

        # ── Transaction rows ──────────────────────────────────────────────────
        html.Div(
            [
                html.Div(
                    "Transactions extraites",
                    style={
                        "fontFamily":  FONTS["sans"],
                        "fontSize":    "11px",
                        "fontWeight":  "700",
                        "letterSpacing": "0.06em",
                        "textTransform": "uppercase",
                        "color":       COLORS["muted"],
                        "marginBottom": f"{SPACE['sm']}px",
                        "paddingBottom": f"{SPACE['xs']}px",
                        "borderBottom": f"1px solid {COLORS['border_light']}",
                    },
                ),

                # Column headers
                html.Div(
                    [
                        html.Span("Date",        style=_header_style("88px")),
                        html.Span("Description", style=_header_style("1")),
                        html.Span("Montant",     style=_header_style("80px")),
                        html.Span("Réf.",        style=_header_style("96px")),
                    ],
                    style={
                        "display": "flex", "gap": "6px",
                        "marginBottom": "4px",
                        "padding": "0 4px",
                    },
                ),

                # One row per transaction
                html.Div(
                    [_tx_row(form_id, i, tx) for i, tx in enumerate(transactions)]
                    if transactions
                    else [html.Div(
                        "Aucune transaction extraite — saisissez-les manuellement ci-dessous.",
                        style={
                            "fontFamily": FONTS["sans"],
                            "fontSize":   "12px",
                            "color":      COLORS["muted"],
                            "padding":    f"{SPACE['sm']}px",
                        },
                    )],
                    style={
                        "maxHeight":  "360px",
                        "overflowY":  "auto",
                        "paddingRight": "4px",
                    },
                ),

                html.Div(
                    f"{len(transactions)} transaction(s) prête(s) à réviser",
                    style={
                        "fontFamily":  FONTS["sans"],
                        "fontSize":    "11px",
                        "color":       COLORS["ok"] if transactions else COLORS["muted"],
                        "marginTop":   f"{SPACE['sm']}px",
                        "textAlign":   "right",
                    },
                ) if transactions else None,
            ],
            style={
                "marginTop":       f"{SPACE['md']}px",
                "padding":         f"{SPACE['md']}px",
                "backgroundColor": COLORS["cream"],
                "borderRadius":    RADIUS["md"],
                "border":          f"1px solid {COLORS['border_light']}",
            },
        ),
    ])


def _header_style(flex_or_width: str) -> dict:
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
        base["width"]     = flex_or_width
        base["flexShrink"] = "0"
    return base


def _tx_row(form_id: str, index: int, tx: dict) -> html.Div:
    """
    Renders one editable transaction row.

    Args:
        form_id: Parent form identifier (for pattern-matching IDs).
        index:   Row index.
        tx:      Dict with keys date, description, amount, ref.

    Returns:
        A flex row of four dcc.Input fields.
    """
    _input_style = {
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

    return html.Div(
        [
            html.Div(
                dcc.DatePickerSingle(
                    id={"type": "form-date", "form": form_id, "field": f"tx_{index}_date"},
                    date=tx.get("date", "") or None,
                    display_format="DD/MM/YY",
                    placeholder="JJ/MM/AA",
                    with_portal=True,
                    style={"width": "100%"},
                ),
                style={"width": "88px", "flexShrink": "0", "overflow": "hidden"},
            ),
            dcc.Input(
                id={"type": "form-field", "form": form_id, "field": f"tx_{index}_desc"},
                type="text",
                value=tx.get("description", ""),
                placeholder="Description",
                style={**_input_style, "flex": "1", "minWidth": "0"},
                debounce=True,
            ),
            dcc.Input(
                id={"type": "form-field", "form": form_id, "field": f"tx_{index}_amount"},
                type="text",
                value=tx.get("amount", ""),
                placeholder="0.00",
                style={**_input_style, "width": "80px", "flexShrink": "0", "textAlign": "right"},
                debounce=True,
            ),
            dcc.Input(
                id={"type": "form-field", "form": form_id, "field": f"tx_{index}_ref"},
                type="text",
                value=tx.get("ref", ""),
                placeholder="TXN-…",
                style={**_input_style, "width": "96px", "flexShrink": "0",
                       "fontSize": "10px", "color": COLORS["muted"]},
                debounce=True,
            ),
        ],
        style={
            "display":      "flex",
            "gap":          "6px",
            "marginBottom": "4px",
            "alignItems":   "center",
        },
    )
