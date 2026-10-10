"""Manajemen konfigurasi BellSound (JSON)."""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional

from . import __version__
from .models import BellEvent, Profile, new_id
from .paths import config_path
from .security import hash_password

DEFAULT_PASSWORD = "admin123"

DEFAULT_SETTINGS = {
    "volume": 0.85,
    "active_profile": "normal",
    "default_duration": 20,
    "default_loop": True,
    "lock_on_start": False,
    "start_minimized": False,
    "autostart": False,
    "repeat_guard": True,
}

PROFILE_COLORS = [
    "#3B82F6",
    "#10B981",
    "#F59E0B",
    "#8B5CF6",
    "#EF4444",
    "#14B8A6",
    "#EC4899",
    "#F97316",
]


def _default_profiles() -> Dict[str, dict]:
    normal = Profile(
        key="normal",
        name="Normal",
        color="#3B82F6",
        events=[
            BellEvent(name="Bell Masuk", kind="masuk", time="07:00", days=[0, 1, 2, 3, 4], duration=20),
            BellEvent(name="Istirahat 1", kind="istirahat", time="09:30", days=[0, 1, 2, 3, 4], duration=30),
            BellEvent(name="Kopi Break", kind="kopi", time="10:00", days=[0, 1, 2, 3, 4], duration=20),
            BellEvent(name="Istirahat 2", kind="istirahat", time="12:00", days=[0, 1, 2, 3, 4], duration=30),
            BellEvent(name="Bell Pulang", kind="pulang", time="14:00", days=[0, 1, 2, 3, 4], duration=30),
        ],
    )
    ramadhan = Profile(
        key="ramadhan",
        name="Ramadhan",
        color="#10B981",
        events=[
            BellEvent(name="Bell Masuk", kind="masuk", time="07:30", days=[0, 1, 2, 3, 4], duration=20),
            BellEvent(name="Istirahat", kind="istirahat", time="12:00", days=[0, 1, 2, 3, 4], duration=30),
            BellEvent(name="Bell Pulang", kind="pulang", time="13:30", days=[0, 1, 2, 3, 4], duration=20),
        ],
    )
    return {"normal": normal.to_dict(), "ramadhan": ramadhan.to_dict()}


def default_config() -> dict:
    return {
        "version": __version__,
        "security": {"algorithm": "pbkdf2_sha256", **hash_password(DEFAULT_PASSWORD)},
        "settings": dict(DEFAULT_SETTINGS),
        "profiles": _default_profiles(),
        "active_profile": "normal",
    }


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "profil"


class Config:
    """Pembungkus konfigurasi dengan baca/tulis atomik."""

    def __init__(self, data: dict):
        self.data = data
        self._normalize()

    # ------------------------------------------------------------------ io
    @classmethod
    def load(cls) -> "Config":
        path = config_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return cls(data)
            except (json.JSONDecodeError, OSError):
                try:
                    path.replace(path.with_suffix(".rusak.json"))
                except OSError:
                    pass
        config = cls(default_config())
        config.save()
        return config

    def save(self) -> None:
        path = config_path()
        tmp = path.with_suffix(".tmp")
        # Simpan salinan versi sebelumnya sebagai cadangan (1 tingkat undo),
        # supaya perubahan yang tidak diinginkan tidak menghilangkan jadwal.
        if path.exists():
            try:
                previous = path.read_text(encoding="utf-8")
            except OSError:
                previous = None
            if previous and previous != json.dumps(self.data, indent=2, ensure_ascii=False):
                try:
                    path.with_name(path.name + ".bak").write_text(previous, encoding="utf-8")
                except OSError:
                    pass
        tmp.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(tmp, path)

    # ------------------------------------------------------------ normalize
    def _normalize(self) -> None:
        self.data.setdefault("version", __version__)
        self.data.setdefault("security", {"algorithm": "pbkdf2_sha256", **hash_password(DEFAULT_PASSWORD)})
        settings = self.data.setdefault("settings", {})
        for key, value in DEFAULT_SETTINGS.items():
            settings.setdefault(key, value)
        profiles = self.data.get("profiles")
        if not isinstance(profiles, dict) or not profiles:
            self.data["profiles"] = _default_profiles()
        # pastikan tiap profil punya key
        for key, value in list(self.data["profiles"].items()):
            if not isinstance(value, dict):
                del self.data["profiles"][key]
                continue
            value.setdefault("key", key)
            value.setdefault("name", key.title())
            value.setdefault("color", "#3B82F6")
            value.setdefault("events", [])
        active = self.data.get("active_profile")
        if active not in self.data["profiles"]:
            self.data["active_profile"] = next(iter(self.data["profiles"]))

    # ------------------------------------------------------------- settings
    @property
    def settings(self) -> dict:
        return self.data["settings"]

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def set(self, key: str, value) -> None:
        self.settings[key] = value

    @property
    def volume(self) -> float:
        try:
            return max(0.0, min(1.0, float(self.settings.get("volume", 0.85))))
        except (TypeError, ValueError):
            return 0.85

    # ------------------------------------------------------------- profiles
    @property
    def active_profile_key(self) -> str:
        return self.data.get("active_profile")

    @active_profile_key.setter
    def active_profile_key(self, key: str) -> None:
        if key in self.data["profiles"]:
            self.data["active_profile"] = key

    def profile_keys(self) -> List[str]:
        return list(self.data["profiles"].keys())

    def iter_profiles(self) -> List[Profile]:
        return [Profile.from_dict(self.data["profiles"][k]) for k in self.profile_keys()]

    def get_profile(self, key: str) -> Optional[Profile]:
        raw = self.data["profiles"].get(key)
        if raw is None:
            return None
        return Profile.from_dict(raw)

    def set_profile(self, profile: Profile) -> None:
        self.data["profiles"][profile.key] = profile.to_dict()

    def add_profile(self, name: str) -> Profile:
        base = slugify(name)
        key = base
        counter = 2
        while key in self.data["profiles"]:
            key = f"{base}-{counter}"
            counter += 1
        color = PROFILE_COLORS[len(self.data["profiles"]) % len(PROFILE_COLORS)]
        profile = Profile(key=key, name=name, color=color, events=[])
        self.set_profile(profile)
        return profile

    def remove_profile(self, key: str) -> bool:
        if len(self.data["profiles"]) <= 1:
            return False
        if key not in self.data["profiles"]:
            return False
        del self.data["profiles"][key]
        if self.data["active_profile"] == key:
            self.data["active_profile"] = next(iter(self.data["profiles"]))
        return True

    def duplicate_profile(self, key: str) -> Optional[Profile]:
        source = self.get_profile(key)
        if source is None:
            return None
        name = f"{source.name} (copy)"
        base = slugify(name)
        new_key = base
        counter = 2
        while new_key in self.data["profiles"]:
            new_key = f"{base}-{counter}"
            counter += 1
        clone = Profile(key=new_key, name=name, color=source.color, events=list(source.events))
        self.set_profile(clone)
        return clone

    # ------------------------------------------------------------- security
    @property
    def security(self) -> dict:
        return self.data["security"]

    def set_password(self, password: str) -> None:
        self.data["security"] = {"algorithm": "pbkdf2_sha256", **hash_password(password)}

    def active_profile(self) -> Optional[Profile]:
        return self.get_profile(self.active_profile_key)

    def next_event_id(self) -> str:
        return new_id()
