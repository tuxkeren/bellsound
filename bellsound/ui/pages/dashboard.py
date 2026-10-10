"""Halaman Dashboard: jam, bell berikutnya, jadwal hari ini, aksi cepat."""

from __future__ import annotations

import datetime as dt
import os
import tkinter as tk

from ...models import DAY_LABELS, KIND_COLORS, KIND_LABELS, duration_label, sort_events
from ..theme import Palette, ui_font
from ..widgets import Badge, Dropdown, RoundedButton, RoundedFrame, ScrollableFrame, Separator
from .base import BasePage


class DashboardPage(BasePage):
    name = "dashboard"
    label = "Dashboard"
    icon = "\U0001F3E0"

    def build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._next_holder = None
        self._quick_events = []

        # Hero -------------------------------------------------------------
        hero = RoundedFrame(self, parent_bg=Palette.BG, padding=24)
        self.hero = hero
        hero.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 12))
        hero.configure(height=224)
        hero.grid_propagate(False)
        body = hero.body
        body.columnconfigure(0, weight=1)

        left = tk.Frame(body, bg=Palette.SURFACE)
        left.grid(row=0, column=0, sticky="nsew")
        tk.Label(left, text="BELL BERIKUTNYA", bg=Palette.SURFACE, fg=Palette.TEXT_DIM,
                 font=ui_font(10, "bold"), anchor="w").pack(anchor="w")

        self.next_name = tk.Label(left, text="Tidak ada jadwal", bg=Palette.SURFACE, fg=Palette.TEXT,
                                  font=ui_font(22, "bold"), anchor="w")
        self.next_name.pack(anchor="w", pady=(4, 2))

        self.next_meta = tk.Label(left, text="Tambahkan jadwal bell terlebih dahulu", bg=Palette.SURFACE,
                                  fg=Palette.TEXT_MUTED, font=ui_font(11), anchor="w", justify="left")
        self.next_meta.pack(anchor="w")

        self.next_countdown = tk.Label(left, text="", bg=Palette.SURFACE, fg=Palette.PRIMARY,
                                       font=ui_font(15, "bold"), anchor="w")
        self.next_countdown.pack(anchor="w", pady=(8, 0))

        self.next_badges = tk.Frame(left, bg=Palette.SURFACE)
        self.next_badges.pack(anchor="w", pady=(10, 0))

        right = tk.Frame(body, bg=Palette.SURFACE)
        right.grid(row=0, column=1, sticky="nse")
        self.clock = tk.Label(right, text="--:--:--", bg=Palette.SURFACE, fg=Palette.TEXT,
                              font=ui_font(42, "bold"), anchor="e")
        self.clock.pack(anchor="e")
        self.date_label = tk.Label(right, text="", bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                                   font=ui_font(11), anchor="e")
        self.date_label.pack(anchor="e")

        # Konten -----------------------------------------------------------
        content = tk.Frame(self, bg=Palette.BG)
        self.content = content
        content.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 18))
        content.columnconfigure(0, weight=3, minsize=420)
        content.columnconfigure(1, weight=1, minsize=280)
        content.rowconfigure(0, weight=1)

        # Jadwal hari ini
        today_card = RoundedFrame(content, parent_bg=Palette.BG, padding=18)
        self.today_card = today_card
        today_card.grid(row=0, column=0, sticky="nsew")
        head = tk.Frame(today_card.body, bg=Palette.SURFACE)
        head.pack(fill="x")
        tk.Label(head, text="Jadwal Hari Ini", bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(14, "bold")).pack(side="left")
        self.today_count = tk.Label(head, text="", bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                                    font=ui_font(10, "bold"))
        self.today_count.pack(side="right")
        Separator(today_card.body).pack(fill="x", pady=(10, 8))
        self.today_scroll = ScrollableFrame(today_card.body, bg=Palette.SURFACE)
        self.today_scroll.pack(fill="both", expand=True)

        # Kolom kanan (dapat digulir agar tidak terpotong)
        side_scroll = ScrollableFrame(content, bg=Palette.BG)
        self.side_scroll = side_scroll
        side_scroll.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        side = side_scroll.inner
        self.side = side
        side.columnconfigure(0, weight=1)

        status_card = RoundedFrame(side, parent_bg=Palette.BG, padding=18, autosize=True)
        self.status_card = status_card
        status_card.grid(row=0, column=0, sticky="ew")
        tk.Label(status_card.body, text="Status Sistem", bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(14, "bold")).pack(anchor="w", pady=(0, 10))
        self.status_rows = {}
        for key, label in [
            ("audio", "Perangkat audio"),
            ("profile", "Jenis bell aktif"),
            ("active", "Jadwal aktif"),
            ("last", "Bell terakhir"),
        ]:
            self.status_rows[key] = self._status_row(status_card.body, label)

        quick_card = RoundedFrame(side, parent_bg=Palette.BG, padding=18, autosize=True)
        self.quick_card = quick_card
        quick_card.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        tk.Label(quick_card.body, text="Aksi Cepat", bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(14, "bold")).pack(anchor="w", pady=(0, 10))
        self.quick_dropdown = Dropdown(
            quick_card.body,
            text="Pilih bell...",
            command=self._on_quick_select,
            parent_bg=Palette.SURFACE,
        )
        self.quick_dropdown.pack(fill="x")
        quick_buttons = tk.Frame(quick_card.body, bg=Palette.SURFACE)
        quick_buttons.pack(fill="x", pady=(10, 0))
        RoundedButton(quick_buttons, "Putar", self._quick_play, bg=Palette.SUCCESS,
                      parent_bg=Palette.SURFACE, height=38).pack(side="left", fill="x", expand=True)
        RoundedButton(quick_buttons, "Stop", self.app.stop_audio, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE,
                      height=38).pack(side="left", padx=(8, 0))

        self._selected_quick = None

    # ------------------------------------------------------------------ ui
    def _status_row(self, parent, label):
        row = tk.Frame(parent, bg=Palette.SURFACE)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                 font=ui_font(10)).pack(side="left")
        value = tk.Label(row, text="-", bg=Palette.SURFACE, fg=Palette.TEXT,
                         font=ui_font(10, "bold"))
        value.pack(side="right")
        return value

    # -------------------------------------------------------------- refresh
    def refresh(self):
        self._refresh_next()
        self._refresh_today()
        self._refresh_status()
        self._refresh_quick()

    def _refresh_next(self):
        result = self.app.scheduler.next_bell()
        for child in self.next_badges.winfo_children():
            child.destroy()
        if not result:
            self.next_name.configure(text="Tidak ada jadwal")
            self.next_meta.configure(text="Tambahkan jadwal bell untuk profil ini")
            self.next_countdown.configure(text="")
            return
        event, when = result
        self.next_name.configure(text=event.name)
        days = ", ".join(DAY_LABELS[d] for d in event.days)
        sound = os.path.basename(event.sound) if event.sound else "belum ada file suara"
        self.next_meta.configure(
            text=f"{event.time}  |  {KIND_LABELS.get(event.kind, event.kind)}  |  {days}\n{sound}"
        )
        Badge(self.next_badges, KIND_LABELS.get(event.kind, event.kind),
              bg=KIND_COLORS.get(event.kind, Palette.PRIMARY)).pack(side="left")
        Badge(self.next_badges, duration_label(event.duration), bg=Palette.SURFACE_3,
              fg=Palette.TEXT).pack(side="left", padx=(6, 0))
        self._next_dt = when

    def _refresh_today(self):
        for child in self.today_scroll.inner.winfo_children():
            child.destroy()
        events = self.app.scheduler.today_bells()
        self.today_count.configure(text=f"{len(events)} bell")
        if not events:
            tk.Label(self.today_scroll.inner, text="Belum ada bell untuk hari ini.",
                     bg=Palette.SURFACE, fg=Palette.TEXT_MUTED, font=ui_font(11)).pack(pady=20)
            return
        now = dt.datetime.now()
        next_id = None
        for event in events:
            try:
                hour, minute = (int(p) for p in event.time.split(":"))
                when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except ValueError:
                when = now
            if when >= now and next_id is None:
                next_id = event.id
            self._today_row(event, when, is_next=(event.id == next_id))

    def _today_row(self, event, when, is_next=False):
        row = tk.Frame(self.today_scroll.inner, bg=Palette.SURFACE_2)
        row.pack(fill="x", pady=4)
        color = KIND_COLORS.get(event.kind, Palette.PRIMARY)
        bar = tk.Frame(row, bg=color, width=5)
        bar.pack(side="left", fill="y")
        inner = tk.Frame(row, bg=Palette.SURFACE_2)
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        tk.Label(inner, text=event.time, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                 font=ui_font(14, "bold")).pack(side="left")
        info = tk.Frame(inner, bg=Palette.SURFACE_2)
        info.pack(side="left", padx=(14, 0))
        tk.Label(info, text=event.name, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                 font=ui_font(11, "bold"), anchor="w").pack(anchor="w")
        tk.Label(info, text=f"{KIND_LABELS.get(event.kind, event.kind)}  -  {duration_label(event.duration)}",
                 bg=Palette.SURFACE_2, fg=Palette.TEXT_MUTED, font=ui_font(9), anchor="w").pack(anchor="w")
        if is_next:
            Badge(inner, "BERIKUTNYA", bg=Palette.PRIMARY).pack(side="right")
        elif when < dt.datetime.now():
            Badge(inner, "SELESAI", bg=Palette.SURFACE_3, fg=Palette.TEXT_MUTED).pack(side="right")

    def _refresh_status(self):
        if self.app.player.available:
            audio, fg = "Siap", Palette.SUCCESS
        else:
            detail = (self.app.player.error or "").replace("\n", " ").strip()
            audio = "Tidak tersedia"
            fg = Palette.DANGER
            if detail:
                audio += " - " + detail[:40]
                if len(detail) > 40:
                    audio += ".."
        self.status_rows["audio"].configure(text=audio, fg=fg)
        profile = self.app.cfg.active_profile()
        self.status_rows["profile"].configure(text=profile.name if profile else "-")
        active_count = sum(1 for e in (profile.events if profile else []) if e.enabled)
        self.status_rows["active"].configure(text=str(active_count))
        last = self.app.last_bell
        if last:
            self.status_rows["last"].configure(text=f"{last['name']} ({last['time']})")
        else:
            self.status_rows["last"].configure(text="-")

    def _refresh_quick(self):
        profile = self.app.cfg.active_profile()
        events = sort_events(profile.events) if profile else []
        self._quick_events = events
        options = [(f"{e.time}  {e.name}", e.id) for e in events]
        self.quick_dropdown.set_options(options)
        self._selected_quick = events[0].id if events else None

    def _on_quick_select(self, value):
        self._selected_quick = value

    def _quick_play(self):
        event = next((e for e in self._quick_events if e.id == self._selected_quick), None)
        if event is None and self._quick_events:
            event = self._quick_events[0]
        if event:
            self.app.play_event(event, manual=True)

    # ----------------------------------------------------------------- tick
    def on_tick(self, now: dt.datetime):
        self.clock.configure(text=now.strftime("%H:%M:%S"))
        self.date_label.configure(text=now.strftime("%A, %d %B %Y"))
        when = getattr(self, "_next_dt", None)
        if when:
            remaining = when - now
            seconds = int(remaining.total_seconds())
            if seconds > 0:
                hours, rem = divmod(seconds, 3600)
                minutes, secs = divmod(rem, 60)
                text = f"dalam {hours}j {minutes}m {secs}s" if hours else f"dalam {minutes}m {secs}s"
                self.next_countdown.configure(text=text)
            else:
                self.next_countdown.configure(text="sekarang")

    def on_bell(self, event, profile, when):
        self._refresh_next()
        self._refresh_today()
        self._refresh_status()
