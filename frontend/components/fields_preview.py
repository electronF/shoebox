"""
Fields preview component.

Shows the expected fields and their required/optional status
for the currently selected document type, with info tooltips.
"""

from dash import html
from frontend.theme import COLORS, FONTS, SPACE, RADIUS

# Field definitions per document type:
# (field_name, required, tooltip_hint)
_FIELDS: dict[str, list[tuple]] = {
    "REC": [
        ("Marchand",       True,  None),
        ("Date",           True,  None),
        ("Sous-total",     True,  "Montant hors taxes"),
        ("TPS (5%)",       False, "Taxe fédérale — calculée si absente"),
        ("TVQ (9.975%)",   False, "Taxe provinciale — calculée si absente"),
        ("Total TTC",      True,  "Montant final incluant les taxes"),
        ("Mode paiement",  False, None),
        ("N° transaction", False, "Présent sur les reçus officiels imprimés"),
    ],
    "STMT": [
        ("Période du",    True,  "Date de début du relevé"),
        ("Période au",    True,  "Date de fin du relevé"),
        ("Titulaire",     True,  None),
        ("Numéro carte",  True,  "4 derniers chiffres suffisent"),
        ("Date tx",       True,  "Par transaction"),
        ("Description",   True,  "Par transaction"),
        ("Montant",       True,  "Par transaction — négatif = remboursement"),
        ("Réf. tx",       False, "Identifiant unique de la transaction"),
    ],
    "INV": [
        ("N° facture",    True,  None),
        ("Client",        True,  None),
        ("Description",   True,  None),
        ("Montant HT",    True,  "Montant hors taxes"),
        ("TPS / TVQ",     False, None),
        ("Total facturé", True,  None),
        ("Date envoi",    False, None),
        ("Date paiement", False, "Laisser vide si non encore payée"),
        ("Statut",        True,  "payée · en attente · impayée · annulée"),
    ],
    "NOTE": [
        ("[todo] tâche",  False, "Crée un élément ouvert dans les actions"),
        ("[done] tâche",  False, "Crée un élément complété"),
        ("Notes libres",  False, "Ligne sans préfixe → note contextuelle"),
    ],
}


def fields_preview(doc_type_id: str) -> html.Div:
    """
    Renders the fields list for a given document type.

    Args:
        doc_type_id: Selected doc type ID (e.g. "REC").

    Returns:
        List of field rows with required/optional badges and tooltips.
    """
    fields = _FIELDS.get(doc_type_id, [])
    rows   = []

    for field_name, required, hint in fields:
        rows.append(_field_row(field_name, required, hint))

    return html.Div(rows)


def _field_row(name: str, required: bool, hint: str | None) -> html.Div:
    """Renders a single field row with badge and optional tooltip."""
    return html.Div(
        [
            # Field name + indicators
            html.Div(
                [
                    html.Span(name, style={
                        "fontFamily": FONTS["sans"],
                        "fontSize":   "13px",
                        "color":      COLORS["ink"],
                    }),
                    html.Span(" *", style={
                        "color":      COLORS["error"],
                        "fontSize":   "12px",
                        "marginLeft": "2px",
                    }) if required else None,
                    html.Span(" ℹ", title=hint, style={
                        "fontFamily": FONTS["mono"],
                        "fontSize":   "11px",
                        "color":      COLORS["info"],
                        "cursor":     "help",
                        "marginLeft": "4px",
                    }) if hint else None,
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            # Required / optional badge
            html.Span(
                "obligatoire" if required else "optionnel",
                style={
                    "fontFamily":      FONTS["mono"],
                    "fontSize":        "10px",
                    "color":           COLORS["ok"] if required else COLORS["muted"],
                    "backgroundColor": COLORS["ok_bg"] if required else COLORS["cream"],
                    "padding":         "1px 6px",
                    "borderRadius":    RADIUS["sm"],
                },
            ),
        ],
        style={
            "display":        "flex",
            "justifyContent": "space-between",
            "alignItems":     "center",
            "padding":        f"{SPACE['xs']}px 0",
            "borderBottom":   f"1px solid {COLORS['border_light']}",
        },
    )
