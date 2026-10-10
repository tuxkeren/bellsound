"""Jendela utama aplikasi BellSound."""

from __future__ import annotations

import datetime as dt
import json
import os
import tkinter as tk
from typing import Dict, Optional

from . import APP_SUBTITLE, APP_TITLE, AUTHOR, __version__
from .config import Config
from .models import Profile, BellEvent
from .paths import history_path, log_path
from .player import AudioPlayer
from .scheduler import BellScheduler
from .security import verify_password as _verify
from .ui.dialogs import PasswordDialog
from .ui.pages.dashboard import DashboardPage
from .ui.pages.history import HistoryPage
from .ui.pages.profiles import ProfilesPage
from .ui.pages.schedule import SchedulePage
from .ui.pages.settings import SettingsPage
from .ui.theme import Palette, ui_font
from .ui.widgets import Dropdown, RoundedButton, RoundedFrame, ScrollableFrame

MAX_HISTORY = 500


class NavItem(tk.Frame):
    def __init__(self, master, page: str, label: str, icon: str, command):
        super().__init__(master, bg=Palette.SIDEBAR, cursor="hand2")
        self.page = page
        self._active = False
        self.indicator = tk.Frame(self, bg=Palette.SIDEBAR, width=4)
        self.indicator.pack(side="left", fill="y")
        content = tk.Frame(self, bg=Palette.SIDEBAR)
        content.pack(side="left", fill="both", expand=True, padx=(14, 12), pady=10)
        self.icon_label = tk.Label(content, text=icon, bg=Palette.SIDEBAR, fg=Palette.TEXT_MUTED,
                                   font=ui_font(13))
        self.icon_label.pack(side="left")
        self.text_label = tk.Label(content, text=label, bg=Palette.SIDEBAR, fg=Palette.TEXT_MUTED,
                                   font=ui_font(11, "bold"))
        self.text_label.pack(side="left", padx=(12, 0))
        self._parts = [self, content, self.icon_label, self.text_label]
        for widget in self._parts:
            widget.bind("<Button-1>", lambda e: command(self.page))
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event):
        if not self._active:
            for widget in self._parts:
                widget.configure(bg=Palette.SURFACE)

    def _on_leave(self, _event):
        if not self._active:
            for widget in self._parts:
                widget.configure(bg=Palette.SIDEBAR)

    def set_active(self, active: bool):
        self._active = active
        bg = Palette.SURFACE_2 if active else Palette.SIDEBAR
        fg = Palette.TEXT if active else Palette.TEXT_MUTED
        for widget in self._parts:
            widget.configure(bg=bg)
        self.indicator.configure(bg=Palette.PRIMARY if active else Palette.SIDEBAR)
        self.icon_label.configure(fg=Palette.PRIMARY if active else Palette.TEXT_MUTED)
        self.text_label.configure(fg=fg)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} - {APP_SUBTITLE}")
        self.geometry("1200x760")
        self.minsize(1024, 660)
        self.configure(bg=Palette.BG)
        self._fullscreen = True  # mulai dalam mode layar penuh

        # Catat semua error callback Tk ke log agar tidak "diam-diam" berhenti
        self.report_callback_exception = self._report_exception

        self.cfg = Config.load()
        self.history = self._load_history()
        self.last_bell: Optional[dict] = None
        self.pages: Dict[str, object] = {}
        self.nav_items: Dict[str, NavItem] = {}
        self._lock_overlay: Optional[tk.Frame] = None
        self._toast: Optional[tk.Frame] = None
        self._toast_after = None
        self._current_page = "dashboard"

        # Audio & penjadwal
        self.player = AudioPlayer(on_error=self._on_audio_error)
        self.player.init()
        self.player.set_volume(self.cfg.volume)
        self.scheduler = BellScheduler(lambda: self.cfg, self._on_bell_trigger)

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close_request)
        self.bind("<Alt-F4>", lambda e: (self._on_close_request(), "break")[1])
        self.bind("<Control-q>", lambda e: (self._on_close_request(), "break")[1])
        self.bind("<Escape>", self._toggle_fullscreen)
        self.bind_all("<MouseWheel>", self._on_wheel)
        self.bind_all("<Button-4>", self._on_wheel)
        self.bind_all("<Button-5>", self._on_wheel)

        self._apply_fullscreen()
        self.show_page("dashboard")
        self._tick()

        if self.cfg.get("lock_on_start"):
            self.after(300, self.lock)
        if self.cfg.get("start_minimized"):
            self.after(300, self.iconify)
        if self.verify_password("admin123"):
            self.after(1200, lambda: self.show_toast(
                "Password masih default (admin123). Segera ubah di Pengaturan.", "warning"))

    # -------------------------------------------------------------- layout
    def _build_layout(self):
        self.columnconfigure(0, minsize=238)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()

        main = tk.Frame(self, bg=Palette.BG)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        self._build_topbar(main)

        content = tk.Frame(main, bg=Palette.BG)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        for page_class in (DashboardPage, SchedulePage, ProfilesPage, HistoryPage, SettingsPage):
            page = page_class(content, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[page.name] = page

    def _build_sidebar(self):
        sidebar = tk.Frame(self, bg=Palette.SIDEBAR, width=238)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = tk.Frame(sidebar, bg=Palette.SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(22, 18))
        logo = tk.Canvas(brand, width=40, height=40, bg=Palette.SIDEBAR, highlightthickness=0)
        logo.pack(side="left")
        logo.create_oval(2, 2, 38, 38, fill=Palette.PRIMARY, outline="")
        logo.create_text(20, 21, text="\U0001F514", font=ui_font(16))
        title_box = tk.Frame(brand, bg=Palette.SIDEBAR)
        title_box.pack(side="left", padx=(12, 0))
        tk.Label(title_box, text=APP_TITLE, bg=Palette.SIDEBAR, fg=Palette.TEXT,
                 font=ui_font(15, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Bel Otomatis", bg=Palette.SIDEBAR, fg=Palette.TEXT_MUTED,
                 font=ui_font(9)).pack(anchor="w")

        tk.Label(sidebar, text="MENU", bg=Palette.SIDEBAR, fg=Palette.TEXT_DIM,
                 font=ui_font(9, "bold")).pack(anchor="w", padx=24, pady=(4, 6))

        for page_class in (DashboardPage, SchedulePage, ProfilesPage, HistoryPage, SettingsPage):
            item = NavItem(sidebar, page_class.name, page_class.label, page_class.icon, self.show_page)
            item.pack(fill="x")
            self.nav_items[page_class.name] = item

        bottom = tk.Frame(sidebar, bg=Palette.SIDEBAR)
        bottom.pack(side="bottom", fill="x", padx=16, pady=16)

        self.audio_status = tk.Label(bottom, text="", bg=Palette.SIDEBAR, fg=Palette.TEXT_MUTED,
                                     font=ui_font(9), anchor="w")
        self.audio_status.pack(fill="x", pady=(0, 8))
        RoundedButton(bottom, "Kunci Aplikasi", self.lock, icon="\U0001F512", bg=Palette.SURFACE_2,
                      fg=Palette.TEXT, hover_bg=Palette.SURFACE_3, parent_bg=Palette.SIDEBAR,
                      height=40, width=200).pack(fill="x")
        tk.Label(bottom, text=f"v{__version__}", bg=Palette.SIDEBAR, fg=Palette.TEXT_DIM,
                 font=ui_font(9)).pack(pady=(10, 0))
        tk.Label(bottom, text=f"oleh {AUTHOR}", bg=Palette.SIDEBAR, fg=Palette.TEXT_MUTED,
                 font=ui_font(9, "bold"), wraplength=200, justify="center").pack(pady=(2, 0))

        self._update_audio_status()

    def _build_topbar(self, parent):
        topbar = tk.Frame(parent, bg=Palette.BG)
        topbar.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 0))
        topbar.columnconfigure(1, weight=1)

        self.page_title = tk.Label(topbar, text="Dashboard", bg=Palette.BG, fg=Palette.TEXT,
                                   font=ui_font(16, "bold"))
        self.page_title.grid(row=0, column=0, sticky="w")

        right = tk.Frame(topbar, bg=Palette.BG)
        right.grid(row=0, column=2, sticky="e")

        tk.Label(right, text="Jenis bell aktif", bg=Palette.BG, fg=Palette.TEXT_MUTED,
                 font=ui_font(9, "bold")).pack(side="left", padx=(0, 8))
        self.profile_dropdown = Dropdown(right, text="", command=self.set_active_profile,
                                         parent_bg=Palette.BG, width=12)
        self.profile_dropdown.pack(side="left", padx=(0, 16))

        self.top_clock = tk.Label(right, text="--:--", bg=Palette.BG, fg=Palette.TEXT,
                                  font=ui_font(15, "bold"))
        self.top_clock.pack(side="left", padx=(0, 14))
        RoundedButton(right, "Kunci", self.lock, icon="\U0001F512", bg=Palette.SURFACE_2,
                      fg=Palette.TEXT, hover_bg=Palette.SURFACE_3, parent_bg=Palette.BG,
                      height=40, padx=14).pack(side="left")
        self._refresh_profile_dropdown()

    # --------------------------------------------------------------- window
    def _apply_fullscreen(self):
        """Terapkan mode layar penuh sesuai nilai self._fullscreen."""
        try:
            self.attributes("-fullscreen", bool(self._fullscreen))
        except tk.TclError:
            # Sebagian window manager tidak mendukung -fullscreen; abaikan.
            pass

    def _toggle_fullscreen(self, _event=None):
        """ESC: beralih antara mode layar penuh dan mode jendela."""
        # Jangan ganggu bila ada dialog modal yang sedang terbuka (Esc menutup dialog).
        try:
            if self.grab_current() not in (None, self):
                return None
        except tk.TclError:
            pass
        self._fullscreen = not self._fullscreen
        self._apply_fullscreen()
        return "break"

    # ---------------------------------------------------------------- pages
    def show_page(self, name: str):
        if name not in self.pages:
            return
        page = self.pages[name]
        page.tkraise()
        self._current_page = name
        self.page_title.configure(text=getattr(page, "label", name.title()))
        for key, item in self.nav_items.items():
            item.set_active(key == name)
        page.on_show()

    def refresh_all(self):
        self._refresh_profile_dropdown()
        self._update_audio_status()
        for page in self.pages.values():
            try:
                page.refresh()
            except Exception:
                pass

    def _refresh_profile_dropdown(self):
        options = [(p.name, p.key) for p in self.cfg.iter_profiles()]
        active = self.cfg.active_profile()
        self.profile_dropdown.set_options(options)
        if active:
            self.profile_dropdown.set_text(active.name)

    def set_active_profile(self, key: str):
        self.cfg.active_profile_key = key
        self.save_config()
        self.refresh_all()
        active = self.cfg.active_profile()
        self.show_toast(f"Jenis bell aktif: {active.name if active else key}", "info")

    # ------------------------------------------------------------- playback
    def play_event(self, event: BellEvent, manual: bool = False):
        if not event.sound or not os.path.isfile(event.sound):
            self.show_toast(f"File suara untuk '{event.name}' belum diatur.", "error")
            return
        volume = event.volume if event.volume is not None else self.cfg.volume
        ok = self.player.play(event.sound, duration=event.duration, loop=event.loop, volume=volume)
        if ok:
            self.last_bell = {
                "name": event.name,
                "time": event.time,
                "kind": event.kind,
                "profile": self.cfg.active_profile().name if self.cfg.active_profile() else "-",
            }
            self._record_history(event, "diputar")
            self._update_audio_status()
            self.show_toast(f"Memutar: {event.name}", "success")
        self._refresh_current()

    def stop_audio(self):
        self.player.stop()
        self._update_audio_status()

    def _on_bell_trigger(self, event: BellEvent, profile: Profile, when: dt.datetime):
        if not event.sound or not os.path.isfile(event.sound):
            self._record_history(event, "file tidak ada", profile=profile)
            self.show_toast(f"Bell '{event.name}' dilewati: file suara tidak ada.", "error")
            self._refresh_current()
            return
        volume = event.volume if event.volume is not None else self.cfg.volume
        ok = self.player.play(event.sound, duration=event.duration, loop=event.loop, volume=volume)
        status = "diputar" if ok else "gagal"
        self.last_bell = {
            "name": event.name,
            "time": event.time,
            "kind": event.kind,
            "profile": profile.name,
        }
        self._record_history(event, status, profile=profile)
        self._log(f"BELL {event.time} {event.name} ({profile.name}) -> {status}")
        self._update_audio_status()
        if ok:
            self.show_toast(f"Bell berbunyi: {event.name} ({event.time})", "success")
        for page in self.pages.values():
            try:
                page.on_bell(event, profile, when)
            except Exception:
                pass

    def _refresh_current(self):
        page = self.pages.get(self._current_page)
        if page and hasattr(page, "refresh"):
            try:
                page.refresh()
            except Exception:
                pass

    # -------------------------------------------------------------- history
    def _load_history(self):
        path = history_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data[-MAX_HISTORY:]
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save_history(self):
        path = history_path()
        try:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.history[-MAX_HISTORY:], ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, path)
        except OSError:
            pass

    def _record_history(self, event: BellEvent, status: str, profile: Optional[Profile] = None):
        profile = profile or self.cfg.active_profile()
        self.history.append({
            "when": dt.datetime.now().isoformat(timespec="seconds"),
            "name": event.name,
            "kind": event.kind,
            "time": event.time,
            "profile": profile.name if profile else "-",
            "status": status,
        })
        self.history = self.history[-MAX_HISTORY:]
        self._save_history()

    def clear_history(self):
        self.history = []
        self._save_history()

    def _log(self, message: str):
        try:
            with open(log_path(), "a", encoding="utf-8") as handle:
                handle.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {message}\n")
        except OSError:
            pass

    def _report_exception(self, exc_type, exc_value, tb):
        import traceback

        detail = "".join(traceback.format_exception(exc_type, exc_value, tb))
        self._log("UNHANDLED EXCEPTION:\n" + detail)
        try:
            self.show_toast("Terjadi kesalahan internal. Detail tercatat di log.", "error")
        except Exception:
            pass

    # --------------------------------------------------------------- config
    def save_config(self):
        try:
            self.cfg.save()
        except OSError:
            self.show_toast("Gagal menyimpan konfigurasi.", "error")

    def reset_config(self):
        from .config import default_config

        self.cfg = Config(default_config())
        self.cfg.save()
        self.player.set_volume(self.cfg.volume)
        self.refresh_all()
        self.show_toast("Konfigurasi direset ke pengaturan awal.", "success")

    # ------------------------------------------------------------- security
    def verify_password(self, password: str) -> bool:
        return _verify(password, self.cfg.security)

    def require_password(self, prompt: str = "Masukkan password:") -> bool:
        return bool(PasswordDialog(self, prompt=prompt, verifier=self.verify_password).show())

    def lock(self):
        if self._lock_overlay is not None:
            return
        overlay = tk.Frame(self, bg=Palette.BG_ALT)
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        overlay.lift()
        self._lock_overlay = overlay

        card = RoundedFrame(overlay, parent_bg=Palette.BG_ALT, padding=30, width=420, height=340)
        card.place(relx=0.5, rely=0.5, anchor="center")
        body = card.body
        tk.Label(body, text="\U0001F512", bg=Palette.SURFACE, font=ui_font(34)).pack(pady=(4, 6))
        tk.Label(body, text="Aplikasi Terkunci", bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(18, "bold")).pack()
        tk.Label(body, text="Masukkan password untuk membuka", bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                 font=ui_font(10)).pack(pady=(2, 14))

        from .ui.dialogs import make_entry

        entry = make_entry(body, show="\u2022")
        entry.pack(fill="x", ipady=9)
        error = tk.Label(body, text="", bg=Palette.SURFACE, fg=Palette.DANGER, font=ui_font(10))
        error.pack(pady=(6, 0))

        def attempt(_event=None):
            if self.verify_password(entry.get()):
                self._unlock()
            else:
                error.configure(text="Password salah.")
                entry.delete(0, "end")

        entry.bind("<Return>", attempt)
        RoundedButton(body, "Buka", attempt, bg=Palette.PRIMARY, parent_bg=Palette.SURFACE,
                      height=40).pack(fill="x", pady=(14, 0))

        self._lock_entry = entry
        entry.focus_set()
        try:
            overlay.grab_set()
        except tk.TclError:
            pass

    def _unlock(self):
        if self._lock_overlay is not None:
            try:
                self._lock_overlay.grab_release()
            except tk.TclError:
                pass
            self._lock_overlay.destroy()
            self._lock_overlay = None

    # ------------------------------------------------------------- close
    def _on_close_request(self):
        if self._lock_overlay is not None:
            try:
                self._lock_overlay.grab_release()
            except tk.TclError:
                pass
        if not self.require_password("Aplikasi hanya bisa ditutup dengan password."):
            return
        self._quit()

    def _quit(self):
        try:
            self.player.stop()
        except Exception:
            pass
        self.save_config()
        self.destroy()

    # --------------------------------------------------------------- toast
    def show_toast(self, message: str, kind: str = "info"):
        colors = {
            "info": Palette.PRIMARY,
            "success": Palette.SUCCESS,
            "error": Palette.DANGER,
            "warning": Palette.WARNING,
        }
        color = colors.get(kind, Palette.PRIMARY)
        if self._toast is not None:
            try:
                self._toast.destroy()
            except tk.TclError:
                pass
        toast = tk.Frame(self, bg=Palette.SURFACE_2, highlightbackground=color, highlightthickness=2)
        tk.Label(toast, text=message, bg=Palette.SURFACE_2, fg=Palette.TEXT, font=ui_font(10, "bold"),
                 justify="left", wraplength=340).pack(padx=16, pady=12)
        toast.place(relx=1.0, rely=1.0, anchor="se", x=-22, y=-22)
        toast.lift()
        self._toast = toast
        if self._toast_after:
            try:
                self.after_cancel(self._toast_after)
            except Exception:
                pass
        self._toast_after = self.after(4000, self._hide_toast)

    def _hide_toast(self):
        if self._toast is not None:
            try:
                self._toast.destroy()
            except tk.TclError:
                pass
            self._toast = None

    # ----------------------------------------------------------- periodic
    def _on_wheel(self, event):
        widget = getattr(event, "widget", None)
        while widget is not None:
            if isinstance(widget, ScrollableFrame):
                try:
                    widget.wheel_scroll(event)
                except Exception:
                    pass
                return "break"
            widget = getattr(widget, "master", None)
        return None

    def _update_audio_status(self):
        if not hasattr(self, "audio_status"):
            return
        if self.player.available:
            playing = self.player.is_playing()
            text = "\U0001F50A Audio siap" + ("  -  memutar..." if playing else "")
            color = Palette.SUCCESS
        else:
            text = "\U0001F50A Audio tidak tersedia"
            if self.player.error:
                detail = self.player.error.replace("\n", " ").strip()
                text += f" - {detail}"
            color = Palette.DANGER
        self.audio_status.configure(text=text, fg=color)

    def _on_audio_error(self, message: str):
        self._log(f"AUDIO ERROR: {message}")
        try:
            self.show_toast(message, "error")
        except Exception:
            pass

    def _tick(self):
        now = dt.datetime.now()
        self.top_clock.configure(text=now.strftime("%H:%M:%S"))
        try:
            self.scheduler.tick(now)
        except Exception as exc:
            self._log(f"SCHEDULER ERROR: {exc}")
        page = self.pages.get(self._current_page)
        if page and hasattr(page, "on_tick"):
            try:
                page.on_tick(now)
            except Exception:
                pass
        self.after(1000, self._tick)


def run():
    app = App()
    app.mainloop()
