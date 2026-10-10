"""Penjadwal bell berbasis waktu (dipanggil dari loop Tkinter tiap detik)."""

from __future__ import annotations

import datetime as dt
from typing import Callable, Optional, Tuple

from .config import Config
from .models import BellEvent, Profile, sort_events


class BellScheduler:
    def __init__(self, get_config: Callable[[], Config], on_trigger: Callable[[BellEvent, Profile, dt.datetime], None]):
        self._get_config = get_config
        self._on_trigger = on_trigger
        self._minute_key: Optional[str] = None
        self._fired: set = set()
        self._sequence = 0

    def tick(self, now: Optional[dt.datetime] = None) -> None:
        """Periksa apakah ada bell yang harus dibunyikan pada detik ini."""
        now = now or dt.datetime.now()
        config = self._get_config()
        profile = config.active_profile()
        if profile is None:
            return

        minute_key = now.strftime("%Y%m%d%H%M")
        if minute_key != self._minute_key:
            self._minute_key = minute_key
            self._fired = set()

        weekday = now.weekday()
        current = now.strftime("%H:%M")
        for event in list(profile.events):
            if not event.enabled or event.id in self._fired:
                continue
            if weekday not in event.days:
                continue
            if event.time != current:
                continue
            self._fired.add(event.id)
            self._sequence += 1
            try:
                self._on_trigger(event, profile, now)
            except Exception:
                pass

    def next_bell(self, now: Optional[dt.datetime] = None) -> Optional[Tuple[BellEvent, dt.datetime]]:
        """Cari bell berikutnya (event, waktu) dari profil aktif."""
        now = now or dt.datetime.now()
        config = self._get_config()
        profile = config.active_profile()
        if profile is None:
            return None

        best: Optional[Tuple[BellEvent, dt.datetime]] = None
        for event in profile.events:
            if not event.enabled:
                continue
            try:
                hour, minute = (int(part) for part in event.time.split(":"))
            except (ValueError, AttributeError):
                continue
            for offset in range(0, 8):
                day = (now + dt.timedelta(days=offset)).date()
                if day.weekday() not in event.days:
                    continue
                candidate = dt.datetime.combine(day, dt.time(hour, minute))
                if candidate < now:
                    continue
                if best is None or candidate < best[1]:
                    best = (event, candidate)
                break
        return best

    def today_bells(self, now: Optional[dt.datetime] = None):
        """Daftar bell yang berlaku hari ini, terurut berdasarkan jam."""
        now = now or dt.datetime.now()
        config = self._get_config()
        profile = config.active_profile()
        if profile is None:
            return []
        weekday = now.weekday()
        events = [e for e in profile.events if e.enabled and weekday in e.days]
        return sort_events(events)

    @property
    def sequence(self) -> int:
        return self._sequence
