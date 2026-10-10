"""Dialog modal (password, konfirmasi, input teks)."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from .theme import Palette, ui_font
from .widgets import RoundedButton


def make_entry(master, *, show: Optional[str] = None, width: int = 24, font=None, justify="left"):
    entry = tk.Entry(
        master,
        bg=Palette.SURFACE_2,
        fg=Palette.TEXT,
        insertbackground=Palette.TEXT,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=Palette.BORDER,
        highlightcolor=Palette.PRIMARY,
        font=font or ui_font(12),
        show=show or "",
        width=width,
        justify=justify,
        disabledbackground=Palette.SURFACE_3,
        disabledforeground=Palette.TEXT_MUTED,
        readonlybackground=Palette.SURFACE_2,
        selectbackground=Palette.PRIMARY_SOFT,
        selectforeground=Palette.TEXT,
    )
    return entry


class Modal(tk.Toplevel):
    def __init__(self, parent, title: str, width: int = 400, height: int = 240):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.configure(bg=Palette.SURFACE)
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self._result = None
        self._parent = parent
        self._width = width
        self._height = height
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass

    def show(self):
        self.update_idletasks()
        parent = self._parent
        try:
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
            x = px + (pw - self._width) // 2
            y = py + (ph - self._height) // 3
        except tk.TclError:
            x, y = 200, 200
        self.geometry(f"{self._width}x{self._height}+{max(0, x)}+{max(0, y)}")
        self.deiconify()
        self.grab_set()
        self.focus_force()
        self.wait_window()
        return self._result

    def cancel(self):
        self._result = None
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


class PasswordDialog(Modal):
    def __init__(self, parent, *, title="Konfirmasi Password", prompt="Masukkan password:", verifier=None):
        super().__init__(parent, title, width=420, height=250)
        self._verifier = verifier
        container = tk.Frame(self, bg=Palette.SURFACE)
        container.pack(fill="both", expand=True, padx=26, pady=22)

        tk.Label(container, text=prompt, bg=Palette.SURFACE, fg=Palette.TEXT,
                 font=ui_font(12), anchor="w", justify="left", wraplength=360).pack(fill="x")
        self.entry = make_entry(container, show="\u2022")
        self.entry.pack(fill="x", ipady=8, pady=(12, 6))
        self.error = tk.Label(container, text="", bg=Palette.SURFACE, fg=Palette.DANGER,
                              font=ui_font(10), anchor="w")
        self.error.pack(fill="x")

        buttons = tk.Frame(container, bg=Palette.SURFACE)
        buttons.pack(fill="x", side="bottom", pady=(10, 0))
        RoundedButton(buttons, "Batal", self.cancel, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=38).pack(side="right")
        RoundedButton(buttons, "Buka", self._submit, bg=Palette.PRIMARY,
                      parent_bg=Palette.SURFACE, height=38).pack(side="right", padx=(0, 10))

        self.bind("<Return>", lambda e: self._submit())
        self.bind("<Escape>", lambda e: self.cancel())
        self.entry.focus_set()

    def _submit(self):
        value = self.entry.get()
        if self._verifier and not self._verifier(value):
            self.error.configure(text="Password salah. Coba lagi.")
            self.entry.delete(0, "end")
            return
        self._result = True
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


class ConfirmDialog(Modal):
    def __init__(self, parent, *, title="Konfirmasi", message="", confirm_text="Ya", danger=True):
        super().__init__(parent, title, width=430, height=230)
        container = tk.Frame(self, bg=Palette.SURFACE)
        container.pack(fill="both", expand=True, padx=26, pady=22)
        tk.Label(container, text=message, bg=Palette.SURFACE, fg=Palette.TEXT, font=ui_font(12),
                 anchor="w", justify="left", wraplength=370).pack(fill="both", expand=True)
        buttons = tk.Frame(container, bg=Palette.SURFACE)
        buttons.pack(fill="x", side="bottom")
        RoundedButton(buttons, "Batal", self.cancel, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=38).pack(side="right")
        RoundedButton(buttons, confirm_text, self._confirm, bg=Palette.DANGER if danger else Palette.PRIMARY,
                      parent_bg=Palette.SURFACE, height=38).pack(side="right", padx=(0, 10))
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self.cancel())

    def _confirm(self):
        self._result = True
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


class PromptDialog(Modal):
    def __init__(self, parent, *, title="Input", label="Nama:", initial="", ok_text="Simpan"):
        super().__init__(parent, title, width=420, height=220)
        container = tk.Frame(self, bg=Palette.SURFACE)
        container.pack(fill="both", expand=True, padx=26, pady=22)
        tk.Label(container, text=label, bg=Palette.SURFACE, fg=Palette.TEXT, font=ui_font(12),
                 anchor="w").pack(fill="x")
        self.entry = make_entry(container)
        self.entry.insert(0, initial)
        self.entry.pack(fill="x", ipady=8, pady=(10, 6))
        self.entry.select_range(0, "end")
        buttons = tk.Frame(container, bg=Palette.SURFACE)
        buttons.pack(fill="x", side="bottom", pady=(12, 0))
        RoundedButton(buttons, "Batal", self.cancel, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=38).pack(side="right")
        RoundedButton(buttons, ok_text, self._submit, bg=Palette.PRIMARY,
                      parent_bg=Palette.SURFACE, height=38).pack(side="right", padx=(0, 10))
        self.bind("<Return>", lambda e: self._submit())
        self.bind("<Escape>", lambda e: self.cancel())
        self.entry.focus_set()

    def _submit(self):
        value = self.entry.get().strip()
        if not value:
            return
        self._result = value
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


class ChangePasswordDialog(Modal):
    """Dialog ubah password: password lama, baru, konfirmasi."""

    def __init__(self, parent, *, verifier):
        super().__init__(parent, "Ubah Password", width=440, height=360)
        self._verifier = verifier
        container = tk.Frame(self, bg=Palette.SURFACE)
        container.pack(fill="both", expand=True, padx=26, pady=22)

        self.old = self._field(container, "Password lama")
        self.new = self._field(container, "Password baru")
        self.confirm = self._field(container, "Konfirmasi password baru")

        self.error = tk.Label(container, text="", bg=Palette.SURFACE, fg=Palette.DANGER,
                              font=ui_font(10), anchor="w", wraplength=380)
        self.error.pack(fill="x", pady=(4, 0))

        buttons = tk.Frame(container, bg=Palette.SURFACE)
        buttons.pack(fill="x", side="bottom")
        RoundedButton(buttons, "Batal", self.cancel, bg=Palette.SURFACE_2, fg=Palette.TEXT,
                      hover_bg=Palette.SURFACE_3, parent_bg=Palette.SURFACE, height=38).pack(side="right")
        RoundedButton(buttons, "Simpan", self._submit, bg=Palette.PRIMARY,
                      parent_bg=Palette.SURFACE, height=38).pack(side="right", padx=(0, 10))
        self.bind("<Return>", lambda e: self._submit())
        self.bind("<Escape>", lambda e: self.cancel())
        self.old.focus_set()

    def _field(self, parent, label):
        tk.Label(parent, text=label, bg=Palette.SURFACE, fg=Palette.TEXT_MUTED,
                 font=ui_font(10), anchor="w").pack(fill="x", pady=(8, 2))
        entry = make_entry(parent, show="\u2022")
        entry.pack(fill="x", ipady=7)
        return entry

    def _submit(self):
        old = self.old.get()
        new = self.new.get()
        confirm = self.confirm.get()
        if not self._verifier(old):
            self.error.configure(text="Password lama salah.")
            return
        if len(new) < 4:
            self.error.configure(text="Password baru minimal 4 karakter.")
            return
        if new != confirm:
            self.error.configure(text="Konfirmasi password tidak cocok.")
            return
        self._result = new
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
