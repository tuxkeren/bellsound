"""Halaman Riwayat: daftar bell yang pernah dibunyikan."""

from __future__ import annotations

import datetime as dt
import tkinter as tk

from ...models import KIND_COLORS, KIND_LABELS
from ..dialogs import ConfirmDialog
from ..theme import Palette, ui_font
from ..widgets import Badge, RoundedButton, RoundedFrame, ScrollableFrame
from .base import BasePage


class HistoryPage(BasePage):
    name = "history"
    label = "Riwayat"
    icon = "\U0001F553"

    def build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=Palette.BG)
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 8))
        header.columnconfigure(0, weight=1)
        title = tk.Frame(header, bg=Palette.BG)
        title.grid(row=0, column=0, sticky="w")
        tk.Label(title, text="Riwayat Bell", bg=Palette.BG, fg=Palette.TEXT,
                 font=ui_font(20, "bold")).pack(anchor="w")
        tk.Label(title, text="Catatan bell yang sudah dibunyikan.", bg=Palette.BG,
                 fg=Palette.TEXT_MUTED, font=ui_font(10)).pack(anchor="w")
        RoundedButton(header, "Bersihkan", self._clear, bg=Palette.SURFACE_2, fg=Palette.DANGER,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.BG, height=42).grid(row=0, column=1, sticky="e")

        self.scroll = ScrollableFrame(self, bg=Palette.BG)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 18))

    def refresh(self):
        for child in self.scroll.inner.winfo_children():
            child.destroy()
        entries = list(reversed(self.app.history))
        if not entries:
            tk.Label(self.scroll.inner, text="Belum ada riwayat.", bg=Palette.BG,
                     fg=Palette.TEXT_MUTED, font=ui_font(12)).pack(pady=60)
            return
        for entry in entries:
            self._row(entry)

    def _row(self, entry):
        row = RoundedFrame(self.scroll.inner, parent_bg=Palette.BG, padding=14, autosize=True)
        row.pack(fill="x", pady=5)
        body = row.body

        try:
            when = dt.datetime.fromisoformat(entry.get("when", ""))
            time_text = when.strftime("%d %b %Y  %H:%M:%S")
        except ValueError:
            time_text = entry.get("when", "-")

        color = KIND_COLORS.get(entry.get("kind", "lain"), Palette.PRIMARY)
        bar = tk.Frame(body, bg=color, width=5, height=36)
        bar.pack(side="left", fill="y")
        bar.pack_propagate(False)

        info = tk.Frame(body, bg=Palette.SURFACE)
        info.pack(side="left", padx=(14, 0), fill="x", expand=True)
        tk.Label(info, text=entry.get("name", "Bell"), bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(12, "bold"), anchor="w").pack(anchor="w")
        tk.Label(info, text=f"{time_text}   -   {entry.get('profile', '-')}", bg=Palette.SURFACE,
                 fg=Palette.TEXT_MUTED, font=ui_font(9), anchor="w").pack(anchor="w")

        status = entry.get("status", "diputar")
        status_color = Palette.SUCCESS if status == "diputar" else Palette.DANGER
        Badge(body, status.upper(), bg=status_color).pack(side="right")
        Badge(body, KIND_LABELS.get(entry.get("kind", "lain"), "Lainnya"),
              bg=KIND_COLORS.get(entry.get("kind", "lain"), Palette.PRIMARY)).pack(side="right", padx=(0, 8))

    def _clear(self):
        if not self.app.history:
            return
        confirmed = ConfirmDialog(self, title="Bersihkan Riwayat",
                                  message="Hapus seluruh riwayat bell?", confirm_text="Bersihkan").show()
        if confirmed:
            self.app.clear_history()
            self.refresh()
