"""core.api.video_providers — Video-Provider-Abstraktion (v7.1 Phase 2 / v7.2 R8)

Motivation: Die fünf Pipelines instanziieren vorher direkt ``AgnesVideoAPI``;
ein Wechsel des Video-Modellanbieters (z. B. fal.ai) erforderte Codeänderungen
an jeder Stelle. Dieses Modul liefert den minimalen Provider-Vertrag + Fabrik
+ Modellprofile, sodass „Video-Anbieter wechseln" eine Konfigurationsoption ist.

Vertrag (identisch zur bestehenden öffentlichen Oberfläche von ``AgnesVideoAPI``,
Pipelines rufen ohne Änderungen auf):
    - ``submit_video(prompt, reference_image_paths, duration, width, height,
      seed, negative_prompt, progress_callback, **kwargs) -> video_id``
    - ``wait_for_video(video_id, progress_callback=None) -> VideoOutput``
    - ``resolve_image_ref(ref) -> str`` (lokale Uploads → öffentlich referenzierbare URL)
    - ``shutdown_event``-Attribut; ``capabilities``-Fähigkeitsbeschreibung
    - ``estimate_clip_cost_usd(duration, width, height) -> float`` (bezahlte Provider;
      Agnes-Preis = 0 → Pipelines behandeln das Attribut als optional, getattr)

Modellprofile (v7.2 R8): fal-Endpunkte unterscheiden sich je Familie — Dauer-Typ
(int 5-15 vs. String "5"/"10"), Seed-/Negative-Prompt-Unterstützung,
Auflösungsstufen, feste Modellparameter. ``_FAL_MODEL_PROFILES`` beschreibt pro
Endpunkt-Familie, wie ``submit_video`` die Argumente aufbaut; unbekannte Modelle
fallen auf ein konservatives generisches Profil zurück. Preise pro Sekunde sind
fal-Listenpreise (Stand Okt. 2026, ohne Gewähr) und treiben die Kosten-/Budget-
Abschätzung; 0.0 = unbekannt/free.

Kosten-/Budget-Gate (v7.2 R8): Bezahlte Provider akkumulieren die geplante
Clip-Kosten-Summe pro Provider-Instanz (``_spent_usd``). Ist
``AGNES_VIDEO_BUDGET_USD`` > 0, bricht ``submit_video`` mit klarer Meldung ab,
sobald die Grenze gerissen würde — harte Obergrenze gegen Retry-Explosionen.
Die großzügige Schätzung über alle Szenen erfolgt zusätzlich pipeline-seitig
(``MultiScenePipeline._announce_video_cost``) als Fail-fast vor der ersten
Ausgabe. Grenze: ``_spent_usd`` lebt nur im RAM eines Pipeline-Laufs (Neustart
setzt zurück); die pipeline-seitige Schätzung deckt den Restart-Fall ab.

Konfiguration:
    - ``AGNES_VIDEO_PROVIDER``: ``agnes`` (Standard) | ``fal``
    - ``FAL_VIDEO_MODEL``: fal endpoint id, Standard ``minimax/h3-max/image-to-video``
      (MiniMax H3 Max, fal-nachtrainiert: 5-15 s, 480P/768P, Seed, End-Frame);
      Text-to-Video-Endpunkt wird daraus abgeleitet (/image-to-video → /text-to-video)
    - ``AGNES_VIDEO_BUDGET_USD``: Kostenobergrenze in USD je Task-Durchlauf (0 = aus)
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from core.api.agnes_video import VideoOutput, VideoTaskCancelled
from core.config import get_settings, width_height_to_aspect_ratio

logger = logging.getLogger(__name__)

# fal.ai-Polling-Intervall (Sekunden): fal-Queue lebt serverseitig, lokales
# Festintervall genügt
_FAL_POLL_INTERVAL_SECONDS = 20.0

# ── Modellprofil-Registry (v7.2 R8) ─────────────────────────────────────
# Key = Endpoint-Präfix (längster/erst passender gewinnt). Felder:
#   durations                 diskrete Dauerstufen (Kling 5/10; Submit als String)
#   duration_range            stetige (min, max) — gesetzt → Submit als int
#                             (H3 Max 5-15); None → durations/String verwenden
#   resolution_tiers          Auflösungsstufen ("480P"/"768P"); leer = Parameter
#                             existiert nicht (Auswahl: nächste Stufe zu max(w,h))
#   price_usd_per_second      Preis pro Ausgabesekunde — bei Stufen-Modellen nach
#                             Auflösungsstufe geschlüsselt, sonst (Kling) nach
#                             Endpoint-Teilstring; leer = Preis unbekannt (0.0)
#   supports_*                Parameterunterstützung je Modellfamilie
#   default_params            feste Modellparameter (H3 Max: prompt_expansion_mode
#                             "disabled" — Screenwriter-Prompts bleiben exakt,
#                             keine ~30 s Expansions-Latenz; Kling: cfg_scale 0.5)
_FAL_MODEL_PROFILES: "list[tuple[str, dict]]" = [
    (
        "minimax/h3-max",
        {
            "durations": tuple(range(5, 16)),
            "duration_range": (5, 15),
            "resolution_tiers": ("480P", "768P"),
            "price_usd_per_second": {"480P": 0.05, "768P": 0.08},
            "max_reference_images": 1,
            "supports_negative_prompt": False,
            "supports_seed": True,
            "supports_aspect_ratio": False,      # Output-Seitenverhältnis folgt dem First Frame
            "supports_first_last_frame": True,   # end_image_url (First→Last Keyframe)
            "aspect_ratios": (),                 # leer = Parameter nicht vorhanden
            "default_params": {"prompt_expansion_mode": "disabled"},
            "notes": (
                "H3 Max (fal post-trained): 5-15s int duration, 480P/768P, Seed + "
                "end_image_url unterstützt; Ausgabeformat folgt dem First Frame"
            ),
        },
    ),
    (
        "fal-ai/kling-video",
        {
            "durations": (5, 10),
            "duration_range": None,
            "resolution_tiers": (),
            "price_usd_per_second": {"v3/pro": 0.14, "v2.5-turbo/pro": 0.07},
            "max_reference_images": 1,
            "supports_negative_prompt": True,
            "supports_seed": False,
            "supports_aspect_ratio": True,
            "supports_first_last_frame": False,
            "aspect_ratios": ("16:9", "9:16", "1:1"),  # Kling akzeptiert nur diese drei
            "default_params": {"cfg_scale": 0.5},
            "notes": (
                "Kling: cfg_scale 0.4-0.6 beste Bewegungskonsistenz; >0.7 bricht "
                "Frame-Geometrie; Dauer nur 5/10 (String)"
            ),
        },
    ),
]

# Konservatives generisches Profil für unbekannte Endpunkte (altes Kling-Verhalten)
_FAL_DEFAULT_PROFILE: dict = {
    "durations": (5, 10),
    "duration_range": None,
    "resolution_tiers": (),
    "price_usd_per_second": {},
    "max_reference_images": 1,
    "supports_negative_prompt": True,
    "supports_seed": False,
    "supports_aspect_ratio": True,
    "supports_first_last_frame": False,
    "aspect_ratios": (),       # leer = nicht einschränken (Breite/Höhe unverändert durchreichen)
    "default_params": {},
    "notes": "unbekanntes fal-Modell — konservatives generisches Profil",
}


def _resolve_profile(model: str) -> dict:
    """Passendes Modellprofil für einen fal-Endpoint-Id liefern (Präfix-Match)."""
    for prefix, profile in _FAL_MODEL_PROFILES:
        if model.startswith(prefix):
            return profile
    return _FAL_DEFAULT_PROFILE


def _snap_duration(duration: Optional[int], profile: dict):
    """Dauer auf die vom Modell unterstützten Stufen/Range snapen.

    duration_range gesetzt (H3 Max) → int, auf (min, max) geklemmt;
    sonst (Kling) → String, auf nächste diskrete Stufe gesnapt.
    """
    lo_hi = profile.get("duration_range")
    if lo_hi:
        lo, hi = lo_hi
        d = int(duration) if duration else lo
        return max(lo, min(hi, d))
    allowed = profile["durations"]
    if not duration:
        return str(allowed[0])
    d = int(duration)
    return str(min(allowed, key=lambda a: (abs(a - d), a)))


def _resolution_tier(width: int, height: int, tiers: tuple) -> str:
    """Nächstgelegene Auflösungsstufe zu max(width, height); "" wenn keine Stufen."""
    if not tiers:
        return ""
    target = max(int(width or 0), int(height or 0))
    return min(tiers, key=lambda t: abs(int(str(t).rstrip("Pp")) - target))


def _snap_aspect_ratio(width: int, height: int, profile: dict) -> str:
    """Seitenverhältnis auf die vom Modell unterstützten Formate snappen.

    Projekt-Pixel zuerst auf die Standard-Agnes-Ratio mappen; unterstützt das
    Profil nur eine Teilmenge (Kling: 16:9 / 9:16 / 1:1), auf die nächstgelegene
    unterstützte Ratio snappen — sonst lehnt der Endpoint den Submit ab.
    """
    ratio = width_height_to_aspect_ratio(width, height)
    supported = profile.get("aspect_ratios") or ()
    if supported and ratio not in supported:
        w, h = ratio.split(":")
        target = int(w) / int(h)

        def _dist(candidate: str) -> float:
            cw, ch = candidate.split(":")
            return abs(int(cw) / int(ch) - target)

        snapped = min(supported, key=_dist)
        logger.info(
            "[VideoProvider] aspect ratio %s not supported, snapping to %s", ratio, snapped,
        )
        ratio = snapped
    return ratio


@dataclass(frozen=True)
class VideoProviderCapabilities:
    """Video-Provider-Fähigkeitsbeschreibung (Validierung / Frontend / Kosten)."""

    provider: str
    label: str
    model: str
    max_reference_images: int          # maximale Anzahl Referenzbilder pro Submission
    supports_negative_prompt: bool
    supports_seed: bool
    durations: tuple = ()              # unterstützte Dauern (Sekunden; diskret oder Range)
    duration_range: Optional[tuple] = None   # stetige (min, max) statt diskreter Stufen
    aspect_ratios: tuple = ()          # unterstützte Formate ("16:9" etc.); leer = Parameter nicht vorhanden
    resolution_tiers: tuple = ()       # Auflösungsstufen ("480P" …); leer = Parameter nicht vorhanden
    supports_first_last_frame: bool = False  # end_image_url (First→Last-Keyframe)
    default_params: dict = field(default_factory=dict)   # feste Modellparameter
    price_usd_per_second: dict = field(default_factory=dict)  # Preis je Stufe/Endpoint (USD/s)
    notes: str = ""


class VideoProviderBase(ABC):
    """Video-Provider-Abstraktionsbasisklasse (Formalisierung des Duck-Type-Vertrags)."""

    provider_id: str = "base"
    model: str = ""
    shutdown_event: Optional[asyncio.Event] = None
    capabilities: VideoProviderCapabilities

    @abstractmethod
    async def submit_video(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        duration: Optional[int] = None,
        width: int = 1280,
        height: int = 720,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        progress_callback=None,
        **kwargs,
    ) -> str:
        """Video-Generierungsauftrag einreichen, Provider-seitige Task-ID zurückgeben."""
        ...

    @abstractmethod
    async def wait_for_video(
        self, video_id: str, progress_callback=None
    ) -> VideoOutput:
        """Auf Abschluss des Auftrags warten, speicherbares ``VideoOutput`` zurückgeben."""
        ...

    @abstractmethod
    async def resolve_image_ref(self, ref: str) -> str:
        """Lokalen Pfad in eine Provider-referenzierbare öffentliche URL auflösen; http/data unverändert."""
        ...

    def _is_shutdown(self) -> bool:
        return self.shutdown_event is not None and self.shutdown_event.is_set()


class FalVideoProvider(VideoProviderBase):
    """fal.ai-Provider (produktionierte Konvergenz von fal_clip_pipeline.py).

    Modellabhängiges Verhalten (Dauer-Typ, Seed, Auflösung, End-Frame, Preis)
    kommt aus ``_FAL_MODEL_PROFILES``; Standard ist MiniMax H3 Max I2V
    (schnell + günstig, 5-15 s, First/Last-Frame). Bekannte Einschränkungen
    (MVP): ``progress_callback`` No-op, Cancel nur über Shutdown-Event statt
    serverseitigem Widerruf, Restart-Resume für t2v eingeschränkt (Endpoint-Map
    nur im RAM, siehe PRD).
    """

    provider_id = "fal"

    def __init__(
        self,
        model: str = "minimax/h3-max/image-to-video",
        shutdown_event: Optional[asyncio.Event] = None,
    ):
        self.model = (model or "").strip()
        if not self.model:
            raise ValueError("[VideoProvider] FAL_VIDEO_MODEL is empty")
        self.shutdown_event = shutdown_event
        self._profile = _resolve_profile(self.model)
        # video_id(request_id) → Endpoint zur Einreichung (Warten/Ergebnis wird
        # per Endpoint adressiert; nach Dienstneustart ist das Dictionary weg,
        # Rückfall auf Haupt-Endpoint — t2v-Fortsetzung über Neustart eingeschränkt, siehe PRD)
        self._endpoints: dict = {}
        # v7.2 R8: geplante Kosten dieses Durchlaufs (USD) — harte Budgetgrenze
        self._spent_usd: float = 0.0
        self.capabilities = VideoProviderCapabilities(
            provider="fal",
            label=f"fal.ai · {self.model.rsplit('/', 2)[-2]}",
            model=self.model,
            max_reference_images=self._profile["max_reference_images"],
            supports_negative_prompt=self._profile["supports_negative_prompt"],
            supports_seed=self._profile["supports_seed"],
            durations=self._profile["durations"],
            duration_range=self._profile["duration_range"],
            aspect_ratios=("16:9", "9:16", "1:1") if self._profile["supports_aspect_ratio"] else (),
            resolution_tiers=self._profile["resolution_tiers"],
            supports_first_last_frame=self._profile["supports_first_last_frame"],
            default_params=dict(self._profile["default_params"]),
            price_usd_per_second=dict(self._profile["price_usd_per_second"]),
            notes=self._profile["notes"],
        )

    # ── Kostenabschätzung (v7.2 R8) ─────────────────────────────

    def _price_per_second(self, width: int = 0, height: int = 0) -> float:
        """Konkreter Preis je Ausgabesekunde in USD (0.0 = unbekannt/free)."""
        prices = self._profile["price_usd_per_second"]
        if not prices:
            return 0.0
        tier = _resolution_tier(width, height, self._profile["resolution_tiers"])
        if tier:
            return float(prices.get(tier, 0.0))
        # Stufenlose Modelle (Kling): Preis nach Endpoint-Teilstring
        for key, price in prices.items():
            if key in self.model:
                return float(price)
        return 0.0

    def estimate_clip_cost_usd(
        self, duration: Optional[int], width: int = 1280, height: int = 720
    ) -> float:
        """Geschätzte Kosten eines Clips in USD (0.0 bei unbekanntem/free Preis)."""
        price = self._price_per_second(width, height)
        if price <= 0:
            return 0.0
        d = int(_snap_duration(duration, self._profile))
        return round(price * d, 4)

    @property
    def spent_usd(self) -> float:
        """Summe der bereits eingeplanten Clip-Kosten dieses Durchlaufs (USD)."""
        return self._spent_usd

    # ── Interne Hilfsfunktionen ───────────────────────────────────────────────

    def _client(self):
        """fal_client lazy importieren (optionale Abhängigkeit), bei Fehlen umsetzbaren Hinweis geben."""
        try:
            import fal_client
        except ImportError as e:
            raise RuntimeError(
                "[VideoProvider] provider=fal benötigt fal-client: pip install fal-client"
            ) from e
        if not os.environ.get("FAL_KEY"):
            raise RuntimeError(
                "[VideoProvider] Umgebungsvariable FAL_KEY fehlt (fal.ai-Zugriffsschlüssel)"
            )
        return fal_client

    @staticmethod
    def _text_endpoint(i2v_endpoint: str) -> str:
        """T2V-Endpoint aus dem I2V-Endpoint ableiten (Pfadersetzung derselben Familie)."""
        return i2v_endpoint.replace("/image-to-video", "/text-to-video")

    @staticmethod
    def _is_completed(status_obj) -> bool:
        """„Abgeschlossen" über fal_client-Versionen hinweg entscheiden (Klassenname / Status-Enum, doppeltes Signal)."""
        if type(status_obj).__name__ == "Completed":
            return True
        return str(getattr(status_obj, "status", "")).upper().endswith("COMPLETED")

    # ── Vertragsimplementierung ──────────────────────────────────────────────

    async def resolve_image_ref(self, ref: str) -> str:
        if not ref:
            return ref
        if ref.startswith(("http://", "https://", "data:")):
            return ref
        if os.path.exists(ref):
            fal_client = self._client()
            return await asyncio.to_thread(fal_client.upload_file, ref)
        return ref

    async def submit_video(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        duration: Optional[int] = None,
        width: int = 1280,
        height: int = 720,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        progress_callback=None,
        **kwargs,
    ) -> str:
        fal_client = self._client()
        profile = self._profile
        refs = list(reference_image_paths or [])
        if len(refs) > self.capabilities.max_reference_images:
            logger.warning(
                "[VideoProvider] fal: %d reference images given, "
                "using the first only (model takes %d)",
                len(refs), self.capabilities.max_reference_images,
            )
            refs = refs[:1]

        duration_value = _snap_duration(duration, profile)

        # Kosten-/Budget-Gate (v7.2 R8): bei bezahlten Modellen vor dem Submit
        # gegen AGNES_VIDEO_BUDGET_USD prüfen — Überschreitung = klarer Abbruch,
        # nicht still teuer weiterretryen
        cost = self.estimate_clip_cost_usd(duration, width, height)
        if cost > 0:
            budget = float(get_settings().agnes_video_budget_usd or 0.0)
            if budget > 0 and self._spent_usd + cost > budget:
                raise RuntimeError(
                    f"[VideoProvider] cost budget exceeded: ${self._spent_usd:.2f} "
                    f"planned so far + ${cost:.2f} for this clip > budget "
                    f"${budget:.2f} (AGNES_VIDEO_BUDGET_USD) — aborted before spend"
                )
            self._spent_usd += cost

        tier = _resolution_tier(width, height, profile["resolution_tiers"])
        if refs:
            endpoint = self.model
            arguments = {
                "prompt": prompt,
                "image_url": await self.resolve_image_ref(refs[0]),
                "duration": duration_value,
            }
            end_image = str(kwargs.get("end_image_path") or "")
            if end_image and self.capabilities.supports_first_last_frame:
                arguments["end_image_url"] = await self.resolve_image_ref(end_image)
            mode_desc = "i2v"
        else:
            endpoint = self._text_endpoint(self.model)
            arguments = {
                "prompt": prompt,
                "duration": duration_value,
            }
            mode_desc = "t2v"
        if profile["supports_aspect_ratio"]:
            arguments["aspect_ratio"] = _snap_aspect_ratio(width, height, profile)
        if tier:
            arguments["resolution"] = tier
        for k, v in profile["default_params"].items():
            arguments.setdefault(k, v)
        if profile["supports_negative_prompt"] and negative_prompt:
            arguments["negative_prompt"] = negative_prompt
        if profile["supports_seed"] and seed is not None:
            arguments["seed"] = int(seed)
        elif seed is not None:
            logger.debug("[VideoProvider] fal: seed not supported, ignored")
        cfg_scale = kwargs.get("cfg_scale", profile["default_params"].get("cfg_scale"))
        if cfg_scale is not None:
            arguments["cfg_scale"] = float(cfg_scale)

        logger.info(
            "[VideoProvider] fal %s (%s, %s s, ~$%.4f): %s...",
            mode_desc, self.model, duration_value, cost, prompt[:80],
        )
        handler = await asyncio.to_thread(fal_client.submit, endpoint, arguments)
        video_id = str(getattr(handler, "request_id", "") or "")
        if not video_id:
            raise RuntimeError(
                f"[VideoProvider] fal submit returned no request_id: {handler!r}"
            )
        self._endpoints[video_id] = endpoint
        return video_id

    async def wait_for_video(
        self, video_id: str, progress_callback=None, endpoint: str = ""
    ) -> VideoOutput:
        """Auf Abschluss warten; ``endpoint`` für Restart-Resume nachreichbar.

        - ``endpoint`` (optional): nach einem Dienstneustart ist die RAM-Endpoint-
          Map weg; ohne Nachreichen gilt der I2V-Haupt-Endpoint — bei einem T2V-
          Job schaltet dieser Code **einmalig** automatisch auf den Schwester-
          Endpoint um (Selbstheilung, ``_sibling_endpoint``) und merkt ihn an.
        - ``progress_callback(status, waited_seconds)``: wird bei jedem Polling
          mit dem fal-Queue-Status gerufen (v7.2 R8 Batch 3 — zuvor No-op).
        """
        fal_client = self._client()
        endpoint = endpoint or self._endpoints.get(video_id, self.model)
        waited = 0.0
        timeout = get_settings().agnes_video_poll_timeout
        switched = False
        while True:
            if self._is_shutdown():
                raise VideoTaskCancelled(
                    f"fal request {video_id[:16]} cancelled by shutdown"
                )
            if waited >= timeout:
                raise RuntimeError(
                    f"[VideoProvider] fal request {video_id[:16]} "
                    f"not finished after {timeout}s"
                )
            try:
                status_obj = await asyncio.to_thread(
                    fal_client.status, endpoint, video_id
                )
            except Exception as e:
                # Restart-Resume: Endpoint-Map verloren → I2V-Default trifft auf
                # einen T2V-Job. Einmalig auf den Schwester-Endpoint ausweichen;
                # scheitert auch der, ist der ursprüngliche Fehler irrelevant
                # (der zweite Aufruf wirft durch).
                sibling = self._sibling_endpoint(endpoint)
                if not switched and sibling:
                    logger.warning(
                        "[VideoProvider] fal status on %s failed (%s) — "
                        "trying sibling endpoint %s (restart-resume self-heal)",
                        endpoint, e, sibling,
                    )
                    endpoint = sibling
                    switched = True
                    self._endpoints[video_id] = endpoint
                    continue
                raise
            if progress_callback:
                try:
                    progress_callback(
                        str(getattr(status_obj, "status", "") or "unknown"), waited
                    )
                except Exception as e:
                    logger.debug("[VideoProvider] fal progress callback error: %s", e)
            if self._is_completed(status_obj):
                payload = await asyncio.to_thread(
                    fal_client.result, endpoint, video_id
                )
                video_url = (payload or {}).get("video", {}).get("url") \
                    or (payload or {}).get("video_url")
                if not video_url:
                    raise RuntimeError(
                        f"[VideoProvider] fal result has no video url: {payload!r}"
                    )
                return VideoOutput(fmt="url", ext="mp4", data=video_url)
            await asyncio.sleep(_FAL_POLL_INTERVAL_SECONDS)
            waited += _FAL_POLL_INTERVAL_SECONDS

    @staticmethod
    def _sibling_endpoint(endpoint: str) -> str:
        """Schwester-Endpoint derselben Modellfamilie (i2v ↔ t2v); "" falls unbekannt."""
        if "/image-to-video" in endpoint:
            return endpoint.replace("/image-to-video", "/text-to-video")
        if "/text-to-video" in endpoint:
            return endpoint.replace("/text-to-video", "/image-to-video")
        return ""


# ═══════════════════════════════════════════════════════════════
# Fabrik
# ═══════════════════════════════════════════════════════════════


def create_video_provider(
    api_key: str = "",
    default_model: str = "agnes-video-v2.0",
    shutdown_event: Optional[asyncio.Event] = None,
):
    """Video-Provider gemäß Laufzeitkonfiguration bauen.

    Routing-Reihenfolge (v7.3 „Modell wählen = Provider wechseln"):
    1. **Modell-ID-Präfix**: UI-seitig gewähltes fremdes Modell (``fal-ai/*`` /
       ``minimax/*``) → ``FalVideoProvider`` mit genau diesem Modell — je Task,
       ohne Neustart und ohne Umgebungsvariable.
    2. ``AGNES_VIDEO_PROVIDER=fal`` (Legacy-Umschalter): ``FalVideoProvider``
       mit ``FAL_VIDEO_MODEL`` (unverändertes Verhalten für Bestands-Setups).
    3. ``agnes`` (Standard): ``AgnesVideoAPI`` zum Aufrufzeitpunkt importieren
       (Mock-Regression-Patch-Punkt).
    """
    model = (default_model or "").strip()
    if model.startswith(("fal-ai/", "minimax/")):
        return FalVideoProvider(model=model, shutdown_event=shutdown_event)

    provider = (get_settings().agnes_video_provider or "agnes").strip().lower()
    if provider == "fal":
        return FalVideoProvider(
            model=get_settings().fal_video_model,
            shutdown_event=shutdown_event,
        )
    if provider != "agnes":
        raise ValueError(
            f"[VideoProvider] AGNES_VIDEO_PROVIDER={provider!r} nicht unterstützt"
            " (Optionen: agnes / fal)"
        )
    # Import zum Aufrufzeitpunkt: monkeypatch("core.api.agnes_video.AgnesVideoAPI") wirkt auf diese Fabrik
    from core.api.agnes_video import AgnesVideoAPI

    api = AgnesVideoAPI(api_key=api_key, model=model or default_model)
    if shutdown_event is not None:
        api.shutdown_event = shutdown_event
    return api


# Kuratierte fal-Modelle für die Provider-/Modellauswahl im Frontend
# (Preise = fal-Listenpreise, Stand Okt. 2026, ohne Gewähr)
_FAL_MODEL_CATALOG = [
    {
        "model": "minimax/h3-max/image-to-video",
        "label": "MiniMax H3 Max (5–15s · 768p · schnell)",
        "price_usd_per_second": 0.08,
    },
    {
        "model": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
        "label": "Kling v2.5 Turbo Pro (10s · 1080p)",
        "price_usd_per_second": 0.07,
    },
    {
        "model": "fal-ai/kling-video/v3/pro/image-to-video",
        "label": "Kling v3 Pro (10s · 1080p · Audio)",
        "price_usd_per_second": 0.14,
    },
]


def get_video_provider_catalog() -> dict:
    """Provider-/fal-Modell-Metadaten für ``GET /api/models`` (v7.2 R8 Batch 3).

    Hebt die PRD-Limitierung Nr. 5 (Modell-Dropdown agnes-only): Das Frontend
    erhält den Server-Default plus eine kuratierte fal-Modelliste mit
    Preisindikation — ohne eigene Preis-/Modellpflege im UI.
    """
    return {
        "default": (get_settings().agnes_video_provider or "agnes").strip().lower(),
        "choices": ["agnes", "fal"],
        "fal_models": _FAL_MODEL_CATALOG,
    }
