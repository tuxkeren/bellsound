#!/usr/bin/env python3
"""Build BellSound menjadi executable dengan PyInstaller.

Contoh pemakaian:
    python build.py            # menghasilkan satu file (dist/bellsound[.exe])
    python build.py --onedir   # menghasilkan folder dist/bellsound/
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "bellsound"


def main() -> int:
    onedir = "--onedir" in sys.argv
    keep_console = "--console" in sys.argv

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        NAME,
        "--collect-all",
        "pygame",
    ]
    args.append("--onedir" if onedir else "--onefile")
    if not keep_console:
        args.append("--windowed")

    for icon in (ROOT / "assets" / "icon.ico", ROOT / "assets" / "icon.png"):
        if icon.exists():
            args += ["--icon", str(icon)]
            break

    args.append(str(ROOT / "main.py"))

    print("Menjalankan PyInstaller...")
    print("  " + " ".join(args))
    try:
        subprocess.check_call(args, cwd=ROOT)
    except FileNotFoundError:
        print("\nPyInstaller tidak ditemukan. Jalankan dulu:")
        print("  pip install -r requirements-dev.txt")
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"\nBuild gagal dengan kode {exc.returncode}.")
        return exc.returncode

    target = ROOT / "dist" / (NAME + ".exe" if sys.platform.startswith("win") else NAME)
    print("\nSelesai! Hasil build:")
    if onedir:
        print(f"  {ROOT / 'dist' / NAME}/")
    else:
        print(f"  {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
