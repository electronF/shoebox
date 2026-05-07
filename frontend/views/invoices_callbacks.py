"""
Callbacks for the Invoices page (/invoices).

Handles filter tab selection and inline mark-as-paid actions.
Guards every callback with a pathname check so outputs targeting
invoices-table-container are safely ignored on other pages.
"""

import logging
from datetime import date

from dash import ALL, Input, Output, State, callback, ctx, html, no_update

import frontend.api_client as api
from frontend.theme import COLORS, FONTS, RADIUS, SPACE, BTN_PRIMARY

log = logging.getLogger(__name__)

_FILTER_LABELS = {
    "all":     "Toutes",
    "unpaid":  "À encaisser",
    "paid":    "Payées",
    "overdue": "Impayées",
}
_FILTER_STATUS = {
    "all":     None,
    "unpaid":  "unpaid",
    "paid":    "paid",
    "overdue": "overdue",
}


@callback(
    Output("invoices-table-container", "children"),
    Output({"type": "invoice-filter-tab", "value": ALL}, "style"),
    Input({"type": "invoice-filter-tab", "value": ALL}, "n_clicks"),
    Input({"type": "btn-mark-paid", "invoice_id": ALL}, "n_clicks"),
    State({"type": "invoice-filter-tab", "value": ALL}, "id"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def handle_invoice_actions(
    tab_clicks: list,
    pay_clicks: list,
    tab_ids: list,
    pathname: str,
):
    """
    Handles both filter tab selection and mark-as-paid button clicks.

    On tab click: reloads invoices filtered by selected status.
    On pay click: PATCHes the invoice to paid status, then reloads.

    Args:
        tab_clicks:  Click counts for each filter tab.
        pay_clicks:  Click counts for each mark-as-paid button.
        tab_ids:     ID dicts for each filter tab (contains "value").
        pathname:    Current browser URL path.

    Returns:
        Updated (table_children, tab_styles).
    """
    if pathname != "/invoices":
        return no_update, no_update

    triggered = ctx.triggered_id
    if not triggered:
        return no_update, no_update

    # Determine active filter
    active_filter = "all"

    if isinstance(triggered, dict):
        if triggered.get("type") == "invoice-filter-tab":
            active_filter = triggered.get("value", "all")

        elif triggered.get("type") == "btn-mark-paid":
            invoice_id = triggered.get("invoice_id", "")
            if invoice_id:
                try:
                    api.update_invoice(invoice_id, {
                        "status":    "paid",
                        "date_paid": str(date.today()),
                    })
                    log.info("Invoice %s marked as paid", invoice_id)
                except Exception as exc:
                    log.error("Failed to mark invoice %s as paid: %s", invoice_id, exc)
            # Keep current filter after action — derive from tab styles
            for tab_id in (tab_ids or []):
                active_filter = tab_id.get("value", "all")
                break

    # Reload invoices with active filter
    status_filter = _FILTER_STATUS.get(active_filter)
    if status_filter:
        invoices = api.get_invoices(status=status_filter)
    else:
        invoices = api.get_invoices()

    from frontend.views.invoices import _invoices_table
    table = _invoices_table(invoices)

    # Rebuild tab styles
    tab_styles = [_tab_style(tab_id.get("value", "all"), active_filter)
                  for tab_id in (tab_ids or [])]

    return table, tab_styles


def _tab_style(value: str, active: str) -> dict:
    is_active = value == active
    return {
        "padding":         "6px 16px",
        "borderRadius":    RADIUS["sm"],
        "cursor":          "pointer",
        "backgroundColor": COLORS["accent"] if is_active else "transparent",
        "color":           COLORS["white"]  if is_active else COLORS["muted"],
        "border":          f"1px solid {COLORS['border']}",
    }
