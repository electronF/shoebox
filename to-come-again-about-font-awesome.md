Tu as raison sur les deux points.

---

## Problème des clics — isolation des scopes

Le vrai problème est architectural. Tous les callbacks partagent le même espace de noms Dash — un `n_clicks` qui change quelque part peut déclencher d'autres callbacks. La solution propre est de vérifier `ctx.triggered_id` **en premier** dans chaque callback et de retourner `no_update` immédiatement si ce n'est pas le bon déclencheur.

Voici le callback `proceed_to_forms` corrigé de façon définitive :

```python
@callback(
    Output("url", "pathname"),
    Input("btn-confirm-upload", "n_clicks"),
    Input("btn-manual-entry",   "n_clicks"),
    State("uploaded-files-store", "data"),
    prevent_initial_call=True,
)
def proceed_to_forms(confirm_clicks, manual_clicks, stored_files):
    triggered = ctx.triggered_id

    # Strict scope — only these two buttons can trigger navigation
    if triggered not in ("btn-confirm-upload", "btn-manual-entry"):
        return no_update

    if triggered == "btn-confirm-upload":
        # Must have files AND a real click (not initial render)
        if not confirm_clicks or not stored_files:
            return no_update
        return "/upload/forms"

    if triggered == "btn-manual-entry":
        if not manual_clicks:
            return no_update
        return "/upload/forms"

    return no_update
```

Même principe pour `toggle_popup` — vérifier strictement :

```python
@callback(
    Output("upload-popup-overlay", "style"),
    Output("popup-open",           "data"),
    Input("btn-open-upload",   "n_clicks"),
    Input("btn-close-popup",   "n_clicks"),
    Input("btn-cancel-upload", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_popup(open_clicks, close_clicks, cancel_clicks):
    triggered = ctx.triggered_id

    # Strict scope — only these three buttons control the popup
    if triggered not in ("btn-open-upload", "btn-close-popup", "btn-cancel-upload"):
        return no_update, no_update

    should_open = triggered == "btn-open-upload"
    style = {
        "display":         "flex" if should_open else "none",
        "position":        "fixed",
        "top": "0", "left": "0",
        "width": "100vw", "height": "100vh",
        "backgroundColor": "rgba(0,0,0,0.45)",
        "alignItems":      "center",
        "justifyContent":  "center",
        "zIndex":          "1000",
    }
    return style, should_open
```

**Règle générale Dash :** tout callback commence par :
```python
triggered = ctx.triggered_id
if triggered != "expected-id":
    return no_update
```

---

## Icônes — Font Awesome vs emojis

Font Awesome est tout à fait utilisable dans Dash. Ajoute-le dans `app.py` :

```python
app = dash.Dash(
    __name__,
    external_stylesheets=[
        GOOGLE_FONTS_URL,
        # Font Awesome 6 Free
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css",
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap-grid.min.css",
    ],
    ...
)
```

Ensuite partout dans le code, remplace les emojis par des `html.I` :

```python
# ❌ Emoji
html.Span("📁", style={"marginRight": "8px"})

# ✅ Font Awesome
html.I(className="fa-solid fa-folder-open",
       style={"marginRight": "8px", "color": COLORS["muted"]})
```

Quelques icônes utiles pour notre app :

| Usage | Classe FA |
|---|---|
| Upload | `fa-solid fa-upload` |
| Clavier / manuel | `fa-solid fa-keyboard` |
| Reçu | `fa-solid fa-receipt` |
| Carte bancaire | `fa-solid fa-credit-card` |
| Facture | `fa-solid fa-file-invoice` |
| Notes | `fa-solid fa-note-sticky` |
| Fermer | `fa-solid fa-xmark` |
| Succès | `fa-solid fa-circle-check` |
| Warning | `fa-solid fa-triangle-exclamation` |
| Erreur | `fa-solid fa-circle-xmark` |
| Info | `fa-solid fa-circle-info` |
| Vue d'ensemble | `fa-solid fa-chart-pie` |
| Récurrents | `fa-solid fa-rotate` |
| Fichiers | `fa-solid fa-folder` |
| Rapport | `fa-solid fa-file-lines` |
| Abonnements | `fa-solid fa-layer-group` |

Tu veux qu'on intègre Font Awesome maintenant ou après avoir réglé le flux d'upload ?