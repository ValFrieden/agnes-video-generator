"""tests.test_suno_music — Тесты для клиента генерации музыки Suno AI и библиотеки стилей."""

from unittest.mock import MagicMock

from core.api.suno_music import (
    SunoMusicAPI,
    compose_music_prompt,
    get_preset_by_name,
    MUSIC_STYLE_CATEGORIES,
    SUNO_MODELS,
)


def run_coroutine(coro):
    """Выполняет простую замоканную корутину без создания сетевого socketpair в песочнице."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value


def test_compose_music_prompt():
    """Проверяет формирование формулы музыкального промпта для Suno."""
    prompt = compose_music_prompt(
        genre="Cyberpunk Synthwave",
        instruments="analog synths, punchy kick, gated snare",
        bpm=128,
        key_signature="D Minor",
        mood="Dark and energetic",
        resonance_hz=432,
    )
    assert "Cyberpunk Synthwave" in prompt
    assert "128 BPM" in prompt
    assert "D Minor" in prompt
    assert "432 Hz harmonic resonance" in prompt
    assert "analog synths" in prompt


def test_compose_music_prompt_defaults():
    """Проверяет значения по умолчанию."""
    prompt = compose_music_prompt()
    assert "Cinematic Soundtrack" in prompt
    assert "120 BPM" in prompt
    assert "instrumental, audiophile master" in prompt


def test_preset_catalog_and_lookup():
    """Проверяет наличие категорий и поиск пресетов по имени."""
    assert "cinematic" in MUSIC_STYLE_CATEGORIES
    assert "synthwave" in MUSIC_STYLE_CATEGORIES
    assert "rock" in MUSIC_STYLE_CATEGORIES
    assert "hiphop" in MUSIC_STYLE_CATEGORIES

    preset = get_preset_by_name("80s Outrun Synthwave")
    assert preset is not None
    assert preset["bpm"] == 120
    assert "analog synth bass" in preset["instruments"]

    preset_epic = get_preset_by_name("Epic Orchestral Trailer")
    assert preset_epic is not None
    assert preset_epic["key"] == "D Minor"

    assert get_preset_by_name("non_existent_preset_xyz") is None


def test_suno_models_list():
    """Проверяет список поддерживаемых моделей Suno AI."""
    model_ids = [m["id"] for m in SUNO_MODELS]
    assert "V6" in model_ids
    assert "V6_WILD" in model_ids
    assert "V6_MINI" in model_ids
    assert "V5" in model_ids
    assert "V4" in model_ids


def test_suno_api_configuration():
    """Проверяет флаг is_configured."""
    api_no_key = SunoMusicAPI(api_key="")
    assert not api_no_key.is_configured()

    api_with_key = SunoMusicAPI(api_key="kie_test_key_123456789")
    assert api_with_key.is_configured()


class FakeAsyncClient:
    last_payload = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def post(self, url, json=None, headers=None):
        FakeAsyncClient.last_payload = json
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "code": 200,
            "data": {"taskId": "task-suno-12345"},
            "msg": "success",
        }
        resp.raise_for_status = MagicMock()

        async def _ret():
            return resp

        return _ret()

    def get(self, url, headers=None):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "code": 200,
            "data": {
                "taskId": "task-suno-12345",
                "state": "success",
                "response": {
                    "sunoData": [
                        {
                            "audioUrl": "https://example.com/track.mp3",
                            "duration": 45.2,
                            "title": "Epic Track",
                        }
                    ]
                },
            },
        }
        resp.raise_for_status = MagicMock()

        async def _ret():
            return resp

        return _ret()


def test_generate_music_payload(monkeypatch):
    """Проверяет отправку запроса на генерацию с правильным payload."""
    monkeypatch.setattr("core.api.suno_music.httpx.AsyncClient", FakeAsyncClient)

    api = SunoMusicAPI(api_key="test_api_key_valid")
    res = run_coroutine(
        api.generate_music(
            prompt="Epic cyber battle theme",
            style="Synthwave, 120 BPM",
            title="Wardenclyffe Beat",
            instrumental=True,
            model="V6",
        )
    )

    assert res.get("taskId") == "task-suno-12345"
    payload = FakeAsyncClient.last_payload
    assert payload.get("prompt") == "Epic cyber battle theme"
    assert payload.get("style") == "Synthwave, 120 BPM"
    assert payload.get("model") == "V6"
    assert payload.get("instrumental") is True


def test_get_record_info(monkeypatch):
    """Проверяет опрос статуса задачи."""
    monkeypatch.setattr("core.api.suno_music.httpx.AsyncClient", FakeAsyncClient)

    api = SunoMusicAPI(api_key="test_api_key_valid")
    info = run_coroutine(api.get_record_info("task-suno-12345"))
    assert info.get("taskId") == "task-suno-12345"
    assert info.get("state") == "success"


def test_generate_music_missing_key_raises():
    """Проверяет возбуждение исключения при отсутствии ключа."""
    import pytest
    api = SunoMusicAPI(api_key="")
    with pytest.raises(ValueError, match="не сконфигурирован"):
        run_coroutine(api.generate_music(prompt="Test song"))
