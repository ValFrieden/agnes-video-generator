"""core.api.google_flow_ui — Selektoren der Google-Flow-Oberfläche.

**Einzige Pflegestelle.** Flow ist eine Angular-Anwendung ohne stabile
Test-Kennungen, deshalb hängt die Automatisierung an ``aria-label``-Texten und
``flow-*``-Komponentennamen. Ändert Google die Oberfläche, wird nur diese Datei
angepasst, nicht die Engine.

Stand der Prüfung: 2026-10-27, Chrome 156, Flow-Oberfläche auf Deutsch,
Konto mit Tarif „Google AI Pro“ (Agent-Composer-Variante). Die Werte wurden
live über das Chrome DevTools Protocol ausgelesen, nicht geraten.

``VERIFIED`` markiert live bestätigte Selektoren, ``UNVERIFIED`` solche, die
mangels Inhalt im Projekt (keine Clips, keine Charaktere) noch nicht gegen die
echte Oberfläche geprüft werden konnten.
"""

from __future__ import annotations

# ── Navigation (nur innerhalb eines Projekts sichtbar) ──────────────────────
# VERIFIED: Innentext ist „<material-ligatur> <Label>“, z. B.
# „accessibility_new Charakter“. Deutsch nutzt den Singular „Charakter“.
# Das französische „Personnages“ der Node-Werkzeuge kommt hier nicht vor.
NAV_CHARACTERS = (
    'button:has-text("Charakter"), button:has-text("Characters"), '
    'button:has-text("Character"), button:has-text("Personnages")'
)
NAV_SCENES = (
    'button:has-text("Szenen"), button:has-text("Scenes"), '
    'button:has-text("Scènes")'
)
NAV_ALL_MEDIA = (
    'button:has-text("Alle Medien"), button:has-text("All media")'
)

# VERIFIED: /character ist direkt navigierbar. Für Szenen gibt es KEINE eigene
# Seite — /scenes liefert 404, der Eintrag filtert nur die Medienansicht.
CHARACTER_PATH = "/character"

# ── Prompt-Editor ───────────────────────────────────────────────────────────
# VERIFIED: ProseMirror existiert innerhalb von flow-rich-text-editor.
PROMPT_EDITOR = ".ProseMirror"
PROMPT_BOX_FALLBACK = '.ProseMirror, [contenteditable="true"]'
# VERIFIED. Die Selektoren der Anhängen-Strecke tragen bewusst nur ASCII-Präfixe
# (kein „ü“): Umlaute gingen beim Schreiben von Skripten schon verloren und
# ließen den Selektor still ins Leere laufen.
ATTACH_MEDIA_BUTTON = (
    'button[aria-label^="Bildelemente zum Prompt-Feld hinzuf"], '
    'button[aria-label^="Add media"]'
)
# VERIFIED: Eintrag im Asset-Menü; die Datei-Schaltfläche mit gleichem
# aria-label im Fuß ist unsichtbar und darf nicht getroffen werden.
ASSET_ITEM = "button:visible"
ASSET_TYPE_PATTERN = "Bild|Image"
# VERIFIED: „Uploads“ in der Seitenleiste (mat-mdc-list-item) passt auch auf
# „Upload“ und lag im DOM vor dem Menü-Button: .first öffnete nie einen Dateidialog.
ASSET_UPLOAD_BUTTON = (
    'button.sidebar-upload-btn:visible, '
    'button:has-text("Medien hoch"):not(.mat-mdc-list-item), '
    'button:has-text("Upload"):not(.mat-mdc-list-item)'
)
# VERIFIED: erscheint nur, wenn Flow den Klick auf das Asset nicht schon selbst
# als Anhängen wertet. Immer klicken würde den Chip doppelt anhängen.
ADD_TO_PROMPT_BUTTON = 'button:has-text("Zum Prompt hinzuf"), button:has-text("Add to prompt")'
# VERIFIED: Referenz-Chip im Prompt-Feld = Schaltfläche „Bildelement“ mit dem
# Innentext „cancel“. Miniaturen im Chatverlauf heißen auch „Bildelement“,
# haben aber keinen „cancel“.
CHIP_REMOVE_BUTTON = (
    'button[aria-label^="Bildelement"]:has-text("cancel"), '
    'button[aria-label^="Image element"]:has-text("cancel")'
)
CHIP_COUNT_JS = (
    "() => Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent "
    "&& /^(Bildelement|Image element)/.test(b.getAttribute('aria-label') || '') "
    "&& (b.innerText || '').includes('cancel')).length"
)
SUBMIT_BUTTON = (
    '[aria-label="Generierung starten"], [aria-label="Generate"], '
    'button:has-text("arrow_forward")'
)

# ── Agent-Einstellungen (Kostenbestätigung) ─────────────────────────────────
# VERIFIED: Zahnrad mit Innentext „tune“; das Kopfzeilen-Zahnrad heißt
# „settings_2“ und führt woandershin, deshalb wird das LETZTE genommen.
AGENT_SETTINGS_BUTTON = 'button[aria-label="Einstellungen"]'
# VERIFIED: aria-labelledby ist stabil und sprachunabhängig.
CONFIRM_POLICY_GROUP = (
    'mat-radio-group[aria-labelledby="agent-settings-confirm-policy-label"]'
)
# VERIFIED: Wert „1“ = Immer (fragt nach), „2“ = Nie (gibt automatisch aus).
CONFIRM_POLICY_ALWAYS_VALUE = "1"
CONFIRM_POLICY_NEVER_VALUE = "2"
SETTINGS_SAVE_BUTTON = 'button:has-text("Speichern"), button:has-text("Save")'
SETTINGS_BACK_BUTTON = '[aria-label="Zurück"], [aria-label="Back"]'

# ── Kostenkarte ─────────────────────────────────────────────────────────────
# VERIFIED über den Node-Server (cost-guard.js), gleiche Oberfläche.
COST_CARD = "flow-permission-message"
COST_APPROVE_LABELS = ("Genehmigen", "Approve")
COST_REJECT_LABELS = ("Ablehnen", "Decline", "Reject")
# Nie klicken: schaltet das Projekt dauerhaft auf automatisches Ausgeben.
COST_ALWAYS_APPROVE_LABELS = ("Immer genehmigen", "Always approve")

# ── Charakterseite ──────────────────────────────────────────────────────────
CHARACTER_PAGE = "flow-character-page"
CHARACTER_HEADER = "flow-character-header"
CHARACTER_NEW_BUTTON = (
    'button:has-text("Neuer Charakter"), button:has-text("Charakter hinzufügen"), '
    'button:has-text("Charakter erstellen"), button:has-text("New Character"), '
    'button:has-text("Create Character"), button:has-text("Add character"), '
    'button:has-text("Nouveau personnage"), button[aria-label*="Charakter"], '
    'button[aria-label*="Character"]'
)
CHARACTER_DESCRIPTION = (
    'div[role="textbox"][aria-label="Charakter beschreiben…"], '
    'div[role="textbox"][aria-label*="Charakter beschreib"], '
    'div[role="textbox"][aria-label*="Describe"], '
    'textarea[placeholder*="Charakter"], textarea[placeholder*="character"]'
)
CHARACTER_UPLOAD_BUTTON = (
    'button:has-text("Hochladen"), button:has-text("Upload"), '
    'button:has-text("Importer"), button[aria-label*="Upload"], '
    'button[aria-label*="Hochladen"]'
)
CHARACTER_FROM_PROJECT_BUTTON = (
    'button:has-text("Aus Projekt hinzufügen"), button:has-text("Add from project")'
)
CHARACTER_FOOTER = "flow-create-character-footer"

CHARACTER_NAME_INPUT = (
    'input[aria-label*="Name"], input[placeholder*="Name"], '
    'input[aria-label="Bearbeitbarer Text"], '
    'div[role="textbox"][aria-label*="Name"]'
)
CHARACTER_DONE_BUTTON = (
    'button:has-text("Fertig"), button:has-text("Done"), '
    'button:has-text("Speichern"), button:has-text("Save"), '
    'button:has-text("Erstellen"), button:has-text("Create"), '
    'button:has-text("Terminer")'
)
CHARACTER_CARD = (
    "flow-character-card, flow-character-tile, [class*='character-card'], "
    "[data-testid*='character'], flow-card"
)
CHARACTER_MENTION_OPTION = (
    '[role="option"], [role="menuitem"], flow-mention-option, mat-option, '
    '.mention-option, .flow-mention-item, [class*="mention-item"]'
)

# ── Szenen-Montage (über das Kachelmenü eines Clips) ────────────────────────
VIDEO_TILE = "flow-video-tile"
VIDEO_TILE_CONTAINER = "flow-grid-tile-container:has(flow-video-tile)"
TILE_MORE_BUTTON = (
    '[aria-label="Weitere Optionen"], [aria-label="More options"], '
    '[aria-label="More"]'
)
ADD_TO_SCENE_ITEM = (
    'Zu Szene hinzufügen', 'Add to Scene', 'Add to scene', 'Zur Szene hinzufügen',
)
SCENE_DOWNLOAD_BUTTON = (
    '[aria-label*="herunterladen"], [aria-label*="Download"]'
)
SCENE_LIST_CONTAINER = (
    'flow-scenes-view, [class*="scenes-view"], flow-scene-card, flow-scene-tile'
)

# ── Download einer Videokachel ──────────────────────────────────────────────
DOWNLOAD_MEDIA_BUTTON = (
    'button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]'
)

# ── Konto und Guthaben ──────────────────────────────────────────────────────
# VERIFIED: der Avatar ist ein Link (A) mit aria-label „Google-Konto: <Name> …“;
# nach dem Klick steht „<N> Google Flow-Guthabenpunkte“ im Seitentext.
ACCOUNT_LINK = 'a[aria-label^="Google-Konto"], a[aria-label^="Google Account"]'
CREDITS_REGEX = r"([\d.,]+)\s+(?:Google Flow-Guthabenpunkte|Google Flow credits)"

# ── Bilder aus dem Canvas ───────────────────────────────────────────────────
# VERIFIED: neu generierte Bilder erscheinen als <img alt="Option 1"> mit
# naturalWidth >= 1000; die Kacheln hochgeladener Bilder haben ein anderes alt.
GENERATED_IMAGE_JS = (
    "() => [...new Set(Array.from(document.querySelectorAll('img'))"
    ".filter(i => i.naturalWidth >= 1000 && i.alt === 'Option 1')"
    ".map(i => i.currentSrc))]"
)

# ── Absenden ────────────────────────────────────────────────────────────────
# VERIFIED (27.10.2026): „Generierung starten“ gibt es in der Seite MEHRFACH
# (je eine Schaltfläche pro Chat-Nachricht). querySelector nahm die erste, nicht
# die des Eingabefelds: der Prompt wurde nie gesendet, der Code meldete trotzdem
# Erfolg. Richtig ist die LETZTE sichtbare, aktive.
SUBMIT_REAL_CLICK = 'button.generate-icon-button:visible:enabled'
SUBMIT_CLICK_JS = """(() => {
    const sel = 'button[aria-label*="Generierung starten"], button[aria-label*="Generate"], button.generate-icon-button';
    const live = Array.from(document.querySelectorAll(sel)).filter(b => b.offsetParent && !b.disabled);
    const btn = live[live.length - 1];
    if (btn) { btn.click(); return true; }
    const fwd = Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent && !b.disabled)
        .reverse().find(b => (b.innerText || '').includes('arrow_forward'));
    if (fwd) { fwd.click(); return true; }
    return false;
})()"""
PROMPT_TEXT_JS = (
    "() => { const e = document.querySelector('.ProseMirror'); "
    "return e ? (e.innerText || '').trim() : ''; }"
)
