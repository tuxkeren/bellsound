"""Dialog tambah/edit jadwal bell."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from typing import Dict, Optional

from ..models import (
    DAY_LABELS,
    DURATION_CHOICES,
    KIND_COLORS,
    KIND_LABELS,
    KINDS,
    BellEvent,
)
from ..paths import resolve_sound_path
from .dialogs import Modal, make_entry
from .theme import Palette, ui_font
from .widgets import RoundedButton, Toggle


class EventDialog(Modal):
    def __init__(self, parent, *, event: Optional[BellEvent], defaults: dict, player):
        super().__init__(parent, "Jadwal Bell", width=580, height=680)
        self._player = player
        self.event = BellEvent.from_dict(event.to_dict()) if event else BellEvent(
            duration=defaults.get("duration", 20),
            loop=defaults.get("loop", True),
            volume=defaults.get("volume"),
        )
        self._sound_var = tk.StringVar(value=self.event.sound or "")
        self._enabled = tk.BooleanVar(value=self.event.enabled)
        self._loop = tk.BooleanVar(value=self.event.loop)
        self._selected_kind = self.event.kind
        self._selected_days = set(self.event.days)
        self._selected_duration = self.event.duration
        self._kind_buttons: Dict[str, RoundedButton] = {}
        self._day_buttons: Dict[int, RoundedButton] = {}
        self._duration_buttons: Dict[str, RoundedButton] = {}

        self._build()

    # ---------------------------------------------------------------- build
    def _build(self):
        container = tk.Frame(self, bg=Palette.SURFACE)
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Nama
        self._section(container, "Nama Bell")
        self.name_entry = make_entry(container, font=ui_font(12))
        self.name_entry.insert(0, self.event.name)
        self.name_entry.pack(fill="x", ipady=8, pady=(0, 12))

        # Kategori
        self._section(container, "Kategori")
        kind_row = tk.Frame(container, bg=Palette.SURFACE)
        kind_row.pack(fill="x", pady=(0, 12))
        for kind in KINDS:
            button = RoundedButton(
                kind_row,
                KIND_LABELS[kind],
                lambda k=kind: self._select_kind(k),
                bg=Palette.SURFACE_2,
                fg=Palette.TEXT_MUTED,
                hover_bg=Palette.SURFACE_3,
                parent_bg=Palette.SURFACE,
                height=34,
                radius=8,
                padx=12,
                font=ui_font(10, "bold"),
            )
            button.pack(side="left", padx=(0, 6))
            self._kind_buttons[kind] = button
        self._select_kind(self._selected_kind, initial=True)

        # Waktu + volume dalam satu baris
        row = tk.Frame(container, bg=Palette.SURFACE)
        row.pack(fill="x", pady=(0, 12))
        time_box = tk.Frame(row, bg=Palette.SURFACE)
        time_box.pack(side="left")
        self._section(time_box, "Waktu")
        spinner = tk.Frame(time_box, bg=Palette.SURFACE)
        spinner.pack(anchor="w")
        self.hour = self._spin(spinner, 0, 23, self.event.time.split(":")[0])
        tk.Label(spinner, text=":", bg=Palette.SURFACE, fg=Palette.TEXT, font=ui_font(18, "bold")).pack(side="left", padx=4)
        self.minute = self._spin(spinner, 0, 59, self.event.time.split(":")[1])

        vol_box = tk.Frame(row, bg=Palette.SURFACE)
        vol_box.pack(side="left", fill="x", expand=True, padx=(30, 0))
        self._section(vol_box, "Volume")
        vol_row = tk.Frame(vol_box, bg=Palette.SURFACE)
        vol_row.pack(fill="x")
        current_volume = self.event.volume if self.event.volume is not None else 0.85
        self.volume = tk.Scale(
            vol_row,
            from_=0,
            to=100,
            orient="horizontal",
            bg=Palette.SURFACE,
            fg=Palette.TEXT,
            troughcolor=Palette.SURFACE_3,
            activebackground=Palette.PRIMARY,
            highlightthickness=0,
            bd=0,
            showvalue=False,
            sliderrelief="flat",
            length=160,
            command=self._on_volume,
        )
        self.volume.set(int(current_volume * 100))
        self.volume.pack(side="left")
        self.volume_label = tk.Label(vol_row, text=f"{int(current_volume * 100)}%", bg=Palette.SURFACE,
                                     fg=Palette.TEXT_MUTED, font=ui_font(10, "bold"), width=4)
        self.volume_label.pack(side="left", padx=(6, 0))

        # Hari
        self._section(container, "Hari Aktif")
        day_row = tk.Frame(container, bg=Palette.SURFACE)
        day_row.pack(fill="x", pady=(0, 12))
        for index, label in enumerate(DAY_LABELS):
            button = RoundedButton(
                day_row,
                label,
                lambda i=index: self._toggle_day(i),
                bg=Palette.SURFACE_2,
                fg=Palette.TEXT_MUTED,
                hover_bg=Palette.SURFACE_3,
                parent_bg=Palette.SURFACE,
                width=52,
                height=34,
                radius=8,
                padx=0,
                font=ui_font(10, "bold"),
            )
            button.pack(side="left", padx=(0, 6))
            self._day_buttons[index] = button
        self._refresh_days()

        # File suara
        self._section(container, "File Suara (MP3)")
        sound_row = tk.Frame(container, bg=Palette.SURFACE)
        sound_row.pack(fill="x", pady=(0, 12))
        self.sound_entry = make_entry(sound_row, font=ui_font(10))
        self.sound_entry.configure(textvariable=self._sound_var, state="readonly")
        self.sound_entry.pack(side="left", fill="x", expand=True, ipady=7)
        RoundedButton(sound_row, "Pilih", self._choose_file, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=36,
                      font=ui_font(10, "bold")).pack(side="left", padx=(8, 0))
        self.preview_button = RoundedButton(sound_row, "Putar", self._preview, bg=Palette.SUCCESS,
                                            parent_bg=Palette.SURFACE, height=36, font=ui_font(10, "bold"))
        self.preview_button.pack(side="left", padx=(6, 0))
        RoundedButton(sound_row, "Stop", self._stop, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=36,
                      font=ui_font(10, "bold")).pack(side="left", padx=(6, 0))

        # Durasi
        self._section(container, "Durasi Pemutaran")
        duration_row = tk.Frame(container, bg=Palette.SURFACE)
        duration_row.pack(fill="x", pady=(0, 6))
        for label, value in DURATION_CHOICES:
            key = "full" if value is None else str(value)
            button = RoundedButton(
                duration_row,
                label,
                lambda v=value: self._select_duration(v),
                bg=Palette.SURFACE_2,
                fg=Palette.TEXT_MUTED,
                hover_bg=Palette.SURFACE_3,
                parent_bg=Palette.SURFACE,
                height=34,
                radius=8,
                padx=12,
                font=ui_font(10, "bold"),
            )
            button.pack(side="left", padx=(0, 6))
            self._duration_buttons[key] = button
        self._refresh_duration()

        # Loop + aktif
        option_row = tk.Frame(container, bg=Palette.SURFACE)
        option_row.pack(fill="x", pady=(10, 0))
        self.loop_toggle = self._option(option_row, "Ulangi file (loop) sampai durasi tercapai",
                                        self._loop, self._on_loop)
        self.enabled_toggle = self._option(option_row, "Aktifkan jadwal ini", self._enabled)

        # Cutback/Reject time for Friday breaks
        break_row = tk.Frame(container, bg=Palette.SURFACE)
        break_row.pack(fill="x", pady=(8, 0))
        tk.Label(break_row, text="Cutback/Reject (Jumat):", bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                 font=ui_font(10), anchor="w").pack(anchor="w")
        
        cutback_frame = tk.Frame(break_row, bg=Palette.SURFACE)
        cutback_frame.pack(fill="x", pady=(4, 0))
        tk.Label(cutback_frame, text="Keluar istirahat:", bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(9)).pack(side="left")
        cb_parts = (self.event.cutback_time or "").split(":") if self.event.cutback_time else None
        self.cutback_hour = self._spin(cutback_frame, 0, 23, cb_parts[0] if cb_parts and cb_parts[0] else "11")
        tk.Label(cutback_frame, text=":", bg=Palette.SURFACE, fg=Palette.TEXT, font=ui_font(18, "bold")).pack(side="left", padx=4)
        self.cutback_minute = self._spin(cutback_frame, 0, 59, cb_parts[1] if cb_parts and len(cb_parts) > 1 else "30")

        reject_frame = tk.Frame(break_row, bg=Palette.SURFACE)
        reject_frame.pack(fill="x", pady=(4, 0))
        tk.Label(reject_frame, text="Masuk kembali:", bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(9)).pack(side="left")
        rj_parts = (self.event.reject_time or "").split(":") if self.event.reject_time else None
        self.reject_hour = self._spin(reject_frame, 0, 23, rj_parts[0] if rj_parts and rj_parts[0] else "13")
        tk.Label(reject_frame, text=":", bg=Palette.SURFACE, fg=Palette.TEXT, font=ui_font(18, "bold")).pack(side="left", padx=4)
        self.reject_minute = self._spin(reject_frame, 0, 59, rj_parts[1] if rj_parts and len(rj_parts) > 1 else "30")

        # Buttons
        buttons = tk.Frame(container, bg=Palette.SURFACE)
        buttons.pack(fill="x", side="bottom", pady=(16, 0))
        RoundedButton(buttons, "Batal", self.cancel, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=40).pack(side="right")
        RoundedButton(buttons, "Simpan", self._submit, bg=Palette.PRIMARY,
                      parent_bg=Palette.SURFACE, height=40).pack(side="right", padx=(0, 10))

        self.bind("<Escape>", lambda e: self._stop())
        self.name_entry.focus_set()

    def _section(self, parent, text: str):
        tk.Label(parent, text=text.upper(), bg=Palette.SURFACE, fg=Palette.TEXT_DIM,
                 font=ui_font(9, "bold"), anchor="w").pack(fill="x", pady=(0, 4))

    def _spin(self, parent, start, end, value):
        spin = tk.Spinbox(
            parent,
            from_=start,
            to=end,
            width=3,
            wrap=True,
            format="%02.0f",
            font=ui_font(18, "bold"),
            bg=Palette.SURFACE_2,
            fg=Palette.TEXT,
            buttonbackground=Palette.SURFACE_3,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=Palette.BORDER,
            highlightcolor=Palette.PRIMARY,
            justify="center",
        )
        try:
            spin.configure(insertbackground=Palette.TEXT)
        except tk.TclError:
            pass
        spin.delete(0, "end")
        spin.insert(0, value)
        spin.pack(side="left", ipady=4)
        return spin

    def _option(self, parent, text, variable, command=None):
        row = tk.Frame(parent, bg=Palette.SURFACE)
        row.pack(fill="x", pady=3)
        toggle = Toggle(row, variable=variable, command=lambda v: command and command(v),
                        parent_bg=Palette.SURFACE)
        toggle.pack(side="left")
        tk.Label(row, text=text, bg=Palette.SURFACE, fg=Palette.TEXT, font=ui_font(11)).pack(side="left", padx=(10, 0))
        return toggle

    # -------------------------------------------------------------- handlers
    def _select_kind(self, kind: str, initial: bool = False):
        self._selected_kind = kind
        for key, button in self._kind_buttons.items():
            if key == kind:
                button.set_colors(KIND_COLORS.get(key, Palette.PRIMARY), Palette.WHITE)
            else:
                button.set_colors(Palette.SURFACE_2, Palette.TEXT_MUTED)
        if not initial and self.name_entry.get().strip() in ("", "Bell"):
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, KIND_LABELS[kind])

    def _toggle_day(self, index: int):
        if index in self._selected_days:
            self._selected_days.discard(index)
        else:
            self._selected_days.add(index)
        self._refresh_days()

    def _refresh_days(self):
        for index, button in self._day_buttons.items():
            if index in self._selected_days:
                button.set_colors(Palette.PRIMARY, Palette.WHITE)
            else:
                button.set_colors(Palette.SURFACE_2, Palette.TEXT_MUTED)

    def _select_duration(self, value):
        self._selected_duration = value
        self._refresh_duration()

    def _refresh_duration(self):
        selected_key = "full" if self._selected_duration is None else str(self._selected_duration)
        for key, button in self._duration_buttons.items():
            if key == selected_key:
                button.set_colors(Palette.PURPLE, Palette.WHITE)
            else:
                button.set_colors(Palette.SURFACE_2, Palette.TEXT_MUTED)

    def _on_loop(self, value: bool):
        if self._selected_duration is None:
            self._loop.set(False)
            self.loop_toggle.set(False)

    def _on_volume(self, value):
        self.volume_label.configure(text=f"{int(float(value))}%")

    def _choose_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Pilih file suara",
            filetypes=[("Audio", "*.mp3 *.wav *.ogg *.flac *.m4a"), ("Semua file", "*.*")],
        )
        if path:
            self._sound_var.set(path)

    def _preview(self):
        path = self._sound_var.get()
        if not path:
            return
        resolved_path = resolve_sound_path(path)
        volume = float(self.volume.get()) / 100.0
        self._player.play(
            resolved_path,
            duration=self._selected_duration,
            loop=bool(self._loop.get()),
            volume=volume,
        )

    def _stop(self):
        self._player.stop()

    def _submit(self):
        name = self.name_entry.get().strip() or KIND_LABELS.get(self._selected_kind, "Bell")
        try:
            hour = int(float(self.hour.get()))
            minute = int(float(self.minute.get()))
        except ValueError:
            return
        hour = max(0, min(23, hour))
        minute = max(0, min(59, minute))
        if not self._selected_days:
            self._selected_days = {0, 1, 2, 3, 4}

        self.event.name = name
        self.event.kind = self._selected_kind
        self.event.time = f"{hour:02d}:{minute:02d}"
        self.event.days = sorted(self._selected_days)
        self.event.sound = self._sound_var.get()
        self.event.duration = self._selected_duration
        self.event.loop = bool(self._loop.get()) and self._selected_duration is not None
        self.event.volume = float(self.volume.get()) / 100.0
        self.event.enabled = bool(self._enabled.get())
        
        # Set cutback/reject times for Friday breaks
        try:
            cb_hour = int(float(self.cutback_hour.get()))
            cb_min = int(float(self.cutback_minute.get()))
            rj_hour = int(float(self.reject_hour.get()))
            rj_min = int(float(self.reject_minute.get()))
            self.event.cutback_time = f"{cb_hour:02d}:{cb_min:02d}"
            self.event.reject_time = f"{rj_hour:02d}:{rj_min:02d}"
        except (ValueError, TypeError):
            pass

        self._player.stop()
        self._result = self.event
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
