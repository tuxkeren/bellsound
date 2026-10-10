"""Autostart lintas platform (Windows registry, Linux .desktop, macOS LaunchAgent)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .paths import app_dir, data_dir, is_frozen

APP_KEY = "BellSound"


def _launch_command() -> str:
    if is_frozen():
        return f'"{sys.executable}"'
    entry = app_dir() / "main.py"
    return f'"{sys.executable}" "{entry}"'


def is_enabled() -> bool:
    try:
        if sys.platform.startswith("win"):
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                winreg.QueryValueEx(key, APP_KEY)
            return True
        if sys.platform == "darwin":
            return (Path.home() / "Library/LaunchAgents/com.bellsound.app.plist").exists()
        return (Path.home() / ".config/autostart/bellsound.desktop").exists()
    except OSError:
        return False


def enable() -> bool:
    try:
        if sys.platform.startswith("win"):
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(key, APP_KEY, 0, winreg.REG_SZ, _launch_command())
            return True
        if sys.platform == "darwin":
            path = Path.home() / "Library/LaunchAgents/com.bellsound.app.plist"
            path.parent.mkdir(parents=True, exist_ok=True)
            args = _launch_command().strip('"').split('" "')
            program_args = "".join(f"<string>{a}</string>" for a in args)
            path.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                '<plist version="1.0"><dict><key>Label</key><string>com.bellsound.app</string>'
                f'<key>ProgramArguments</key><array>{program_args}</array>'
                "<key>RunAtLoad</key><true/></dict></plist>\n",
                encoding="utf-8",
            )
            return True
        path = Path.home() / ".config/autostart/bellsound.desktop"
        path.parent.mkdir(parents=True, exist_ok=True)
        command = _launch_command().replace('"', "")
        path.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_KEY}\n"
            f"Exec={command}\n"
            "X-GNOME-Autostart-enabled=true\n"
            "Terminal=false\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def disable() -> bool:
    try:
        if sys.platform.startswith("win"):
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, APP_KEY)
            return True
        if sys.platform == "darwin":
            (Path.home() / "Library/LaunchAgents/com.bellsound.app.plist").unlink(missing_ok=True)
            return True
        (Path.home() / ".config/autostart/bellsound.desktop").unlink(missing_ok=True)
        return True
    except OSError:
        return False


def open_data_dir() -> None:
    path = data_dir()
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError:
        pass
