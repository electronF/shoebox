"""
File upload popup overlay component.

Renders the modal with drag-and-drop zone, format validation,
and file list. Opened by the method_section upload button.
"""

from dash import html, dcc
from frontend.theme import (
    COLORS, FONTS, SPACE, RADIUS, SHADOW,
    BTN_PRIMARY, BTN_SECONDARY, DROPZONE,
)
from frontend.views.upload._doc_types import DOC_TYPES, ACCEPT_MIME


def upload_popup(
    selected_type: str,
    page_id: str = "s3",
    is_open: bool = False,
) -> html.Div:
    """
    Renders the file upload popup overlay.

    Args:
        selected_type: Currently selected doc type ID.
        page_id:       Namespace suffix for all internal IDs so that
                       step3 (page_id="s3") and step4 (page_id="s4")
                       each own distinct component IDs.
        is_open:       Whether to display the popup on initial render.

    Returns:
        Fixed-position overlay with upload zone and actions.
    """
    doc    = next((d for d in DOC_TYPES if d["id"] == selected_type), DOC_TYPES[0])
    accept = ACCEPT_MIME.get(selected_type, "*")

    return html.Div(
        _popup_inner(doc, accept, page_id),
        id=f"upload-popup-overlay-{page_id}",
        style={
            "display":         "flex" if is_open else "none",
            "position":        "fixed",
            "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "backgroundColor": "rgba(0,0,0,0.45)",
            "alignItems":      "center",
            "justifyContent":  "center",
            "zIndex":          "1000",
        },
    )


def _popup_inner(doc: dict, accept: str, page_id: str) -> html.Div:
    """
    Renders the inner popup card.

    Args:
        doc:     Doc-type metadata dict.
        accept:  MIME type string for the dcc.Upload widget.
        page_id: ID namespace suffix.

    Returns:
        Styled card div containing header, upload zone, and actions.
    """
    return html.Div(
        [
            _popup_header(doc, page_id),
            _popup_format_info(doc),
            dcc.Upload(
                id=f"dcc-upload-{page_id}",
                children=_dropzone_content(),
                style=DROPZONE,
                multiple=doc["multi"],
                accept=accept,
            ),
            html.Div(id=f"uploaded-files-list-{page_id}"),
            html.Div(id=f"upload-format-errors-{page_id}"),
            _popup_actions(page_id),
        ],
        style={
            "backgroundColor": COLORS["white"],
            "borderRadius":    RADIUS["xl"],
            "padding":         f"{SPACE['2xl']}px",
            "width":           "100%",
            "maxWidth":        "520px",
            "boxShadow":       SHADOW["lg"],
        },
    )


def _popup_header(doc: dict, page_id: str) -> html.Div:
    """
    Renders the popup header with title and close button.

    Args:
        doc:     Doc-type metadata dict.
        page_id: ID namespace suffix.

    Returns:
        Flex row with label and close button.
    """
    return html.Div(
        [
            html.Div([
                html.Span(doc["icon"], style={"marginRight": "8px", "fontSize": "16px"}),
                html.Span(f"Sélectionner — {doc['label']}", style={
                    "fontFamily": FONTS["sans"],
                    "fontSize":   "14px",
                    "fontWeight": "600",
                    "color":      COLORS["ink"],
                }),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Button("✕", id=f"btn-close-popup-{page_id}", n_clicks=0, style={
                **BTN_SECONDARY, "padding": "4px 10px", "fontSize": "14px",
            }),
        ],
        style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center", "marginBottom": f"{SPACE['md']}px",
        },
    )


def _popup_format_info(doc: dict) -> html.Div:
    """
    Renders the accepted formats hint below the header.

    Args:
        doc: Doc-type metadata dict.

    Returns:
        Div with format label and value.
    """
    return html.Div(
        [
            html.Span("Formats acceptés : ", style={
                "fontFamily": FONTS["sans"], "fontSize": "12px", "color": COLORS["muted"],
            }),
            html.Span(doc["formats"], style={
                "fontFamily": FONTS["mono"], "fontSize": "12px",
                "fontWeight": "600", "color": COLORS["ink"],
            }),
        ],
        style={"marginBottom": f"{SPACE['md']}px"},
    )


def _dropzone_content() -> html.Div:
    """
    Renders the drag-and-drop zone inner content.

    Returns:
        Centred div with icon, primary and secondary text.
    """
    return html.Div(
        [
            html.Div("☁️", style={"fontSize": "28px", "marginBottom": "8px"}),
            html.Div("Glisser-déposer ici", style={
                "fontFamily": FONTS["sans"], "fontSize": "13px",
                "fontWeight": "600", "color": COLORS["ink"], "marginBottom": "4px",
            }),
            html.Div("ou cliquer pour parcourir", style={
                "fontFamily": FONTS["sans"], "fontSize": "12px", "color": COLORS["muted"],
            }),
        ],
        style={"textAlign": "center"},
    )


def _popup_actions(page_id: str) -> html.Div:
    """
    Renders the cancel and confirm action buttons.

    Args:
        page_id: ID namespace suffix.

    Returns:
        Flex row with cancel and confirm buttons.
    """
    return html.Div(
        [
            html.Button(
                "Annuler",
                id=f"btn-cancel-upload-{page_id}",
                n_clicks=0,
                style=BTN_SECONDARY,
            ),
            html.Button(
                "Extraire et créer formulaires →",
                id=f"btn-confirm-upload-{page_id}",
                n_clicks=0,
                disabled=True,
                style={**BTN_PRIMARY, "opacity": "0.5"},
            ),
        ],
        style={
            "display": "flex", "justifyContent": "flex-end",
            "gap": f"{SPACE['sm']}px", "marginTop": f"{SPACE['md']}px",
        },
    )
