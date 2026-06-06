"""Symmetric encryption for secrets at rest (ADR-0008, security_requirements.md).

Connector credentials must never be stored in plaintext. ``SecretBox`` wraps Fernet
(AES-128-CBC + HMAC) with a key derived from the configured ``secret_key`` so any
passphrase works while the stored key stays a valid Fernet key.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


class SecretBox:
    """Encrypt/decrypt short secrets (e.g. connector tokens) with a derived key."""

    def __init__(self, secret_key: str) -> None:
        # Derive a deterministic 32-byte Fernet key from the passphrase.
        digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:  # pragma: no cover - corrupt/rotated key
            raise ValueError("Unable to decrypt secret (wrong key?)") from exc
