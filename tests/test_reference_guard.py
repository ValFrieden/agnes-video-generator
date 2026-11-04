"""Tests für die Referenz-Pflicht (铁律 No pure Text-to-Video).

Prüft, dass die Sperre dort greift, wo Charakter-Konsistenz Vertrag ist
(creative / anchor), und dass die designierten T2V-Pipelines (poetry / manuscript)
nur warnen statt zu blockieren.

Importe bewusst lazy (wie in ``tests/mock_regression/test_pipelines.py``): die
Pipeline-Module ziehen schwere Abhängigkeiten und sollen erst im Test laden.
"""
from types import SimpleNamespace

import pytest


def _bare_instance(cls, **attrs):
    """Instanz ohne __init__ (die Pipelines brauchen im Test keine echten Clients)."""
    obj = object.__new__(cls)
    obj.__dict__.update(attrs)
    return obj


@pytest.fixture
def t_stub():
    return lambda key, **params: f"{key}:{params}"


def test_creative_blocks_without_character_card(t_stub):
    from core.pipelines import PipelineShutdown
    from core.pipelines.creative.pipeline import CreativeVideoPipeline

    pipeline = _bare_instance(
        CreativeVideoPipeline,
        _state=SimpleNamespace(character_ref_file=""),
        _character_ref_path="",
        _t=t_stub,
    )
    with pytest.raises(PipelineShutdown) as exc:
        pipeline._require_character_reference()
    assert "pipeline.reference_required" in str(exc.value)


def test_creative_accepts_existing_character_card(t_stub, tmp_path):
    from core.pipelines.creative.pipeline import CreativeVideoPipeline

    card = tmp_path / "character_reference.png"
    card.write_bytes(b"fake")
    pipeline = _bare_instance(
        CreativeVideoPipeline,
        _state=SimpleNamespace(character_ref_file=""),
        _character_ref_path=str(card),
        _t=t_stub,
    )
    pipeline._require_character_reference()  # darf nicht werfen


def test_anchor_blocks_without_anchor_image(t_stub):
    from core.pipelines import PipelineShutdown
    from core.pipelines.anchor_video import AnchorVideoPipeline

    pipeline = _bare_instance(
        AnchorVideoPipeline,
        _state=SimpleNamespace(anchor_image_path=""),
        _t=t_stub,
    )
    with pytest.raises(PipelineShutdown):
        pipeline._require_anchor_image()


def test_anchor_accepts_existing_anchor_image(t_stub, tmp_path):
    from core.pipelines.anchor_video import AnchorVideoPipeline

    image = tmp_path / "anchor.png"
    image.write_bytes(b"fake")
    pipeline = _bare_instance(
        AnchorVideoPipeline,
        _state=SimpleNamespace(anchor_image_path=str(image)),
        _t=t_stub,
    )
    pipeline._require_anchor_image()


def test_character_pipelines_declare_hard_policy():
    from core.pipelines.anchor_video import AnchorVideoPipeline
    from core.pipelines.creative.pipeline import CreativeVideoPipeline
    from core.pipelines.poetry_video import PoetryVideoPipeline

    assert CreativeVideoPipeline._reference_required(object.__new__(CreativeVideoPipeline)) is True
    assert AnchorVideoPipeline._reference_required(object.__new__(AnchorVideoPipeline)) is True
    # Designierte T2V-Pipeline bleibt weich
    assert PoetryVideoPipeline._reference_required(object.__new__(PoetryVideoPipeline)) is False


@pytest.mark.asyncio
async def test_warn_mode_does_not_block(t_stub):
    """Basis-Pipeline (poetry/manuscript): leere Referenz nur Warnung, kein Abbruch."""
    from core.pipelines.multi_scene import MultiScenePipeline

    class _ConcreteMultiScene(MultiScenePipeline):
        async def _build_reference_images(self): pass
        async def _build_scenes(self): pass
        async def _composite_final(self): return ""

    emitted = []

    async def _fake_emit(*args, **kwargs):
        emitted.append(args)

    pipeline = _bare_instance(
        _ConcreteMultiScene,
        _state=SimpleNamespace(),
        _t=t_stub,
        _emit=_fake_emit,
    )
    await pipeline._guard_scene_reference(SimpleNamespace(), 0, [])
    assert emitted, "Warnung soll als Fortschritt sichtbar werden"


@pytest.mark.asyncio
async def test_hard_mode_blocks_without_refs(t_stub):
    from core.pipelines import PipelineShutdown
    from core.pipelines.creative.pipeline import CreativeVideoPipeline

    pipeline = _bare_instance(
        CreativeVideoPipeline,
        _state=SimpleNamespace(),
        _t=t_stub,
    )
    with pytest.raises(PipelineShutdown):
        await pipeline._guard_scene_reference(SimpleNamespace(), 2, [])


@pytest.mark.asyncio
async def test_guard_is_silent_when_refs_present(t_stub):
    from core.pipelines.creative.pipeline import CreativeVideoPipeline

    async def _boom(*args, **kwargs):
        raise AssertionError("darf bei vorhandener Referenz nicht emittieren")

    pipeline = _bare_instance(
        CreativeVideoPipeline,
        _state=SimpleNamespace(),
        _t=t_stub,
        _emit=_boom,
    )
    await pipeline._guard_scene_reference(SimpleNamespace(), 0, ["scene_0/keyframe.png"])
