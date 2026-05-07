"""
Step progress indicator component.

Renders a horizontal bar showing the current position
in the upload flow (Step 3 → 4 → 5).
"""

from dash import html
from frontend.theme import (
    COLORS, FONTS, SPACE,
    STEP_DOT_ACTIVE, STEP_DOT_DONE, STEP_DOT_IDLE,
)

_STEPS = [
    (3, "Type de document"),
    (4, "Formulaires"),
    (5, "Historique"),
]


def step_bar(current: int) -> html.Div:
    """
    Renders the step progress bar.

    Args:
        current: Step number currently active (3, 4, or 5).

    Returns:
        Horizontal bar with numbered dots and labels.
    """
    items = []

    for i, (step, label) in enumerate(_STEPS):
        dot_style = (
            STEP_DOT_ACTIVE if step == current
            else STEP_DOT_DONE if step < current
            else STEP_DOT_IDLE
        )

        items.append(html.Div(
            "✓" if step < current else str(step),
            style={**dot_style, "marginRight": "6px"},
        ))
        items.append(html.Span(
            label,
            style={
                "fontFamily": FONTS["sans"],
                "fontSize":   "12px",
                "fontWeight": "600" if step == current else "400",
                "color": COLORS["ink"] if step == current else COLORS["muted"],
                "marginRight": "16px",
            },
        ))

        if i < len(_STEPS) - 1:
            items.append(html.Div(style={
                "width":           "20px",
                "height":          "1px",
                "backgroundColor": COLORS["border"],
                "marginRight":     "16px",
                "flexShrink":      "0",
            }))

    return html.Div(
        items,
        style={
            "display":      "flex",
            "alignItems":   "center",
            "marginBottom": f"{SPACE['lg']}px",
            "flexWrap":     "wrap",
        },
    )