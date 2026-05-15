"""Tests for audio playback helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

import audio_playback
from audio_playback import playback_backends, sound_file_path


def test_sound_file_path_uses_plain_name_for_bell(tmp_path: Path) -> None:
    assert sound_file_path("bell", tmp_path) == tmp_path / "bell.wav"


def test_sound_file_path_uses_variant_for_typewriter_sounds(tmp_path: Path) -> None:
    assert (
        sound_file_path("newline", tmp_path, variant_selector=lambda _low, _high: 2)
        == tmp_path / "newline2.wav"
    )
    assert (
        sound_file_path("ratchet", tmp_path, variant_selector=lambda _low, _high: 3)
        == tmp_path / "ratchet3.wav"
    )


def test_playback_backends_follow_platform_order() -> None:
    assert playback_backends("darwin") == [["afplay"], ["paplay"], ["aplay"]]
    assert playback_backends("windows") == [["powershell"]]
    assert playback_backends("linux") == [["paplay"], ["aplay"], ["afplay"]]


def test_play_sound_file_uses_first_available_backend(
    monkeypatch, tmp_path: Path
) -> None:
    sound_path = tmp_path / "bell.wav"
    launched: list[list[str]] = []

    monkeypatch.setattr(
        audio_playback, "playback_backends", lambda: [["missing"], ["aplay"]]
    )
    monkeypatch.setattr(
        audio_playback.shutil,
        "which",
        lambda command: f"/usr/bin/{command}" if command == "aplay" else None,
    )

    class FakePopen:
        def __init__(self, cmd, stdout=None, stderr=None) -> None:
            launched.append(cmd)

    monkeypatch.setattr(audio_playback.subprocess, "Popen", FakePopen)

    audio_playback.play_sound_file(sound_path)

    assert launched == [["aplay", str(sound_path)]]


def test_play_sound_file_uses_powershell_backend(monkeypatch, tmp_path: Path) -> None:
    sound_path = tmp_path / "bell.wav"
    calls: list[list[str]] = []

    monkeypatch.setattr(audio_playback, "playback_backends", lambda: [["powershell"]])
    monkeypatch.setattr(audio_playback.shutil, "which", lambda command: command)

    def fake_run(cmd, stdout=None, stderr=None):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(audio_playback.subprocess, "run", fake_run)

    audio_playback.play_sound_file(sound_path)

    assert calls
    assert calls[0][0] == "powershell"
    assert str(sound_path) in calls[0][2]
