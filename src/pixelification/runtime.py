from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict, dataclass
from pathlib import Path


APP_NAME = "pixelification"
CONFIG_FILENAME = "runtime-config.json"


@dataclass(slots=True)
class RuntimeConfig:
    host_os: str
    hardware_acceleration_available: bool
    backend: str
    audio_settings: dict | None = None


def _config_root() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def config_path() -> Path:
    return _config_root() / CONFIG_FILENAME


def load_or_create_runtime_config(hardware_acceleration_available: bool) -> RuntimeConfig:
    path = config_path()
    current = RuntimeConfig(
        host_os=platform.system(),
        hardware_acceleration_available=hardware_acceleration_available,
        backend="cupy" if hardware_acceleration_available else "cpu",
    )

    stored_audio = None
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                stored_audio = data.get("audio_settings")
                if not isinstance(stored_audio, dict):
                    stored_audio = None
                stored = RuntimeConfig(
                    host_os=str(data.get("host_os", current.host_os)),
                    hardware_acceleration_available=bool(
                        data.get("hardware_acceleration_available", current.hardware_acceleration_available)
                    ),
                    backend=str(data.get("backend", current.backend)),
                    audio_settings=stored_audio,
                )
                if (
                    stored.host_os == current.host_os
                    and stored.hardware_acceleration_available == current.hardware_acceleration_available
                    and stored.backend == current.backend
                ):
                    return stored
        except Exception:
            stored_audio = None

    current.audio_settings = stored_audio
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(current), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return current


def save_audio_settings(audio_settings: dict) -> None:
    """Merge new audio settings into the persisted runtime config."""
    path = config_path()
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
    data["audio_settings"] = audio_settings
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
