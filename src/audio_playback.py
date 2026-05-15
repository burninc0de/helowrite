"""Audio playback helpers for HeloWrite."""

import platform
import random
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

DEFAULT_AUDIO_DIR = Path(__file__).parent / "audio"
VARIANT_SOUNDS = {"newline", "ratchet"}


def sound_file_path(
    sound_name: str,
    audio_dir: Path = DEFAULT_AUDIO_DIR,
    variant_selector: Callable[[int, int], int] = random.randint,
) -> Path:
    """Return the sound file path for a named sound."""
    if sound_name in VARIANT_SOUNDS:
        return audio_dir / f"{sound_name}{variant_selector(1, 3)}.wav"
    return audio_dir / f"{sound_name}.wav"


def playback_backends(system_name: Optional[str] = None) -> list[list[str]]:
    """Return playback backends in preferred order for a platform."""
    system = (system_name or platform.system()).lower()
    if system == "darwin":
        return [["afplay"], ["paplay"], ["aplay"]]
    if system == "windows":
        return [["powershell"]]
    return [["paplay"], ["aplay"], ["afplay"]]


def play_sound(sound_name: str, audio_dir: Path = DEFAULT_AUDIO_DIR) -> None:
    """Play a named sound if its file and a backend are available."""
    sound_path = sound_file_path(sound_name, audio_dir)
    if not sound_path.exists():
        return
    play_sound_file(sound_path)


def play_sound_file(sound_path: Path) -> None:
    """Play a sound file using the first available platform backend."""
    for backend in playback_backends():
        if not shutil.which(backend[0]):
            continue

        if backend[0] == "powershell":
            subprocess.run(
                [
                    "powershell",
                    "-c",
                    f"(New-Object System.Media.SoundPlayer '{sound_path}').PlaySync()",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                backend + [str(sound_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        break
