"""
Document type definitions and accepted format mappings.

Single source of truth for all document type metadata.
Adding a new document type = adding one entry to DOC_TYPES.
"""

from frontend.theme import COLORS

DOC_TYPES: list[dict] = [
    {
        "id":          "REC",
        "icon":        "🧾",
        "icon_bg":     COLORS["warning_bg"],
        "label":       "Reçu / facture reçue",
        "sublabel":    "Dépense",
        "description": (
            "Reçus imprimés ou manuscrits. Chaque fichier génère "
            "un formulaire séparé. L'OCR extrait le marchand, "
            "la date et le total."
        ),
        "formats":     "JPG, PNG, PDF",
        "multi":       True,
    },
    {
        "id":          "STMT",
        "icon":        "💳",
        "icon_bg":     COLORS["info_bg"],
        "label":       "Relevé bancaire / carte",
        "sublabel":    "Historique de transactions",
        "description": (
            "Relevé mensuel PDF ou export XLSX. "
            "Un seul fichier par source de paiement. "
            "Toutes les transactions sont extraites automatiquement."
        ),
        "formats":     "PDF, XLSX",
        "multi":       False,
    },
    {
        "id":          "INV",
        "icon":        "📋",
        "icon_bg":     COLORS["ok_bg"],
        "label":       "Facture émise (revenu)",
        "sublabel":    "Revenu client",
        "description": (
            "Factures envoyées à vos clients. "
            "XLSX multi-lignes ou PDF unitaire. "
            "Saisie manuelle possible sans fichier."
        ),
        "formats":     "PDF, XLSX",
        "multi":       True,
    },
    {
        "id":          "NOTE",
        "icon":        "📝",
        "icon_bg":     COLORS["badge_gray_bg"],
        "label":       "Notes / contexte",
        "sublabel":    "Tâches et annotations",
        "description": (
            "Fichier .txt avec notes libres, tâches [todo] et "
            "éléments [done]. Aucune transaction créée — "
            "les tâches sont extraites séparément."
        ),
        "formats":     "TXT",
        "multi":       False,
    },
]

# Accepted file extensions per doc type
ACCEPTED_FORMATS: dict[str, list[str]] = {
    "REC":  [".jpg", ".jpeg", ".png", ".pdf"],
    "STMT": [".pdf", ".xlsx"],
    "INV":  [".pdf", ".xlsx"],
    "NOTE": [".txt"],
}

# MIME accept string for dcc.Upload per doc type
ACCEPT_MIME: dict[str, str] = {
    "REC":  "image/*,.pdf",
    "STMT": ".pdf,.xlsx",
    "INV":  ".pdf,.xlsx",
    "NOTE": ".txt",
}