"""Halaman Pengaturan."""

from __future__ import annotations

import sys
import tkinter as tk

from ... import AUTHOR, __version__
from ... import autostart
from ...models import DURATION_CHOICES
from ...paths import data_dir
from ..dialogs import ChangePasswordDialog, ConfirmDialog
from ..theme import Palette, ui_font
from ..widgets import Badge, Dropdown, RoundedButton, RoundedFrame, ScrollableFrame, Separator, Slider, Toggle
from .base import BasePage

# Lebar seragam untuk tombol aksi di kolom kanan agar tata letak rapi.
ACTION_WIDTH = 172


class SettingsPage(BasePage):
    name = "settings"
    label = "Pengaturan"
    icon = "\u2699"

    def build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=Palette.BG)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        tk.Label(header, text="Pengaturan", bg=Palette.BG, fg=Palette.TEXT,
                 font=ui_font(20, "bold")).pack(anchor="w")
        tk.Label(header, text="Keamanan, audio, dan preferensi aplikasi.  •  Perubahan tersimpan otomatis.",
                 bg=Palette.BG, fg=Palette.TEXT_MUTED, font=ui_font(10)).pack(anchor="w", pady=(2, 0))

        self.scroll = ScrollableFrame(self, bg=Palette.BG)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 18))
        self.scroll.inner.columnconfigure(0, weight=1)

        self.volume_label = None
        self.volume_slider = None

        self._build_security()
        self._build_audio()
        self._build_application()
        self._build_about()

    # ---------------------------------------------------------- section ui
    def _card(self, title, desc="", icon=""):
        card = RoundedFrame(self.scroll.inner, parent_bg=Palette.BG, padding=22, autosize=True)
        card.pack(fill="x", pady=(4, 8))
        head = tk.Frame(card.body, bg=Palette.SURFACE)
        head.pack(fill="x")
        title_text = f"{icon}  {title}" if icon else title
        tk.Label(head, text=title_text, bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(15, "bold")).pack(anchor="w")
        if desc:
            tk.Label(head, text=desc, bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                     font=ui_font(10), anchor="w", justify="left",
                     wraplength=700).pack(anchor="w", pady=(2, 0))
        Separator(head).pack(fill="x", pady=(10, 2))
        return card.body

    def _setting_row(self, parent, title, desc="", builder=None, *, wraplength=540):
        """Baris pengaturan dua kolom: judul+keterangan kiri, kontrol kanan.

        Kontrol diposisikan tepat di tengah secara vertikal terhadap blok
        teks, apa pun tinggi teksnya (termasuk jika keterangan membungkus).
        """
        row = tk.Frame(parent, bg=Palette.SURFACE)
        row.pack(fill="x", pady=(8, 0))
        row.columnconfigure(0, weight=1)
        row.rowconfigure(1, weight=1)

        text = tk.Frame(row, bg=Palette.SURFACE)
        text.grid(row=0, column=0, rowspan=3, sticky="w", padx=(2, 22))
        tk.Label(text, text=title, bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(11, "bold"), anchor="w").pack(anchor="w")
        if desc:
            tk.Label(text, text=desc, bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                     font=ui_font(9), anchor="w", justify="left",
                     wraplength=wraplength).pack(anchor="w", pady=(2, 0))

        ctrl = tk.Frame(row, bg=Palette.SURFACE)
        ctrl.grid(row=1, column=1, padx=(0, 2))
        if builder:
            builder(ctrl)
        return row

    def _action_button(self, parent, text, command, *, icon="", kind="default"):
        bg_map = {
            "primary": (Palette.PRIMARY, Palette.WHITE, Palette.PRIMARY_HOVER),
            "danger": (Palette.SURFACE_2, Palette.DANGER, Palette.SURFACE_3),
            "default": (Palette.SURFACE_2, Palette.TEXT, Palette.SURFACE_3),
        }
        bg, fg, hover = bg_map.get(kind, bg_map["default"])
        return RoundedButton(
            parent, text, command, icon=icon, width=ACTION_WIDTH, height=40,
            bg=bg, fg=fg, hover_bg=hover, parent_bg=Palette.SURFACE,
            font=ui_font(10, "bold"),
        )

    # ------------------------------------------------------------- security
    def _build_security(self):
        body = self._card("Keamanan", "Aplikasi tidak dapat ditutup tanpa password.", "\U0001F512")
        self._setting_row(
            body, "Password aplikasi",
            "Password default: admin123. Segera ganti agar aplikasi aman.",
            lambda c: self._action_button(
                c, "Ubah Password", self._change_password, icon="\U0001F511", kind="primary").pack(),
        )
        lock_var = tk.BooleanVar(value=bool(self.app.cfg.get("lock_on_start", False)))
        self._setting_row(
            body, "Kunci saat dibuka",
            "Minta password ketika aplikasi pertama kali dijalankan.",
            lambda c: Toggle(c, variable=lock_var, parent_bg=Palette.SURFACE,
                             command=lambda v: self._set_setting("lock_on_start", v)).pack(),
        )
        self._setting_row(
            body, "Kunci layar sekarang",
            "Sembunyikan aplikasi dan minta password untuk membukanya kembali.",
            lambda c: self._action_button(c, "Kunci", self.app.lock, icon="\U0001F510").pack(),
        )

    # ---------------------------------------------------------------- audio
    def _build_audio(self):
        body = self._card("Audio", "Pengaturan pemutaran suara bell.", "\U0001F50A")

        def volume_builder(c):
            holder = tk.Frame(c, bg=Palette.SURFACE)
            holder.pack()
            self.volume_label = tk.Label(holder, text="", bg=Palette.SURFACE, fg=Palette.TEXT,
                                         font=ui_font(11, "bold"), width=4)
            self.volume_label.pack(side="right", padx=(0, 10))
            self.volume_slider = Slider(
                holder, value=self.app.cfg.volume, width=150,
                command=self._on_volume_preview, on_release=self._on_volume_commit,
                parent_bg=Palette.SURFACE,
            )
            self.volume_slider.pack(side="right")
            self._render_volume()

        self._setting_row(
            body, "Volume utama",
            "Volume default untuk memutar bell. Disimpan otomatis saat selesai menyeret.",
            volume_builder,
        )

        dur_options = [(label, value) for label, value in DURATION_CHOICES]
        current_dur = self.app.cfg.get("default_duration", 20)

        def dur_builder(c):
            dd = Dropdown(c, text="", options=dur_options,
                          command=lambda v: self._set_setting("default_duration", v),
                          parent_bg=Palette.SURFACE, width=12)
            dd.set_text(self._duration_text(current_dur))
            dd.pack()
            return dd

        self._setting_row(
            body, "Durasi default",
            "Durasi awal saat membuat bell baru (dapat diubah per bell).",
            dur_builder,
        )

        loop_var = tk.BooleanVar(value=bool(self.app.cfg.get("default_loop", True)))
        self._setting_row(
            body, "Loop default",
            "Ulangi file pendek hingga durasi tercapai.",
            lambda c: Toggle(c, variable=loop_var, parent_bg=Palette.SURFACE,
                             command=lambda v: self._set_setting("default_loop", v)).pack(),
        )

    # ---------------------------------------------------------- application
    def _build_application(self):
        body = self._card("Aplikasi", "Preferensi umum BellSound.", "\U0001F4A1")

        start_min_var = tk.BooleanVar(value=bool(self.app.cfg.get("start_minimized", False)))
        self._setting_row(
            body, "Mulai terminimalkan",
            "Buka aplikasi langsung ke taskbar saat dijalankan.",
            lambda c: Toggle(c, variable=start_min_var, parent_bg=Palette.SURFACE,
                             command=lambda v: self._set_setting("start_minimized", v)).pack(),
        )

        auto_supported = sys.platform.startswith("win") or sys.platform == "darwin" or sys.platform.startswith("linux")
        self._setting_row(
            body, "Jalankan saat startup",
            "Otomatis membuka BellSound ketika komputer dinyalakan." if auto_supported else "Tidak didukung di sistem ini.",
            lambda c: Toggle(c, variable=tk.BooleanVar(value=autostart.is_enabled()),
                             parent_bg=Palette.SURFACE, command=self._on_autostart).pack(),
        )

        self._setting_row(
            body, "Folder data",
            f"Semua konfigurasi, riwayat, dan log disimpan di:\n    {data_dir()}",
            lambda c: self._action_button(c, "Buka Folder", autostart.open_data_dir,
                                          icon="\U0001F4C2").pack(),
        )

        self._setting_row(
            body, "Reset pengaturan",
            "Kembalikan seluruh jadwal, jenis bell, dan password ke pengaturan awal.",
            lambda c: self._action_button(c, "Reset", self._reset,
                                          icon="\u21BA", kind="danger").pack(),
            wraplength=620,
        )

    # ------------------------------------------------------------------ about
    def _build_about(self):
        body = self._card("Tentang", "", "\u2139")
        tk.Label(body, text="BellSound", bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(18, "bold")).pack(anchor="w")
        about_row = tk.Frame(body, bg=Palette.SURFACE)
        about_row.pack(fill="x", pady=(2, 0))
        Badge(about_row, f"v{__version__}", bg=Palette.PRIMARY).pack(side="left")
        tk.Label(about_row, text="  Aplikasi bel otomatis untuk sekolah / kantor",
                 bg=Palette.SURFACE, fg=Palette.TEXT_MUTED, font=ui_font(10)).pack(side="left")
        tk.Label(body, text=f"Dibuat oleh {AUTHOR}", bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                 font=ui_font(10, "bold")).pack(anchor="w", pady=(6, 0))
        tk.Label(body, text="Fitur: bell masuk, istirahat, kopi break, dan pulang. Suara bell dapat "
                            "diganti dengan file MP3, dan durasi pemutaran diatur 20/30/60 detik atau "
                            "seluruh file.",
                 bg=Palette.SURFACE, fg=Palette.TEXT_MUTED, font=ui_font(10), justify="left",
                 wraplength=660).pack(anchor="w", pady=(10, 0))

    # ------------------------------------------------------------- handlers
    def _duration_text(self, value):
        for label, val in DURATION_CHOICES:
            if val == value:
                return label
        return "20 detik"

    def _set_setting(self, key, value):
        self.app.cfg.set(key, value)
        self.app.save_config()
        self.app.refresh_all()

    def _render_volume(self):
        if self.volume_label is not None:
            self.volume_label.configure(text=f"{int(self.app.cfg.volume * 100)}%")

    def _on_volume_preview(self, value):
        # Saat menyeret slider: ubah seketika tanpa menyimpan berulang-ulang.
        self.app.cfg.set("volume", value)
        self.app.player.set_volume(value)
        if self.volume_label is not None:
            self.volume_label.configure(text=f"{int(value * 100)}%")

    def _on_volume_commit(self, value):
        self.app.save_config()
        self.app.refresh_all()

    def _on_autostart(self, value):
        ok = autostart.enable() if value else autostart.disable()
        if not ok:
            self.app.show_toast("Gagal mengubah pengaturan startup.", "error")
        self.app.cfg.set("autostart", value)
        self.app.save_config()

    def _change_password(self):
        new_password = ChangePasswordDialog(self, verifier=self.app.verify_password).show()
        if new_password:
            self.app.cfg.set_password(new_password)
            self.app.save_config()
            self.app.show_toast("Password berhasil diubah.", "success")

    def _reset(self):
        if not self.app.require_password("Reset konfigurasi membutuhkan password."):
            return
        confirmed = ConfirmDialog(self, title="Reset Konfigurasi",
                                  message="Seluruh jadwal, jenis bell, dan password akan dikembalikan ke awal. Lanjutkan?",
                                  confirm_text="Reset").show()
        if confirmed:
            self.app.reset_config()
            self.refresh()

    def refresh(self):
        if self.volume_slider is not None:
            self.volume_slider.set(self.app.cfg.volume)
            self._render_volume()