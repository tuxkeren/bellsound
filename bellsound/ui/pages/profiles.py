"""Halaman Jenis Bell: kelola profil bell (Normal, Ramadhan, dst)."""

from __future__ import annotations

import tkinter as tk

from ..dialogs import ConfirmDialog, PromptDialog
from ..theme import Palette, ui_font
from ..widgets import Badge, RoundedButton, RoundedFrame, ScrollableFrame
from .base import BasePage


class ProfilesPage(BasePage):
    name = "profiles"
    label = "Jenis Bell"
    icon = "\U0001F517"

    def build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=Palette.BG)
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 8))
        header.columnconfigure(0, weight=1)
        title = tk.Frame(header, bg=Palette.BG)
        title.grid(row=0, column=0, sticky="w")
        tk.Label(title, text="Jenis Bell", bg=Palette.BG, fg=Palette.TEXT,
                 font=ui_font(20, "bold")).pack(anchor="w")
        tk.Label(title, text="Buat beberapa set jadwal, misalnya Normal, Ramadhan, atau Ujian.",
                 bg=Palette.BG, fg=Palette.TEXT_MUTED, font=ui_font(10)).pack(anchor="w")
        RoundedButton(header, "Tambah Jenis", self._add_profile, icon="\uFF0B", bg=Palette.PRIMARY,
                      parent_bg=Palette.BG, height=42).grid(row=0, column=1, sticky="e")

        self.scroll = ScrollableFrame(self, bg=Palette.BG)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 18))
        self.scroll.inner.columnconfigure(0, weight=1)
        self.scroll.inner.columnconfigure(1, weight=1)

        self._profile_holder = tk.Frame(self.scroll.inner, bg=Palette.BG)
        self._profile_holder.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self._profile_holder.columnconfigure(0, weight=1)
        self._profile_holder.columnconfigure(1, weight=1)

    def refresh(self):
        for child in self._profile_holder.winfo_children():
            child.destroy()
        profiles = self.app.cfg.iter_profiles()
        for index, profile in enumerate(profiles):
            self._profile_card(index, profile)

    def _profile_card(self, index, profile):
        row, col = divmod(index, 2)
        card = RoundedFrame(self._profile_holder, parent_bg=Palette.BG, padding=18, autosize=True)
        card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 7, 7 if col == 0 else 0), pady=6)
        body = card.body

        head = tk.Frame(body, bg=Palette.SURFACE)
        head.pack(fill="x")
        dot = tk.Frame(head, bg=profile.color, width=14, height=14)
        dot.pack(side="left")
        dot.pack_propagate(False)
        tk.Label(head, text=profile.name, bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(14, "bold")).pack(side="left", padx=(10, 0))
        if profile.key == self.app.cfg.active_profile_key:
            Badge(head, "AKTIF", bg=Palette.SUCCESS).pack(side="right")

        active_events = sum(1 for e in profile.events if e.enabled)
        tk.Label(body, text=f"{len(profile.events)} jadwal  -  {active_events} aktif",
                 bg=Palette.SURFACE, fg=Palette.TEXT_MUTED, font=ui_font(10)).pack(anchor="w", pady=(8, 12))

        buttons = tk.Frame(body, bg=Palette.SURFACE)
        buttons.pack(fill="x")
        if profile.key != self.app.cfg.active_profile_key:
            RoundedButton(buttons, "Aktifkan", lambda k=profile.key: self._activate(k), bg=Palette.SUCCESS,
                          parent_bg=Palette.SURFACE, height=36, padx=14,
                          font=ui_font(10, "bold")).pack(side="left")
        RoundedButton(buttons, "Jadwal", lambda k=profile.key: self._open_schedule(k), bg=Palette.SURFACE_2,
                      fg=Palette.TEXT, hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=36, padx=14,
                      font=ui_font(10, "bold")).pack(side="left", padx=(8, 0))
        RoundedButton(buttons, "Nama", lambda p=profile: self._rename(p), bg=Palette.SURFACE_2,
                      fg=Palette.TEXT, hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=36, padx=14,
                      font=ui_font(10, "bold")).pack(side="left", padx=(8, 0))
        RoundedButton(buttons, "Duplikat", lambda k=profile.key: self._duplicate(k), bg=Palette.SURFACE_2,
                      fg=Palette.TEXT, hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=36, padx=14,
                      font=ui_font(10, "bold")).pack(side="left", padx=(8, 0))
        RoundedButton(buttons, "Hapus", lambda p=profile: self._delete(p), bg=Palette.SURFACE_2,
                      fg=Palette.DANGER, hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=36, padx=14,
                      font=ui_font(10, "bold")).pack(side="left", padx=(8, 0))

    # ------------------------------------------------------------ actions
    def _activate(self, key):
        self.app.set_active_profile(key)

    def _open_schedule(self, key):
        self.app.show_page("schedule")
        schedule_page = self.app.pages["schedule"]
        schedule_page._profile_key = key
        schedule_page.refresh()

    def _add_profile(self):
        name = PromptDialog(self, title="Tambah Jenis Bell", label="Nama jenis bell:", ok_text="Buat").show()
        if name:
            profile = self.app.cfg.add_profile(name)
            self.app.save_config()
            self.app.refresh_all()
            self.refresh()

    def _rename(self, profile):
        name = PromptDialog(self, title="Ganti Nama", label="Nama jenis bell:", initial=profile.name).show()
        if name:
            profile.name = name
            self.app.cfg.set_profile(profile)
            self.app.save_config()
            self.app.refresh_all()
            self.refresh()

    def _duplicate(self, key):
        if self.app.cfg.duplicate_profile(key):
            self.app.save_config()
            self.app.refresh_all()
            self.refresh()

    def _delete(self, profile):
        if len(self.app.cfg.profile_keys()) <= 1:
            ConfirmDialog(self, title="Tidak Bisa Dihapus",
                          message="Minimal harus ada satu jenis bell.", confirm_text="Mengerti",
                          danger=False).show()
            return
        confirmed = ConfirmDialog(
            self,
            title="Hapus Jenis Bell",
            message=f"Hapus jenis bell '{profile.name}' beserta semua jadwalnya?",
            confirm_text="Hapus",
        ).show()
        if confirmed:
            self.app.cfg.remove_profile(profile.key)
            self.app.save_config()
            self.app.refresh_all()
            self.refresh()
