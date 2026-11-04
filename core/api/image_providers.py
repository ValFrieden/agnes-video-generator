"""core.api.image_providers — Bild-Provider-Abstraktion (Spiegelstück zu video_providers)

Motivation: Die Pipelines instanziieren bisher direkt ``AgnesImageAPI``; ein
Wechsel des Bild-Anbieters (z. B. Pollinations gratis, fal.ai bezahlt) war ohne
Codeänderung unmöglich. Dieses Modul liefert den minimalen Provider-Vertrag +
Fabrik + kuratierte Modellprofile — im gleichen Stil wie ``video_providers.py``.

Vertrag (identisch zur öffentlichen Oberfläche von ``AgnesImageAPI``, Pipelines
rufen ohne Änderungen auf):
    - ``generate_single_image(prompt, reference_image_paths=[], size=None,
      max_retries=..., retry_base_delay=..., **kwargs) -> ImageOutput``
    - ``capabilities``-Fähigkeitsbeschreibung (optional, getattr)
    - ``estimate_image_cost_usd() -> float`` (bezahlte Provider; 0.0 = free)

Provider-Routing nach Modell-ID-Präfix (→ „Modell in der UI wählen = Provider-
Wechsel", je Task, ohne Neustart und ohne Umgebungsvariable):
    - ``pollinations/*`` → PollinationsImageProvider (kostenlos, kein Key nötig;
      optional ``POLLINATIONS_API_KEY`` für höheres Limit / ohne Wasserzeichen)
    - ``fal-ai/*``       → FalImageProvider (bezahlt, ``FAL_KEY`` + fal_client)
    - alles andere       → AgnesImageAPI (Gratis-Default, monkeypatch-Punkt)

Referenzbilder (i2i): nur Agnes und ``fal-ai/nano-banana/edit`` unterstützen
sie. T2I-only-Provider ignorieren Referenzbilder mit Warnung statt zu brechen —
mehrere Pipelines reichen Keys optional mit; ein harter Fehler würde ganze
Tasks killen (Fail-soft, dokumentiert in den capabilities).

Kosten-/Budget-Gate: Bezahlt-Provider akkumulieren geplante Bild-Kosten pro
Provider-Instanz (ein Pipeline-Lauf); ``AGNES_IMAGE_BUDGET_USD`` > 0 bricht
vor dem Submit mit klarer Meldung ab. Grenze wie beim Video: nur im RAM des
Laufs; Instanz lebt in der Pipeline (Routes: pro Request).
"""

import asyncio
import base64
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import quote

import requests

from core.api.agnes_image import ImageOutput
from core.config import get_settings

logger = logging.getLogger(__name__)

_POLLINATIONS_ENDPOINT = "https://image.pollinations.ai/prompt"

# Anonymes Pollinations-Throttle: ~1 Request / 15 s (Provider-Seite); ohne
# lokales Einhalten drohen 429-Serien. Klassenweit (pro Prozess/IP), nicht je Instanz.
_POLLINATIONS_MIN_INTERVAL_SECONDS = 15.0
_POLLINATIONS_LOCK = asyncio.Lock()
_POLLINATIONS_LAST_REQUEST_TS = 0.0

_POLLINATIONS_MAX_ATTEMPTS = 3
_POLLINATIONS_RETRY_BASE_DELAY = 15.0

# Pixel-Grenzen für den Query-String (Pollinations rendert bis ~2048 px sinnvoll)
_POLLINATIONS_MIN_PIXELS = 256
_POLLINATIONS_MAX_PIXELS = 2048

# fal-Bild-Polling/Subscribe läuft serverseitig-blocking in fal_client.subscribe
_FAL_IMAGE_SUBSCRIBE_TIMEOUT_SECONDS = 300


# ── Modellprofil-Registry (fal) ─────────────────────────────────────────
# Key = Endpoint-Präfix. Felder:
#   price_usd_per_image   fal-Listenpreis pro Bild (Stand Okt. 2026, ohne Gewähr);
#                         0.0 = unbekannt → kein Budget-Gate
#   max_reference_images  0 = t2i-only (Referenzbilder werden ignoriert)
#   default_params        feste Modellparameter (Ausgabeformat etc.)
_FAL_IMAGE_MODEL_PROFILES: "list[tuple[str, dict]]" = [
    (
        "fal-ai/flux/dev",
        {
            "price_usd_per_image": 0.025,
            "max_reference_images": 0,
            "default_params": {"num_images": 1, "output_format": "png"},
            "notes": "FLUX.1 dev: hohe Detailtreue, t2i-only",
        },
    ),
    (
        "fal-ai/nano-banana/edit",
        {
            "price_usd_per_image": 0.039,
            "max_reference_images": 4,
            "default_params": {"num_images": 1, "output_format": "png"},
            "notes": "Nano Banana Edit: i2i mit bis zu 4 Referenzbildern (image_urls)",
        },
    ),
]

_FAL_IMAGE_DEFAULT_PROFILE: dict = {
    "price_usd_per_image": 0.0,
    "max_reference_images": 0,
    "default_params": {},
    "notes": "unbekanntes fal-Bildmodell — konservatives generisches Profil (t2i-only)",
}


def _resolve_image_profile(model: str) -> dict:
    """Passendes Bildmodellprofil für einen fal-Endpoint-Id liefern (Präfix-Match)."""
    for prefix, profile in _FAL_IMAGE_MODEL_PROFILES:
        if model.startswith(prefix):
            return profile
    return _FAL_IMAGE_DEFAULT_PROFILE


@dataclass(frozen=True)
class ImageProviderCapabilities:
    """Bild-Provider-Fähigkeitsbeschreibung (Validierung / Kosten)."""

    provider: str
    label: str
    model: str
    max_reference_images: int          # 0 = t2i-only (Referenzbilder ignoriert)
    supports_negative_prompt: bool = False
    price_usd_per_image: float = 0.0   # 0.0 = unbekannt/free → kein Budget-Gate
    default_params: dict = field(default_factory=dict)
    notes: str = ""


class ImageProviderBase(ABC):
    """Bild-Provider-Abstraktionsbasisklasse (Formalisierung des Duck-Type-Vertrags)."""

    provider_id: str = "base"
    model: str = ""
    capabilities: ImageProviderCapabilities

    @abstractmethod
    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        size: Optional[str] = None,
        max_retries: int = 4,
        retry_base_delay: float = 20.0,
        **kwargs,
    ) -> ImageOutput:
        """Ein Bild generieren und als speicherbares ``ImageOutput`` zurückgeben."""
        ...


def _parse_size(size: Optional[str]) -> "tuple[int, int]":
    """``"768x1152"`` → (768, 1152); Fallback 1024x1024 (Agnes-Vertrag)."""
    try:
        parts = (size or "").lower().split("x")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except (ValueError, TypeError):
        pass
    return 1024, 1024


class PollinationsImageProvider(ImageProviderBase):
    """Pollinations.ai-Provider (kostenlos, kein Key nötig).

    Legacy-Endpoint ``GET image.pollinations.ai/prompt/{prompt}`` liefert die
    Bilddaten direkt im Response-Body (kein Job/Polling). Anonym ~1 Request/15 s
    mit Wasserzeichen; ``POLLINATIONS_API_KEY`` (enter.pollinations.ai, gratis)
    hebt das Limit und entfernt das Wasserzeichen. Nur t2i — Referenzbilder
    werden mit Warnung ignoriert.
    """

    provider_id = "pollinations"

    def __init__(self, model: str = "pollinations/flux"):
        self.model = (model or "").strip() or "pollinations/flux"
        # URL-Parameter „model" ist der Teil nach dem Präfix (flux/zimage/klein)
        self._model_param = self.model.split("/", 1)[1] if "/" in self.model else self.model
        self.capabilities = ImageProviderCapabilities(
            provider="pollinations",
            label=f"Pollinations · {self._model_param}",
            model=self.model,
            max_reference_images=0,
            supports_negative_prompt=False,
            price_usd_per_image=0.0,
            default_params={"nologo": "true"},
            notes="kostenlos, anonym ~1 req/15s; POLLINATIONS_API_KEY 提额/去水印; t2i-only",
        )

    @staticmethod
    def _api_key() -> str:
        """Optional registrierter Key (höheres Limit, ohne Wasserzeichen)."""
        return (os.environ.get("POLLINATIONS_API_KEY") or "").strip()

    async def _throttle(self) -> None:
        """Anonymes 15-s-Fenster lokal einhalten (seriell über Klassen-Lock)."""
        global _POLLINATIONS_LAST_REQUEST_TS
        async with _POLLINATIONS_LOCK:
            wait = _POLLINATIONS_MIN_INTERVAL_SECONDS - (time.monotonic() - _POLLINATIONS_LAST_REQUEST_TS)
            if wait > 0:
                logger.debug(
                    "[ImageProvider] pollinations throttle: waiting %.1fs (anonymous tier)",
                    wait,
                )
                await asyncio.sleep(wait)
            _POLLINATIONS_LAST_REQUEST_TS = time.monotonic()

    @staticmethod
    def _clamp_pixels(value: int) -> int:
        return max(_POLLINATIONS_MIN_PIXELS, min(_POLLINATIONS_MAX_PIXELS, int(value)))

    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        size: Optional[str] = None,
        max_retries: int = _POLLINATIONS_MAX_ATTEMPTS,
        retry_base_delay: float = _POLLINATIONS_RETRY_BASE_DELAY,
        **kwargs,
    ) -> ImageOutput:
        refs = list(reference_image_paths or [])
        if refs:
            logger.warning(
                "[ImageProvider] pollinations: %d reference image(s) ignored "
                "(t2i-only model %s; pick Agnes or fal-ai/nano-banana/edit for i2i)",
                len(refs), self.model,
            )

        width, height = (self._clamp_pixels(v) for v in _parse_size(size))
        params: dict = {
            "width": width,
            "height": height,
            "model": self._model_param,
            "nologo": "true",
        }
        seed = kwargs.get("seed")
        if seed is not None:
            params["seed"] = int(seed)

        headers: dict = {}
        api_key = self._api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"{_POLLINATIONS_ENDPOINT}/{quote(prompt, safe='')}"
        # S5145-konform: Prompt-Inhalt nicht loggen, nur Länge/Modus
        logger.info(
            "[ImageProvider] pollinations %s %dx%d: prompt %d chars%s",
            self._model_param, width, height, len(prompt),
            " (keyed)" if api_key else " (anonymous)",
        )

        resp = None
        for attempt in range(max_retries):
            await self._throttle()
            try:
                resp = await asyncio.to_thread(
                    requests.get, url,
                    params=params, headers=headers, timeout=(30, 240),
                )
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt < max_retries - 1:
                    delay = retry_base_delay * (attempt + 1)
                    logger.warning(
                        "[ImageProvider] pollinations %s, retry %d/%d in %.0fs...",
                        type(e).__name__, attempt + 1, max_retries, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                delay = retry_base_delay * (attempt + 1)
                logger.warning(
                    "[ImageProvider] pollinations HTTP %d, retry %d/%d in %.0fs...",
                    resp.status_code, attempt + 1, max_retries, delay,
                )
                await asyncio.sleep(delay)
                continue
            resp.raise_for_status()
            break
        else:
            raise RuntimeError(
                f"[ImageProvider] pollinations max retries ({max_retries}) exceeded"
            )

        if not resp.content:
            raise RuntimeError(
                f"[ImageProvider] pollinations returned empty body "
                f"(HTTP {resp.status_code})"
            )
        b64 = base64.b64encode(resp.content).decode("utf-8")
        ext = "png" if "png" in (resp.headers.get("Content-Type") or "") else "jpg"
        logger.info("[ImageProvider] pollinations done: %d bytes", len(resp.content))
        return ImageOutput(fmt="b64", ext=ext, data=b64)


class FalImageProvider(ImageProviderBase):
    """fal.ai-Bild-Provider (bezahlt; ``FAL_KEY`` + fal_client).

    ``fal_client.subscribe`` blockiert bis zum Ergebnis (fal-Queue lebt
    serverseitig). Bezahlte Modelle akkumulieren geplante Kosten pro Instanz
    und prüfen vor dem Submit gegen ``AGNES_IMAGE_BUDGET_USD``.
    """

    provider_id = "fal"

    def __init__(self, model: str = "fal-ai/flux/dev"):
        self.model = (model or "").strip()
        if not self.model:
            raise ValueError("[ImageProvider] fal image model is empty")
        self._profile = _resolve_image_profile(self.model)
        # geplante Kosten dieses Laufs (USD) — harte Budgetgrenze vor dem Submit
        self._spent_usd: float = 0.0
        self.capabilities = ImageProviderCapabilities(
            provider="fal",
            label=f"fal.ai · {self.model.rsplit('/', 1)[-1]}",
            model=self.model,
            max_reference_images=self._profile["max_reference_images"],
            price_usd_per_image=float(self._profile["price_usd_per_image"]),
            default_params=dict(self._profile["default_params"]),
            notes=self._profile["notes"],
        )

    def _client(self):
        """fal_client lazy importieren (optionale Abhängigkeit), Key prüfen."""
        try:
            import fal_client
        except ImportError as e:
            raise RuntimeError(
                "[ImageProvider] provider=fal benötigt fal-client: pip install fal-client"
            ) from e
        if not os.environ.get("FAL_KEY"):
            raise RuntimeError(
                "[ImageProvider] Umgebungsvariable FAL_KEY fehlt (fal.ai-Zugriffsschlüssel)"
            )
        return fal_client

    def estimate_image_cost_usd(self) -> float:
        """Kosten des nächsten Bildes in USD (0.0 = unbekannt/free)."""
        return float(self._profile["price_usd_per_image"])

    @property
    def spent_usd(self) -> float:
        """Summe der bereits eingeplanten Bild-Kosten dieses Laufs (USD)."""
        return self._spent_usd

    async def _resolve_image_ref(self, fal_client, ref: str) -> str:
        if ref.startswith(("http://", "https://", "data:")):
            return ref
        if os.path.exists(ref):
            return await asyncio.to_thread(fal_client.upload_file, ref)
        return ref

    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        size: Optional[str] = None,
        max_retries: int = 4,
        retry_base_delay: float = 20.0,
        **kwargs,
    ) -> ImageOutput:
        fal_client = self._client()
        profile = self._profile
        refs = list(reference_image_paths or [])
        if refs and len(refs) > self.capabilities.max_reference_images:
            logger.warning(
                "[ImageProvider] fal: %d reference images given, "
                "using the first %d (model takes %d)",
                len(refs), self.capabilities.max_reference_images,
                self.capabilities.max_reference_images,
            )
            refs = refs[: self.capabilities.max_reference_images]

        # Kosten-/Budget-Gate: vor dem Submit prüfen — Überschreitung = klarer
        # Abbruch, nicht still teuer weiterretryen (Spiegel zu FalVideoProvider)
        cost = self.estimate_image_cost_usd()
        if cost > 0:
            budget = float(get_settings().agnes_image_budget_usd or 0.0)
            if budget > 0 and self._spent_usd + cost > budget:
                raise RuntimeError(
                    f"[ImageProvider] cost budget exceeded: ${self._spent_usd:.2f} "
                    f"planned so far + ${cost:.2f} for this image > budget "
                    f"${budget:.2f} (AGNES_IMAGE_BUDGET_USD) — aborted before spend"
                )
            self._spent_usd += cost

        arguments: dict = {"prompt": prompt}
        arguments.update(profile["default_params"])
        width, height = _parse_size(size)
        arguments.setdefault("image_size", {"width": width, "height": height})
        if refs:
            arguments["image_urls"] = [
                await self._resolve_image_ref(fal_client, r) for r in refs
            ]

        logger.info(
            "[ImageProvider] fal %s (%d ref(s), ~$%.4f): prompt %d chars",
            self.model, len(refs), cost, len(prompt),
        )
        result = await asyncio.to_thread(
            fal_client.subscribe, self.model, arguments,
        )
        images = (result or {}).get("images") or []
        url = (images[0] or {}).get("url", "") if images else ""
        if not url:
            raise RuntimeError(
                f"[ImageProvider] fal result has no image url: {result!r}"
            )
        logger.info("[ImageProvider] fal done: %s...", url[:80])
        return ImageOutput(fmt="url", ext="png", data=url)


# ═══════════════════════════════════════════════════════════════
# Fabrik
# ═══════════════════════════════════════════════════════════════


def create_image_provider(api_key: str = "", model: str = ""):
    """Bild-Provider gemäß ausgewähltem Modell bauen (Routing nach ID-Präfix).

    - ``pollinations/*`` → PollinationsImageProvider (kostenlos)
    - ``fal-ai/*``       → FalImageProvider (bezahlt, FAL_KEY lazy validiert)
    - alles andere       → AgnesImageAPI (Gratis-Default; Import zum Aufruf-
      zeitpunkt: monkeypatch("core.api.agnes_image.AgnesImageAPI") wirkt auf
      diese Fabrik — Mock-Regression-Patch-Punkt)
    """
    from core.config import DEFAULT_IMAGE_MODEL

    m = (model or DEFAULT_IMAGE_MODEL).strip()
    if m.startswith("pollinations/"):
        return PollinationsImageProvider(model=m)
    if m.startswith("fal-ai/"):
        return FalImageProvider(model=m)
    from core.api.agnes_image import AgnesImageAPI

    return AgnesImageAPI(api_key=api_key, model=m)
