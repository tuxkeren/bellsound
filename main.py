#!/usr/bin/env python3
"""BellSound - Aplikasi Bel Otomatis.

Titik masuk aplikasi. Jalankan dengan:
    python main.py
"""

import multiprocessing
import sys
from typing import List


def _check_runtime() -> List[str]:
    """Periksa dependensi wajib pada interpreter yang sedang dipakai.

    Mengembalikan daftar modul yang tidak bisa diimpor pada interpreter ini.
    """
    missing: List[str] = []
    for module in ("tkinter", "pygame"):
        try:
            __import__(module)
        except Exception:
            missing.append(module)
    return missing


def main() -> int:
    multiprocessing.freeze_support()

    # Jalankan cek dependensi hanya saat dari source, bukan dari executable.
    # Saat dari executable (PyInstaller) modul pasti terbungkus di dalamnya.
    if not getattr(sys, "frozen", False):
        missing = _check_runtime()
        if missing:
            print("=" * 62)
            print("BellSound gagal dimuat: ada dependensi yang tidak ditemukan.")
            print(f"  Modul hilang : {', '.join(missing)}")
            print(f"  Python dipakai: {sys.executable}")
            print("=" * 62)
            print("Kemungkinan besar venv proyek belum diaktifkan. Coba:")
            print("  cd /home/atha/projects/bellsound")
            print("  source .venv/bin/activate")
            print("  pip install -r requirements.txt")
            print("  python main.py")
            print()
            print("Atau langsung pakai interpreter venv-nya:")
            print("  /home/atha/projects/bellsound/.venv/bin/python main.py")
            print("=" * 62)
            return 1

    try:
        from bellsound.app import run
    except ImportError as exc:  # pragma: no cover
        sys.stderr.write(
            "Gagal memuat BellSound. Pastikan dependensi sudah terpasang:\n"
            "    pip install -r requirements.txt\n"
            f"Detail: {exc}\n"
        )
        return 1
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())