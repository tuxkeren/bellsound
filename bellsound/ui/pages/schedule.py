"""Halaman Jadwal: kelola daftar bell untuk setiap jenis bell (profil)."""

from __future__ import annotations

import os
import tkinter as tk

from ...models import DAY_LABELS, KIND_COLORS, KIND_LABELS, duration_label, sort_events
from ..dialogs import ConfirmDialog
from ..event_dialog import EventDialog
from ..theme import Palette, ui_font
from ..widgets import Badge, Dropdown, ElidedLabel, RoundedButton, RoundedFrame, ScrollableFrame, Toggle
from .base import BasePage


class SchedulePage(BasePage):
    name = "schedule"
    label = "Jadwal Bell"
    icon = "\U0001F4C5"

    def build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._profile_key = self.app.cfg.active_profile_key
        self._rows = {}      # event.id -> dict referensi widget baris
        self._order = []     # urutan id baris yang sedang tampil
        self._signature = None  # tanda tangan data; untuk hindari bangun ulang sia-sia

        header = tk.Frame(self, bg=Palette.BG)
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 8))
        header.columnconfigure(0, weight=1)
        title = tk.Frame(header, bg=Palette.BG)
        title.grid(row=0, column=0, sticky="w")
        tk.Label(title, text="Jadwal Bell", bg=Palette.BG, fg=Palette.TEXT,
                 font=ui_font(20, "bold")).pack(anchor="w")
        tk.Label(title, text="Atur jam, hari, file suara, dan durasi untuk setiap bel.",
                 bg=Palette.BG, fg=Palette.TEXT_MUTED, font=ui_font(10)).pack(anchor="w")

        controls = tk.Frame(header, bg=Palette.BG)
        controls.grid(row=0, column=1, sticky="e")
        tk.Label(controls, text="Jenis bell", bg=Palette.BG, fg=Palette.TEXT_MUTED,
                 font=ui_font(9, "bold")).pack(side="left", padx=(0, 6))
        self.profile_dropdown = Dropdown(controls, text="", command=self._on_profile_change,
                                         parent_bg=Palette.BG)
        self.profile_dropdown.pack(side="left", padx=(0, 12))
        RoundedButton(controls, "Tambah Bell", self._add_event, icon="\uFF0B", bg=Palette.PRIMARY,
                      parent_bg=Palette.BG, height=42).pack(side="left")

        self.scroll = ScrollableFrame(self, bg=Palette.BG)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 18))

    # ------------------------------------------------------------- helpers
    def _on_profile_change(self, key):
        self._profile_key = key
        self.refresh()

    def _profile(self):
        return self.app.cfg.get_profile(self._profile_key)

    def refresh(self):
        # dropdown opsi
        options = []
        for profile in self.app.cfg.iter_profiles():
            options.append((profile.name, profile.key))
        self.profile_dropdown.set_options(options)
        for label, value in options:
            if value == self._profile_key:
                self.profile_dropdown.set_text(label)
                break

        profile = self._profile()
        signature = (self._profile_key, self._profile_signature(profile))
        if signature == self._signature:
            # Data tidak berubah: jangan bangun ulang baris (hemat waktu).
            return

        for child in self.scroll.inner.winfo_children():
            child.destroy()
        self._rows = {}
        self._order = []
        self._signature = signature
        if profile is None:
            return
        if not profile.events:
            self._show_empty_state()
            return
        for event in self._sorted_events(profile):
            self._event_row(profile, event)
        self._order = [e.id for e in self._sorted_events(profile)]

    def _profile_signature(self, profile):
        if profile is None:
            return None
        return tuple(
            (e.id, e.time, e.name, tuple(e.days), e.sound, e.duration, e.kind, bool(e.enabled))
            for e in self._sorted_events(profile)
        )

    # --------------------------------------------------- update inkremental
    def _sorted_events(self, profile):
        return sort_events(profile.events)

    def _show_empty_state(self):
        lbl = tk.Label(self.scroll.inner, text="Belum ada jadwal bell.\nKlik 'Tambah Bell' untuk membuat.",
                       bg=Palette.BG, fg=Palette.TEXT_MUTED, font=ui_font(12), justify="center")
        lbl._bellsound_empty = True
        lbl.pack(pady=60)

    def _clear_empty_state(self):
        for child in self.scroll.inner.winfo_children():
            if getattr(child, "_bellsound_empty", False):
                child.destroy()

    def _relayout(self, profile):
        """Susun ulang baris yang sudah ada sesuai urutan jam. Tidak membuat ulang widget."""
        order = []
        for event in self._sorted_events(profile):
            refs = self._rows.get(event.id)
            if refs is not None and refs["row"].winfo_exists():
                refs["row"].pack_forget()
                refs["row"].pack(fill="x", pady=5)
                order.append(event.id)
        self._order = order

    def _sync_order(self, profile):
        """Susun ulang hanya bila urutan jam berubah (mis. jam diedit)."""
        if [e.id for e in self._sorted_events(profile)] != self._order:
            self._relayout(profile)

    def _update_row(self, profile, event):
        """Perbarui HANYA baris `event`. Bila baris belum ada, buat; kalau sudah,
        cukup ubah teks/warna — tidak membangun ulang widget (jauh lebih cepat)."""
        self._clear_empty_state()
        refs = self._rows.get(event.id)
        if refs is None or not refs["row"].winfo_exists():
            self._event_row(profile, event)
        else:
            self._apply_event(refs, event)
        self._sync_order(profile)
        self._signature = (self._profile_key, self._profile_signature(profile))

    def _apply_event(self, refs, event):
        """Salin data `event` ke widget baris yang sudah ada (tanpa membuat ulang)."""
        refs["event"] = event
        color = KIND_COLORS.get(event.kind, Palette.PRIMARY) if event.enabled else Palette.SURFACE_3
        text_fg = Palette.TEXT if event.enabled else Palette.TEXT_MUTED

        refs["bar"].configure(bg=color)
        refs["time"].configure(text=event.time, fg=text_fg)
        if refs["name"].full_text != event.name:
            refs["name"].set_text(event.name)
        refs["name"].configure(fg=text_fg)
        days = " ".join(DAY_LABELS[d] for d in event.days)
        sound = os.path.basename(event.sound) if event.sound else "belum ada file"
        meta = f"{days}   -   {sound}"
        if refs["meta"].full_text != meta:
            refs["meta"].set_text(meta)
        refs["kind"].configure(text=KIND_LABELS.get(event.kind, event.kind),
                               bg=KIND_COLORS.get(event.kind, Palette.PRIMARY))
        refs["dur"].configure(text=duration_label(event.duration))
        if bool(refs["toggle"].variable.get()) != bool(event.enabled):
            refs["toggle"].set(event.enabled)

    def _event_row(self, profile, event):
        refs = {"event": event}
        row = RoundedFrame(self.scroll.inner, parent_bg=Palette.BG, padding=14, autosize=True)
        row.pack(fill="x", pady=5)
        refs["row"] = row
        body = row.body
        # kolom tengah (info) yang menyerap sisa lebar; kolom lain tetap.
        body.columnconfigure(2, weight=1)

        # garis aksen kiri (setinggi baris)
        refs["bar"] = bar = tk.Frame(body, bg=Palette.SURFACE_3, width=5)
        bar.grid(row=0, column=0, sticky="ns")
        bar.grid_propagate(False)

        # jam
        refs["time"] = time_lbl = tk.Label(body, text="", bg=Palette.SURFACE, fg=Palette.TEXT,
                                           font=ui_font(18, "bold"))
        time_lbl.grid(row=0, column=1, sticky="w", padx=(14, 0))

        # info: nama + hari/file. ElidedLabel mencegah teks panjang
        # (mis. nama file) menabrak kontrol di kanan.
        info = tk.Frame(body, bg=Palette.SURFACE)
        info.grid(row=0, column=2, sticky="ew", padx=(16, 16))
        info.columnconfigure(0, weight=1)
        refs["name"] = name_lbl = ElidedLabel(info, text="", bg=Palette.SURFACE, fg=Palette.TEXT,
                                              font=ui_font(12, "bold"))
        name_lbl.grid(row=0, column=0, sticky="ew")
        refs["meta"] = meta_lbl = ElidedLabel(info, text="", bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                                              font=ui_font(9))
        meta_lbl.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        # kelompok kontrol kanan: toggle, badge, tombol aksi
        right = tk.Frame(body, bg=Palette.SURFACE)
        right.grid(row=0, column=3, sticky="e")

        actions = tk.Frame(right, bg=Palette.SURFACE)
        actions.pack(side="right")
        RoundedButton(actions, "Hapus", lambda: self._delete_event(profile, refs["event"]),
                      bg=Palette.SURFACE_2, fg=Palette.DANGER, hover_bg=Palette.SURFACE_3,
                      parent_bg=Palette.SURFACE, height=34, padx=12,
                      font=ui_font(10, "bold")).pack(side="left")
        RoundedButton(actions, "Edit", lambda: self._edit_event(profile, refs["event"]),
                      bg=Palette.SURFACE_2, fg=Palette.TEXT, hover_bg=Palette.SURFACE_3,
                      parent_bg=Palette.SURFACE, height=34, padx=12,
                      font=ui_font(10, "bold")).pack(side="left", padx=(6, 0))
        RoundedButton(actions, "Putar", lambda: self.app.play_event(refs["event"], manual=True),
                      bg=Palette.SURFACE_2, fg=Palette.SUCCESS, hover_bg=Palette.SURFACE_3,
                      parent_bg=Palette.SURFACE, height=34, padx=12,
                      font=ui_font(10, "bold")).pack(side="left", padx=(6, 0))

        badges = tk.Frame(right, bg=Palette.SURFACE)
        badges.pack(side="right", padx=(0, 12))
        refs["kind"] = kind_badge = Badge(badges, "", bg=Palette.SURFACE_3)
        kind_badge.pack(side="left")
        refs["dur"] = dur_badge = Badge(badges, "", bg=Palette.SURFACE_3, fg=Palette.TEXT)
        dur_badge.pack(side="left", padx=(6, 0))

        toggle_holder = tk.Frame(right, bg=Palette.SURFACE)
        toggle_holder.pack(side="right", padx=(0, 14))
        refs["toggle"] = Toggle(toggle_holder, variable=tk.BooleanVar(value=event.enabled),
                                command=lambda v: self._toggle_enabled(profile, refs["event"], v),
                                parent_bg=Palette.SURFACE, width=40, height=22)
        refs["toggle"].pack()

        self._rows[event.id] = refs
        self._apply_event(refs, event)

    # ------------------------------------------------------------ actions
    def _toggle_enabled(self, profile, event, value):
        event.enabled = value
        profile.events = [event if e.id == event.id else e for e in profile.events]
        self.app.cfg.set_profile(profile)
        self.app.save_config()
        self._update_row(profile, event)

    def _add_event(self):
        profile = self._profile()
        if profile is None:
            return
        dialog = EventDialog(
            self,
            event=None,
            defaults={
                "duration": self.app.cfg.get("default_duration", 20),
                "loop": self.app.cfg.get("default_loop", True),
                "volume": self.app.cfg.volume,
            },
            player=self.app.player,
        )
        result = dialog.show()
        if result:
            profile.events.append(result)
            self.app.cfg.set_profile(profile)
            self.app.save_config()
            self._update_row(profile, result)

    def _edit_event(self, profile, event):
        dialog = EventDialog(self, event=event, defaults={}, player=self.app.player)
        result = dialog.show()
        if result:
            profile.events = [result if e.id == result.id else e for e in profile.events]
            self.app.cfg.set_profile(profile)
            self.app.save_config()
            self._update_row(profile, result)

    def _delete_event(self, profile, event):
        confirmed = ConfirmDialog(
            self,
            title="Hapus Bell",
            message=f"Hapus bell '{event.name}' pada jam {event.time}?",
            confirm_text="Hapus",
        ).show()
        if confirmed:
            profile.events = [e for e in profile.events if e.id != event.id]
            self.app.cfg.set_profile(profile)
            self.app.save_config()
            refs = self._rows.pop(event.id, None)
            if refs is not None and refs["row"].winfo_exists():
                refs["row"].destroy()
            if not profile.events:
                self._order = []
                self._show_empty_state()
            else:
                self._relayout(profile)
            self._signature = (self._profile_key, self._profile_signature(profile))

