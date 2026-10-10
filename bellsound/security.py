"""Utilitas keamanan untuk password aplikasi.

Password tidak pernah disimpan sebagai teks biasa. Digunakan PBKDF2-HMAC-SHA256
dengan salt acak per instalasi.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Dict, Optional

_ITERATIONS = 200_000


def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    """Kembalikan dict berisi salt dan hash dari ``password``."""
    if salt:
        salt_bytes = bytes.fromhex(salt)
    else:
        salt_bytes = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt_bytes, _ITERATIONS
    )
    return {"salt": salt_bytes.hex(), "hash": digest.hex()}


def verify_password(password: str, stored: Dict[str, str]) -> bool:
    """Verifikasi ``password`` terhadap data hash yang tersimpan."""
    if not stored:
        return False
    salt = stored.get("salt")
    expected = stored.get("hash")
    if not salt or not expected:
        return False
    candidate = hash_password(password, salt)["hash"]
    return hmac.compare_digest(candidate, expected)
