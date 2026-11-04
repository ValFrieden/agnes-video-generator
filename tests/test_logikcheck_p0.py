"""Regressionstests zu Logikcheck Befund 9 (qc.py) und dem Zusatzfund (_clamp_pixels).

Gehört zu den untracked Modulen core/quality/qc.py und core/api/image_providers.py und
wird zusammen mit ihnen committet. Befund 7 steht in tests/test_stop_semantics.py.

Jeder Test wurde zuerst gegen den unkorrigierten Code ausgeführt und schlug dort
fehl. Sie laufen ohne Netz, ohne Browser und ohne Guthaben.
"""

from __future__ import annotations

import typing

# ── Befund 9: qc.py lässt sich unter Python ≤ 3.13 nicht importieren ────────


def test_qc_annotations_resolve_on_every_python_version():
    """``Optional`` fehlte im Import. Python 3.14 wertet Annotationen verzögert aus
    und verdeckt das lokal; ``get_type_hints`` wertet sie unter jeder Version aus
    (Docker nutzt 3.11, die CI 3.10/3.12)."""
    from core.quality.qc import ClipQCGate

    hints = typing.get_type_hints(ClipQCGate._deterministic_frame_checks)

    assert "return" in hints


# ── Zusatzfund: _clamp_pixels ohne ``self.`` aufgerufen ─────────────────────


class _FakeResponse:
    status_code = 200
    content = b"\x89PNG-bytes"
    headers = {"Content-Type": "image/png"}

    def raise_for_status(self):
        return None


async def test_pollinations_generate_does_not_raise_name_error(monkeypatch):
    """Jede Pollinations-Bildgenerierung endete mit NameError, in allen Python-Versionen."""
    from core.api import image_providers

    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["params"] = params
        return _FakeResponse()

    async def no_throttle(self):
        return None

    monkeypatch.setattr(image_providers.requests, "get", fake_get)
    monkeypatch.setattr(image_providers.PollinationsImageProvider, "_throttle", no_throttle)

    provider = image_providers.PollinationsImageProvider("pollinations/flux")
    out = await provider.generate_single_image("a red balloon", size="1280x720")

    assert out.fmt == "b64"
    assert captured["params"]["width"] == 1280
    assert captured["params"]["height"] == 720


async def test_pollinations_clamps_pixel_range(monkeypatch):
    """Die Klemmung muss tatsächlich greifen, nicht nur aufrufbar sein."""
    from core.api import image_providers

    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["params"] = params
        return _FakeResponse()

    async def no_throttle(self):
        return None

    monkeypatch.setattr(image_providers.requests, "get", fake_get)
    monkeypatch.setattr(image_providers.PollinationsImageProvider, "_throttle", no_throttle)

    provider = image_providers.PollinationsImageProvider("pollinations/flux")
    await provider.generate_single_image("x", size="99999x99999")

    lo = image_providers._POLLINATIONS_MIN_PIXELS
    hi = image_providers._POLLINATIONS_MAX_PIXELS
    assert lo <= captured["params"]["width"] <= hi
    assert lo <= captured["params"]["height"] <= hi
