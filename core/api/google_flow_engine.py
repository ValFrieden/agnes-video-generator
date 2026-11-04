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

from core.api import google_flow_ui as ui
from core.api.google_flow_errors import FlowStoppedError
from core.flow_shot_state import ShotStatus, prompt_hash

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

    async def count_attached_chips(self) -> int:
        """Zählt die Referenz-Chips im Prompt-Feld (nicht die Miniaturen im Verlauf)."""
        page = await self.connect()
        return int(await page.evaluate(ui.CHIP_COUNT_JS))

    async def _remove_extra_chips(self, target: int) -> None:
        """Entfernt Chips vom Ende, bis höchstens ``target`` übrig sind."""
        page = await self.connect()
        for _ in range(8):
            if await self.count_attached_chips() <= target:
                return
            await page.locator(ui.CHIP_REMOVE_BUTTON).last.click(force=True)
            await asyncio.sleep(0.6)

    @staticmethod
    def _asset_item(page: Page, name: str):
        """Sichtbarer Bild-Eintrag im Asset-Menü (nicht die versteckte Fußschaltfläche)."""
        return (
            page.locator(ui.ASSET_ITEM)
            .filter(has_text=name)
            .filter(has_text=re.compile(ui.ASSET_TYPE_PATTERN))
            .first
        )

    async def attach_reference_image(self, image_path: str, max_retries: int = 2) -> bool:
        """Lädt eine Referenzabbildung hoch oder wählt sie aus und hängt sie an den Prompt an.

        Prüft das Ergebnis: Nach dem Anhängen muss genau ein Chip mehr im Feld
        stehen. Hat Flow das Asset schon beim Klick angehängt, wird die
        Bestätigung nicht zusätzlich geklickt (sonst Doppelchip); überzählige
        Chips werden entfernt.

        Raises:
            RuntimeError: Nach allen Versuchen steht nicht genau ein neuer Chip im Feld.
        """
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
                before = await self.count_attached_chips()

                # 1. Asset-Menü öffnen
                add_btn = page.locator(ui.ATTACH_MEDIA_BUTTON).last
                if not await self._visible(add_btn, 3000):
                    raise RuntimeError("attach-media button not visible")
                await add_btn.click(force=True)
                await asyncio.sleep(1.5)

                # 2. Asset auswählen (ggf. erst hochladen)
                asset = self._asset_item(page, img_name)
                if await self._visible(asset, 2500):
                    logger.info(f"[GoogleFlowEngine] Asset '{img_name}' found in project library. Selecting it.")
                else:
                    logger.info(f"[GoogleFlowEngine] Asset '{img_name}' not in library. Uploading...")
                    upload_btn = page.locator(ui.ASSET_UPLOAD_BUTTON).first
                    async with page.expect_file_chooser(timeout=15000) as fc_info:
                        await upload_btn.click(force=True)
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(norm_path)
                    logger.info(f"[GoogleFlowEngine] Upload started for {img_name}. Waiting for thumbnail...")
                    await asyncio.sleep(5.0)
                    asset = self._asset_item(page, img_name)
                    await asset.wait_for(state="visible", timeout=12000)
                await asset.click(force=True)
                await asyncio.sleep(1.5)

                # 3. Bestätigen, aber nur wenn der Klick nicht schon angehängt hat
                if await self.count_attached_chips() <= before:
                    confirm = page.locator(ui.ADD_TO_PROMPT_BUTTON).first
                    if await self._visible(confirm, 3000):
                        await confirm.click(force=True)
                        await asyncio.sleep(1.0)

                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)

                # 4. Ergebnis prüfen: genau ein neuer Chip
                after = await self.count_attached_chips()
                if after > before + 1:
                    await self._remove_extra_chips(before + 1)
                    after = await self.count_attached_chips()
                if after != before + 1:
                    raise RuntimeError(
                        f"expected {before + 1} chips after attaching '{img_name}', found {after}"
                    )
                logger.info(f"[GoogleFlowEngine] Successfully attached '{img_name}' to prompt ({after} chips).")
                return True

            except Exception as e:
                logger.warning(f"[GoogleFlowEngine] Attempt {attempt} attaching image failed: {e}")
                await page.keyboard.press("Escape")
                await asyncio.sleep(1.5)

        raise RuntimeError(f"[GoogleFlowEngine] Failed to attach reference image '{image_path}' after retries.")

    async def attach_references(self, image_paths: List[str]) -> int:
        """Hängt mehrere Referenzbilder in der angegebenen Reihenfolge an.

        Das Feld sollte vorher leer sein (``clear_prompt``). Jedes Bild wird
        einzeln geprüft; am Ende müssen genau ``len(image_paths)`` neue Chips
        im Feld stehen.

        Returns:
            Anzahl der Chips im Feld nach dem Anhängen.

        Raises:
            RuntimeError: Anzahl der Chips stimmt nicht.
        """
        start = await self.count_attached_chips()
        for path in image_paths:
            await self.attach_reference_image(path)
        total = await self.count_attached_chips()
        if total != start + len(image_paths):
            raise RuntimeError(
                f"[GoogleFlowEngine] Expected {start + len(image_paths)} chips, found {total}."
            )
        return total

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
        """Klickt auf den Generieren-Absendebutton des Eingabefelds.

        Gilt nur als gesendet, wenn das Eingabefeld danach leer ist; sonst
        ``False`` (der Aufrufer darf dann nicht auf eine Antwort warten).
        """
        page = await self.connect()
        before = await page.evaluate(ui.PROMPT_TEXT_JS)
        # VERIFIED live: ein JS-``click()`` löst das Absenden nicht aus, ein echter
        # Mausklick (Playwright) schon. Das JS bleibt nur als Rückfall.
        clicked = False
        try:
            btn = page.locator(ui.SUBMIT_REAL_CLICK).last
            await btn.click(timeout=5000)
            clicked = True
        except Exception as e:
            logger.warning(f"[GoogleFlowEngine] Real submit click failed ({e}); falling back to JS click.")
            clicked = await page.evaluate(ui.SUBMIT_CLICK_JS)
        await asyncio.sleep(2.0)
        if not clicked:
            return False
        if not before:
            return True  # nichts zu prüfen: Feld war schon leer
        return not await page.evaluate(ui.PROMPT_TEXT_JS)

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
        try:
            baseline_bubble = await page.locator("flow-chat-bubble").last.inner_text()
        except Exception:
            baseline_bubble = ""
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

            # Rückfrage statt Kostenkarte (z. B. „Dauer nicht unterstützt, welche Option?“):
            # sofort melden, statt bis zum Zeitablauf zu warten.
            if (
                (time.time() - start) > 10
                and bubble
                and bubble != baseline_bubble
                and bubble.rstrip().endswith("?")
            ):
                logger.warning("[GoogleFlowEngine] Agent asked a question instead of showing a cost card.")
                return {"cost": None, "agent_question": True, "agent_text": bubble[:600]}
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
        policy: Optional[Any] = None,
        ledger: Optional[Any] = None,
        shot_id: Optional[str] = None,
        account: str = "default",
    ) -> int:
        """Liest den Preis und genehmigt nur innerhalb des Limits.

        Args:
            previous_card_count: Kartenzahl **vor** dem Absenden.
            max_credits: Obergrenze pro Generierung; ``None`` nutzt
                ``self.max_credits``.
            timeout_seconds: Wartezeit auf die Kostenkarte.
            policy: Optional ``core.flow_budget.BudgetPolicy`` (Gesamtbudget,
                Reserve). Verletzt der Preis sie, wird abgelehnt.
            ledger: Optional ``core.flow_budget.CreditLedger``; jede Genehmigung
                und jede Ablehnung wird dort protokolliert.
            shot_id: Nur für das Journal.
            account: Konto-Name für Policy und Journal.
            prompt_as_is: ``prompt`` unverändert senden (z. B. aus
                ``core.flow_prompts.video_prompt``), ohne Präfix und Stilsuffix.

        Returns:
            Die genehmigten Guthabenpunkte.

        Raises:
            FlowStoppedError: Preis über dem Limit, unlesbar oder
                Aktivitätswarnung — es wurde nichts genehmigt.
        """
        limit = self.max_credits if max_credits is None else max_credits
        if max_credits is None and policy is not None:
            limit = policy.per_clip_max
        card = await self.wait_for_cost_card(previous_card_count, timeout_seconds)
        cost = card.get("cost")

        if cost is None and card.get("agent_question"):
            # Keine Kostenkarte, daher nichts zu genehmigen oder abzulehnen.
            raise FlowStoppedError(
                f"Der Agent stellt eine Rückfrage statt eine Kostenkarte zu zeigen: "
                f"{card.get('agent_text', '')[:400]}",
                status="agent_question",
            )

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

        balance = ledger.last_balance(account) if ledger is not None else None
        if policy is not None:
            spent = ledger.spent(account) if ledger is not None else 0
            reason = policy.check(cost, spent=spent, balance=balance)
            if reason:
                await self.reject_cost_card()
                if ledger is not None:
                    ledger.record("blocked", cost, account=account, shot_id=shot_id, note=reason)
                raise FlowStoppedError(f"Budget-Policy: {reason} — nicht generiert.", status="budget_blocked")

        if not await self.approve_cost_card():
            raise FlowStoppedError(
                "'Genehmigen' war auf der Kostenkarte nicht klickbar — nichts genehmigt.",
                status="approve_failed",
            )
        if ledger is not None:
            ledger.record(
                "approved",
                cost,
                account=account,
                shot_id=shot_id,
                balance_before=balance,
                balance_after=(balance - cost) if balance is not None else None,
            )
        logger.info(f"[GoogleFlowEngine] Approved once: {cost} credits (limit {limit})")
        await asyncio.sleep(2.0)
        return cost

    # =========================================================================
    # Teil C: Projekt-Einstellungen prüfen (nur lesen, nie ändern)
    # =========================================================================

    async def read_confirm_policy(self) -> Optional[str]:
        """Liest „Vor dem Generieren bestätigen“ aus den Agent-Einstellungen.

        Returns:
            ``"always"`` (Flow fragt vor dem Ausgeben), ``"never"`` (Flow gibt
            Guthaben automatisch aus) oder ``None`` bei unlesbarer Oberfläche.
            Die Einstellung wird nur gelesen und beim Verlassen nicht gespeichert.
        """
        page = await self.connect()
        try:
            await page.locator(ui.AGENT_SETTINGS_BUTTON).last.click(timeout=5000)
            group = page.locator(ui.CONFIRM_POLICY_GROUP).first
            await group.wait_for(state="visible", timeout=5000)
            value = await group.evaluate(
                "g => g.querySelector('input[type=\"radio\"]:checked')?.value || null"
            )
        except Exception as e:
            logger.warning(f"[GoogleFlowEngine] Could not read confirm policy: {e}")
            return None
        finally:
            try:
                back = page.locator(ui.SETTINGS_BACK_BUTTON).first
                if await self._visible(back, 1000):
                    await back.click()
            except Exception:
                pass
        if value == ui.CONFIRM_POLICY_ALWAYS_VALUE:
            return "always"
        if value == ui.CONFIRM_POLICY_NEVER_VALUE:
            return "never"
        return None

    async def ensure_cost_guard_active(self) -> None:
        """Bricht ab, wenn Flow Guthaben ohne Rückfrage ausgeben würde.

        Steht die Bestätigung auf „Nie“, generiert Flow schon beim Absenden und
        zieht das Guthaben ab — ``confirm_within_budget`` käme zu spät. Die
        Einstellung gehört dem Nutzer und wird deshalb nicht automatisch geändert.

        Raises:
            FlowStoppedError: Bestätigung steht auf „Nie“ oder ist unlesbar.
        """
        policy = await self.read_confirm_policy()
        if policy == "always":
            return
        shown = "Nie" if policy == "never" else "unlesbar"
        raise FlowStoppedError(
            f"Flow-Einstellung 'Vor dem Generieren bestätigen' ist {shown}. Dann wird beim "
            "Absenden sofort bezahlt und der Kostenschutz greift nicht. In den "
            "Agent-Einstellungen auf 'Immer' stellen und erneut starten.",
            status="confirm_policy_off",
        )

    async def clear_prompt(self) -> None:
        """Leert das Prompt-Feld samt angehängter Referenzen.

        Ohne das bleiben Referenz-Chips der vorigen Szene im Feld und die nächste
        Generierung zeigt die falsche Figur.

        Raises:
            RuntimeError: Das Feld ließ sich nicht leeren.
        """
        page = await self.connect()
        await self._remove_extra_chips(0)
        if await self.count_attached_chips():
            raise RuntimeError("[GoogleFlowEngine] Reference chips could not be removed.")
        editor = page.locator(ui.PROMPT_EDITOR).first
        for _ in range(3):
            await editor.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.4)
            left = await editor.evaluate(
                "e => ({text: (e.innerText || '').trim(), "
                "chips: e.querySelectorAll('[contenteditable=\"false\"], img').length})"
            )
            if not left["text"] and left["chips"] == 0:
                return
        raise RuntimeError(
            f"[GoogleFlowEngine] Prompt field not empty after clearing: {left}"
        )

    # =========================================================================
    # Teil A: Charaktere (gleiches Aussehen in allen Clips)
    # =========================================================================
    #
    # Ein Flow-Charakter ist ein gespeichertes Bündel aus 1–2 Referenzbildern.
    # Er wird im Prompt per ``@Name`` angesprochen. Ein Charakter aus hochgeladenen
    # Bildern kostet keine Credits. NIEMALS 'Generierung starten' auf der
    # Charakterseite klicken: das würde Referenzbilder generieren (kostet).

    @staticmethod
    def _project_base_url(page_url: str) -> str:
        """Schneidet ``…/project/<id>`` aus einer Flow-URL."""
        if "/project/" not in page_url:
            raise RuntimeError(f"[GoogleFlowEngine] Not inside a Flow project: {page_url}")
        head, tail = page_url.split("/project/", 1)
        return f"{head}/project/{tail.split('/', 1)[0].split('?', 1)[0]}"

    async def _open_character_page(self) -> Page:
        page = await self.connect()
        target_url = self._project_base_url(page.url) + ui.CHARACTER_PATH
        if not page.url.startswith(target_url):
            await page.goto(
                target_url,
                wait_until="domcontentloaded",
            )
            await asyncio.sleep(2.5)
        if not await self._visible(page.locator(ui.CHARACTER_PAGE).first, 2000):
            nav_btn = page.locator(ui.NAV_CHARACTERS).first
            if await self._visible(nav_btn, 2000):
                await nav_btn.click()
                await asyncio.sleep(2.0)
        return page

    async def list_characters(self) -> List[str]:
        """Namen der vorhandenen Charaktere des Projekts.

        UNVERIFIED: Das Prüfprojekt hatte noch keine Charaktere, die Kartenform
        stammt aus Annahmen. Ergebnis ist deshalb als Mindestliste zu lesen.
        """
        page = await self._open_character_page()
        names = await page.evaluate(
            """(sel) => Array.from(document.querySelectorAll(sel))
                .map(c => (c.innerText || '').trim().split('\\n')[0])
                .filter(Boolean)""",
            ui.CHARACTER_CARD,
        )
        return [n.strip() for n in names]

    async def create_character(
        self,
        name: str,
        image_paths: List[str],
        description: Optional[str] = None,
    ) -> bool:
        """Legt einen Charakter aus 1–2 hochgeladenen Bildern an (0 Credits).

        Idempotent: Existiert der Name schon, passiert nichts. Flow legt bei
        gleichem Namen sonst einen zweiten Charakter an.

        Returns:
            ``True`` wenn neu angelegt, ``False`` wenn er bereits existierte.

        Raises:
            ValueError: Keine oder mehr als 2 Bilder.
            FileNotFoundError: Ein Bild fehlt.
            RuntimeError: Anlegen nicht bestätigt (Charakter danach nicht gelistet).
        """
        if not 1 <= len(image_paths) <= 2:
            raise ValueError("A Flow character needs 1 or 2 reference images.")
        files = []
        for p in image_paths:
            f = Path(p)
            if not f.exists():
                raise FileNotFoundError(f"Character image not found: {p}")
            files.append(str(f.resolve()).replace("\\", "/"))

        existing = await self.list_characters()
        if name.strip().lower() in {c.lower() for c in existing}:
            logger.info(f"[GoogleFlowEngine] Character '{name}' already exists. Skipping.")
            return False

        page = await self._open_character_page()

        new_char_btn = page.locator(ui.CHARACTER_NEW_BUTTON).first
        if await self._visible(new_char_btn, 2500):
            await new_char_btn.click()
            await asyncio.sleep(1.5)

        upload_btn = page.locator(ui.CHARACTER_UPLOAD_BUTTON).first
        if await self._visible(upload_btn, 3000):
            async with page.expect_file_chooser(timeout=15000) as fc_info:
                await upload_btn.click()
            chooser = await fc_info.value
            await chooser.set_files(files)
        else:
            file_input = page.locator('input[type="file"]').first
            if await file_input.count() > 0:
                await file_input.set_input_files(files)
            else:
                raise RuntimeError("[GoogleFlowEngine] Character upload button / file input not found.")
        await asyncio.sleep(4.0)

        name_input = page.locator(ui.CHARACTER_NAME_INPUT).first
        if not await self._visible(name_input, 8000):
            raise RuntimeError("[GoogleFlowEngine] Character name field did not appear after upload.")
        await name_input.click()
        await name_input.fill(name)

        if description:
            desc = page.locator(ui.CHARACTER_DESCRIPTION).first
            if await self._visible(desc, 2000):
                await desc.click()
                await page.keyboard.type(description)

        done = page.locator(ui.CHARACTER_DONE_BUTTON).first
        if not await self._visible(done, 5000):
            raise RuntimeError("[GoogleFlowEngine] Character 'Done' button not found.")
        await done.click()
        await asyncio.sleep(3.0)

        try:
            await page.goto(self._project_base_url(page.url), wait_until="domcontentloaded")
            await asyncio.sleep(2.0)
            await self.exit_editor_if_open()
        except Exception as e:
            logger.warning(f"[GoogleFlowEngine] Could not return to canvas after character creation: {e}")

        logger.info(f"[GoogleFlowEngine] Character '{name}' created successfully.")
        return True

    async def insert_character_mention(self, name: str) -> None:
        """Fügt ``@Name`` an den Anfang des Prompts ein und wählt den Treffer.

        Nur getippter Text würde keine Referenz anhängen, die Identität ginge
        verloren. Darum wird der Vorschlagseintrag wirklich ausgewählt.

        UNVERIFIED: Selektor der Vorschlagsliste (Projekt hatte keinen Charakter).

        Raises:
            RuntimeError: Kein passender Vorschlag erschien (Name unbekannt).
        """
        page = await self.connect()
        await page.locator(ui.PROMPT_EDITOR).first.click()
        await page.keyboard.press("Control+Home")
        await page.keyboard.type(f"@{name}", delay=40)
        option = page.locator(ui.CHARACTER_MENTION_OPTION).filter(has_text=name).first
        if not await self._visible(option, 4000):
            option = page.locator(ui.CHARACTER_MENTION_OPTION).first
            if not await self._visible(option, 2000):
                await page.keyboard.press("Escape")
                raise RuntimeError(
                    f"[GoogleFlowEngine] No character suggestion for '@{name}' — "
                    "does the character exist in this project?"
                )
        await option.click()
        await asyncio.sleep(0.6)
        await page.keyboard.type(" ")

    # =========================================================================
    # Teil B: Szenen-Montage in Flow (statt ffmpeg-Zusammenschnitt)
    # =========================================================================
    #
    # Eine Flow-Szene ist eine geordnete Folge fertiger Clips (umsortieren,
    # trimmen, herunterladen). Es gibt dafür keine eigene Seite: ``/scenes``
    # liefert 404, „Szenen“ filtert nur die Medienansicht. Der Zusammenschnitt
    # kostet nichts, enthält aber nicht unseren Song — den legt weiter ffmpeg darüber.

    async def open_scenes_view(self) -> bool:
        """Öffnet die Szenen-Ansicht über die Seitenleiste/Navigation."""
        page = await self.connect()
        try:
            nav = page.locator(ui.NAV_SCENES).first
            if await self._visible(nav, 4000):
                await nav.click()
                await asyncio.sleep(1.5)
                return True
        except Exception as e:
            logger.warning(f"[GoogleFlowEngine] Could not open scenes view: {e}")
        return False

    async def add_latest_clip_to_scene(self) -> bool:
        """Kachelmenü des neuesten Clips → „Zu Szene hinzufügen“.

        UNVERIFIED: Das Prüfprojekt hatte keine Clips, der Menüeintrag stammt
        aus Googles Hilfe. Fehler sind darum nur eine Warnung, nie fatal.
        """
        page = await self.connect()
        tile = page.locator(ui.VIDEO_TILE_CONTAINER).first
        try:
            await tile.hover()
            await tile.locator(ui.TILE_MORE_BUTTON).first.click(timeout=5000)
            await asyncio.sleep(0.8)
            for label in ui.ADD_TO_SCENE_ITEM:
                item = page.locator('[role="menuitem"], button').filter(has_text=label).first
                if await self._visible(item, 1200):
                    await item.click()
                    await asyncio.sleep(1.5)
                    logger.info("[GoogleFlowEngine] Clip added to scene.")
                    return True
            await page.keyboard.press("Escape")
        except Exception as e:
            logger.warning(f"[GoogleFlowEngine] Could not add clip to scene: {e}")
        return False

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
                    progress: match ? match[1] : null,
                    editor: !!document.querySelector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
                };
            })()"""
            status = await page.evaluate(status_script)
            current_tiles = status.get("tiles", 0)
            progress = status.get("progress")

            # Flow öffnet den Clip-Editor nach dem Rendern von selbst: Download-Schaltfläche = fertig
            # VERIFIED live: Platzhalter-Kachel und Editor erscheinen schon beim
            # Rendern (z. B. 42 %); fertig ist erst, wenn kein Prozentwert mehr steht.
            if (current_tiles > initial_tiles_count or status.get("editor")) and elapsed > 20 and progress is None:
                logger.info(f"[GoogleFlowEngine] [+{elapsed}s] New video tile ready! (tiles: {current_tiles})")
                await asyncio.sleep(2.5)
                return True
            elif progress:
                logger.info(f"[GoogleFlowEngine] [+{elapsed}s] Progress: {progress}%")
            else:
                logger.info(f"[GoogleFlowEngine] [+{elapsed}s] Rendering in progress...")

        logger.warning(f"[GoogleFlowEngine] Timed out waiting for video completion after {timeout_seconds}s.")
        return False

    async def _editor_download_button_visible(self) -> bool:
        page = await self.connect()
        return await self._visible(page.locator(ui.DOWNLOAD_MEDIA_BUTTON).first, 1500)

    async def download_latest_video(
        self,
        target_clip_path: str,
        resolution: str = "720p",
        timeout_seconds: int = 45,
    ) -> str:
        """Lädt den neuesten Clip herunter und speichert ihn direkt am Zielort.

        Ist der Clip-Editor schon offen (Flow öffnet ihn nach dem Rendern von
        selbst), wird die Kachel nicht erneut angeklickt. Der Download wird über
        Playwright (``expect_download``) abgefangen; nur wenn das nicht greift,
        wird der Downloads-Ordner nach einer neuen MP4 durchsucht.
        """
        page = await self.connect()
        target_path = Path(target_clip_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not await self._editor_download_button_visible():
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

        # Snapshot des Downloads-Ordners für den Rückfallweg (Befund 4): nur
        # Dateien NACH diesem Zeitpunkt gelten.
        initial_downloads = set(os.listdir(self.downloads_dir)) if os.path.exists(self.downloads_dir) else set()
        click_time = time.time()

        async def _open_menu_and_pick() -> None:
            if not await page.evaluate(
                """(() => {
                    const btn = document.querySelector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]');
                    if (btn) { btn.click(); return true; }
                    return false;
                })()"""
            ):
                raise RuntimeError("[GoogleFlowEngine] Download button not found in the video editor.")
            await asyncio.sleep(1.2)
            # Ohne Blindklick-Fallback: ein beliebiger erster Menüeintrag kann „Löschen“ sein.
            picked = await page.evaluate(
                """(res) => {
                    const items = Array.from(document.querySelectorAll('button, [role="menuitem"], flow-menu-item'));
                    const target = items.find(el => (el.innerText || '').includes(res));
                    if (!target) return false;
                    const b = target.tagName === 'BUTTON' ? target : (target.querySelector('button') || target);
                    b.click();
                    return true;
                }""",
                resolution,
            )
            if not picked:
                raise RuntimeError(
                    f"[GoogleFlowEngine] Download menu item '{resolution}' not found — nothing clicked."
                )

        try:
            async with page.expect_download(timeout=timeout_seconds * 1000) as dl_info:
                await _open_menu_and_pick()
            download = await dl_info.value
            tmp_target = target_path.with_suffix(target_path.suffix + ".part")
            await download.save_as(str(tmp_target))
            if tmp_target.stat().st_size < 300000:
                # VERIFIED live: Download vor Rendering-Ende liefert eine leere Datei.
                tmp_target.unlink()
                raise RuntimeError("[GoogleFlowEngine] Downloaded clip is empty/too small (render not finished?).")
            os.replace(tmp_target, target_path)
            logger.info(f"[GoogleFlowEngine] Saved video clip to: {target_path} ({target_path.stat().st_size} bytes)")
            return str(target_path)
        except RuntimeError:
            raise  # Schaltfläche/Menüeintrag fehlt: nichts angeklickt, Rückfallweg sinnlos
        except Exception as exc:
            logger.warning(f"[GoogleFlowEngine] expect_download failed ({exc}); watching downloads folder.")

        # ── Rückfallweg: Downloads-Ordner beobachten ──
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

        if target_path.exists():
            target_path.unlink()
        shutil.copy2(downloaded_file, str(target_path))
        try:
            os.unlink(downloaded_file)
        except Exception:
            pass

        logger.info(f"[GoogleFlowEngine] Saved video clip to: {target_path} ({target_path.stat().st_size} bytes)")
        await self.exit_editor_if_open()
        return str(target_path)

    async def read_credit_balance(self) -> Optional[int]:
        """Liest den Kontostand (Guthabenpunkte) über den Konto-Link; ``None`` wenn nicht lesbar.

        Reiner Lesevorgang: öffnet das Konto-Popup und schließt es wieder.
        """
        page = await self.connect()
        try:
            link = page.locator(ui.ACCOUNT_LINK).first
            if not await self._visible(link, 3000):
                return None
            await link.click(force=True)
            await asyncio.sleep(2.0)
            text = await page.evaluate("() => document.body.innerText")
            match = re.search(ui.CREDITS_REGEX, text or "")
            return int(re.sub(r"[.,]", "", match.group(1))) if match else None
        except Exception as exc:
            logger.warning(f"[GoogleFlowEngine] Could not read credit balance: {exc}")
            return None
        finally:
            try:
                await page.keyboard.press("Escape")
            except Exception:
                pass

    async def generate_image(
        self,
        prompt: str,
        references: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        timeout_seconds: int = 240,
        character: Optional[str] = None,
    ) -> str:
        """Erzeugt ein Bild (Nano Banana) und speichert das neue Ergebnis.

        Bilder zeigten bisher keine Kostenkarte. Erscheint doch eine, wird sie
        abgelehnt und ``FlowStoppedError`` geworfen: Bildanfragen genehmigt
        diese Methode nie.

        Returns:
            Pfad der gespeicherten Datei.
        """
        page = await self.connect()
        await self.exit_editor_if_open()
        await self.clear_prompt()
        await self.set_prompt(prompt)
        if character:
            await self.insert_character_mention(character)
        if references:
            await self.attach_references(list(references))

        # VERIFIED live: nach dem Verlassen des Clip-Editors lädt Flow die Bildkacheln
        # nach; ohne Pause galten alte Kacheln als „neu“ (falsches Bild gespeichert).
        await asyncio.sleep(4.0)
        before_srcs = set(await page.evaluate(ui.GENERATED_IMAGE_JS))
        cards_before = await self.count_cost_cards()
        if not await self.submit_prompt():
            raise RuntimeError("[GoogleFlowEngine] Prompt was not sent (submit button or cleared field not confirmed).")

        new_src = None
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            await asyncio.sleep(5.0)
            if await self.count_cost_cards() > cards_before:
                await self.reject_cost_card()
                raise FlowStoppedError(
                    "Bildgenerierung zeigt eine Kostenkarte — abgelehnt, nichts genehmigt.",
                    status="image_cost_card",
                )
            fresh = [s for s in await page.evaluate(ui.GENERATED_IMAGE_JS) if s not in before_srcs]
            if fresh:
                new_src = fresh[0]
                break
        if not new_src:
            raise TimeoutError(f"[GoogleFlowEngine] No new image within {timeout_seconds}s.")

        b64 = await page.evaluate(
            """async (u) => { const r = await fetch(u); const b = await r.blob();
                return await new Promise(res => { const f = new FileReader();
                    f.onload = () => res(f.result.split(',')[1]); f.readAsDataURL(b); }); }""",
            new_src,
        )
        import base64

        data = base64.b64decode(b64)
        suffix = ".png" if data[:4] == b"\x89PNG" else ".jpg"
        target = Path(output_path) if output_path else Path(self.downloads_dir) / f"flow_image_{int(time.time())}{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        logger.info(f"[GoogleFlowEngine] Saved image to {target} ({len(data)} bytes)")
        return str(target)

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
        character: Optional[str] = None,
        add_to_scene: bool = False,
        shot_store: Optional[Any] = None,
        shot_id: Optional[str] = None,
        policy: Optional[Any] = None,
        ledger: Optional[Any] = None,
        account: str = "default",
        prompt_as_is: bool = False,
        extra_references: Optional[List[str]] = None,
    ) -> bool:
        """Führt eine komplette Szene Ende-zu-Ende durch.

        Args:
            character: Name eines Flow-Charakters; wird per ``@Name`` im Prompt
                angesprochen, damit die Figur in allen Clips gleich aussieht.
            add_to_scene: Fertigen Clip zusätzlich der Flow-Szene hinzufügen
                (kostenloser Zusammenschnitt in Flow, Fehler nur Warnung).
            shot_store: Optional ``core.flow_shot_state.ShotStateStore``. Mit
                ``shot_id`` wird der Status mitgeschrieben und ein zweites
                Absenden desselben Shots verhindert (``ShotAlreadySubmittedError``).
            policy: Optional ``core.flow_budget.BudgetPolicy`` (Gesamtbudget, Reserve).
            ledger: Optional ``core.flow_budget.CreditLedger`` für das Credit-Journal.
            account: Konto-Name für Policy und Journal.

        Raises:
            FlowStoppedError: Bestätigung steht auf „Nie“, Kosten über dem Limit,
                Kostenkarte unlesbar oder Aktivitätswarnung — nichts genehmigt.
        """
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

        use_state = shot_store is not None and bool(shot_id)
        if use_state:
            # Vor allem anderen: ein schon angefragter Shot wird nie erneut gesendet.
            shot_store.guard_submit(shot_id)

        def _mark(status: ShotStatus, **fields: Any) -> None:
            if use_state:
                shot_store.advance(shot_id, status, **fields)

        full_prompt = prompt if prompt_as_is else f"Generate video with Veo: {prompt}. {style_suffix}".strip()

        # Teil C: VOR dem Absenden prüfen. Bei „Nie“ zahlt Flow schon beim Absenden,
        # der Kostenschutz käme zu spät. Bewusst außerhalb des try-Blocks: der
        # FlowStoppedError muss den Stapel anhalten und darf nicht abgefangen werden.
        await self.ensure_cost_guard_active()

        # ── Phase 1: Vorbereitung (kostenlos, daher wiederholbar) ──
        prepared = False
        initial_tiles = 0
        cards_before = 0
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[GoogleFlowEngine] Preparing generation, attempt {attempt} for {target.name}...")
                await self.exit_editor_if_open()
                await self.clear_prompt()
                if reference_image_path and os.path.exists(reference_image_path):
                    await self.attach_reference_image(reference_image_path)
                # Regel 7 (ПРАВИЛА_КЛИПА.md): Charakterkarte/Props-Karte hinter dem Startkader.
                for extra in extra_references or []:
                    await self.attach_reference_image(extra)
                await self.set_prompt(full_prompt)
                if character:
                    await self.insert_character_mention(character)
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
        if use_state:
            shot_store.update(
                shot_id,
                prompt_hash=prompt_hash(full_prompt),
                frames=[reference_image_path] if reference_image_path else [],
                clip=str(target),
            )
        try:
            await self.submit_prompt()
        except Exception as e:
            logger.error(f"[GoogleFlowEngine] Submit for {target.name} failed: {e}")
            self._write_pending_marker(pending_marker, target, "submit_failed", str(e))
            return False
        _mark(ShotStatus.REQUESTED)

        # FlowStoppedError (Limit/unlesbar/Aktivitätswarnung) reicht nach oben
        # durch: dann wurde nichts genehmigt und der Stapel soll anhalten.
        confirm_kwargs: Dict[str, Any] = {}
        if policy is not None or ledger is not None:
            confirm_kwargs = {"policy": policy, "ledger": ledger, "shot_id": shot_id, "account": account}
        cost = await self.confirm_within_budget(cards_before, **confirm_kwargs)
        _mark(ShotStatus.APPROVED, credits=cost)

        try:
            completed = await self.wait_for_video_completion(initial_tiles)
            if not completed:
                raise TimeoutError("Render timed out or tile count did not increment.")
        except Exception as e:
            logger.error(f"[GoogleFlowEngine] Waiting for {target.name} failed: {e}")
            self._write_pending_marker(pending_marker, target, "render_timeout", str(e), cost)
            return False
        _mark(ShotStatus.RENDERED)

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
        _mark(ShotStatus.DOWNLOADED, clip=str(target))

        # ── QA-Kontaktbogen: Zusatznutzen, kein Grund zur Neugenerierung ──
        try:
            self.generate_qa_trio(str(target))
        except Exception as e:
            logger.warning(f"[GoogleFlowEngine] QA contact sheet for {target.name} failed (clip is fine): {e}")

        # ── Szenen-Montage in Flow: Zusatz, der den fertigen Clip nie gefährdet ──
        if add_to_scene:
            await self.add_latest_clip_to_scene()

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
