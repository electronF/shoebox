"""
Reusable form field component.

Single source of truth for all labelled inputs across
receipt, statement, invoice, and manual forms.

When input_type == "date", renders dcc.DatePickerSingle with ID type
"form-date" (not "form-field"). The handle_submit callback in
step4_callbacks.py collects both patterns separately.
"""

from dash import html, dcc
from frontend.theme import COLORS


def form_field(
    label:        str,
    form_id:      str,
    field_id:     str,
    value:        str  = "",
    required:     bool = False,
    hint:         str|None  = None,
    field_status: str  = "neutral",
    input_type:   str  = "text",
    placeholder:  str  = "",
) -> html.Div:
    """
    Renders a labelled input field with status styling.

    When input_type == "date", renders dcc.DatePickerSingle (ID type
    "form-date", property "date") instead of dcc.Input (ID type
    "form-field", property "value").

    Args:
        label:        Uppercase label text.
        form_id:      Parent form identifier (for pattern-matching IDs).
        field_id:     Field identifier within the form.
        value:        Pre-filled value (from OCR or defaults).
        required:     Shows red label and asterisk when True.
        hint:         Tooltip text shown on the info icon.
        field_status: "ok" | "error" | "warning" | "neutral"
        input_type:   "text", "number", or "date" (renders DatePickerSingle).
        placeholder:  Placeholder text shown when field is empty.

    Returns:
        A labelled input with optional tooltip and error message.
    """
    label_class = "field-label-required" if required else "field-label"

    input_class = {
        "ok":      "dash-input input-ok",
        "error":   "dash-input input-error",
        "warning": "dash-input input-warning",
    }.get(field_status, "dash-input")

    label_row = html.Div(
        [
            html.Span(label, className=label_class),
            html.Span(" *", className="required-star") if required else None,
            html.I(
                className="fa-solid fa-circle-info",
                title=hint,
                style={
                    "color":      COLORS["info"],
                    "fontSize":   "11px",
                    "cursor":     "help",
                    "marginLeft": "4px",
                },
            ) if hint else None,
        ],
        style={
            "display":     "flex",
            "alignItems":  "center",
            "marginBottom": "5px",
        },
    )

    error_row = html.Div(
        [
            html.I(
                className="fa-solid fa-circle-exclamation",
                style={"marginRight": "4px"},
            ),
            "Champ requis — veuillez remplir ce champ.",
        ],
        className="field-error-msg",
        style={"display": "flex" if field_status == "error" else "none"},
    )

    if input_type == "date":
        control = dcc.DatePickerSingle(
            id={"type": "form-date", "form": form_id, "field": field_id},
            date=value if value else None,
            display_format="DD/MM/YYYY",
            placeholder="JJ/MM/AAAA",
            style={"width": "100%"},
        )
    elif input_type == "textarea":
        control = dcc.Textarea(
            id={"type": "form-field", "form": form_id, "field": field_id},
            value=value,
            placeholder=placeholder,
            className=input_class,
            style={"width": "100%", "minHeight": "140px", "resize": "vertical",
                   "fontFamily": "inherit", "fontSize": "12px"},
        )
    else:
        control = dcc.Input(
            id={"type": "form-field", "form": form_id, "field": field_id},
            value=value,
            type=input_type,
            placeholder=placeholder,
            className=input_class,
            debounce=True,
        )

    return html.Div(
        [label_row, control, error_row],
        style={"display": "flex", "flexDirection": "column"},
    )
