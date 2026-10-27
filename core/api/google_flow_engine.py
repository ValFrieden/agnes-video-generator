"""core/api/google_flow_engine.py — Native Python Playwright Engine für Google Flow.

Ermöglicht vollautomatisierte, resiliente Video- und Bildgenerierung mit Google Veo 3.1
und Imagen über Google Flow (flow.google.com) via Chrome DevTools Protocol (CDP).

Merkmale:
- Reines Python über Playwright (async_api) — keine temporären Node.js-Skripte mehr.
- Resiliente mehrsprachige Selektoren (DE/EN) für alle Buttons, Menüs und Modale.
- Kostenschutz: liest die Kostenkarte des Agenten und genehmigt **einmalig**
  ('Genehmigen') nur innerhalb von ``max_credits``; 'Immer genehmigen' wird nie
  geklickt, weil das das Projekt dauerhaft auf automatisches Ausgeben schaltet.
- Nach dem Absenden wird nie automatisch neu abgeschickt: ein unklares Ergebnis
  hinterlässt eine ``.flow_pending.json``-Marke neben dem Zielclip.
- Sicheres Download-Handling mit direktem Speichern am Zielort.
- Integrierte automatische QA-Trio-Extraktion (25%, 50%, 75% Kontaktbogen) via FFmpeg.
- Voll kompatibel mit dem VideoGenerator Master Playbook.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from core.api.google_flow_errors import FlowStoppedError

logger = logging.getLogger(__name__)

# Kostenkarte des Agenten, z. B. "Das kostet 20 Guthabenpunkte."
# (Wortlaut wie in tools/google-flow-browser-mcp/src/utils/cost-guard.js)
_COST_REGEX = re.compile(
    r"(?:Das kostet|This (?:will )?costs?|Cela coûte)\s+(\d+)\s+"
    r"(?:Guthabenpunkte|credits|crédits)",
    re.IGNORECASE,
)
_UNUSUAL_REGEX = re.compile(r"ungewöhnliche Aktivitäten|unusual activity", re.IGNORECASE)

# Obergrenze der Guthabenpunkte pro Generierung (wie maxCreditsPerVideo
# in tools/google-flow-browser-mcp/config/flow.config.json)
DEFAULT_MAX_CREDITS = 20


class GoogleFlowEngine:
    """Robuste, native Python-Engine zur Steuerung von Google Flow via CDP."""

    def __init__(
        self,
        cdp_url: str = "http://127.0.0.1:9222",
        downloads_dir: Optional[str] = None,
        default_model: str = "Veo 3.1 - Fast",
        default_resolution: str = "720p",
        max_credits: int = DEFAULT_MAX_CREDITS,
    ):
        self.cdp_url = cdp_url
        self.downloads_dir = os.path.abspath(downloads_dir or os.path.expanduser("~/Downloads"))
        self.default_model = default_model
        self.default_resolution = default_resolution
        self.max_credits = max_credits

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def connect(self, timeout_sec: float = 15.0) -> Page:
        """Verbindet mit der laufenden Chrome-Instanz über CDP und findet den Flow-Tab."""
        if self._page and not self._page.is_closed():
            return self._page

        logger.info(f"[GoogleFlowEngine] Connecting to Chrome CDP at {self.cdp_url}...")
        self._playwright = await async_playwright().start()
        try:
            self._browser = await asyncio.wait_for(
                self._playwright.chromium.connect_over_cdp(self.cdp_url),
                timeout=timeout_sec,
            )
        except Exception as e:
            await self._cleanup()
            raise RuntimeError(
                f"[GoogleFlowEngine] Could not connect to Chrome on {self.cdp_url}. "
                f"Ensure Chrome is running with '--remote-debugging-port=9222'. Error: {e}"
            )

        contexts = self._browser.contexts
        if not contexts:
            await self._cleanup()
            raise RuntimeError("[GoogleFlowEngine] No browser context found in active Chrome session.")

        self._context = contexts[0]
        pages = self._context.pages

        # Find existing Flow page
        target_page = None
        for p in pages:
            url = p.url
            if "flow.google.com/project" in url:
                target_page = p
                break
            elif "flow.google.com" in url:
                target_page = p

        if not target_page:
            logger.info("[GoogleFlowEngine] Flow tab not found. Opening https://flow.google.com ...")
            target_page = await self._context.new_page()
            await target_page.goto("https://flow.google.com", wait_until="domcontentloaded")
            await asyncio.sleep(2)

        self._page = target_page
        logger.info(f"[GoogleFlowEngine] Connected to Flow page: {self._page.url}")
        return self._page

    async def _cleanup(self):
        """Räumt Ressourcen auf."""
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def close(self):
        """Schließt die Engine-Sitzung."""
        await self._cleanup()

    # =========================================================================
    # Resiliente UI-Interaktionen (Mehrsprachig DE / EN)
    # =========================================================================

    @staticmethod
    async def _visible(locator, timeout_ms: float = 2000) -> bool:
        """Prüft, ob ein Locator sichtbar wird, ohne bei Zeitablauf zu werfen.

        ``locator.is_visible()`` nimmt in Playwright-Python kein ``timeout``
        entgegen (der Parameter wird ignoriert), deshalb ``wait_for``.
        """
        try:
            await locator.wait_for(state="visible", timeout=timeout_ms)
            return True
        except Exception:
            return False

    async def exit_editor_if_open(self) -> bool:
        """Verlässt den Clip-Editor und kehrt zum Projekt-Canvas zurück."""
        page = await self.connect()
        exit_script = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const fertig = btns.find(b => {
                const t = (b.innerText || '').trim();
                return t === 'Fertig' || t === 'Done' || t === 'Schließen' || t === 'Close';
            });
            if (fertig) { fertig.click(); return true; }
            return false;
        })()"""
        exited = await page.evaluate(exit_script)
        if exited:
            logger.info("[GoogleFlowEngine] Exited clip editor back to canvas.")
            await asyncio.sleep(1.5)
        return bool(exited)

    async def attach_reference_image(self, image_path: str, max_retries: int = 2) -> bool:
        """Lädt eine Referenzabbildung hoch oder wählt sie aus und hängt sie an den Prompt an."""
        page = await self.connect()
        img_file = Path(image_path)
        if not img_file.exists():
            raise FileNotFoundError(f"Reference image not found: {image_path}")

        img_name = img_file.name
        norm_path = str(img_file.resolve()).replace("\\", "/")

        for attempt in range(1, max_retries + 1):
            try:
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.4)

                # 1. Klicke auf 'Bildelemente hinzufügen' / 'Medien hinzufügen' / '+'
                add_btn_selectors = [
                    'button[aria-label*="Bildelemente"]',
                    'button[aria-label*="hinzufügen"]',
                    'button[aria-label*="Add media"]',
                    'button[aria-label*="Add"]',
                ]
                add_btn = None
                for sel in add_btn_selectors:
                    locator = page.locator(sel).last
                    if await self._visible(locator, 2000):
                        add_btn = locator
                        break

                if not add_btn:
                    # Fallback auf generische Buttons
                    add_btn = page.locator('button:has(svg), button.add-media-button').last

                await add_btn.click(force=True)
                await asyncio.sleep(1.5)

                # 2. Prüfen, ob das Asset bereits in der Bibliothek liegt
                asset = page.locator(f'text="{img_name}"').first
                is_visible = await self._visible(asset, 2000)

                if is_visible:
                    logger.info(f"[GoogleFlowEngine] Asset '{img_name}' found in project library. Selecting it.")
                    await asset.click(force=True)
                else:
                    logger.info(f"[GoogleFlowEngine] Asset '{img_name}' not in library. Uploading...")
                    upload_btn = page.locator(
                        'button:has-text("Medien hoch"), button:has-text("Upload"), [aria-label*="hochladen"], [aria-label*="Upload"]'
                    ).first

                    async with page.expect_file_chooser(timeout=15000) as fc_info:
                        await upload_btn.click(force=True)
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(norm_path)

                    logger.info(f"[GoogleFlowEngine] Upload started for {img_name}. Waiting for thumbnail...")
                    await asyncio.sleep(5.0)

                    asset = page.locator(f'text="{img_name}"').first
                    await asset.wait_for(state="visible", timeout=12000)
                    await asset.click(force=True)

                # 3. Klicke auf 'Zum Prompt hinzufügen' / 'Add to prompt'
                add_to_prompt_btn = page.locator(
                    'button:has-text("Zum Prompt hinzufügen"), button:has-text("Add to prompt")'
                ).first
                if await self._visible(add_to_prompt_btn, 3000):
                    await add_to_prompt_btn.click(force=True)
                    logger.info(f"[GoogleFlowEngine] Successfully attached '{img_name}' to prompt.")

                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
                return True

            except Exception as e:
                logger.warning(f"[GoogleFlowEngine] Attempt {attempt} attaching image failed: {e}")
                await page.keyboard.press("Escape")
                await asyncio.sleep(1.5)

        raise RuntimeError(f"[GoogleFlowEngine] Failed to attach reference image '{image_path}' after retries.")

    async def set_prompt(self, prompt_text: str) -> bool:
        """Fügt den Prompt in den ProseMirror-Editor von Flow ein."""
        page = await self.connect()
        set_script = f"""(() => {{
            const pm = document.querySelector('.ProseMirror');
            if (!pm) return false;
            pm.focus();
            pm.innerText = {json.dumps(prompt_text)};
            pm.dispatchEvent(new Event('input', {{ bubbles: true }}));
            return true;
        }})()"""
        success = await page.evaluate(set_script)
        if not success:
            # Fallback: Playwright locator fill
            pm_loc = page.locator('.ProseMirror, [contenteditable="true"]').first
            await pm_loc.click()
            await pm_loc.fill(prompt_text)
        await asyncio.sleep(0.8)
        return True

    async def submit_prompt(self) -> bool:
        """Klickt auf den Generieren-Absendebutton."""
        page = await self.connect()
        submit_script = """(() => {
            const btn = document.querySelector('button[aria-label*="Generierung starten"], button[aria-label*="Generate"], button.generate-icon-button');
            if (btn) { btn.click(); return true; }
            const allBtns = Array.from(document.querySelectorAll('button'));
            const fwd = allBtns.find(b => {
                const t = (b.innerText || '');
                return t.includes('arrow_forward') || t.includes('Generieren') || t.includes('Generate');
            });
            if (fwd) { fwd.click(); return true; }
            return false;
        })()"""
        res = await page.evaluate(submit_script)
        await asyncio.sleep(2.0)
        return bool(res)

    # =========================================================================
    # Kostenschutz (Logikcheck Befund 2)
    # =========================================================================
    #
    # Die Kostenkarte des Flow-Agenten ist kein Knopf, sondern eine
    # ``<flow-permission-message>`` mit ``[role="radio"]``-Optionen
    # ('Genehmigen' / 'Immer genehmigen' / 'Ablehnen'). 'Immer genehmigen'
    # schaltet das Projekt dauerhaft auf automatisches Ausgeben und wird hier
    # **nie** geklickt — identisch zur Regel des Node-Servers
    # (tools/google-flow-browser-mcp/src/utils/cost-guard.js).

    async def count_cost_cards(self) -> int:
        """Zählt die aktuell sichtbaren Kostenkarten im Agenten-Verlauf."""
        page = await self.connect()
        try:
            text = await page.inner_text("body")
        except Exception:
            return 0
        return len(_COST_REGEX.findall(text or ""))

    async def wait_for_cost_card(
        self,
        previous_count: int,
        timeout_seconds: float = 120.0,
    ) -> Dict[str, Any]:
        """Wartet auf eine **neue** Kostenkarte und liest den Preis.

        Returns:
            ``{"cost": int}`` bei lesbarem Preis, sonst ``{"cost": None, ...}``
            mit ``unusual_activity`` bzw. ``agent_text``. Es wird nichts
            geklickt, also kein Guthaben ausgegeben.
        """
        page = await self.connect()
        start = time.time()
        while (time.time() - start) < timeout_seconds:
            try:
                text = await page.inner_text("body")
            except Exception:
                text = ""
            matches = _COST_REGEX.findall(text or "")
            if len(matches) > previous_count:
                cost = int(matches[-1])
                logger.info(f"[GoogleFlowEngine] Cost card detected: {cost} credits")
                return {"cost": cost}

            # Missbrauchsschutz von Google: sofort anhalten, nie automatisch wiederholen
            try:
                bubble = await page.locator("flow-chat-bubble").last.inner_text()
            except Exception:
                bubble = ""
            if _UNUSUAL_REGEX.search(bubble or ""):
                logger.warning("[GoogleFlowEngine] Flow reported unusual activity.")
                return {
                    "cost": None,
                    "unusual_activity": True,
                    "agent_text": (bubble or "")[:400],
                }
            await asyncio.sleep(1.5)

        return {"cost": None, "agent_text": "cost card did not appear in time"}

    async def _choose_on_last_card(self, labels: List[str]) -> bool:
        """Wählt die erste verfügbare Option auf der letzten Kostenkarte."""
        page = await self.connect()
        card = page.locator("flow-permission-message").last
        for label in labels:
            option = card.locator(f'[role="radio"][aria-label="{label}"]').first
            if not await self._visible(option, 2000):
                continue
            # Eine bereits entschiedene Karte ist nur noch lesbar
            try:
                if await option.get_attribute("aria-disabled") == "true":
                    return False
            except Exception:
                pass
            await option.click(timeout=5000)
            for _ in range(10):
                await asyncio.sleep(0.5)
                try:
                    if await option.get_attribute("aria-checked") == "true":
                        return True
                except Exception:
                    pass
                if not await self._visible(option, 500):
                    return True  # Karte nach der Entscheidung ersetzt
            logger.warning(f"[GoogleFlowEngine] Cost card choice not confirmed: {label}")
            return False
        return False

    async def approve_cost_card(self) -> bool:
        """Genehmigt **einmalig** ('Genehmigen'), niemals 'Immer genehmigen'."""
        return await self._choose_on_last_card(["Genehmigen", "Approve"])

    async def reject_cost_card(self) -> bool:
        """Lehnt die Kostenkarte ab ('Ablehnen')."""
        return await self._choose_on_last_card(["Ablehnen", "Decline", "Reject"])

    async def confirm_within_budget(
        self,
        previous_card_count: int,
        max_credits: Optional[int] = None,
        timeout_seconds: float = 120.0,
    ) -> int:
        """Liest den Preis und genehmigt nur innerhalb des Limits.

        Args:
            previous_card_count: Kartenzahl **vor** dem Absenden.
            max_credits: Obergrenze pro Generierung; ``None`` nutzt
                ``self.max_credits``.
            timeout_seconds: Wartezeit auf die Kostenkarte.

        Returns:
            Die genehmigten Guthabenpunkte.

        Raises:
            FlowStoppedError: Preis über dem Limit, unlesbar oder
                Aktivitätswarnung — es wurde nichts genehmigt.
        """
        limit = self.max_credits if max_credits is None else max_credits
        card = await self.wait_for_cost_card(previous_card_count, timeout_seconds)
        cost = card.get("cost")

        if cost is None:
            # Fail closed: ohne lesbaren Preis wird nichts genehmigt
            await self.reject_cost_card()
            if card.get("unusual_activity"):
                raise FlowStoppedError(
                    "Flow meldet ungewöhnliche Aktivitäten. Nicht automatisch wiederholen — "
                    f"Konto in Flow prüfen. Agent: {card.get('agent_text', '')[:200]}",
                    status="flow_unusual_activity",
                )
            raise FlowStoppedError(
                "Keine lesbare Kostenkarte — es wurde nichts genehmigt. "
                f"Agent: {card.get('agent_text', '')[:200]}",
                status="cost_unreadable",
            )

        if cost > limit:
            declined = await self.reject_cost_card()
            raise FlowStoppedError(
                f"Kosten {cost} Guthabenpunkte über dem Limit {limit} — nicht generiert"
                + ("." if declined else ", und 'Ablehnen' war nicht klickbar: in Flow manuell ablehnen."),
                status="cost_blocked",
            )

        if not await self.approve_cost_card():
            raise FlowStoppedError(
                "'Genehmigen' war auf der Kostenkarte nicht klickbar — nichts genehmigt.",
                status="approve_failed",
            )
        logger.info(f"[GoogleFlowEngine] Approved once: {cost} credits (limit {limit})")
        await asyncio.sleep(2.0)
        return cost

    async def get_video_tiles_count(self) -> int:
        """Gibt die aktuelle Anzahl der Videokacheln im Canvas zurück."""
        page = await self.connect()
        return await page.evaluate("document.querySelectorAll('flow-video-tile').length")

    async def wait_for_video_completion(
        self,
        initial_tiles_count: int,
        timeout_seconds: int = 240,
        poll_interval: float = 4.0,
    ) -> bool:
        """Wartet, bis die neu generierte Videokachel fertiggestellt ist."""
        page = await self.connect()
        start_time = time.time()
        logger.info(f"[GoogleFlowEngine] Waiting for video render (initial count: {initial_tiles_count})...")

        while (time.time() - start_time) < timeout_seconds:
            await asyncio.sleep(poll_interval)
            elapsed = int(time.time() - start_time)

            status_script = """(() => {
                const tiles = document.querySelectorAll('flow-video-tile').length;
                const body = document.body.innerText;
                const match = body.match(/(\\d+)\\s*%/);
                return {
                    tiles,
                    progress: match ? match[1] : null
                };
            })()"""
            status = await page.evaluate(status_script)
            current_tiles = status.get("tiles", 0)
            progress = status.get("progress")

            if current_tiles > initial_tiles_count and elapsed > 20:
                logger.info(f"[GoogleFlowEngine] [+{elapsed}s] New video tile ready! (tiles: {current_tiles})")
                await asyncio.sleep(2.5)
                return True
            elif progress:
                logger.info(f"[GoogleFlowEngine] [+{elapsed}s] Progress: {progress}%")
            else:
                logger.info(f"[GoogleFlowEngine] [+{elapsed}s] Rendering in progress...")

        logger.warning(f"[GoogleFlowEngine] Timed out waiting for video completion after {timeout_seconds}s.")
        return False

    async def download_latest_video(
        self,
        target_clip_path: str,
        resolution: str = "720p",
        timeout_seconds: int = 45,
    ) -> str:
        """Öffnet die neueste Kachel (Index 0), triggert den 720p Download und speichert direkt."""
        page = await self.connect()
        target_path = Path(target_clip_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Opening latest video tile (index 0)...")
        opened = await page.evaluate("""(() => {
            const tiles = document.querySelectorAll('flow-video-tile');
            if (tiles.length > 0) {
                tiles[0].click();
                return true;
            }
            return false;
        })()""")
        if not opened:
            raise RuntimeError("No flow-video-tile found to open.")
        await asyncio.sleep(2.0)

        # Snapshot vor Download im Downloads-Ordner (Logikcheck Befund 4):
        # Nur Dateien gelten, die NACH diesem Zeitpunkt entstanden sind — sonst
        # wird eine beliebige fremde .mp4 des Nutzers als Ergebnis ausgegeben.
        initial_downloads = set(os.listdir(self.downloads_dir)) if os.path.exists(self.downloads_dir) else set()
        click_time = time.time()

        # Download-Button im Video-Editor klicken
        click_dl_btn_script = """(() => {
            const btn = document.querySelector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]');
            if (btn) { btn.click(); return true; }
            return false;
        })()"""
        if not await page.evaluate(click_dl_btn_script):
            raise RuntimeError("[GoogleFlowEngine] Download button not found in the video editor.")
        await asyncio.sleep(1.2)

        # Auflösung auswählen (z.B. 720p) — ohne Blindklick-Fallback:
        # ein beliebiger erster Menüeintrag kann 'Löschen' o. Ä. sein.
        click_res_script = f"""(() => {{
            const items = Array.from(document.querySelectorAll('button, [role="menuitem"], flow-menu-item'));
            const target = items.find(el => (el.innerText || '').includes('{resolution}'));
            if (target) {{
                const b = target.tagName === 'BUTTON' ? target : (target.querySelector('button') || target);
                b.click();
                return true;
            }}
            return false;
        }})()"""
        if not await page.evaluate(click_res_script):
            raise RuntimeError(
                f"[GoogleFlowEngine] Download menu item '{resolution}' not found — nothing clicked."
            )

        # Warten auf heruntergeladene MP4-Datei (jüngste passende Datei)
        logger.info(f"[GoogleFlowEngine] Awaiting downloaded MP4 for {target_path.name}...")
        downloaded_file = None
        for _ in range(timeout_seconds):
            await asyncio.sleep(1.0)
            if not os.path.exists(self.downloads_dir):
                continue
            candidates = []
            for name in os.listdir(self.downloads_dir):
                if name in initial_downloads or not name.endswith(".mp4"):
                    continue
                path = os.path.join(self.downloads_dir, name)
                try:
                    stat = os.stat(path)
                except OSError:
                    continue
                if stat.st_mtime < click_time or stat.st_size <= 50000:
                    continue
                candidates.append((stat.st_mtime, path))
            if candidates:
                downloaded_file = max(candidates)[1]
                break

        if not downloaded_file:
            raise TimeoutError(f"[GoogleFlowEngine] Download failed to complete within {timeout_seconds}s.")

        # Datei zum Zielort verschieben
        if target_path.exists():
            target_path.unlink()
        shutil.copy2(downloaded_file, str(target_path))
        try:
            os.unlink(downloaded_file)
        except Exception:
            pass

        logger.info(f"[GoogleFlowEngine] Saved video clip to: {target_path} ({target_path.stat().st_size} bytes)")

        # Zurück zum Canvas
        await self.exit_editor_if_open()
        return str(target_path)

    # =========================================================================
    # QA-Extraktion via FFmpeg
    # =========================================================================

    @staticmethod
    def generate_qa_trio(video_path: str, output_trio_path: Optional[str] = None) -> str:
        """Extrahiert Frames bei 25%, 50% und 75% der Laufzeit und erstellt ein Kontaktblatt."""
        v_path = Path(video_path)
        if not v_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Dauer abfragen
        cmd_dur = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(v_path)
        ]
        dur_str = subprocess.check_output(cmd_dur, text=True).strip()
        dur = float(dur_str)

        t1 = str(round(dur * 0.25, 2))
        t2 = str(round(dur * 0.50, 2))
        t3 = str(round(dur * 0.75, 2))

        clips_dir = v_path.parent
        stem = v_path.stem
        qa25 = clips_dir / f"{stem}_qa25.png"
        qa50 = clips_dir / f"{stem}_qa50.png"
        qa75 = clips_dir / f"{stem}_qa75.png"
        trio = Path(output_trio_path) if output_trio_path else (clips_dir / f"{stem}_qa_trio.png")

        subprocess.run(["ffmpeg", "-y", "-ss", t1, "-i", str(v_path), "-frames:v", "1", str(qa25)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-ss", t2, "-i", str(v_path), "-frames:v", "1", str(qa50)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-ss", t3, "-i", str(v_path), "-frames:v", "1", str(qa75)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Horizontale Montage (hstack)
        subprocess.run([
            "ffmpeg", "-y", "-i", str(qa25), "-i", str(qa50), "-i", str(qa75),
            "-filter_complex", "[0:v][1:v][2:v]hstack=inputs=3[v]",
            "-map", "[v]", str(trio)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        logger.info(f"[GoogleFlowEngine] Created QA contact sheet: {trio}")
        return str(trio)

    # =========================================================================
    # High-Level Full Scene Pipeline
    # =========================================================================

    async def generate_scene(
        self,
        prompt: str,
        reference_image_path: Optional[str],
        output_clip_path: str,
        style_suffix: str = "Authentic 35mm film still, Kodak Portra 400 grain, Roger Deakins natural lighting, human documentary realism, quiet emotion, 16:9 widescreen",
        skip_if_exists: bool = True,
        max_retries: int = 2,
    ) -> bool:
        """Führt eine komplette Szene Ende-zu-Ende durch."""
        target = Path(output_clip_path)
        pending_marker = target.with_suffix(target.suffix + ".flow_pending.json")

        if skip_if_exists and target.exists() and target.stat().st_size > 500000:
            logger.info(f"[GoogleFlowEngine] Clip '{target.name}' already exists ({target.stat().st_size} bytes). Skipping.")
            return True

        # Logikcheck Befund 3/4: Eine frühere Generierung wurde genehmigt, ihr
        # Ergebnis ist aber unbekannt. Nicht erneut abschicken (das würde ein
        # zweites Mal Guthaben kosten) — erst in Flow nachsehen.
        if pending_marker.exists():
            logger.warning(
                f"[GoogleFlowEngine] '{target.name}' has a pending marker ({pending_marker.name}). "
                "Check the clip in Flow and delete the marker to retry. Skipping."
            )
            return False

        full_prompt = f"Generate video with Veo: {prompt}. {style_suffix}".strip()

        # ── Phase 1: Vorbereitung (kostenlos, daher wiederholbar) ──
        prepared = False
        initial_tiles = 0
        cards_before = 0
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[GoogleFlowEngine] Preparing generation, attempt {attempt} for {target.name}...")
                await self.exit_editor_if_open()
                if reference_image_path and os.path.exists(reference_image_path):
                    await self.attach_reference_image(reference_image_path)
                await self.set_prompt(full_prompt)
                initial_tiles = await self.get_video_tiles_count()
                cards_before = await self.count_cost_cards()
                prepared = True
                break
            except Exception as e:
                logger.error(f"[GoogleFlowEngine] Preparation attempt {attempt} for {target.name} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(5.0)

        if not prepared:
            return False

        # ── Phase 2: Absenden, Kosten prüfen, genehmigen, warten (genau EINMAL) ──
        # Ab hier wird nie neu abgeschickt: jeder weitere Versuch kostet erneut.
        try:
            await self.submit_prompt()
        except Exception as e:
            logger.error(f"[GoogleFlowEngine] Submit for {target.name} failed: {e}")
            self._write_pending_marker(pending_marker, target, "submit_failed", str(e))
            return False

        # FlowStoppedError (Limit/unlesbar/Aktivitätswarnung) reicht nach oben
        # durch: dann wurde nichts genehmigt und der Stapel soll anhalten.
        cost = await self.confirm_within_budget(cards_before)

        try:
            completed = await self.wait_for_video_completion(initial_tiles)
            if not completed:
                raise TimeoutError("Render timed out or tile count did not increment.")
        except Exception as e:
            logger.error(f"[GoogleFlowEngine] Waiting for {target.name} failed: {e}")
            self._write_pending_marker(pending_marker, target, "render_timeout", str(e), cost)
            return False

        # ── Phase 3: Download (bis zu 2 Versuche, ohne neues Absenden) ──
        downloaded = False
        last_error = "unknown"
        for attempt in range(1, 3):
            try:
                await self.download_latest_video(str(target), resolution=self.default_resolution)
                downloaded = True
                break
            except Exception as e:
                logger.error(f"[GoogleFlowEngine] Download attempt {attempt} for {target.name} failed: {e}")
                last_error = str(e)
                if attempt < 2:
                    await asyncio.sleep(3.0)
                    await self.exit_editor_if_open()

        if not downloaded:
            self._write_pending_marker(pending_marker, target, "download_failed", last_error, cost)
            return False

        # ── QA-Kontaktbogen: Zusatznutzen, kein Grund zur Neugenerierung ──
        try:
            self.generate_qa_trio(str(target))
        except Exception as e:
            logger.warning(f"[GoogleFlowEngine] QA contact sheet for {target.name} failed (clip is fine): {e}")

        return True

    @staticmethod
    def _write_pending_marker(
        marker: Path,
        target: Path,
        status: str,
        detail: str,
        cost: Optional[int] = None,
    ) -> None:
        """Vermerkt eine genehmigte, aber unbestätigte Generierung auf Platte."""
        payload = {
            "status": status,
            "detail": detail[:500],
            "clip": str(target),
            "approved_credits": cost,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "hint": "Clip in Google Flow prüfen; zum erneuten Versuch diese Datei löschen.",
        }
        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.warning(f"[GoogleFlowEngine] Wrote pending marker: {marker}")
        except OSError as e:
            logger.error(f"[GoogleFlowEngine] Could not write pending marker {marker}: {e}")
