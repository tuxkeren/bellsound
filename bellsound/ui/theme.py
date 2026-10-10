"""Palet warna, font, dan helper tampilan."""

from __future__ import annotations

import tkinter.font as tkfont


class Palette:
    BG = "#0E1320"
    BG_ALT = "#0A0F1A"
    SIDEBAR = "#111827"
    SURFACE = "#161F30"
    SURFACE_2 = "#1C2740"
    SURFACE_3 = "#26334F"
    BORDER = "#28344C"
    BORDER_SOFT = "#1E2940"
    TEXT = "#E8EDF7"
    TEXT_MUTED = "#94A0B8"
    TEXT_DIM = "#5F6B84"
    PRIMARY = "#3B82F6"
    PRIMARY_HOVER = "#2E6FE0"
    PRIMARY_SOFT = "#1E3A8A"
    SUCCESS = "#22C55E"
    SUCCESS_HOVER = "#1EA84E"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    DANGER_HOVER = "#D63B3B"
    PURPLE = "#8B5CF6"
    TEAL = "#14B8A6"
    PINK = "#EC4899"
    WHITE = "#FFFFFF"


_FAMILY: str | None = None


def font_family() -> str:
    global _FAMILY
    if _FAMILY:
        return _FAMILY
    try:
        available = set(tkfont.families())
    except Exception:
        available = set()
    for name in (
        "Segoe UI Variable Text",
        "Segoe UI",
        "Inter",
        "Roboto",
        "Helvetica Neue",
        "Ubuntu",
        "Cantarell",
        "Noto Sans",
        "DejaVu Sans",
        "Arial",
    ):
        if name in available:
            _FAMILY = name
            return name
    _FAMILY = "TkDefaultFont"
    return _FAMILY


def ui_font(size: int = 11, weight: str = "normal", family: str | None = None):
    return (family or font_family(), size, weight)


def _clamp(value: float) -> int:
    return max(0, min(255, int(round(value))))


def hex_to_rgb(color: str):
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(_clamp(v) for v in rgb)


def mix(color_a: str, color_b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    a = hex_to_rgb(color_a)
    b = hex_to_rgb(color_b)
    return rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def lighten(color: str, t: float = 0.12) -> str:
    return mix(color, "#FFFFFF", t)


def darken(color: str, t: float = 0.12) -> str:
    return mix(color, "#000000", t)
