"""Kelas dasar halaman."""

from __future__ import annotations

import tkinter as tk

from ..theme import Palette, ui_font
from ..widgets import RoundedFrame


class BasePage(tk.Frame):
    name = "page"
    label = "Halaman"
    icon = ""

    def __init__(self, master, app):
        super().__init__(master, bg=Palette.BG)
        self.app = app
        self.build()

    # untuk ditimpa
    def build(self) -> None:  # pragma: no cover - abstrak
        pass

    def refresh(self) -> None:
        pass

    def on_show(self) -> None:
        self.refresh()

    def on_tick(self, now) -> None:
        pass

    def on_bell(self, event, profile, when) -> None:
        pass

    # helper --------------------------------------------------------------
    def card(self, parent, **kwargs) -> RoundedFrame:
        return RoundedFrame(parent, parent_bg=Palette.BG, **kwargs)

    def section_label(self, parent, text: str, sub: str = ""):
        holder = tk.Frame(parent, bg=Palette.BG)
        tk.Label(holder, text=text, bg=Palette.BG, fg=Palette.TEXT,
                 font=ui_font(14, "bold"), anchor="w").pack(anchor="w")
        if sub:
            tk.Label(holder, text=sub, bg=Palette.BG, fg=Palette.TEXT_MUTED,
                     font=ui_font(10), anchor="w").pack(anchor="w")
        return holder
