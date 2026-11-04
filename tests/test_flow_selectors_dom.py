"""Selektoren der Anhängen-Strecke gegen ein DOM, das die echte Flow-Seite nachbildet.

Die Struktur stammt aus dem live ausgelesenen Seitenbaum (Oktober 2026):

- Referenz-Chip im Prompt-Feld: Schaltfläche ``aria-label="Bildelement"`` mit
  Innentext ``cancel``.
- Miniaturen im Chatverlauf: ebenfalls ``aria-label="Bildelement"``, aber ohne ``cancel``.
- Asset-Menü: sichtbare Einträge mit Name und „Bild“; im Fuß eine UNSICHTBARE
  Schaltfläche mit dem Dateinamen als ``aria-label`` (traf der alte Selektor).

Der Test braucht einen Chrome mit Debug-Port 9222 (derselbe wie für Flow) und
wird sonst übersprungen. Er öffnet nur eine leere Seite und lädt keine Flow-URL.
"""

from __future__ import annotations

import re

import pytest

from core.api import google_flow_ui as ui

playwright_sync = pytest.importorskip("playwright.sync_api")

HTML = """
<html><body>
  <div id="history">
    <button aria-label="Bildelement" class="chip-container"></button>
    <button aria-label="Bildelement" class="chip-container"></button>
  </div>
  <div id="menu">
    <button><span>s02_keyframe.jpg</span><span>Bild</span></button>
    <button><span>Sunspot transforms woman</span><span>Video</span></button>
    <button><span>wide_01.jpg</span><span>Bild</span></button>
  </div>
  <button class="footer-left" aria-label="s02_keyframe.jpg" style="display:none"></button>
  <div id="composer">
    <button aria-label="Bildelement"><span>cancel</span></button>
    <button aria-label="Bildelement"><span>cancel</span></button>
    <button aria-label="Bildelemente zum Prompt-Feld hinzuf&uuml;gen"><span>add</span></button>
  </div>
  <button><span>Zum Prompt hinzuf&uuml;gen</span></button>
</body></html>
"""


@pytest.fixture(scope="module")
def page():
    pw = playwright_sync.sync_playwright().start()
    try:
        try:
            browser = pw.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=3000)
        except Exception:
            pytest.skip("kein Chrome mit Debug-Port 9222")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        pg = context.new_page()
        pg.set_content(HTML)
        yield pg
        pg.close()
    finally:
        pw.stop()


def test_chip_count_counts_only_composer_chips(page):
    assert page.evaluate(ui.CHIP_COUNT_JS) == 2


def test_chip_remove_selector_ignores_history_thumbnails(page):
    assert page.locator(ui.CHIP_REMOVE_BUTTON).count() == 2


def test_asset_item_finds_only_the_visible_image_entry(page):
    items = page.locator(ui.ASSET_ITEM).filter(has_text="s02_keyframe.jpg").filter(
        has_text=re.compile(ui.ASSET_TYPE_PATTERN)
    )
    assert items.count() == 1
    assert page.locator(ui.ASSET_ITEM).filter(has_text="Sunspot").filter(
        has_text=re.compile(ui.ASSET_TYPE_PATTERN)
    ).count() == 0


def test_attach_button_and_confirm_selectors_match(page):
    assert page.locator(ui.ATTACH_MEDIA_BUTTON).count() == 1
    assert page.locator(ui.ADD_TO_PROMPT_BUTTON).count() == 1


SUBMIT_HTML = """
<button id="a" aria-label="Generierung starten" onclick="window.hit='stale'">go</button>
<button id="b" aria-label="Generierung starten" onclick="window.hit='composer'">go</button>
<button id="c" aria-label="Generierung starten" disabled onclick="window.hit='disabled'">go</button>
"""


def test_submit_click_takes_the_last_active_button_not_the_first(page):
    """Flow hat mehrere „Generierung starten“-Schaltflächen; die erste ist nicht die des Eingabefelds."""
    other = page.context.new_page()
    try:
        other.set_content(SUBMIT_HTML)
        assert other.evaluate(ui.SUBMIT_CLICK_JS) is True
        assert other.evaluate("window.hit") == "composer"
    finally:
        other.close()
