"""Penentuan lokasi file data aplikasi (config, log, riwayat).

Data disimpan di folder konfigurasi user agar aman ketika aplikasi di-install
di Program Files (Windows) atau /opt (Linux). Mode portable dapat diaktifkan
dengan membuat file bernama ``bellsound.portable`` di samping executable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import APP_NAME


def is_frozen() -> bool:
    """True jika aplikasi berjalan sebagai hasil build (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """Folder aplikasi (lokasi exe ketika di-build, root proyek saat dev)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """Folder penyimpanan data (config, log, riwayat)."""
    env = os.environ.get("BELLSOUND_DATA_DIR")
    if env:
        path = Path(env).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    if (app_dir() / "bellsound.portable").exists():
        path = app_dir() / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        path = base / APP_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        path = base / APP_NAME

    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return data_dir() / "config.json"


def history_path() -> Path:
    return data_dir() / "history.json"


def log_path() -> Path:
    return data_dir() / "bellsound.log"


def sound_path(filename: str = "japan-bell.mp3") -> Path:
    """Path ke file sound default (relative path konversi ke absolute)."""
    return app_dir() / "sounds" / filename


def resolve_sound_path(path: str) -> str:
    """Konversi path sound (relatif atau absolut) ke absolute path."""
    if not path:
        return ""
    p = Path(path)
    if p.is_absolute():
        return str(p.resolve())
    # Path relatif - konversi ke absolute relatif ke app_dir
    return str((app_dir() / path).resolve())
