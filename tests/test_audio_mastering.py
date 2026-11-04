"""tests.test_audio_mastering — Тесты для мастеринга, сведения дорожек и обрезки звука."""

import os
import pytest
from unittest.mock import patch, MagicMock

from core.compositor.concatenator.audio_overlay import AudioOverlayMixin
from core.audio.audio_trimmer import trim_audio_segment


def test_mastering_eq_profiles():
    """Проверяет генерацию параметров FFmpeg эквалайзера для всех профилей мастеринга."""
    warm_eq = AudioOverlayMixin.get_mastering_eq("warm")
    assert "200" in warm_eq and "9000" in warm_eq

    club_eq = AudioOverlayMixin.get_mastering_eq("club")
    assert "60" in club_eq and "120" in club_eq

    radio_eq = AudioOverlayMixin.get_mastering_eq("radio")
    assert "11000" in radio_eq and "3500" in radio_eq

    lofi_eq = AudioOverlayMixin.get_mastering_eq("lofi")
    assert "highpass" in lofi_eq and "lowpass" in lofi_eq

    flat_eq = AudioOverlayMixin.get_mastering_eq("flat")
    assert flat_eq == ""

    # Неизвестный профиль должен возвращать пустую строку (flat)
    unknown_eq = AudioOverlayMixin.get_mastering_eq("unknown_xyz")
    assert unknown_eq == ""


def test_trim_audio_segment_validation(tmp_path):
    """Проверяет валидацию входных параметров при обрезке звука."""
    fake_audio = str(tmp_path / "test.mp3")
    with open(fake_audio, "wb") as f:
        f.write(b"ID3" + b"\x00" * 100)

    out_audio = str(tmp_path / "out.mp3")

    # end_sec <= start_sec
    with pytest.raises(ValueError, match="Некорректный интервал"):
        trim_audio_segment(fake_audio, out_audio, start_sec=10.0, end_sec=5.0)

    # Несуществующий файл
    with pytest.raises(FileNotFoundError):
        trim_audio_segment("non_existent_file.mp3", out_audio, start_sec=0.0, end_sec=5.0)


def test_trim_audio_segment_ffmpeg_call(tmp_path):
    """Проверяет построение команды FFmpeg при обрезке звука."""
    fake_audio = str(tmp_path / "input.mp3")
    with open(fake_audio, "wb") as f:
        f.write(b"ID3" + b"\x00" * 100)

    out_audio = str(tmp_path / "output.mp3")

    mock_run = MagicMock()
    mock_run.returncode = 0

    with patch("subprocess.run", return_value=mock_run) as mock_sub:
        with patch("core.audio.audio_trimmer.probe_duration", return_value=15.0):
            dur = trim_audio_segment(fake_audio, out_audio, start_sec=5.0, end_sec=20.0, bitrate="320k")

            assert dur == 15.0
            mock_sub.assert_called_once()
            cmd = mock_sub.call_args[0][0]
            assert "-ss" in cmd
            assert "5.000" in cmd
            assert "-to" in cmd
            assert "20.000" in cmd
            assert "320k" in cmd


def test_mix_voice_and_bgm_ffmpeg_call(tmp_path):
    """Проверяет построение фильтра FFmpeg при сведении голоса и BGM."""
    fake_voice = str(tmp_path / "voice.mp3")
    fake_bgm = str(tmp_path / "bgm.mp3")
    out_mix = str(tmp_path / "mix.mp3")

    with open(fake_voice, "wb") as f:
        f.write(b"ID3" + b"\x00" * 100)
    with open(fake_bgm, "wb") as f:
        f.write(b"ID3" + b"\x00" * 100)

    with patch("core.compositor.concatenator.concat.VideoConcatenator._get_duration", return_value=25.0):
        with patch("core.compositor.concatenator.concat.VideoConcatenator._run_ffmpeg") as mock_run:
            AudioOverlayMixin.mix_voice_and_bgm(
                voice_path=fake_voice,
                bgm_path=fake_bgm,
                output_path=out_mix,
                voice_volume=1.3,
                bgm_volume=0.2,
                mastering_profile="warm",
                target_duration=25.0,
            )

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            filter_str = cmd[cmd.index("-filter_complex") + 1]

            # Проверяем наличие сайдчейна, громкостей и мастеринга
            assert "volume=1.30" in filter_str
            assert "volume=0.20" in filter_str
            assert "amix=inputs=2" in filter_str
            assert "equalizer=f=200" in filter_str  # Профиль 'warm'
