"""Model data BellSound: profil (jenis bell) dan jadwal bell."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# Kategori bell
KINDS = ["masuk", "istirahat", "kopi", "pulang", "lain"]
KIND_LABELS = {
    "masuk": "Bell Masuk",
    "istirahat": "Bell Istirahat",
    "kopi": "Kopi Break",
    "pulang": "Bell Pulang",
    "lain": "Lainnya",
}
KIND_COLORS = {
    "masuk": "#3B82F6",
    "istirahat": "#F59E0B",
    "kopi": "#8B5CF6",
    "pulang": "#EF4444",
    "lain": "#14B8A6",
}

# Senin = 0 ... Minggu = 6 (mengikuti datetime.weekday())
DAY_LABELS = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
DAY_FULL = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# Pilihan durasi pemutaran bell
DURATION_CHOICES = [
    ("20 detik", 20),
    ("30 detik", 30),
    ("60 detik", 60),
    ("Full file", None),
]


def duration_label(duration: Optional[int]) -> str:
    if duration is None:
        return "Full"
    return f"{duration} detik"


def new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class BellEvent:
    """Satu jadwal bell."""

    id: str = field(default_factory=new_id)
    name: str = "Bell"
    kind: str = "masuk"
    time: str = "07:00"
    days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    sound: str = ""
    duration: Optional[int] = 20
    loop: bool = True
    volume: Optional[float] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BellEvent":
        kind = data.get("kind", "masuk")
        if kind not in KINDS:
            kind = "lain"
        days = []
        for value in data.get("days", [0, 1, 2, 3, 4]):
            try:
                value = int(value)
            except (TypeError, ValueError):
                continue
            if 0 <= value <= 6:
                days.append(value)
        if not days:
            days = [0, 1, 2, 3, 4]
        duration = data.get("duration", 20)
        if duration is not None:
            duration = int(duration)
        return cls(
            id=str(data.get("id") or new_id()),
            name=str(data.get("name", "Bell")),
            kind=kind,
            time=str(data.get("time", "07:00")),
            days=sorted(set(days)),
            sound=str(data.get("sound", "")),
            duration=duration,
            loop=bool(data.get("loop", True)),
            volume=data.get("volume"),
            enabled=bool(data.get("enabled", True)),
        )


def event_time_key(event):
    """Kunci urut berdasarkan jam (HH:MM) — bukan jenis bell.

    Dibandingkan sebagai angka (jam, menit) supaya tetap benar walau ada
    nilai jam yang tidak zero-padded. Jam tidak valid ditaruh paling akhir.
    """
    raw = (event.time or "").strip()
    try:
        hour, minute = raw.split(":")
        return (int(hour), int(minute))
    except (ValueError, AttributeError):
        return (24, 0)


def sort_events(events):
    """Urutkan daftar BellEvent menaik berdasarkan jam."""
    return sorted(events, key=event_time_key)


@dataclass
class Profile:
    """Sekumpulan jadwal bell (jenis bell: Normal, Ramadhan, dst)."""

    key: str
    name: str
    color: str = "#3B82F6"
    events: List[BellEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "color": self.color,
            "events": [event.to_dict() for event in sort_events(self.events)],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        return cls(
            key=str(data.get("key")),
            name=str(data.get("name", data.get("key", "Profil"))),
            color=str(data.get("color", "#3B82F6")),
            events=[BellEvent.from_dict(e) for e in data.get("events", [])],
        )
