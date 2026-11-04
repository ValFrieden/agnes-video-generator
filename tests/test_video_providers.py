"""
core.api.video_providers — Unit-Tests zur Video-Provider-Abstraktion (v7.1 Phase 2 / v7.2 R8)

Abgedeckt (vgl. docs/plans/v7.1/video_provider_PRD.md §四 + R8 P0/P2):
- Fabrik: Standard agnes (AgnesVideoAPI-Instanz), unbekannter Wert wirft Fehler, env=fal → FalVideoProvider
- FalVideoProvider (Standard MiniMax H3 Max): Submit-I2V/T2V-Pfade, Dauer-Klemmung 5-15 (int),
  Resolution-Tier, Seed-Durchleitung, negative_prompt verworfen, end_image_url (First/Last-Frame),
  Cost-Estimate, Budget-Gate (AGNES_VIDEO_BUDGET_USD), Status-Polling → Result → VideoOutput,
  Shutdown-Cancel, resolve_image_ref Durchleitung/Upload
- Legacy-Profil Kling v1.5: Dauer-Snap {5,10} (String), aspect_ratio, cfg_scale, negative_prompt
- Pipeline-Verkabelung über die Fabrik (manuscript: Standard agnes; env=fal → FalVideoProvider)

fal_client wird per sys.modules-injiziertem Stub ersetzt — niemals echtes Netz.

Ausführung:
    python -m pytest tests/test_video_providers.py -v
"""

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

import pytest

# ═══════════════════════════════════════════════════
# fal_client-Stub (simuliert SDK-Oberfläche: submit / status / result / upload_file)
# ═══════════════════════════════════════════════════


class _Handler:
    def __init__(self, request_id: str):
        self.request_id = request_id


class _Status:
    """Simuliert die drei fal_client-Zustandsobjekte Queued / InProgress / Completed.

    Liefert sowohl das Klassennamen-Signal (Completed) als auch das status-Attribut
    (Enum-String "COMPLETED") — korrespondiert mit der Doppel-Signal-Prüfung in
    FalVideoProvider._is_completed.
    """

    def __init__(self, name: str):
        self._name = name
        self.status = name

    def __repr__(self):
        return f"Status.{self._name}"


def _install_fake_fal(monkeypatch, *, result_url="https://cdn.fal/example.mp4"):
    """Injiziert den fal_client-Stub in sys.modules und gibt den Aufruf-Recorder zurück."""
    calls = {"submit": [], "status": [], "result": [], "upload": []}
    state = {"completed": False, "status_name": "IN_QUEUE"}

    mod = types.ModuleType("fal_client")

    def submit(endpoint, arguments):
        calls["submit"].append({"endpoint": endpoint, "arguments": arguments})
        return _Handler(f"req_{len(calls['submit'])}")

    def status(endpoint, request_id):
        calls["status"].append({"endpoint": endpoint, "request_id": request_id})
        # v7.2 R8: konfigurierbarer Endpunkt-Fehler (Restart-Resume-Selbstheilung)
        fail_on = state.get("fail_endpoint")
        if fail_on and fail_on in endpoint:
            raise RuntimeError(f"404 Not Found: {endpoint}")
        if state["completed"]:
            return _Status("COMPLETED")
        return _Status(state["status_name"])

    def result(endpoint, request_id):
        calls["result"].append({"endpoint": endpoint, "request_id": request_id})
        return {"video": {"url": result_url}}

    def upload_file(path):
        calls["upload"].append(path)
        return f"https://cdn.fal/upload/{os.path.basename(path)}"

    mod.submit = submit
    mod.status = status
    mod.result = result
    mod.upload_file = upload_file
    monkeypatch.setitem(sys.modules, "fal_client", mod)
    monkeypatch.setenv("FAL_KEY", "test-fal-key")
    return calls, state


# ═══════════════════════════════════════════════════
# 1. Fabrik
# ═══════════════════════════════════════════════════


class TestFactory:
    def test_default_returns_agnes(self, monkeypatch):
        monkeypatch.delenv("AGNES_VIDEO_PROVIDER", raising=False)
        from core.api.video_providers import create_video_provider

        provider = create_video_provider(api_key="k1", default_model="agnes-video-v2.0")
        from core.api.agnes_video import AgnesVideoAPI

        assert isinstance(provider, AgnesVideoAPI)
        assert provider.model == "agnes-video-v2.0"

    def test_unknown_provider_raises(self, monkeypatch):
        monkeypatch.setenv("AGNES_VIDEO_PROVIDER", "veo")
        from core.api.video_providers import create_video_provider

        with pytest.raises(ValueError, match="AGNES_VIDEO_PROVIDER"):
            create_video_provider(api_key="k1")

    def test_fal_provider_selected(self, monkeypatch):
        monkeypatch.setenv("AGNES_VIDEO_PROVIDER", "fal")
        _install_fake_fal(monkeypatch)
        from core.api.video_providers import FalVideoProvider, create_video_provider

        provider = create_video_provider(api_key="k1")
        assert isinstance(provider, FalVideoProvider)
        # v7.2 R8: fal-Standard ist MiniMax H3 Max (nicht mehr Kling v1.5)
        assert provider.model.startswith("minimax/h3-max")

    def test_fal_provider_missing_client_hint(self, monkeypatch):
        monkeypatch.setenv("AGNES_VIDEO_PROVIDER", "fal")
        monkeypatch.delitem(sys.modules, "fal_client", raising=False)
        import builtins

        real_import = builtins.__import__

        def _no_fal(name, *a, **kw):
            if name == "fal_client":
                raise ImportError("No module named 'fal_client'")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", _no_fal)
        from core.api.video_providers import FalVideoProvider, create_video_provider

        # Fabrik validiert lazy: Konstruktion gelingt, beim Submit kommt ein
        # umsetzbarer Installations-Hinweis
        provider = create_video_provider(api_key="k1")
        assert isinstance(provider, FalVideoProvider)
        with pytest.raises(RuntimeError, match="pip install fal-client"):
            asyncio.run(provider.submit_video(prompt="x"))


# ═══════════════════════════════════════════════════
# 2. FalVideoProvider-Verhalten — MiniMax H3 Max (Standard-Profil)
# ═══════════════════════════════════════════════════

KLING_V15 = "fal-ai/kling-video/v1.5/pro/image-to-video"


def _make_fal_provider(monkeypatch, model=None, **kw):
    monkeypatch.setenv("AGNES_VIDEO_PROVIDER", "fal")
    calls, state = _install_fake_fal(monkeypatch, **kw)
    from core.api import video_providers

    # Härtung: Poll-Intervall im Test auf 0 — ein Logikfehler darf nie wieder
    # echte 20s-Schläfen × 1800s-Timeout in einen Minuten-Hang verwandeln
    monkeypatch.setattr(video_providers, "_FAL_POLL_INTERVAL_SECONDS", 0)
    from core.api.video_providers import FalVideoProvider

    provider = FalVideoProvider() if model is None else FalVideoProvider(model=model)
    return provider, calls, state


class TestH3MaxProvider:
    def test_submit_i2v_path(self, monkeypatch, tmp_path):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        frame = tmp_path / "frame.png"
        frame.write_bytes(b"\x89PNG-fake")
        vid = asyncio.run(provider.submit_video(
            prompt="motion only",
            reference_image_paths=[str(frame)],
            duration=5, width=1280, height=720,
        ))
        assert vid == "req_1"
        sub = calls["submit"][0]
        assert sub["endpoint"].endswith("/image-to-video")
        assert sub["arguments"]["image_url"].startswith("https://cdn.fal/upload/")
        # H3 Max: Dauer als int, kein aspect_ratio (Output folgt dem First Frame)
        assert sub["arguments"]["duration"] == 5
        assert "aspect_ratio" not in sub["arguments"]
        # 1280x720 → nächstgelegene Stufe 768P; Screenwriter-Prompts bleiben exakt
        assert sub["arguments"]["resolution"] == "768P"
        assert sub["arguments"]["prompt_expansion_mode"] == "disabled"
        assert "cfg_scale" not in sub["arguments"]

    def test_submit_t2v_path_derived_endpoint(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        asyncio.run(provider.submit_video(prompt="pure text", duration=10))
        sub = calls["submit"][0]
        assert sub["endpoint"].endswith("/text-to-video")
        assert "image_url" not in sub["arguments"]
        assert sub["arguments"]["duration"] == 10

    def test_duration_clamped_to_5_15(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        asyncio.run(provider.submit_video(prompt="x", duration=7))
        asyncio.run(provider.submit_video(prompt="x", duration=3))
        asyncio.run(provider.submit_video(prompt="x", duration=20))
        args = [c["arguments"]["duration"] for c in calls["submit"]]
        assert args == [7, 5, 15]

    def test_seed_passthrough(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        asyncio.run(provider.submit_video(prompt="x", seed=42))
        assert calls["submit"][0]["arguments"]["seed"] == 42

    def test_negative_prompt_dropped(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        asyncio.run(provider.submit_video(prompt="x", negative_prompt="blurry"))
        assert "negative_prompt" not in calls["submit"][0]["arguments"]

    def test_end_image_first_last_frame(self, monkeypatch, tmp_path):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        frame = tmp_path / "f.png"
        frame.write_bytes(b"\x89PNG")
        end = tmp_path / "e.png"
        end.write_bytes(b"\x89PNG")
        asyncio.run(provider.submit_video(
            prompt="x",
            reference_image_paths=[str(frame)],
            end_image_path=str(end),
        ))
        args = calls["submit"][0]["arguments"]
        assert args["end_image_url"].startswith("https://cdn.fal/upload/")
        assert len(calls["upload"]) == 2  # First + Last Frame

    def test_extra_refs_truncated(self, monkeypatch, tmp_path):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        frames = []
        for i in range(3):
            f = tmp_path / f"f{i}.png"
            f.write_bytes(b"\x89PNG")
            frames.append(str(f))
        asyncio.run(provider.submit_video(prompt="x", reference_image_paths=frames))
        # nur die erste wurde hochgeladen
        assert len(calls["upload"]) == 1

    def test_wait_polls_until_completed(self, monkeypatch, tmp_path):
        provider, calls, state = _make_fal_provider(monkeypatch)
        frame = tmp_path / "f.png"
        frame.write_bytes(b"\x89PNG")
        vid = asyncio.run(provider.submit_video(prompt="x", reference_image_paths=[str(frame)]))
        # Stub startet in IN_QUEUE; nach „completed" kehrt das Warten sofort zurück
        state["completed"] = True
        out = asyncio.run(provider.wait_for_video(vid))
        assert out.fmt == "url" and out.data.endswith(".mp4")
        assert out.ext == "mp4"
        # Warten adressiert über den Submit-Endpoint (I2V)
        assert calls["result"][0]["endpoint"].endswith("/image-to-video")

    def test_shutdown_raises_cancelled(self, monkeypatch):
        provider, calls, state = _make_fal_provider(monkeypatch)
        vid = asyncio.run(provider.submit_video(prompt="x"))
        provider.shutdown_event = asyncio.Event()
        provider.shutdown_event.set()
        from core.api.agnes_video import VideoTaskCancelled

        with pytest.raises(VideoTaskCancelled):
            asyncio.run(provider.wait_for_video(vid))

    def test_resolve_image_ref_passthrough(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        url = asyncio.run(provider.resolve_image_ref("https://example.com/a.png"))
        assert url == "https://example.com/a.png"
        assert calls["upload"] == []

    def test_capabilities(self, monkeypatch):
        provider, _, _ = _make_fal_provider(monkeypatch)
        caps = provider.capabilities
        assert caps.max_reference_images == 1
        assert caps.supports_negative_prompt is False
        assert caps.supports_seed is True
        assert caps.supports_first_last_frame is True
        assert caps.durations == tuple(range(5, 16))
        assert caps.duration_range == (5, 15)
        assert caps.resolution_tiers == ("480P", "768P")
        assert caps.price_usd_per_second["768P"] == pytest.approx(0.08)
        assert caps.default_params["prompt_expansion_mode"] == "disabled"

    def test_estimate_clip_cost(self, monkeypatch):
        provider, _, _ = _make_fal_provider(monkeypatch)
        # 768P = $0.08/s
        assert provider.estimate_clip_cost_usd(5, 1280, 720) == pytest.approx(0.40)
        assert provider.estimate_clip_cost_usd(10, 768, 1152) == pytest.approx(0.80)
        # unbekannter Preis (Kling v1.5 hat keinen hinterlegten Preis) → 0
        kling, _, _ = _make_fal_provider(monkeypatch, model=KLING_V15)
        assert kling.estimate_clip_cost_usd(5, 1280, 720) == 0.0

    def test_budget_gate_blocks_before_submit(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        monkeypatch.setenv("AGNES_VIDEO_BUDGET_USD", "0.2")
        # 5 s × $0.08 = $0.40 > $0.20 → Abbruch VOR dem Submit
        with pytest.raises(RuntimeError, match="budget"):
            asyncio.run(provider.submit_video(prompt="x", duration=5))
        assert calls["submit"] == []

    def test_budget_accumulates_across_clips(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch)
        monkeypatch.setenv("AGNES_VIDEO_BUDGET_USD", "1.0")
        asyncio.run(provider.submit_video(prompt="x", duration=5))   # $0.40
        asyncio.run(provider.submit_video(prompt="x", duration=5))   # $0.40
        assert provider.spent_usd == pytest.approx(0.80)
        # dritter Clip ($1.20 kumuliert) reißt das Budget
        with pytest.raises(RuntimeError, match="budget"):
            asyncio.run(provider.submit_video(prompt="x", duration=5))
        assert len(calls["submit"]) == 2

    def test_budget_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("AGNES_VIDEO_BUDGET_USD", raising=False)
        provider, calls, _ = _make_fal_provider(monkeypatch)
        for _ in range(3):
            asyncio.run(provider.submit_video(prompt="x", duration=5))
        assert len(calls["submit"]) == 3

    def test_wait_self_heals_to_sibling_endpoint_after_restart(self, monkeypatch):
        """Restart-Resume: leere Endpoint-Map + T2V-Job → einmaliger Wechsel i2v→t2v."""
        provider, calls, state = _make_fal_provider(monkeypatch)
        asyncio.run(provider.submit_video(prompt="x"))  # t2v-Submission
        vid = "req_1"
        provider._endpoints.clear()          # simulierter Dienstneustart
        state["fail_endpoint"] = "/image-to-video"   # Default-i2v scheitert (404)
        state["completed"] = True

        out = asyncio.run(provider.wait_for_video(vid))

        assert out.fmt == "url" and out.data.endswith(".mp4")
        # Ergebnis am Schwester-Endpoint (t2v) adressiert + wieder eingelernt
        assert calls["result"][0]["endpoint"].endswith("/text-to-video")
        assert provider._endpoints[vid].endswith("/text-to-video")

    def test_wait_fails_through_when_sibling_also_fails(self, monkeypatch):
        provider, calls, state = _make_fal_provider(monkeypatch)
        asyncio.run(provider.submit_video(prompt="x"))
        provider._endpoints.clear()
        state["fail_endpoint"] = "-to-video"  # substring: trifft i2v UND t2v

        with pytest.raises(RuntimeError, match="404"):
            asyncio.run(provider.wait_for_video("req_1"))
        # genau ein Wechselversuch, kein Endlos-Loop
        assert len(calls["status"]) == 2

    def test_wait_reports_progress_callback(self, monkeypatch):
        provider, calls, state = _make_fal_provider(monkeypatch)
        vid = asyncio.run(provider.submit_video(prompt="x"))
        state["completed"] = True
        seen = []

        asyncio.run(provider.wait_for_video(
            vid, progress_callback=lambda status, waited: seen.append((status, waited)),
        ))

        assert seen and seen[0][0] == "COMPLETED"

    def test_provider_catalog(self, monkeypatch):
        monkeypatch.delenv("AGNES_VIDEO_PROVIDER", raising=False)
        from core.api.video_providers import get_video_provider_catalog

        cat = get_video_provider_catalog()
        assert cat["default"] == "agnes"
        assert cat["choices"] == ["agnes", "fal"]
        assert any(m["model"].startswith("minimax/") for m in cat["fal_models"])
        assert all(m["price_usd_per_second"] > 0 for m in cat["fal_models"])


# ═══════════════════════════════════════════════════
# 3. Legacy-Profil: Kling v1.5 (altes Verhalten bleibt über FAL_VIDEO_MODEL erreichbar)
# ═══════════════════════════════════════════════════


class TestKlingLegacyProfile:
    def test_submit_keeps_string_duration_aspect_and_cfg(self, monkeypatch, tmp_path):
        provider, calls, _ = _make_fal_provider(monkeypatch, model=KLING_V15)
        frame = tmp_path / "f.png"
        frame.write_bytes(b"\x89PNG")
        asyncio.run(provider.submit_video(
            prompt="x",
            reference_image_paths=[str(frame)],
            duration=5, width=1280, height=720,
        ))
        sub = calls["submit"][0]
        assert sub["endpoint"].endswith("/image-to-video")
        assert sub["arguments"]["duration"] == "5"          # String-Stufen
        assert sub["arguments"]["aspect_ratio"] == "16:9"   # Kling hat aspect_ratio
        assert sub["arguments"]["cfg_scale"] == pytest.approx(0.5)

    def test_cfg_scale_and_negative_passthrough(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch, model=KLING_V15)
        asyncio.run(provider.submit_video(
            prompt="x", cfg_scale=0.6, negative_prompt="blurry", seed=7,
        ))
        args = calls["submit"][0]["arguments"]
        assert args["cfg_scale"] == pytest.approx(0.6)
        assert args["negative_prompt"] == "blurry"
        assert "seed" not in args  # Kling: Seed nicht unterstützt

    def test_duration_snapped_to_allowed(self, monkeypatch):
        provider, calls, _ = _make_fal_provider(monkeypatch, model=KLING_V15)
        asyncio.run(provider.submit_video(prompt="x", duration=7))
        asyncio.run(provider.submit_video(prompt="x", duration=9))
        assert calls["submit"][0]["arguments"]["duration"] == "5"
        assert calls["submit"][1]["arguments"]["duration"] == "10"

    def test_capabilities(self, monkeypatch):
        provider, _, _ = _make_fal_provider(monkeypatch, model=KLING_V15)
        caps = provider.capabilities
        assert caps.max_reference_images == 1
        assert caps.supports_negative_prompt is True
        assert caps.supports_seed is False
        assert caps.supports_first_last_frame is False
        assert 5 in caps.durations and 10 in caps.durations
        assert caps.default_params["cfg_scale"] == pytest.approx(0.5)


# ═══════════════════════════════════════════════════
# 4. Pipeline-Verkabelung über die Fabrik
# ═══════════════════════════════════════════════════


class TestPipelineWiring:
    def test_manuscript_default_agnes(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AGNES_REGRESSION_WORKING_DIR", str(tmp_path))
        monkeypatch.delenv("AGNES_VIDEO_PROVIDER", raising=False)
        from core.api.agnes_video import AgnesVideoAPI
        from core.pipelines.manuscript_video import ManuscriptVideoPipeline

        p = ManuscriptVideoPipeline(api_key="k1", task_id="w1", dir_name="w1")
        assert isinstance(p.video_api, AgnesVideoAPI)

    def test_manuscript_fal_provider(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AGNES_REGRESSION_WORKING_DIR", str(tmp_path))
        monkeypatch.setenv("AGNES_VIDEO_PROVIDER", "fal")
        _install_fake_fal(monkeypatch)
        from core.api.video_providers import FalVideoProvider
        from core.pipelines.manuscript_video import ManuscriptVideoPipeline

        p = ManuscriptVideoPipeline(api_key="k1", task_id="w2", dir_name="w2")
        assert isinstance(p.video_api, FalVideoProvider)
