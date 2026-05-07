"""
Callbacks for Step 4 — form generation, validation, and submission.

All components targeted here (forms-container, upload-panel-s4, etc.)
exist only on the Step 4 page (/upload/forms), so there is no risk of
cross-page callback contamination.
"""

import base64
import logging
import os
from collections import defaultdict

from dash import ALL, MATCH, Input, Output, State, callback, ctx, html, no_update

import frontend.api_client as api
from frontend.theme import COLORS, FONTS, SPACE, RADIUS, BTN_PRIMARY, BTN_SECONDARY
from frontend.views.upload._doc_types import ACCEPTED_FORMATS, DOC_TYPES
from frontend.views.upload.form_builder import build_form_section

log = logging.getLogger(__name__)

_REQUIRED_PER_TYPE: dict[str, set[str]] = {
    "REC":  {"merchant", "date", "total"},
    "STMT": {"holder", "last_four", "period_from", "period_to"},
    "INV":  {"client", "amount", "date_sent"},
    "NOTE": {"note_text"},
}
_REQUIRED_MANUAL: set[str] = {"description", "amount", "date"}

_FIELD_LABELS: dict[str, str] = {
    "merchant":    "Marchand",
    "date":        "Date",
    "total":       "Total TTC",
    "holder":      "Titulaire",
    "last_four":   "Numéro de carte",
    "period_from": "Période du",
    "period_to":   "Période au",
    "client":      "Client",
    "amount":      "Montant",
    "date_sent":   "Date d'envoi",
    "note_text":   "Texte de la note",
}


# ── Form generation ───────────────────────────────────────────────────────────

_DOC_TYPE_LABELS: dict[str, tuple[str, str]] = {
    "REC":  ("Reçus",             "fa-solid fa-receipt"),
    "STMT": ("Relevé de carte",   "fa-solid fa-credit-card"),
    "INV":  ("Factures émises",   "fa-solid fa-file-invoice-dollar"),
    "NOTE": ("Notes",             "fa-solid fa-note-sticky"),
}


def _doc_type_badge(doc_type: str) -> html.Div:
    label, icon = _DOC_TYPE_LABELS.get(doc_type or "", ("—", "fa-solid fa-file"))
    return html.Div(
        [
            html.I(className=icon, style={"marginRight": "7px", "fontSize": "13px"}),
            html.Span(label, style={"fontWeight": "600"}),
        ],
        style={
            "display":         "inline-flex",
            "alignItems":      "center",
            "fontFamily":      FONTS["sans"],
            "fontSize":        "12px",
            "color":           COLORS["ink"],
            "backgroundColor": COLORS["cream"],
            "border":          f"1px solid {COLORS['border']}",
            "borderRadius":    "20px",
            "padding":         "4px 14px",
        },
    )


@callback(
    Output("forms-container",      "children"),
    Output("forms-summary-banner", "children"),
    Output("step4-doc-type",       "data"),
    Output("step4-doc-type-label", "children"),
    Input("step4-mount-trigger",   "n_intervals"),
    State("uploaded-files-store",  "data"),
    State("selected-doc-type",     "data"),
    prevent_initial_call=True,
)
def generate_forms(n_intervals: int, stored_files: list, doc_type: str):
    """
    Generates form sections by parsing uploaded files.

    Fires once after the DOM is ready (max_intervals=1 on the interval).
    For each file, calls POST /files/parse to extract field values.
    Falls back to a blank manual form if no files are staged.

    Args:
        n_intervals:  Fires once after mount.
        stored_files: Files staged in Step 3.
        doc_type:     Document type selected in Step 3.

    Returns:
        Tuple of (form_sections, summary_banner, doc_type, doc_type_label).
    """
    if not n_intervals:
        return no_update, no_update, no_update

    sections = []
    errors   = 0

    if stored_files:
        for i, file_info in enumerate(stored_files):
            filename = file_info.get("filename", f"fichier_{i}")
            content  = file_info.get("content", "")

            try:
                raw_bytes = base64.b64decode(
                    content.split(",")[1] if "," in content else content
                )
                result    = api.parse_file_preview(filename, raw_bytes, doc_type or "REC")
                extracted = result.get("data", {})
                status    = result.get("status", "ok")
            except Exception as exc:
                log.error("Parse preview failed for '%s': %s", filename, exc)
                extracted = {}
                status    = "error"

            if status == "error":
                errors += 1

            sections.append(build_form_section(
                index=i,
                filename=filename,
                content=content,
                doc_type=doc_type or "REC",
                data=extracted,
                status=status if status in ("ok", "warning", "error") else "ok",
            ))
    else:
        sections.append(build_form_section(
            index=0, filename="manual", content="",
            doc_type=doc_type or "REC", data={}, status="manual",
        ))

    return sections, _summary_banner(len(sections), errors), doc_type, _doc_type_badge(doc_type)


# ── Add-file inline panel ─────────────────────────────────────────────────────

@callback(
    Output("upload-panel-s4", "style"),
    Input("btn-add-from-file", "n_clicks"),
    Input("btn-cancel-s4",     "n_clicks"),
    Input("btn-cancel2-s4",    "n_clicks"),
    Input("btn-confirm-s4",    "n_clicks"),
    State("url",               "pathname"),
    prevent_initial_call=True,
)
def toggle_upload_panel(
    from_file_clicks: int,
    cancel_clicks: int,
    cancel2_clicks: int,
    confirm_clicks: int,
    pathname: str,
):
    """
    Shows the inline upload panel when "Charger un fichier" is clicked,
    hides it on cancel or after confirm.

    Args:
        from_file_clicks: Clicks on "Charger un fichier" menu item.
        cancel_clicks:    Clicks on the ✕ header button.
        cancel2_clicks:   Clicks on the "Annuler" footer button.
        confirm_clicks:   Clicks on "Ajouter au formulaire →".
        pathname:         Current browser pathname.

    Returns:
        Style dict for the upload panel div.
    """
    if pathname != "/upload/forms":
        return no_update

    triggered = ctx.triggered_id
    if not triggered:
        return no_update

    _visible = {
        "display":         "block",
        "backgroundColor": COLORS["white"],
        "border":          f"1px solid {COLORS['border']}",
        "borderRadius":    RADIUS["lg"],
        "padding":         f"{SPACE['lg']}px",
        "marginBottom":    f"{SPACE['md']}px",
        "boxShadow":       "0 2px 8px rgba(0,0,0,0.06)",
    }
    _hidden = {**_visible, "display": "none"}

    if triggered == "btn-add-from-file" and from_file_clicks:
        return _visible
    return _hidden


@callback(
    Output("upload-file-list-s4",  "children"),
    Output("upload-errors-s4",     "children"),
    Output("btn-confirm-s4",       "disabled"),
    Output("btn-confirm-s4",       "style"),
    Output("uploaded-files-store", "data",     allow_duplicate=True),
    Input("dcc-upload-s4",         "contents"),
    State("dcc-upload-s4",         "filename"),
    State("step4-doc-type",        "data"),
    State("uploaded-files-store",  "data"),
    prevent_initial_call=True,
)
def handle_upload_s4(
    contents_list,
    filenames,
    doc_type: str,
    existing: list,
):
    """
    Validates files dropped into the Step 4 upload panel.

    Appends valid files to the existing store without replacing it,
    so previously staged files are preserved.

    Args:
        contents_list: Base64-encoded file contents from dcc.Upload.
        filenames:     Corresponding filenames.
        doc_type:      Active document type.
        existing:      Files already in the store.

    Returns:
        Tuple of (file_rows, error_alerts, btn_disabled, btn_style, updated_store).
    """
    if not contents_list:
        return [], [], True, {**BTN_PRIMARY, "opacity": "0.5"}, no_update

    if isinstance(contents_list, str):
        contents_list = [contents_list]
        filenames     = [filenames]

    accepted_exts            = ACCEPTED_FORMATS.get(doc_type or "REC", [])
    error_names, file_rows   = [], []
    new_files                = []

    for i, (content, filename) in enumerate(zip(contents_list, filenames)):
        ext      = os.path.splitext(filename)[1].lower()
        is_valid = ext in accepted_exts or not accepted_exts

        if is_valid:
            new_files.append({"filename": filename, "content": content, "ext": ext})
        else:
            error_names.append(filename)

        file_rows.append(_file_row_s4(filename, ext, is_valid, i))

    has_valid     = bool(new_files)
    btn_style     = BTN_PRIMARY if has_valid else {**BTN_PRIMARY, "opacity": "0.5"}
    updated_store = (existing or []) + new_files

    return (
        html.Div(file_rows, style={"marginTop": "8px"}),
        [_error_alert_s4(n, accepted_exts) for n in error_names],
        not has_valid,
        btn_style,
        updated_store,
    )


@callback(
    Output("forms-container",      "children",  allow_duplicate=True),
    Output("forms-summary-banner", "children",  allow_duplicate=True),
    Input("btn-confirm-s4",        "n_clicks"),
    State("uploaded-files-store",  "data"),
    State("forms-container",       "children"),
    State("step4-doc-type",        "data"),
    State("url",                   "pathname"),
    prevent_initial_call=True,
)
def append_file_section(
    confirm: int,
    stored_files: list,
    current_sections: list,
    doc_type: str,
    pathname: str,
):
    """
    Appends a new file-based form section when the Step 4 upload panel is confirmed.

    Args:
        confirm:          Click count on the confirm button.
        stored_files:     Files currently in the store.
        current_sections: Existing form section components.
        doc_type:         Active document type.
        pathname:         Current browser pathname.

    Returns:
        Updated (form_sections, summary_banner).
    """
    if pathname != "/upload/forms" or not confirm or not stored_files:
        return no_update, no_update

    current     = current_sections or []
    new_file    = stored_files[-1]
    new_section = build_form_section(
        index=len(current),
        filename=new_file.get("filename", "fichier"),
        content=new_file.get("content", ""),
        doc_type=doc_type or "REC",
        data={},
        status="ok",
    )
    updated = current + [new_section]
    return updated, _summary_banner(len(updated), 0)


# ── Add-section menu ──────────────────────────────────────────────────────────

@callback(
    Output("add-section-menu", "style"),
    Input("btn-add-section",   "n_clicks"),
    Input("btn-add-from-file", "n_clicks"),
    Input("btn-add-manual",    "n_clicks"),
    State("add-section-menu",  "style"),
    State("url",               "pathname"),
    prevent_initial_call=True,
)
def toggle_add_menu(
    add_clicks: int,
    from_file_clicks: int,
    manual_clicks: int,
    current_style: dict,
    pathname: str,
):
    """
    Toggles the add-section dropdown. Closes when any option is selected.

    Args:
        add_clicks:       Clicks on the "Ajouter une section" button.
        from_file_clicks: Clicks on the "Charger un fichier" option.
        manual_clicks:    Clicks on the "Entrer manuellement" option.
        current_style:    Current style of the menu div.
        pathname:         Current browser pathname.

    Returns:
        Updated style dict for the menu.
    """
    if pathname != "/upload/forms":
        return no_update

    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, str):
        return no_update

    clicks_map = {
        "btn-add-section":   add_clicks,
        "btn-add-from-file": from_file_clicks,
        "btn-add-manual":    manual_clicks,
    }
    if not clicks_map.get(triggered):
        return no_update

    if triggered in ("btn-add-from-file", "btn-add-manual"):
        return {**current_style, "display": "none"}

    is_open = current_style.get("display") == "block"
    return {**current_style, "display": "none" if is_open else "block"}


@callback(
    Output("forms-container",      "children",  allow_duplicate=True),
    Output("forms-summary-banner", "children",  allow_duplicate=True),
    Input("btn-add-manual",        "n_clicks"),
    State("forms-container",       "children"),
    State("step4-doc-type",        "data"),
    State("url",                   "pathname"),
    prevent_initial_call=True,
)
def add_manual_section(
    n_clicks: int,
    current_sections: list,
    doc_type: str,
    pathname: str,
):
    """
    Appends a blank manual-entry form section.

    Args:
        n_clicks:         Click count on the "Entrer manuellement" option.
        current_sections: Existing form section components.
        doc_type:         Active document type.
        pathname:         Current browser pathname.

    Returns:
        Updated (form_sections, summary_banner).
    """
    if pathname != "/upload/forms" or not n_clicks:
        return no_update, no_update

    current   = current_sections or []
    new_index = len(current)
    new_section = build_form_section(
        index=new_index,
        filename="manual",
        content="",
        doc_type=doc_type or "REC",
        data={},
        status="manual",
    )
    updated = current + [new_section]
    return updated, _summary_banner(len(updated), 0)


# ── Section removal ───────────────────────────────────────────────────────────

@callback(
    Output("forms-container",      "children",  allow_duplicate=True),
    Output("forms-summary-banner", "children",  allow_duplicate=True),
    Input({"type": "btn-remove-section", "index": ALL}, "n_clicks"),
    State("forms-container",       "children"),
    State("url",                   "pathname"),
    prevent_initial_call=True,
)
def remove_section(n_clicks_list: list, current_sections: list, pathname: str):
    """
    Removes a form section when its close button is clicked.

    Args:
        n_clicks_list:    Click counts for all section close buttons.
        current_sections: Current form section components.
        pathname:         Current browser pathname.

    Returns:
        Updated (form_sections, summary_banner).
    """
    if pathname != "/upload/forms":
        return no_update, no_update

    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return no_update, no_update

    if not any(n for n in n_clicks_list if n and n > 0):
        return no_update, no_update

    remove_index = triggered.get("index")
    updated = [
        s for s in (current_sections or [])
        if _section_index(s) != remove_index
    ]
    return updated, _summary_banner(len(updated), 0)


# ── Preview toggle ────────────────────────────────────────────────────────────

@callback(
    Output({"type": "preview-panel",     "index": MATCH}, "style"),
    Input({"type": "btn-toggle-preview", "index": MATCH}, "n_clicks"),
    State({"type": "preview-panel",      "index": MATCH}, "style"),
    prevent_initial_call=True,
)
def toggle_preview(n_clicks: int, current_style: dict):
    """
    Toggles the document preview panel for one form section.

    Uses MATCH so each section controls its own panel independently.

    Args:
        n_clicks:      Click count on the preview button.
        current_style: Current style of the preview panel.

    Returns:
        Updated style dict.
    """
    if not n_clicks:
        return no_update
    is_visible = current_style.get("display") == "block"
    return {**current_style, "display": "none" if is_visible else "block"}


# ── Submit ────────────────────────────────────────────────────────────────────

@callback(
    Output("url",              "pathname",  allow_duplicate=True),
    Output("validation-popup", "children"),
    Output("validation-popup", "style"),
    Input("btn-step4-submit",  "n_clicks"),
    State({"type": "form-field", "form": ALL, "field": ALL}, "value"),
    State({"type": "form-field", "form": ALL, "field": ALL}, "id"),
    State({"type": "form-date",  "form": ALL, "field": ALL}, "date"),
    State({"type": "form-date",  "form": ALL, "field": ALL}, "id"),
    State("uploaded-files-store", "data"),
    State("selected-doc-type",    "data"),
    prevent_initial_call=True,
)
def handle_submit(
    n_clicks: int,
    all_values: list,
    all_ids: list,
    all_dates: list,
    all_date_ids: list,
    stored_files: list,
    doc_type: str,
):
    """
    Validates all required fields across form sections, then saves to DB.

    Groups fields by form section, counts missing required values,
    and shows an error popup if validation fails. On success, uploads
    files and navigates to the history page.

    Collects two patterns: "form-field" (value prop) and "form-date"
    (date prop from dcc.DatePickerSingle), then merges them by form_id.

    Args:
        n_clicks:     Submit button click count.
        all_values:   Values from all dcc.Input form fields.
        all_ids:      ID dicts for all_values.
        all_dates:    Dates from all dcc.DatePickerSingle form fields.
        all_date_ids: ID dicts for all_dates.
        stored_files: Files staged in the upload store.
        doc_type:     Document type selected in Step 3.

    Returns:
        Tuple of (new_pathname, popup_children, popup_style).
    """
    if not n_clicks:
        return no_update, no_update, no_update

    forms: dict[str, dict[str, str]] = defaultdict(dict)
    for field_id_dict, value in zip(all_ids, all_values):
        form  = field_id_dict.get("form", "")
        field = field_id_dict.get("field", "")
        if form and field:
            forms[form][field] = value or ""

    for field_id_dict, date_val in zip(all_date_ids, all_dates):
        form  = field_id_dict.get("form", "")
        field = field_id_dict.get("field", "")
        if form and field:
            forms[form][field] = date_val or ""

    missing: list[str] = []
    for fields in forms.values():
        has_tx_rows = any(k.startswith("tx_") for k in fields)

        if "merchant" in fields or "total" in fields:
            required = _REQUIRED_PER_TYPE["REC"]
        elif "holder" in fields:
            required = _REQUIRED_PER_TYPE["STMT"]
        elif "client" in fields:
            required = _REQUIRED_PER_TYPE["INV"]
        elif "note_text" in fields:
            required = _REQUIRED_PER_TYPE["NOTE"]
        elif has_tx_rows:
            # Multi-row form (INV xlsx, STMT tx rows) — no top-level validation
            required = set()
        else:
            required = _REQUIRED_MANUAL

        for f in required:
            if not fields.get(f):
                missing.append(_FIELD_LABELS.get(f, f))

    if missing:
        return (
            no_update,
            _error_popup(missing),
            {
                "display":  "block",
                "position": "fixed",
                "top":      "24px",
                "right":    "24px",
                "zIndex":   "2000",
            },
        )

    if doc_type == "STMT":
        _submit_statement(forms)
    else:
        _submit_files(stored_files, forms, doc_type)
        if doc_type == "INV":
            _create_invoices_from_forms(forms)

    return "/upload/history", None, {"display": "none"}


@callback(
    Output("validation-popup", "style", allow_duplicate=True),
    Input("btn-close-validation-popup", "n_clicks"),
    prevent_initial_call=True,
)
def close_validation_popup(n_clicks: int):
    """Dismisses the validation error popup."""
    if not n_clicks:
        return no_update
    return {"display": "none"}


# ── Navigation ────────────────────────────────────────────────────────────────

@callback(
    Output("url",           "pathname", allow_duplicate=True),
    Input("btn-step4-back", "n_clicks"),
    prevent_initial_call=True,
)
def go_back(n_clicks: int):
    """Returns to Step 3 on back button click."""
    if not n_clicks:
        return no_update
    return "/upload"


# ── Submit helpers ────────────────────────────────────────────────────────────

def _submit_statement(forms: dict[str, dict[str, str]]) -> None:
    """
    Persists a statement: creates or reuses a source, then saves each tx row.

    Args:
        forms: Dict of form_id → {field: value} for all form sections.
    """
    for fields in forms.values():
        if not fields.get("holder"):
            continue

        source_label = fields.get("source_label") or "Carte de crédit"
        last_four    = fields.get("last_four", "")

        # Reuse existing source or create a new one
        existing_sources = api.get_sources()
        source = next(
            (s for s in existing_sources if last_four and last_four in s.get("label", "")),
            None,
        )
        if not source:
            source = api.create_source({"label": source_label, "source_type": "credit_card"})

        source_id = (source or {}).get("id", "")

        # Collect and persist all tx_N_* rows
        i = 0
        while True:
            date_val   = fields.get(f"tx_{i}_date",   "")
            desc_val   = fields.get(f"tx_{i}_desc",   "")
            amount_val = fields.get(f"tx_{i}_amount", "")

            if date_val is None and desc_val is None and amount_val is None:
                break
            if not (date_val or desc_val or amount_val):
                i += 1
                if i > 500:
                    break
                continue

            try:
                amount = float(str(amount_val).replace("$", "").replace(",", ""))
            except (ValueError, TypeError):
                amount = 0.0

            try:
                api.create_transaction({
                    "date":        date_val or "",
                    "description": desc_val or "",
                    "amount":      amount,
                    "source_id":   source_id,
                    "doc_type":    "STMT",
                    "ref":         fields.get(f"tx_{i}_ref", ""),
                    "entry_method": "parsed",
                })
            except Exception as exc:
                log.error("Failed to save transaction row %d: %s", i, exc)

            i += 1


def _submit_invoice_rows(forms: dict[str, dict[str, str]], stored_files: list) -> None:
    """
    Persists invoice rows as individual transactions (income = negative amount).

    For xlsx multi-row forms, creates one transaction per tx_{i} row.
    Falls back to file upload when no row data is present.

    Args:
        forms:        Dict of form_id → {field: value}.
        stored_files: Files staged in upload store (fallback).
    """
    has_rows = any(
        key.startswith("tx_") and key.endswith("_amount")
        for fields in forms.values()
        for key in fields
    )

    if not has_rows:
        _submit_files(stored_files, forms, "INV")
        return

    # Find or create a default income source
    existing = api.get_sources()
    source = next((s for s in existing if "Revenus" in s.get("label", "")), None)
    if not source:
        source = api.create_source({"label": "Revenus clients", "source_type": "personal"})
    source_id = (source or {}).get("id", "")

    for fields in forms.values():
        i = 0
        while True:
            amount_val = fields.get(f"tx_{i}_amount")
            if amount_val is None:
                break

            client    = fields.get(f"tx_{i}_client", "")
            desc      = fields.get(f"tx_{i}_desc", "") or client or "Facture"
            date_val  = (fields.get(f"tx_{i}_date_sent") or
                         fields.get(f"tx_{i}_date_paid") or "")

            if amount_val:
                try:
                    amount = -abs(float(str(amount_val).replace("$", "").replace(",", "")))
                except (ValueError, TypeError):
                    amount = 0.0

                try:
                    api.create_transaction({
                        "date":        date_val or str(__import__("datetime").date.today()),
                        "description": desc,
                        "amount":      amount,
                        "source_id":   source_id,
                        "entry_method": "parsed",
                    })
                except Exception as exc:
                    log.error("Failed to save invoice row %d: %s", i, exc)
            i += 1


def _create_invoices_from_forms(forms: dict[str, dict[str, str]]) -> None:
    """
    Creates Invoice records in the invoices table from the xlsx form rows.

    Called after _submit_files() for INV doc_type. The upload already creates
    Transaction records for analytics; this populates the separate invoices
    table used by the Factures page.

    Args:
        forms: Dict of form_id → {field: value} from handle_submit.
    """
    for fields in forms.values():
        i = 0
        while True:
            client = fields.get(f"tx_{i}_client")
            if client is None:
                break

            amount_val = fields.get(f"tx_{i}_amount", "")
            if not client or not amount_val:
                i += 1
                continue

            desc      = fields.get(f"tx_{i}_desc", "") or client
            date_sent = fields.get(f"tx_{i}_date_sent") or None
            date_paid = fields.get(f"tx_{i}_date_paid") or None
            status    = "paid" if date_paid else "unpaid"

            try:
                amount = abs(float(str(amount_val).replace("$", "").replace(",", "")))
                api.create_invoice({
                    "client":      client,
                    "description": desc,
                    "amount":      amount,
                    "date_sent":   date_sent,
                    "date_paid":   date_paid,
                    "status":      status,
                })
            except Exception as exc:
                log.error("Failed to create invoice row %d: %s", i, exc)
            i += 1


def _submit_files(stored_files: list, forms: dict, doc_type: str) -> None:
    """
    Uploads staged files for non-statement doc types.

    Args:
        stored_files: Files from the upload store.
        forms:        Collected form field values by section.
        doc_type:     Active document type.
    """
    if not stored_files:
        return

    files_payload = []
    for f in stored_files:
        content = f.get("content", "")
        try:
            raw = base64.b64decode(
                content.split(",")[1] if "," in content else content
            )
            files_payload.append((
                f.get("filename", "upload"),
                raw,
                _mime_type(f.get("filename", "upload")),
            ))
        except Exception as exc:
            log.error("Failed to decode file for upload: %s", exc)

    if not files_payload:
        return

    if doc_type == "INV":
        source_label = "Revenus clients"
        source_type  = "personal"
    else:
        source_label = "Comptant — shoebox"
        source_type  = "cash"
        for fields in forms.values():
            pm = fields.get("payment_method", "")
            if pm == "card":
                source_type  = "credit_card"
                source_label = fields.get("source_label", source_label)
                break
            elif pm == "transfer":
                source_type  = "personal"
                break

    api.upload_files(
        files=files_payload,
        doc_type=doc_type or "REC",
        source_label=source_label,
        source_type=source_type,
    )


# ── Private helpers ───────────────────────────────────────────────────────────

def _summary_banner(total: int, errors: int) -> html.Div:
    """
    Renders the summary bar showing ready vs error counts.

    Args:
        total:  Total number of form sections.
        errors: Number of sections with parse errors.

    Returns:
        Styled summary div.
    """
    ready = total - errors
    return html.Div(
        [
            html.Span(
                f"{ready} prête{'s' if ready > 1 else ''}",
                style={
                    "fontFamily": FONTS["sans"],
                    "fontSize":   "12px",
                    "fontWeight": "600",
                    "color":      COLORS["ok"],
                    "marginRight": "12px",
                },
            ),
            html.Span(
                f"{errors} avec erreurs" if errors else "",
                style={
                    "fontFamily": FONTS["sans"],
                    "fontSize":   "12px",
                    "color":      COLORS["error"],
                },
            ),
        ],
        style={
            "display":         "flex",
            "alignItems":      "center",
            "padding":         f"{SPACE['sm']}px {SPACE['md']}px",
            "backgroundColor": COLORS["ok_bg"] if not errors else COLORS["warning_bg"],
            "borderRadius":    "8px",
            "marginBottom":    f"{SPACE['md']}px",
        },
    )


def _error_popup(missing_fields: list[str]) -> html.Div:
    """
    Renders the validation error notification popup with the list of missing fields.

    Args:
        missing_fields: Human-readable names of required fields that are empty.

    Returns:
        Styled popup div.
    """
    field_list = html.Ul(
        [html.Li(name, style={
            "fontFamily": FONTS["mono"],
            "fontSize":   "11px",
            "color":      COLORS["error"],
            "marginBottom": "2px",
        }) for name in missing_fields],
        style={"margin": "6px 0 0 0", "paddingLeft": "16px"},
    )

    return html.Div(
        [
            html.Div(style={
                "width":           "4px",
                "backgroundColor": COLORS["error"],
                "borderRadius":    "4px 0 0 4px",
                "flexShrink":      "0",
            }),
            html.Div(
                [
                    html.Div(
                        [
                            html.I(className="fa-solid fa-xmark", style={
                                "color": COLORS["error"], "fontSize": "14px", "marginRight": "8px",
                            }),
                            html.Span("Champs requis manquants", style={
                                "fontFamily": FONTS["sans"],
                                "fontSize":   "14px",
                                "fontWeight": "600",
                                "color":      COLORS["ink"],
                            }),
                        ],
                        style={"display": "flex", "alignItems": "center", "marginBottom": "4px"},
                    ),
                    field_list,
                ],
                style={"padding": f"{SPACE['md']}px"},
            ),
            html.Button(
                html.I(className="fa-solid fa-xmark"),
                id="btn-close-validation-popup",
                n_clicks=0,
                style={
                    "background": "none", "border": "none", "cursor": "pointer",
                    "color": COLORS["muted"], "fontSize": "14px",
                    "padding": "8px", "alignSelf": "flex-start", "flexShrink": "0",
                },
            ),
        ],
        style={
            "display":         "flex",
            "alignItems":      "stretch",
            "backgroundColor": COLORS["white"],
            "borderRadius":    RADIUS["lg"],
            "border":          f"1px solid {COLORS['border']}",
            "boxShadow":       "0 8px 24px rgba(0,0,0,0.12)",
            "minWidth":        "280px",
            "maxWidth":        "360px",
            "overflow":        "hidden",
        },
    )


def _file_row_s4(filename: str, ext: str, is_valid: bool, index: int) -> html.Div:
    """
    Renders one file row inside the Step 4 upload panel.

    Args:
        filename: Original filename.
        ext:      File extension.
        is_valid: Whether the format is accepted.
        index:    Row index (for layout only — no remove button needed).

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
                "fontFamily": FONTS["sans"], "fontSize": "12px", "flex": "1",
                "color": COLORS["ink"] if is_valid else COLORS["error"],
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
        ],
        style={
            "display":         "flex",
            "alignItems":      "center",
            "gap":             "8px",
            "padding":         f"{SPACE['xs']}px {SPACE['sm']}px",
            "backgroundColor": COLORS["cream"] if is_valid else COLORS["error_bg"],
            "borderRadius":    RADIUS["sm"],
            "marginBottom":    "4px",
        },
    )


def _error_alert_s4(filename: str, accepted: list) -> html.Div:
    """
    Renders a warning banner for a rejected file in the Step 4 panel.

    Args:
        filename: Name of the rejected file.
        accepted: Accepted extensions for this doc type.

    Returns:
        Warning div.
    """
    return html.Div(
        [
            html.Span("⚠️ ", style={"flexShrink": "0"}),
            html.Span(
                f"{filename} — format non accepté. "
                f"Formats attendus : {', '.join(accepted)}. Ce fichier sera ignoré.",
                style={"fontFamily": FONTS["sans"], "fontSize": "12px", "color": COLORS["warning"]},
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


def _mime_type(filename: str) -> str:
    """
    Returns the MIME type for a given filename based on its extension.

    Args:
        filename: Original filename.

    Returns:
        MIME type string.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "pdf":  "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "png":  "image/png",
        "jpg":  "image/jpeg",
        "jpeg": "image/jpeg",
    }.get(ext, "application/octet-stream")


def _section_index(section: dict) -> int | None:
    """
    Extracts the index from a form section component's id dict.

    Args:
        section: Dash component dict.

    Returns:
        Index integer, or None if not extractable.
    """
    try:
        section_id = section.get("props", {}).get("id", {})
        if isinstance(section_id, dict):
            return section_id.get("index")
    except AttributeError:
        pass
    return None
