"""Manajemen konfigurasi BellSound (SQLite)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from . import __version__
from .models import BellEvent, Profile, new_id
from .database import Database
from .security import hash_password

DEFAULT_PASSWORD = "bell123"

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

DEFAULT_SOUND = "./sounds/japan-bell.mp3"


def _default_profiles() -> Dict[str, dict]:
    """Buat profil default sesuai jadwal shift dengan istirahat khusus Jumat."""
    
    # Profil Normal - Semua hari dengan istirahat khusus Jumat
    # Shift 1: 08:00-17:00, Shift 2: 20:00-05:00
    normal_weekday = Profile(
        key="normal",
        name="Normal",
        color="#3B82F6",
        events=[
            # Shift 1 (Senin-Kamis, Sabtu-Minggu - normal)
            BellEvent(name="Masuk Shift 1", kind="masuk", time="08:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Coffebreak 1 Out", kind="kopi", time="10:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Coffebreak 1 In", kind="kopi", time="10:10", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat Out Shift 1", kind="istirahat", time="12:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat In Shift 1", kind="istirahat", time="13:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 1", kind="pulang", time="17:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            # Shift 1 Jumat khusus (11:30-13:30)
            BellEvent(name="Masuk Shift 1", kind="masuk", time="08:00", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(
                name="Istirahat Out Shift 1",
                kind="istirahat",
                time="11:30",
                days=[4],
                duration=None,
                loop=False,
                sound=DEFAULT_SOUND,
                cutback_time="11:30",
                reject_time="13:30",
            ),
            BellEvent(name="Istirahat In Shift 1", kind="istirahat", time="13:30", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 1", kind="pulang", time="17:00", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            # Shift 2 (Semua hari)
            BellEvent(name="Masuk Shift 2", kind="masuk", time="20:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat Out Shift 2", kind="istirahat", time="00:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat In Shift 2", kind="istirahat", time="01:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 2", kind="pulang", time="05:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
        ],
    )
    
    # Untuk hari Jumat - istirahat pukul 11:30-13:30
    normal_friday = Profile(
        key="normal_friday",
        name="Normal Jumat",
        color="#3B82F6",
        events=[
            BellEvent(name="Masuk Shift 1", kind="masuk", time="08:00", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            # Istirahat khusus Jumat 11:30-13:30
            BellEvent(
                name="Istirahat Out Shift 1",
                kind="istirahat",
                time="11:30",
                days=[4],
                duration=None,
                loop=False,
                sound=DEFAULT_SOUND,
                cutback_time="11:30",
                reject_time="13:30",
            ),
            BellEvent(name="Istirahat In Shift 1", kind="istirahat", time="13:30", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 1", kind="pulang", time="17:00", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            # Shift 2
            BellEvent(name="Masuk Shift 2", kind="masuk", time="20:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat Out Shift 2", kind="istirahat", time="00:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat In Shift 2", kind="istirahat", time="01:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 2", kind="pulang", time="05:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
        ],
    )
    
    # Profil Ramadhan - Semua hari dengan istirahat khusus Jumat
    # Shift 1: 07:00-16:00, Shift 2: 20:00-05:00
    ramadhan_weekday = Profile(
        key="ramadhan",
        name="Ramadhan",
        color="#10B981",
        events=[
            # Shift 1 (Senin-Kamis, Sabtu-Minggu - normal)
            BellEvent(name="Masuk Shift 1", kind="masuk", time="07:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat Out Shift 1", kind="istirahat", time="12:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat In Shift 1", kind="istirahat", time="13:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 1", kind="pulang", time="16:00", days=[0, 1, 2, 3, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            # Shift 1 Jumat khusus (11:30-13:30)
            BellEvent(name="Masuk Shift 1", kind="masuk", time="07:00", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(
                name="Istirahat Out Shift 1",
                kind="istirahat",
                time="11:30",
                days=[4],
                duration=None,
                loop=False,
                sound=DEFAULT_SOUND,
                cutback_time="11:30",
                reject_time="13:30",
            ),
            BellEvent(name="Istirahat In Shift 1", kind="istirahat", time="13:30", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 1", kind="pulang", time="16:00", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            # Shift 2 (Semua hari)
            BellEvent(name="Masuk Shift 2", kind="masuk", time="20:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat Out Shift 2", kind="istirahat", time="00:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat In Shift 2", kind="istirahat", time="01:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 2", kind="pulang", time="05:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
        ],
    )
    
    # Untuk hari Jumat - istirahat pukul 11:30-13:30
    ramadhan_friday = Profile(
        key="ramadhan_friday",
        name="Ramadhan Jumat",
        color="#10B981",
        events=[
            BellEvent(name="Masuk Shift 1", kind="masuk", time="07:00", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            # Istirahat khusus Jumat 11:30-13:30
            BellEvent(
                name="Istirahat Out Shift 1",
                kind="istirahat",
                time="11:30",
                days=[4],
                duration=None,
                loop=False,
                sound=DEFAULT_SOUND,
                cutback_time="11:30",
                reject_time="13:30",
            ),
            BellEvent(name="Istirahat In Shift 1", kind="istirahat", time="13:30", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 1", kind="pulang", time="16:00", days=[4], duration=None, loop=False, sound=DEFAULT_SOUND),
            # Shift 2
            BellEvent(name="Masuk Shift 2", kind="masuk", time="20:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat Out Shift 2", kind="istirahat", time="00:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Istirahat In Shift 2", kind="istirahat", time="01:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
            BellEvent(name="Pulang Shift 2", kind="pulang", time="05:00", days=[0, 1, 2, 3, 4, 5, 6], duration=None, loop=False, sound=DEFAULT_SOUND),
        ],
    )
    
    return {
        "normal": normal_weekday.to_dict(),
        "normal_friday": normal_friday.to_dict(),
        "ramadhan": ramadhan_weekday.to_dict(),
        "ramadhan_friday": ramadhan_friday.to_dict(),
    }


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
    """Pembungkus konfigurasi dengan SQLite."""

    def __init__(self, db: Database):
        self._db = db
        self._init_database()

    def _init_database(self):
        """Inisialisasi database dengan data default jika belum ada."""
        # Cek apakah ada data profil
        profiles = self._db.get_all_profiles()
        if not profiles:
            # Buat data default
            config = default_config()
            self._save_full_config(config)

    def _save_full_config(self, data: dict):
        """Simpan seluruh konfigurasi ke database."""
        # Simpan metadata
        self._db.set_metadata({
            "version": data.get("version", __version__),
        })
        # Simpan security
        security = data.get("security", {})
        self._db.set_security(security)
        # Simpan settings
        settings = data.get("settings", DEFAULT_SETTINGS)
        self._db.set_all_settings(settings)
        # Simpan profiles
        for key, profile_data in data.get("profiles", {}).items():
            self._db.set_profile(profile_data)
        # Set active profile
        active_profile = data.get("active_profile")
        if active_profile:
            self._db.set_setting("active_profile", active_profile)

    # ------------------------------------------------------------------ io
    @classmethod
    def load(cls) -> "Config":
        """Muat konfigurasi dari database SQLite."""
        db = Database()
        config = cls(db)
        return config

    def save(self) -> None:
        """Simpan konfigurasi ke database."""
        self._save_full_config(self._get_full_config())

    def _get_full_config(self) -> dict:
        """Dapatkan seluruh konfigurasi sebagai dictionary."""
        profiles_list = self._db.get_all_profiles()
        # Convert list of dicts to dict keyed by profile key
        profiles_dict = {p["key"]: p for p in profiles_list}
        return {
            "version": self._db.get_metadata("version", __version__),
            "security": self._db.get_security(),
            "settings": self._db.get_all_settings(),
            "profiles": profiles_dict,
            "active_profile": self._db.get_setting("active_profile"),
        }

    # ------------------------------------------------------------- settings
    @property
    def settings(self) -> dict:
        return self._db.get_all_settings()

    def get(self, key: str, default=None):
        return self._db.get_setting(key, default)

    def set(self, key: str, value) -> None:
        self._db.set_setting(key, value)

    @property
    def volume(self) -> float:
        try:
            return max(0.0, min(1.0, float(self.get("volume", 0.85))))
        except (TypeError, ValueError):
            return 0.85

    # ------------------------------------------------------------- profiles
    @property
    def active_profile_key(self) -> str:
        return self._db.get_setting("active_profile", "normal")

    @active_profile_key.setter
    def active_profile_key(self, key: str) -> None:
        if key in [p["key"] for p in self._db.get_all_profiles()]:
            self._db.set_setting("active_profile", key)

    def profile_keys(self) -> List[str]:
        return [p["key"] for p in self._db.get_all_profiles()]

    def iter_profiles(self) -> List[Profile]:
        profiles = []
        for raw in self._db.get_all_profiles():
            profiles.append(Profile.from_dict(raw))
        return profiles

    def get_profile(self, key: str) -> Optional[Profile]:
        raw = self._db.get_profile(key)
        if raw is None:
            return None
        return Profile.from_dict(raw)

    def set_profile(self, profile: Profile) -> None:
        self._db.set_profile(profile.to_dict())

    def add_profile(self, name: str) -> Profile:
        base = slugify(name)
        key = base
        counter = 2
        existing_keys = self.profile_keys()
        while key in existing_keys:
            key = f"{base}-{counter}"
            counter += 1
        color = PROFILE_COLORS[len(existing_keys) % len(PROFILE_COLORS)]
        profile = Profile(key=key, name=name, color=color, events=[])
        self.set_profile(profile)
        return profile

    def remove_profile(self, key: str) -> bool:
        return self._db.delete_profile(key)

    def duplicate_profile(self, key: str) -> Optional[Profile]:
        source = self.get_profile(key)
        if source is None:
            return None
        name = f"{source.name} (copy)"
        base = slugify(name)
        new_key = base
        counter = 2
        existing_keys = self.profile_keys()
        while new_key in existing_keys:
            new_key = f"{base}-{counter}"
            counter += 1
        clone = Profile(key=new_key, name=name, color=source.color, events=list(source.events))
        self.set_profile(clone)
        return clone

    # ------------------------------------------------------------- security
    @property
    def security(self) -> dict:
        return self._db.get_security()

    def set_password(self, password: str) -> None:
        self._db.set_security({"algorithm": "pbkdf2_sha256", **hash_password(password)})

    def active_profile(self) -> Optional[Profile]:
        return self.get_profile(self.active_profile_key)

    def next_event_id(self) -> str:
        return new_id()