"""
Design system for the Shoebox frontend.

Single source of truth for colors, typography, spacing, and
reusable inline style dictionaries. All views and components
import from here — changing the visual theme means changing
this file only.
"""


# Color palette

COLORS = {
    # Primary
    "accent":        "#1a4d3e",   # Forest green — header, primary buttons
    "accent_hover":  "#2e7d5e",   # Lighter green — hover state
    "accent_light":  "#e8f0ed",   # Very light green — active nav background

    # Gold accents
    "gold":          "#c8a84b",   # Gold — logo O, separators, highlights
    "gold_light":    "#f0e6c4",   # Light gold — subtle backgrounds

    # Backgrounds
    "paper":         "#f5f0e8",   # Warm cream — main background
    "cream":         "#ede8dc",   # Darker cream — section headers, sidebar
    "white":         "#ffffff",   # Pure white — cards, form fields

    # Text
    "ink":           "#0d1117",   # Near-black — primary text
    "muted":         "#6b6557",   # Warm gray — secondary text, labels
    "placeholder":   "#a89f91",   # Light warm gray — input placeholders

    # Borders
    "border":        "#c9c3b5",   # Warm border
    "border_light":  "#e2ddd4",   # Lighter border — card interiors

    # Semantic states
    "ok":            "#2e6b3e",   # Success green
    "ok_bg":         "#eaf3de",   # Success background
    "warning":       "#854f0b",   # Amber text
    "warning_bg":    "#faeeda",   # Amber background
    "error":         "#b5361c",   # Error red
    "error_bg":      "#fcebeb",   # Error background
    "info":          "#185fa5",   # Info blue
    "info_bg":       "#e6f1fb",   # Info background

    # Badge variants
    "badge_gray":    "#444441",
    "badge_gray_bg": "#f1efe8",
    "badge_purple":  "#3c3489",
    "badge_purple_bg": "#eeedfe",
}


# Typography

FONTS = {
    "serif":  "'Playfair Display', Georgia, serif",   # Titles, headings
    "sans":   "'DM Sans', 'Helvetica Neue', sans-serif",  # Body, UI
    "mono":   "'DM Mono', 'Courier New', monospace",  # Labels, codes, badges
}

# Google Fonts import URL — injected in app.py external_stylesheets
GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Playfair+Display:wght@400;600;700&"
    "family=DM+Sans:wght@300;400;500;600&"
    "family=DM+Mono:wght@400;500&"
    "display=swap"
)


# Spacing scale (px)
SPACE = {
    "xs":  4,
    "sm":  8,
    "md":  16,
    "lg":  24,
    "xl":  32,
    "2xl": 48,
    "3xl": 64,
}


# Border radius
RADIUS = {
    "sm":  "4px",
    "md":  "8px",
    "lg":  "12px",
    "xl":  "16px",
    "pill": "999px",
}


# Shadows
SHADOW = {
    "sm":  "0 1px 3px rgba(0,0,0,0.07)",
    "md":  "0 4px 12px rgba(0,0,0,0.08)",
    "lg":  "0 8px 24px rgba(0,0,0,0.10)",
}


# Reusable component styles

# ── Cards 
CARD = {
    "backgroundColor": COLORS["white"],
    "border":          f"1px solid {COLORS['border_light']}",
    "borderRadius":    RADIUS["lg"],
    "padding":         f"{SPACE['lg']}px",
    "boxShadow":       SHADOW["sm"],
}

CARD_SECTION = {
    **CARD,
    "backgroundColor": COLORS["cream"],
    "padding":         f"{SPACE['md']}px {SPACE['lg']}px",
}

# ── Form fields 
FIELD_LABEL = {
    "fontFamily":  FONTS["mono"],
    "fontSize":    "11px",
    "fontWeight":  "500",
    "letterSpacing": "0.06em",
    "textTransform": "uppercase",
    "color":       COLORS["muted"],
    "marginBottom": f"{SPACE['xs']}px",
    "display":     "flex",
    "alignItems":  "center",
    "gap":         "6px",
}

FIELD_INPUT = {
    "width":           "100%",
    "height":          "38px",
    "padding":         f"0 {SPACE['md']}px",
    "fontFamily":      FONTS["sans"],
    "fontSize":        "13px",
    "color":           COLORS["ink"],
    "backgroundColor": COLORS["white"],
    "border":          f"1px solid {COLORS['border']}",
    "borderRadius":    RADIUS["md"],
    "outline":         "none",
}

FIELD_INPUT_ERROR = {
    **FIELD_INPUT,
    "border":          f"1.5px solid {COLORS['error']}",
    "backgroundColor": COLORS["error_bg"],
}

FIELD_INPUT_WARNING = {
    **FIELD_INPUT,
    "border":          f"1.5px solid #ba7517",
}

FIELD_INPUT_OK = {
    **FIELD_INPUT,
    "border":          f"1.5px solid {COLORS['ok']}",
}

FIELD_HINT = {
    "fontFamily": FONTS["sans"],
    "fontSize":   "11px",
    "color":      COLORS["muted"],
    "marginTop":  f"{SPACE['xs']}px",
}

FIELD_ERROR_MSG = {
    **FIELD_HINT,
    "color": COLORS["error"],
}

FIELD_WARNING_MSG = {
    **FIELD_HINT,
    "color": COLORS["warning"],
}

# ── Buttons 
BTN_PRIMARY = {
    "fontFamily":    FONTS["sans"],
    "fontSize":      "13px",
    "fontWeight":    "500",
    "color":         COLORS["white"],
    "backgroundColor": COLORS["accent"],
    "border":        "none",
    "borderRadius":  RADIUS["md"],
    "padding":       f"{SPACE['sm']}px {SPACE['lg']}px",
    "cursor":        "pointer",
    "letterSpacing": "0.01em",
}

BTN_SECONDARY = {
    **BTN_PRIMARY,
    "color":           COLORS["ink"],
    "backgroundColor": COLORS["white"],
    "border":          f"1px solid {COLORS['border']}",
}

BTN_GHOST = {
    **BTN_PRIMARY,
    "color":           COLORS["muted"],
    "backgroundColor": "transparent",
    "border":          "none",
}

BTN_DANGER = {
    **BTN_PRIMARY,
    "color":           COLORS["error"],
    "backgroundColor": COLORS["error_bg"],
    "border":          f"1px solid {COLORS['error']}",
}

# ── Navigation sidebar 
SIDEBAR = {
    "width":           "220px",
    "minHeight":       "100vh",
    "backgroundColor": COLORS["cream"],
    "borderRight":     f"1px solid {COLORS['border']}",
    "padding":         f"{SPACE['lg']}px 0",
    "display":         "flex",
    "flexDirection":   "column",
    "flexShrink":      "0",
}

NAV_ITEM = {
    "fontFamily":     FONTS["sans"],
    "fontSize":       "13px",
    "fontWeight":     "400",
    "color":          COLORS["muted"],
    "padding":        f"{SPACE['sm']}px {SPACE['lg']}px",
    "paddingLeft":    "21px", 
    "cursor":         "pointer",
    "textDecoration": "none",       # ← important pour le <a>
    "display":        "flex",
    "alignItems":     "center",
    "gap":            "10px",
    "borderLeft":     "3px solid transparent",   # ← espace réservé pour éviter le décalage
}

NAV_ITEM_ACTIVE = {
    **NAV_ITEM,
    "fontWeight":      "600",
    "color":           COLORS["accent"],
    "backgroundColor": COLORS["accent_light"],
    "borderLeft":      f"3px solid {COLORS['accent']}",
    "paddingLeft":     f"{SPACE['lg'] - 3}px",
}

# ── Top bar 

TOPBAR = {
    "height":          "52px",
    "backgroundColor": COLORS["accent"],
    "display":         "flex",
    "alignItems":      "center",
    "justifyContent":  "space-between",
    "padding":         f"0 {SPACE['lg']}px",
    "flexShrink":      "0",
}

# ── Section headings 

SECTION_TITLE = {
    "fontFamily":    FONTS["mono"],
    "fontSize":      "11px",
    "fontWeight":    "500",
    "textTransform": "uppercase",
    "letterSpacing": "0.08em",
    "color":         COLORS["muted"],
    "marginBottom":  f"{SPACE['md']}px",
    "paddingBottom": f"{SPACE['xs']}px",
    "borderBottom":  f"1px solid {COLORS['border_light']}",
}

PAGE_TITLE = {
    "fontFamily": FONTS["serif"],
    "fontSize":   "24px",
    "fontWeight": "600",
    "color":      COLORS["ink"],
    "margin":     f"0 0 {SPACE['xs']}px 0",
}

PAGE_SUBTITLE = {
    "fontFamily": FONTS["sans"],
    "fontSize":   "13px",
    "color":      COLORS["muted"],
    "margin":     f"0 0 {SPACE['lg']}px 0",
}

# ── Step indicator 

STEP_DOT_ACTIVE = {
    "width":           "22px",
    "height":          "22px",
    "borderRadius":    "50%",
    "backgroundColor": COLORS["info_bg"],
    "color":           COLORS["info"],
    "fontFamily":      FONTS["mono"],
    "fontSize":        "11px",
    "fontWeight":      "600",
    "display":         "flex",
    "alignItems":      "center",
    "justifyContent":  "center",
    "flexShrink":      "0",
}

STEP_DOT_DONE = {
    **STEP_DOT_ACTIVE,
    "backgroundColor": COLORS["ok_bg"],
    "color":           COLORS["ok"],
}

STEP_DOT_IDLE = {
    **STEP_DOT_ACTIVE,
    "backgroundColor": COLORS["cream"],
    "color":           COLORS["placeholder"],
}

# ── Doc type tiles 

DOC_TILE = {
    "display":         "flex",
    "alignItems":      "center",
    "gap":             "12px",
    "padding":         f"{SPACE['md']}px",
    "border":          f"1px solid {COLORS['border']}",
    "borderRadius":    RADIUS["lg"],
    "cursor":          "pointer",
    "backgroundColor": COLORS["cream"],
    "marginBottom":    f"{SPACE['sm']}px",
}

DOC_TILE_ACTIVE = {
    **DOC_TILE,
    "border":          f"2px solid {COLORS['accent']}",
    "backgroundColor": COLORS["accent_light"],
}

DOC_TILE_ICON = {
    "width":           "36px",
    "height":          "36px",
    "borderRadius":    RADIUS["md"],
    "display":         "flex",
    "alignItems":      "center",
    "justifyContent":  "center",
    "fontSize":        "18px",
    "flexShrink":      "0",
}

# ── Upload drop zone

DROPZONE = {
    "border":          f"2px dashed {COLORS['border']}",
    "borderRadius":    RADIUS["lg"],
    "padding":         f"{SPACE['2xl']}px {SPACE['lg']}px",
    "textAlign":       "center",
    "backgroundColor": COLORS["cream"],
    "cursor":          "pointer",
    "marginBottom":    f"{SPACE['md']}px",
}

# ── Tables 

TABLE_HEADER_CELL = {
    "fontFamily":    FONTS["mono"],
    "fontSize":      "10px",
    "fontWeight":    "500",
    "textTransform": "uppercase",
    "letterSpacing": "0.06em",
    "color":         COLORS["muted"],
    "padding":       f"{SPACE['sm']}px {SPACE['md']}px",
    "borderBottom":  f"1px solid {COLORS['border']}",
    "backgroundColor": COLORS["cream"],
    "whiteSpace":    "nowrap",
}

TABLE_CELL = {
    "fontFamily": FONTS["sans"],
    "fontSize":   "13px",
    "color":      COLORS["ink"],
    "padding":    f"{SPACE['sm']}px {SPACE['md']}px",
    "borderBottom": f"1px solid {COLORS['border_light']}",
}

# Icon class names — Font Awesome 6 Free
ICONS = {
    "receipt":    "fa-solid fa-receipt",
    "card":       "fa-solid fa-credit-card",
    "invoice":    "fa-solid fa-file-invoice",
    "notes":      "fa-solid fa-note-sticky",
    "upload":     "fa-solid fa-cloud-arrow-up",
    "keyboard":   "fa-solid fa-keyboard",
    "chart":      "fa-solid fa-chart-bar",
    "import":     "fa-solid fa-file-import",
    "recurring":  "fa-solid fa-rotate",
    "report":     "fa-solid fa-file-lines",
    "wallet":     "fa-solid fa-wallet",
    "folder":     "fa-solid fa-folder-open",
    "check":      "fa-solid fa-check",
    "xmark":      "fa-solid fa-xmark",
    "warning":    "fa-solid fa-triangle-exclamation",
    "info":       "fa-solid fa-circle-info",
    "eye":        "fa-solid fa-eye",
    "plus":       "fa-solid fa-plus",
    "trash":      "fa-solid fa-trash",
    "edit":       "fa-solid fa-pen",
}