"""
Shoebox Dash application — entry point.

Runs on port 8050 (separate from the FastAPI backend on port 8000).
Start with: python frontend/app.py  or  make frontend
"""

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from frontend.theme import GOOGLE_FONTS_URL, COLORS, FONTS
from frontend.layout import build_shell

from frontend.views.upload.step4_forms import layout as step4_layout


# ── Import ALL callbacks at startup 
# Must happen before app.layout is set so Dash registers them immediately.
import frontend.views.upload.step3_callbacks   # noqa: F401
import frontend.views.upload.step4_callbacks   # noqa: F401
import frontend.views.sources_callbacks        # noqa: F401
import frontend.views.invoices_callbacks       # noqa: F401

app = dash.Dash(
    __name__,
    # No Bootstrap theme — we use our own design system
    external_stylesheets=[
        GOOGLE_FONTS_URL,
        # Minimal Bootstrap just for the grid system
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap-grid.min.css",
    ],
    suppress_callback_exceptions=True,
    title="Shoebox",
    # update_title=None,
)

# Expose the Flask server for deployment (gunicorn, etc.)
server = app.server

app.layout = build_shell()

# =============================================================================
# Root router callback — maps URL to page content
# =============================================================================

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def route(pathname: str):
    """
    Renders the correct view based on the current URL.

    Args:
        pathname: Current browser URL path.

    Returns:
        Dash component tree for the requested page.
    """
    from frontend.views.upload.step3_type   import layout as upload_layout
    from frontend.views.upload.history      import layout as history_layout
    from frontend.views.overview            import layout as overview_layout
    from frontend.views.subscriptions       import layout as subscriptions_layout
    from frontend.views.report              import layout as report_layout
    from frontend.views.recurring           import layout as recurring_layout
    from frontend.views.sources             import layout as sources_layout
    from frontend.views.files               import layout as files_layout
    from frontend.views.invoices            import layout as invoices_layout

    routes = {
        "/":                overview_layout,
        "/upload":          upload_layout,
        "/upload/forms":    step4_layout,
        "/upload/history":  history_layout,
        "/subscriptions":   subscriptions_layout,
        "/report":          report_layout,
        "/recurring":       recurring_layout,
        "/sources":         sources_layout,
        "/files":           files_layout,
        "/invoices":        invoices_layout,
    }

    # Default to overview for unknown paths
    return routes.get(pathname, overview_layout)()


# =============================================================================
# Active nav item highlight callback
# =============================================================================

NAV_IDS = [
    "nav-overview", "nav-upload", "nav-invoices", "nav-subscriptions",
    "nav-report", "nav-recurring", "nav-sources", "nav-files",
]

NAV_PATHS = {
    "nav-overview":      "/",
    "nav-upload":        "/upload",
    "nav-invoices":      "/invoices",
    "nav-subscriptions": "/subscriptions",
    "nav-report":        "/report",
    "nav-recurring":     "/recurring",
    "nav-sources":       "/sources",
    "nav-files":         "/files",
}

from frontend.theme import NAV_ITEM, NAV_ITEM_ACTIVE

@app.callback(
    [Output(nav_id, "style") for nav_id in NAV_IDS],
    Input("url", "pathname"),
)
def highlight_active_nav(pathname: str):
    """
    Updates nav item styles to reflect the current active page.

    Args:
        pathname: Current browser URL path.

    Returns:
        List of style dicts — one per nav item.
    """
    return [
        NAV_ITEM_ACTIVE if NAV_PATHS[nav_id] == pathname else NAV_ITEM
        for nav_id in NAV_IDS
    ]


if __name__ == "__main__":
    app.run(
        debug=True,
        port="8050",
        host="0.0.0.0",
        
    )

    