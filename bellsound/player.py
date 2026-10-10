"""Pemutaran audio MP3 menggunakan pygame(-ce).

Fitur:
- Memutar file penuh atau membatasi durasi (20/30/60 detik).
- Opsi loop sehingga file pendek diulang sampai durasi tercapai.
- Volume global/per-event.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Callable, Optional


class AudioPlayer:
    def __init__(self, on_error: Optional[Callable[[str], None]] = None):
        self._pygame = None
        self._ready = False
        self.error: Optional[str] = None
        self._on_error = on_error
        self._lock = threading.RLock()
        self._timer: Optional[threading.Timer] = None
        self._volume = 0.85
        self._current: Optional[dict] = None
        self._on_finished: Optional[Callable[[], None]] = None
        self._generation = 0

    # ------------------------------------------------------------------ init
    def init(self) -> bool:
        try:
            import pygame  # type: ignore

            self._pygame = pygame
            try:
                pygame.mixer.pre_init(44100, -16, 2, 2048)
                pygame.mixer.init()
            except pygame.error:
                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
                pygame.mixer.init()
            self._ready = True
            self.error = None
        except Exception as exc:  # pragma: no cover - tergantung lingkungan
            self._ready = False
            self.error = str(exc)
        return self._ready

    @property
    def available(self) -> bool:
        return self._ready

    def set_on_error(self, callback: Callable[[str], None]) -> None:
        self._on_error = callback

    def _fail(self, message: str) -> None:
        self.error = message
        if self._on_error:
            try:
                self._on_error(message)
            except Exception:
                pass

    def _not_ready_message(self) -> str:
        """Pesan error saat audio tidak siap, selengkap mungkin.

        Jika init() gagal karena sebab tertentu (mis. pygame belum terpasang
        pada interpreter yang dipakai), tampilkan penyebab aslinya, bukan
        hanya "perangkat tidak terdeteksi"."""
        detail = (self.error or "").strip()
        if detail:
            detail = detail.replace("\n", " ").strip()
            return f"Audio tidak tersedia: {detail}"
        return "Audio tidak tersedia. Cek speaker/perangkat suara."

    # ---------------------------------------------------------------- volume
    def set_volume(self, volume: float) -> None:
        try:
            volume = max(0.0, min(1.0, float(volume)))
        except (TypeError, ValueError):
            volume = 0.85
        self._volume = volume
        if self._ready and self._pygame:
            try:
                self._pygame.mixer.music.set_volume(volume)
            except Exception:
                pass

    @property
    def volume(self) -> float:
        return self._volume

    # ------------------------------------------------------------ playback
    def play(
        self,
        path: str,
        duration: Optional[int] = None,
        loop: bool = False,
        volume: Optional[float] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> bool:
        with self._lock:
            self._cancel_timer()
            self._generation += 1
            generation = self._generation

            if not self._ready or not self._pygame:
                self._fail(self._not_ready_message())
                return False
            if not path:
                self._fail("Belum ada file suara yang dipilih.")
                return False
            if not os.path.isfile(path):
                self._fail(f"File suara tidak ditemukan:\n{path}")
                return False

            try:
                pygame = self._pygame
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                vol = self._volume if volume is None else max(0.0, min(1.0, float(volume)))
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(loops=-1 if loop else 0)
            except Exception as exc:
                self._fail(f"Gagal memutar file:\n{exc}")
                return False

            self._current = {
                "path": path,
                "duration": duration,
                "loop": loop,
                "started": time.time(),
            }
            self._on_finished = on_finished
            if duration:
                self._timer = threading.Timer(duration, self._auto_stop, args=(generation,))
                self._timer.daemon = True
                self._timer.start()
            elif on_finished:
                self._watch_finish(generation)
            return True

    def _watch_finish(self, generation: int) -> None:
        def worker():
            while True:
                time.sleep(0.25)
                with self._lock:
                    if generation != self._generation:
                        return
                    if not self.is_playing():
                        callback = self._on_finished
                        self._current = None
                        self._on_finished = None
                if callback:
                    try:
                        callback()
                    except Exception:
                        pass
                return

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _auto_stop(self, generation: int) -> None:
        with self._lock:
            if generation != self._generation:
                return
            callback = self._on_finished
            self._on_finished = None
        self.stop(notify=False)
        if callback:
            try:
                callback()
            except Exception:
                pass

    def stop(self, notify: bool = True) -> None:
        with self._lock:
            self._cancel_timer()
            self._generation += 1
            if self._ready and self._pygame:
                try:
                    self._pygame.mixer.music.stop()
                except Exception:
                    pass
            self._current = None
            callback = self._on_finished if notify else None
            self._on_finished = None
        if callback:
            try:
                callback()
            except Exception:
                pass

    def _cancel_timer(self) -> None:
        if self._timer:
            try:
                self._timer.cancel()
            except Exception:
                pass
            self._timer = None

    # --------------------------------------------------------------- status
    def is_playing(self) -> bool:
        if not self._ready or not self._pygame:
            return False
        try:
            return bool(self._pygame.mixer.music.get_busy())
        except Exception:
            return False

    def current(self) -> Optional[dict]:
        return self._current

    def elapsed(self) -> float:
        if not self._current:
            return 0.0
        return time.time() - self._current["started"]
