"""
Callbacks for the Sources & cartes page.

Registered once at startup via app.py import.
Updates the transaction table and highlights the active chip on click.
"""

from dash import Input, Output, ALL, callback, ctx, no_update

import frontend.api_client as api
from frontend.views.sources import _build_tx_table, make_chips


@callback(
    Output("sources-tx-content", "children"),
    Output("sources-chip-bar", "children"),
    Input({"type": "src-chip", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def filter_by_source(n_clicks_list: list):
    """Updates the transaction table and chip highlights when a source is selected.

    Args:
        n_clicks_list: Click counts from all source chips (pattern-matched).

    Returns:
        Tuple of (updated transaction table, updated chip bar children).
    """
    if not any(n_clicks_list):
        return no_update, no_update

    triggered = ctx.triggered_id
    if triggered is None:
        return no_update, no_update

    selected_id = triggered.get("index", "all") if isinstance(triggered, dict) else "all"

    sources    = api.get_sources()
    by_src     = api.get_by_source()
    total      = sum(by_src.values())
    source_map = {s.get("id", ""): s for s in sources}

    if selected_id == "all":
        tx_data = api.get_transactions(size=200)
    else:
        tx_data = api.get_transactions(source_id=selected_id, size=200)

    txs      = tx_data.get("items", []) if isinstance(tx_data, dict) else []
    new_chips = make_chips(sources, by_src, total, selected_id)

    return _build_tx_table(txs, source_map), new_chips
