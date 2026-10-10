"""Widget kustom bergaya modern untuk BellSound."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional

from .theme import Palette, darken, lighten, ui_font


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius, **kwargs):
    """Gambar persegi panjang dengan sudut membulat memakai polygon smooth."""
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedFrame(tk.Canvas):
    """Kartu dengan sudut membulat, berisi frame ``body``."""

    def __init__(
        self,
        master,
        *,
        radius: int = 16,
        bg: str = Palette.SURFACE,
        border: str = Palette.BORDER,
        parent_bg: str = Palette.BG,
        padding: int = 18,
        border_width: int = 1,
        autosize: bool = False,
        **kwargs,
    ):
        super().__init__(master, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self._radius = radius
        self._bg = bg
        self._border = border
        self._border_width = border_width
        self._padding = padding
        self._autosize = autosize
        self.body = tk.Frame(self, bg=bg)
        self._window = self.create_window(padding, padding, window=self.body, anchor="nw")
        if autosize:
            self.body.bind("<Configure>", self._on_body_configure)
        self.bind("<Configure>", self._reenable)

    def _on_body_configure(self, _event=None):
        needed = self.body.winfo_reqheight() + self._padding * 2
        if abs(self.winfo_reqheight() - needed) > 1:
            self.configure(height=needed)

    def _reenable(self, event):
        self._draw(event.width, event.height)

    def _draw(self, width: int, height: int) -> None:
        self.delete("card")
        if width <= 2 or height <= 2:
            return
        outer = round_rect(
            self,
            1,
            1,
            width - 1,
            height - 1,
            self._radius,
            fill=self._bg,
            outline=self._border,
            width=self._border_width,
            tags="card",
        )
        self.tag_lower(outer)
        self.itemconfigure(
            self._window,
            width=max(1, width - self._padding * 2),
            height=max(1, height - self._padding * 2),
        )

    def set_bg(self, color: str) -> None:
        self._bg = color
        self.body.configure(bg=color)
        self._draw(self.winfo_width(), self.winfo_height())


class RoundedButton(tk.Canvas):
    """Tombol dengan sudut membulat dan efek hover."""

    def __init__(
        self,
        master,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        *,
        bg: str = Palette.PRIMARY,
        hover_bg: Optional[str] = None,
        fg: str = Palette.WHITE,
        disabled_bg: str = Palette.SURFACE_3,
        parent_bg: str = Palette.SURFACE,
        height: int = 40,
        radius: int = 10,
        padx: int = 18,
        font=None,
        width: Optional[int] = None,
        icon: str = "",
        outline: str = "",
        tooltip: str = "",
    ):
        self._font = tkfont.Font(font=font or ui_font(11, "bold"))
        self._label = f"{icon}  {text}".strip() if icon else text
        text_width = self._font.measure(self._label) if self._label else 0
        computed_width = width or (text_width + padx * 2)
        super().__init__(
            master,
            width=computed_width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            takefocus=1,
        )
        self._bg = bg
        self._hover_bg = hover_bg or lighten(bg, 0.12)
        self._fg = fg
        self._disabled_bg = disabled_bg
        self._radius = radius
        self._command = command
        self._state = "normal"
        self._outline = outline
        self._width = computed_width
        self._height = height
        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Return>", lambda e: self._invoke())
        self.bind("<space>", lambda e: self._invoke())

    def _draw(self, fill: Optional[str] = None) -> None:
        self.delete("all")
        if self._state == "disabled":
            color = self._disabled_bg
            text_color = Palette.TEXT_DIM
        else:
            color = fill or self._bg
            text_color = self._fg
        round_rect(
            self,
            0,
            0,
            self._width,
            self._height,
            self._radius,
            fill=color,
            outline=self._outline or color,
        )
        self.create_text(
            self._width / 2,
            self._height / 2,
            text=self._label,
            fill=text_color,
            font=self._font,
        )

    def _on_enter(self, _event):
        if self._state == "normal":
            self.configure(cursor="hand2")
            self._draw(self._hover_bg)

    def _on_leave(self, _event):
        if self._state == "normal":
            self.configure(cursor="")
            self._draw()

    def _on_press(self, _event):
        if self._state == "normal":
            self._draw(darken(self._hover_bg, 0.1))

    def _on_release(self, event):
        if self._state != "normal":
            return
        inside = 0 <= event.x <= self._width and 0 <= event.y <= self._height
        self._draw()
        if inside:
            self._invoke()

    def _invoke(self):
        if self._state == "normal" and self._command:
            self._command()

    def set_state(self, state: str) -> None:
        self._state = state
        self.configure(cursor="hand2" if state == "normal" else "")
        self._draw()

    def set_text(self, text: str, icon: str = "") -> None:
        self._label = f"{icon}  {text}".strip() if icon else text
        text_width = self._font.measure(self._label) if self._label else 0
        self._width = max(self._width, text_width + 36)
        self.configure(width=self._width)
        self._draw()

    def set_colors(self, bg: str, fg: str = Palette.WHITE, hover_bg: Optional[str] = None) -> None:
        self._bg = bg
        self._hover_bg = hover_bg or lighten(bg, 0.12)
        self._fg = fg
        self._draw()


class IconButton(RoundedButton):
    def __init__(self, master, icon: str, command=None, *, size: int = 38, **kwargs):
        kwargs.setdefault("padx", 0)
        super().__init__(
            master,
            text="",
            icon=icon,
            command=command,
            width=size,
            height=size,
            radius=size // 2,
            **kwargs,
        )


class Toggle(tk.Canvas):
    """Saklar on/off."""

    def __init__(
        self,
        master,
        variable: Optional[tk.Variable] = None,
        command: Optional[Callable[[bool], None]] = None,
        *,
        parent_bg: str = Palette.SURFACE,
        on_color: str = Palette.SUCCESS,
        off_color: str = Palette.SURFACE_3,
        width: int = 46,
        height: int = 26,
    ):
        super().__init__(
            master, width=width, height=height, bg=parent_bg, highlightthickness=0, bd=0
        )
        self._toggle_width = width
        self._toggle_height = height
        self._on_color = on_color
        self._off_color = off_color
        self._command = command
        self.variable = variable or tk.BooleanVar(value=False)
        self._anim = None
        self._draw()
        self.bind("<Button-1>", self._toggle)
        self.configure(cursor="hand2")

    def _draw(self) -> None:
        self.delete("all")
        on = bool(self.variable.get())
        color = self._on_color if on else self._off_color
        r = self._toggle_height / 2
        round_rect(self, 0, 0, self._toggle_width, self._toggle_height, r, fill=color, outline=color)
        knob_r = r - 3
        cx = (self._toggle_width - r) if on else r
        self.create_oval(
            cx - knob_r, r - knob_r, cx + knob_r, r + knob_r,
            fill=Palette.WHITE, outline=Palette.WHITE,
        )

    def _toggle(self, _event=None):
        self.variable.set(not bool(self.variable.get()))
        self._draw()
        if self._command:
            self._command(bool(self.variable.get()))

    def set(self, value: bool) -> None:
        self.variable.set(bool(value))
        self._draw()


class Badge(tk.Label):
    def __init__(self, master, text: str, *, bg: str, fg: str = "#FFFFFF", font=None, **kwargs):
        super().__init__(
            master,
            text=text,
            bg=bg,
            fg=fg,
            font=font or ui_font(9, "bold"),
            padx=9,
            pady=3,
            bd=0,
            **kwargs,
        )


class ElidedLabel(tk.Label):
    """Label yang otomatis memotong teks dengan elipsis (...) sesuai lebar.

    Pakai bersama ``grid(sticky="ew")`` pada kolom ber-bobot. Opsi ``width``
    sengaja kecil (default 1) supaya label tidak memaksa lebar kolom induk;
    teks tetap tampil penuh bila ruang mencukupi.
    """

    def __init__(self, master, text: str = "", **kwargs):
        kwargs.setdefault("anchor", "w")
        kwargs.setdefault("width", 1)
        super().__init__(master, text="", **kwargs)
        self._full_text = str(text)
        self._font = tkfont.Font(font=self.cget("font"))
        self._rendered: Optional[str] = None
        self.bind("<Configure>", self._on_configure)
        self._render(self.winfo_width())

    def set_text(self, text: str) -> None:
        self._full_text = str(text)
        self._rendered = None
        self._render(self.winfo_width())

    @property
    def full_text(self) -> str:
        return self._full_text

    def _on_configure(self, event) -> None:
        self._render(event.width)

    def _render(self, width: int) -> None:
        if width <= 1:
            return
        if self._font.measure(self._full_text) <= width:
            shown = self._full_text
        else:
            shown = self._ellipsize(self._full_text, width)
        if shown != self._rendered:
            self._rendered = shown
            self.configure(text=shown)

    def _ellipsize(self, text: str, width: int) -> str:
        ellipsis = "\u2026"
        if self._font.measure(ellipsis) > width:
            return ""
        low, high = 0, len(text)
        while low < high:
            mid = (low + high + 1) // 2
            if self._font.measure(text[:mid] + ellipsis) <= width:
                low = mid
            else:
                high = mid - 1
        return text[:low].rstrip() + ellipsis


class ScrollableFrame(tk.Frame):
    """Area yang bisa digulir vertikal."""

    def __init__(self, master, *, bg: str = Palette.BG, **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        self._bg = bg
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview, width=10
        )
        try:
            self.scrollbar.configure(
                bg=Palette.SURFACE_2,
                troughcolor=bg,
                activebackground=Palette.SURFACE_3,
                bd=0,
                highlightthickness=0,
                relief="flat",
            )
        except tk.TclError:
            pass
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def wheel_scroll(self, event) -> bool:
        """Gulir berdasarkan event roda mouse. True bila event ditangani."""
        num = getattr(event, "num", None)
        if num == 4:
            delta = -1
        elif num == 5:
            delta = 1
        else:
            delta = -1 if getattr(event, "delta", 0) > 0 else 1
        first, last = self.canvas.yview()
        if first <= 0.0 and last >= 1.0:
            return False
        self.canvas.yview_scroll(delta * 3, "units")
        return True

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)

    def _on_scroll(self, first, last):
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.scrollbar.pack_forget()
        else:
            self.scrollbar.pack(side="right", fill="y")
        self.scrollbar.set(first, last)

    def scroll_to_top(self):
        self.canvas.yview_moveto(0.0)


class Slider(tk.Canvas):
    """Slider horizontal bergaya modern (volume, dll.).

    Nilai ``value`` berkisar 0.0–1.0. ``command`` dipanggil selama drag,
    ``on_release`` dipanggil saat seretan/step selesai.
    """

    def __init__(
        self,
        master,
        *,
        value: float = 0.0,
        command: Optional[Callable[[float], None]] = None,
        on_release: Optional[Callable[[float], None]] = None,
        parent_bg: str = Palette.SURFACE,
        width: int = 170,
        height: int = 28,
        track_color: str = Palette.SURFACE_3,
        fill_color: str = Palette.PRIMARY,
        knob_color: str = Palette.WHITE,
        knob_border: str = Palette.PRIMARY_HOVER,
    ):
        super().__init__(
            master,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            takefocus=1,
        )
        self._value = max(0.0, min(1.0, float(value)))
        self._command = command
        self._on_release = on_release
        self._track_color = track_color
        self._fill_color = fill_color
        self._knob_color = knob_color
        self._knob_border = knob_border
        self._padding = 6
        self._knob_r = 9
        self._track_h = 6
        self._draw()
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_up)
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", lambda _event: self.configure(cursor="hand2"))
        self.bind("<Leave>", lambda _event: self.configure(cursor=""))
        self.bind("<Left>", lambda _event: self._step(-0.05))
        self.bind("<Right>", lambda _event: self._step(0.05))

    @property
    def value(self) -> float:
        return self._value

    def set(self, value: float, *, notify: bool = False) -> None:
        self._set_value(value, notify)

    # ------------------------------------------------------------ geometry
    def _geometry(self):
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 2:
            width = int(self.cget("width"))
        if height <= 2:
            height = int(self.cget("height"))
        return max(width, 10), max(height, 10)

    def _pos_to_value(self, x: float) -> float:
        width, _h = self._geometry()
        span = max(1, width - self._padding * 2)
        return max(0.0, min(1.0, (x - self._padding) / span))

    # ---------------------------------------------------------------- state
    def _set_value(self, value: float, notify: bool) -> float:
        value = max(0.0, min(1.0, float(value)))
        if abs(value - self._value) < 0.001:
            return self._value
        self._value = value
        self._draw()
        if notify and self._command:
            try:
                self._command(value)
            except Exception:
                pass
        return value

    def _step(self, delta: float) -> None:
        self._set_value(self._value + delta, True)
        if self._on_release:
            try:
                self._on_release(self._value)
            except Exception:
                pass

    # -------------------------------------------------------------- events
    def _on_press(self, event):
        self.focus_set()
        self._set_value(self._pos_to_value(event.x), True)

    def _on_drag(self, event):
        self._set_value(self._pos_to_value(event.x), True)

    def _on_up(self, _event):
        if self._on_release:
            try:
                self._on_release(self._value)
            except Exception:
                pass

    # ----------------------------------------------------------------- draw
    def _draw(self):
        self.delete("all")
        width, height = self._geometry()
        y = height / 2
        x1 = self._padding
        x2 = width - self._padding
        knob_x = x1 + (x2 - x1) * self._value
        r = self._knob_r

        # jalur (track) penuh dengan ujung membulat
        self.create_line(
            x1, y, x2, y, width=self._track_h, fill=self._track_color, capstyle="round"
        )
        # bagian yang sudah terisi
        if knob_x - x1 > 1:
            self.create_line(
                x1, y, knob_x, y, width=self._track_h, fill=self._fill_color, capstyle="round"
            )
        # kenop
        self.create_oval(
            knob_x - r, y - r, knob_x + r, y + r,
            fill=self._knob_color, outline=self._knob_border, width=2,
        )


class Dropdown(tk.Menubutton):
    """Tombol dropdown sederhana berbasis tk.Menu."""

    def __init__(
        self,
        master,
        *,
        text: str = "",
        options=None,
        command: Optional[Callable[[str], None]] = None,
        parent_bg: str = Palette.BG,
        width: Optional[int] = None,
        font=None,
        bg: str = Palette.SURFACE_2,
        fg: str = Palette.TEXT,
    ):
        super().__init__(
            master,
            text=text,
            bg=bg,
            fg=fg,
            activebackground=Palette.SURFACE_3,
            activeforeground=Palette.TEXT,
            highlightthickness=0,
            bd=0,
            relief="flat",
            anchor="w",
            padx=12,
            pady=7,
            font=font or ui_font(11),
            cursor="hand2",
        )
        self._parent_bg = parent_bg
        self._command = command
        self._values = []
        self._text = text
        if width:
            self.configure(width=width)
        self._menu = tk.Menu(
            self,
            tearoff=0,
            bg=Palette.SURFACE_2,
            fg=Palette.TEXT,
            activebackground=Palette.PRIMARY,
            activeforeground=Palette.WHITE,
            bd=0,
            font=font or ui_font(11),
        )
        self.configure(menu=self._menu)
        if options:
            self.set_options(options)

    def set_options(self, options) -> None:
        self._menu.delete(0, "end")
        self._values = list(options)
        for option in self._values:
            label, value = option if isinstance(option, (tuple, list)) else (option, option)
            self._menu.add_command(label=label, command=lambda v=value: self._select(v))
        if self._values:
            self.configure(text=str(self._values[0][0] if isinstance(self._values[0], (tuple, list)) else self._values[0]))

    def _select(self, value) -> None:
        for option in self._values:
            label, opt_value = option if isinstance(option, (tuple, list)) else (option, option)
            if opt_value == value:
                self.configure(text=str(label))
                break
        if self._command:
            self._command(value)

    def set_text(self, text: str) -> None:
        self._text = text
        self.configure(text=text)


class Separator(tk.Frame):
    def __init__(self, master, *, bg: str = Palette.BORDER_SOFT, **kwargs):
        super().__init__(master, bg=bg, height=1, **kwargs)
