"""
Shared form section builder.

Used by both step3_callbacks.py and step4_callbacks.py
to avoid circular imports.
"""

from dash import html
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS, CARD,
    BTN_PRIMARY, BTN_SECONDARY,
)
from frontend.views.upload.form_fields.receipt   import receipt_form
from frontend.views.upload.form_fields.statement import statement_form
from frontend.views.upload.form_fields.invoice   import invoice_form
from frontend.views.upload.form_fields.manual    import manual_form


def build_badge(status: str) -> html.Span:
    """Renders a status badge for a form section header."""
    configs = {
        "ok":       ("OCR OK",        "#eaf3de", "#27500a"),
        "warning":  ("Avertissement", "#faeeda", "#633806"),
        "error":    ("Erreurs",       "#fcebeb", "#791f1f"),
        "informal": ("Informel",      "#f1efe8", "#444441"),
        "manual":   ("Manuel",        "#eeedfe", "#3c3489"),
    }
    label, bg, color = configs.get(status, configs["ok"])
    return html.Span(label, style={
        "fontFamily":      "'DM Mono', monospace",
        "fontSize":        "10px",
        "fontWeight":      "600",
        "padding":         "2px 8px",
        "borderRadius":    "4px",
        "backgroundColor": bg,
        "color":           color,
    })


def build_preview_panel(index: int, content: str, filename: str) -> html.Div:
    """Renders the document preview panel (iframe or img)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        preview = html.Iframe(
            src=content,
            style={"width": "100%", "height": "300px",
                   "border": "1px solid #c9c3b5", "borderRadius": "6px"},
        )
    elif ext in ["jpg", "jpeg", "png", "webp"]:
        preview = html.Img(
            src=content,
            style={"maxWidth": "100%", "maxHeight": "280px",
                   "objectFit": "contain", "borderRadius": "6px",
                   "border": "1px solid #c9c3b5"},
        )
    else:
        preview = html.Div("Aperçu non disponible.",
                           style={"fontFamily": "'DM Sans', sans-serif",
                                  "fontSize": "12px", "color": "#6b6557",
                                  "padding": "16px"})

    return html.Div(
        preview,
        id={"type": "preview-panel", "index": index},
        style={"marginBottom": "16px", "display": "none"},
    )


def build_form_section(
    index:    int,
    filename: str,
    content:  str,
    doc_type: str,
    data:     dict,
    status:   str,
) -> html.Div:
    """
    Builds one complete form section.

    Args:
        index:    Section index for pattern-matching IDs.
        filename: Original filename or "manual" for manual entry.
        content:  Base64 file content for preview.
        doc_type: Document type ID.
        data:     Pre-filled field values.
        status:   Validation status badge.
    """
    is_manual = filename == "manual"

    if is_manual and doc_type == "REC":
        form_body = receipt_form(f"form-{index}", {}, "manual")
    elif is_manual and doc_type == "INV":
        form_body = invoice_form(f"form-{index}", {})
    elif is_manual:
        form_body = manual_form(f"form-{index}", doc_type, data)
    elif doc_type == "REC":
        form_body = receipt_form(f"form-{index}", data, status)
    elif doc_type == "STMT":
        form_body = statement_form(f"form-{index}", data)
    elif doc_type == "INV":
        form_body = invoice_form(f"form-{index}", data)
    else:
        form_body = manual_form(f"form-{index}", doc_type, data)

    return html.Div(
        [
            # Header
            html.Div(
                [
                    html.Div(str(index + 1), className="section-number"),
                    build_badge(status),
                    html.Span(
                        "Saisie manuelle" if is_manual else filename,
                        className="section-title-text",
                        style={"marginLeft": "8px"},
                    ),
                    html.Button(
                        [html.I(className="fa-solid fa-eye",
                                style={"marginRight": "6px"}), "Aperçu"],
                        id={"type": "btn-toggle-preview", "index": index},
                        n_clicks=0,
                        style={**BTN_SECONDARY, "padding": "3px 10px",
                               "fontSize": "11px"},
                    ) if not is_manual and content else None,
                    html.Button(
                        html.I(className="fa-solid fa-xmark"),
                        id={"type": "btn-remove-section", "index": index},
                        n_clicks=0,
                        style={**BTN_SECONDARY, "padding": "3px 8px",
                               "fontSize": "13px",
                               "color": "#b5361c", "marginLeft": "4px"},
                    ),
                ],
                className="section-header",
            ),
            # Preview
            html.Div(
                build_preview_panel(index, content, filename)
                if not is_manual else html.Div(),
                style={"padding": "0 20px"},
            ),
            # Form body
            html.Div(form_body, className="section-body"),
        ],
        id={"type": "form-section", "index": index},
        className="form-card",
    )