"""Generic manual entry form for any document type."""

from dash import html
from frontend.theme import COLORS, FONTS, SPACE
from frontend.components.form_field import form_field


def manual_form(form_id: str, doc_type: str = "REC", data: dict | None = None) -> html.Div:
    """
    Renders a manual entry form, optionally pre-populated from parsed file data.

    Args:
        form_id:  Unique form instance identifier.
        doc_type: Document type — determines which extra fields to show.
        data:     Pre-parsed field values (e.g. note_text from a .txt file).
    """
    data      = data or {}
    is_note   = (doc_type == "NOTE")

    extra_fields = {
        "REC": [
            form_field("MARCHAND",          form_id, "merchant",
                       required=True,
                       placeholder="ex: Bureau en Gros"),
            form_field("SOURCE DE PAIEMENT", form_id, "source_label",
                       required=True,
                       placeholder="ex: Comptant"),
        ],
        "INV": [
            form_field("CLIENT",     form_id, "client",
                       required=True,
                       placeholder="ex: BrightPath Marketing"),
            form_field("N° FACTURE", form_id, "invoice_number",
                       placeholder="ex: INV-2025-001"),
        ],
        "STMT": [
            form_field("TRANS ID", form_id, "ref",
                       placeholder="ex: TXN-2025-001"),
        ],
        "NOTE": [
            form_field("TEXTE DE LA NOTE", form_id, "note_text",
                       required=True,
                       value=data.get("note_text", ""),
                       placeholder="Contenu de la note ou tâche",
                       input_type="textarea"),
        ],
    }.get(doc_type, [])

    common = [
        form_field("DESCRIPTION", form_id, "description",
                   required=not is_note,
                   placeholder="Description de l'entrée"),
        form_field("MONTANT",     form_id, "amount",
                   required=not is_note,
                   hint="Montant en CAD — négatif pour un remboursement",
                   placeholder="$0.00"),
        form_field("DATE",        form_id, "date",
                   required=not is_note,
                   input_type="date"),
    ]

    return html.Div([
        html.Div(common + extra_fields, className="field-group"),

        html.Div(
            [
                html.I(className="fa-solid fa-keyboard",
                       style={"marginRight": "8px",
                              "color": COLORS["badge_purple"]}),
                html.Span(
                    "Saisie manuelle — aucun fichier source associé.",
                    style={
                        "fontFamily": FONTS["sans"],
                        "fontSize":   "12px",
                        "color":      COLORS["badge_purple"],
                    },
                ),
            ],
            className="info-banner",
            style={
                "backgroundColor": COLORS["badge_purple_bg"],
                "border":          f"1px solid #c5c2f0",
                "marginTop":       f"{SPACE['md']}px",
            },
        ),
    ])
