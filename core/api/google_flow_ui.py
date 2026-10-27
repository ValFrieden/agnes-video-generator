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
# VERIFIED
ATTACH_MEDIA_BUTTON = '[aria-label="Bildelemente zum Prompt-Feld hinzufügen"]'
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
# VERIFIED
CHARACTER_PAGE = "flow-character-page"
CHARACTER_HEADER = "flow-character-header"
CHARACTER_DESCRIPTION = (
    'div[role="textbox"][aria-label="Charakter beschreiben…"], '
    'div[role="textbox"][aria-label*="Charakter beschreib"], '
    'div[role="textbox"][aria-label*="Describe"]'
)
CHARACTER_UPLOAD_BUTTON = (
    'button:has-text("Hochladen"), button:has-text("Upload")'
)
CHARACTER_FROM_PROJECT_BUTTON = (
    'button:has-text("Aus Projekt hinzufügen"), button:has-text("Add from project")'
)
CHARACTER_FOOTER = "flow-create-character-footer"

# UNVERIFIED: Namensfeld und „Fertig“ erscheinen erst, wenn ein Referenzbild
# vorliegt. In einem leeren Projekt gibt es noch kein input-Element, deshalb
# werden mehrere Kandidaten versucht und das Ergebnis über die Liste geprüft.
CHARACTER_NAME_INPUT = (
    'input[aria-label*="Name"], input[placeholder*="Name"], '
    'input[aria-label="Bearbeitbarer Text"], '
    'div[role="textbox"][aria-label*="Name"]'
)
CHARACTER_DONE_BUTTON = (
    'button:has-text("Fertig"), button:has-text("Done"), '
    'button:has-text("Speichern"), button:has-text("Save")'
)
# UNVERIFIED: Karten vorhandener Charaktere (Projekt war leer).
CHARACTER_CARD = (
    "flow-character-card, flow-character-tile, [class*='character-card']"
)

# ── Szenen-Montage (über das Kachelmenü eines Clips) ────────────────────────
# UNVERIFIED: Das Projekt enthielt keine Clips, daher war das Menü nicht
# auslesbar. Wortlaut aus Googles Hilfe (Clip → Mehr → „Zu Szene hinzufügen“).
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

# ── Download einer Videokachel ──────────────────────────────────────────────
DOWNLOAD_MEDIA_BUTTON = (
    'button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]'
)
