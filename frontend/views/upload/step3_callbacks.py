"""
Callbacks for Step 3 — document type selection and file upload.

Components targeted here only exist on the Step 3 page (/upload),
so there is no risk of cross-page callback contamination.
"""

import os
import logging

from dash import ALL, Input, Output, State, callback, ctx, html, no_update

from frontend.theme            import COLORS, FONTS, SPACE, RADIUS, BTN_PRIMARY
from frontend.components.doc_tile import doc_tile
from frontend.views.upload._doc_types import ACCEPTED_FORMATS, DOC_TYPES

log = logging.getLogger(__name__)


# ── Type selection ────────────────────────────────────────────────────────────

@callback(
    Output("selected-doc-type",   "data"),
    Output("doc-tiles-container", "children"),
    Output("right-column",        "children"),
    Output("fields-col",          "children"),
    [Input(f"tile-{doc['id']}", "n_clicks") for doc in DOC_TYPES],
    State("selected-doc-type",    "data"),
    prevent_initial_call=True,
)
def select_doc_type(*args):
    """
    Fires when any doc-type tile is clicked.

    Updates the store, re-renders tiles, the upload card, and the
    fields preview for the newly selected document type.

    Args:
        *args: n_clicks for each tile followed by the current doc type.
    """
    *_, current_type = args
    triggered = ctx.triggered_id

    if not triggered or not triggered.startswith("tile-"):
        return no_update, no_update, no_update, no_update

    new_type  = triggered.replace("tile-", "")
    new_tiles = [doc_tile(doc, doc["id"] == new_type) for doc in DOC_TYPES]

    from frontend.views.upload.step3_type import _upload_card, _fields_card
    return new_type, new_tiles, [_upload_card(new_type)], [_fields_card(new_type)]


# ── File upload ───────────────────────────────────────────────────────────────

@callback(
    Output("upload-file-list",     "children"),
    Output("upload-errors",        "children"),
    Output("btn-confirm-upload",   "disabled"),
    Output("btn-confirm-upload",   "style"),
    Output("uploaded-files-store", "data"),
    Input("dcc-upload",            "contents"),
    State("dcc-upload",            "filename"),
    State("selected-doc-type",     "data"),
    prevent_initial_call=True,
)
def handle_upload(contents_list, filenames, doc_type):
    """
    Fires when the user drops or selects files in the upload zone.

    Validates each file's extension against the accepted formats for the
    current doc type, renders a status row for each file, and enables the
    confirm button only when at least one valid file is present.

    Args:
        contents_list: Base64-encoded file content(s) from dcc.Upload.
        filenames:     Corresponding filename(s).
        doc_type:      Currently selected document type ID.

    Returns:
        Tuple of (file_rows, error_alerts, btn_disabled, btn_style, stored_files).
    """
    if not contents_list:
        return [], [], True, {**BTN_PRIMARY, "opacity": "0.5"}, []

    if isinstance(contents_list, str):
        contents_list = [contents_list]
        filenames     = [filenames]

    accepted_exts               = ACCEPTED_FORMATS.get(doc_type, [])
    valid_files, error_names    = [], []
    file_rows,   stored         = [], []

    for i, (content, filename) in enumerate(zip(contents_list, filenames)):
        ext      = os.path.splitext(filename)[1].lower()
        is_valid = ext in accepted_exts

        if is_valid:
            valid_files.append(filename)
            stored.append({"filename": filename, "content": content, "ext": ext})
        else:
            error_names.append(filename)

        file_rows.append(_file_row(filename, ext, is_valid, i))

    has_valid = bool(valid_files)
    btn_style = BTN_PRIMARY if has_valid else {**BTN_PRIMARY, "opacity": "0.5"}

    return (
        html.Div(file_rows, style={"marginTop": "8px"}),
        [_error_alert(n, accepted_exts) for n in error_names],
        not has_valid,
        btn_style,
        stored,
    )


@callback(
    Output("uploaded-files-store", "data",     allow_duplicate=True),
    Output("upload-file-list",     "children", allow_duplicate=True),
    Output("btn-confirm-upload",   "disabled", allow_duplicate=True),
    Output("btn-confirm-upload",   "style",    allow_duplicate=True),
    Input({"type": "btn-remove-file", "index": ALL}, "n_clicks"),
    State("uploaded-files-store",  "data"),
    prevent_initial_call=True,
)
def remove_file(n_clicks_list, stored_files):
    """
    Removes a file from the staged list when its ✕ button is clicked.

    Uses pattern-matching ALL so one callback handles every remove button
    regardless of how many files are currently staged.

    Args:
        n_clicks_list: Click counts for all visible remove buttons.
        stored_files:  Currently staged file dicts.

    Returns:
        Updated (store, file_rows, btn_disabled, btn_style).
    """
    if not any(n for n in n_clicks_list if n and n > 0):
        return no_update, no_update, no_update, no_update

    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return no_update, no_update, no_update, no_update

    updated = [
        f for i, f in enumerate(stored_files or [])
        if i != triggered["index"]
    ]
    rows = [
        _file_row(f["filename"], f.get("ext", ""), True, i)
        for i, f in enumerate(updated)
    ]
    has_valid = bool(updated)
    btn_style = BTN_PRIMARY if has_valid else {**BTN_PRIMARY, "opacity": "0.5"}

    return updated, html.Div(rows, style={"marginTop": "8px"}), not has_valid, btn_style


# ── Navigation ────────────────────────────────────────────────────────────────

@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("btn-confirm-upload", "n_clicks"),
    Input("btn-manual-entry",   "n_clicks"),
    State("uploaded-files-store", "data"),
    State("url",                  "pathname"),
    prevent_initial_call=True,
)
def navigate(confirm, manual, stored_files, pathname):
    """
    Navigates to Step 4 when the user confirms an upload or chooses manual entry.

    Ignores the call if we are already on the forms page to avoid
    re-triggering after navigation.

    Args:
        confirm:      Click count on the confirm button.
        manual:       Click count on the manual entry button.
        stored_files: Currently staged file dicts.
        pathname:     Current browser pathname.

    Returns:
        New pathname or no_update.
    """
    if pathname == "/upload/forms":
        return no_update

    triggered = ctx.triggered_id

    if triggered == "btn-confirm-upload" and confirm and stored_files:
        return "/upload/forms"

    if triggered == "btn-manual-entry":
        return "/upload/forms"

    return no_update


# ── Private renderers ─────────────────────────────────────────────────────────

def _file_row(filename: str, ext: str, is_valid: bool, index: int) -> html.Div:
    """
    Renders one file row with icon, name, status badge, and remove button.

    Args:
        filename: Original filename.
        ext:      File extension (e.g. ".pdf").
        is_valid: Whether the format is accepted for the current doc type.
        index:    Position in the file list (used for the remove button ID).

    Returns:
        Styled row div.
    """
    icon = (
        "🖼" if ext in (".jpg", ".jpeg", ".png")
        else "📄" if ext == ".pdf"
        else "📊" if ext == ".xlsx"
        else "📝"
    )
    return html.Div(
        [
            html.Span(icon, style={"fontSize": "14px", "flexShrink": "0"}),
            html.Span(filename, style={
                "fontFamily": FONTS["sans"],
                "fontSize":   "12px",
                "flex":       "1",
                "color":      COLORS["ink"] if is_valid else COLORS["error"],
            }),
            html.Span(
                f"{ext.upper().lstrip('.')} ✓" if is_valid else "Type invalide",
                style={
                    "fontFamily":      FONTS["mono"],
                    "fontSize":        "10px",
                    "fontWeight":      "600",
                    "padding":         "2px 7px",
                    "borderRadius":    RADIUS["sm"],
                    "backgroundColor": COLORS["ok_bg"]    if is_valid else COLORS["error_bg"],
                    "color":           COLORS["ok"]       if is_valid else COLORS["error"],
                },
            ),
            html.Button(
                "✕",
                id={"type": "btn-remove-file", "index": index},
                n_clicks=0,
                style={
                    "background": "none",
                    "border":     "none",
                    "cursor":     "pointer",
                    "color":      COLORS["muted"],
                    "fontSize":   "14px",
                    "fontWeight": "600",
                    "padding":    "0 4px",
                    "lineHeight": "1",
                    "flexShrink": "0",
                },
            ),
        ],
        style={
            "display":         "flex",
            "alignItems":      "center",
            "gap":             "8px",
            "padding":         f"{SPACE['xs']}px {SPACE['sm']}px",
            "backgroundColor": COLORS["cream"]     if is_valid else COLORS["error_bg"],
            "borderRadius":    RADIUS["sm"],
            "marginBottom":    "4px",
        },
    )


def _error_alert(filename: str, accepted: list) -> html.Div:
    """
    Renders a warning banner for a file that failed format validation.

    Args:
        filename: Name of the rejected file.
        accepted: List of accepted extensions for this doc type.

    Returns:
        Warning div.
    """
    return html.Div(
        [
            html.Span("⚠️ ", style={"flexShrink": "0"}),
            html.Span(
                f"{filename} — format non accepté. "
                f"Formats attendus : {', '.join(accepted)}. Ce fichier sera ignoré.",
                style={
                    "fontFamily": FONTS["sans"],
                    "fontSize":   "12px",
                    "color":      COLORS["warning"],
                },
            ),
        ],
        style={
            "display":         "flex",
            "gap":             "8px",
            "padding":         f"{SPACE['sm']}px {SPACE['md']}px",
            "backgroundColor": COLORS["warning_bg"],
            "borderRadius":    RADIUS["md"],
            "marginTop":       "8px",
            "border":          "1px solid #ef9f27",
        },
    )
