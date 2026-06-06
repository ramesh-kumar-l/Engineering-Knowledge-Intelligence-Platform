"""Secret encryption tests (ADR-0008)."""

from __future__ import annotations

from app.core.crypto import SecretBox


def test_encrypt_decrypt_roundtrip() -> None:
    box = SecretBox("a-passphrase")
    assert box.decrypt(box.encrypt("ghp_token")) == "ghp_token"


def test_ciphertext_is_not_plaintext() -> None:
    box = SecretBox("a-passphrase")
    assert box.encrypt("ghp_token") != "ghp_token"


def test_wrong_key_cannot_decrypt() -> None:
    cipher = SecretBox("key-one").encrypt("secret")
    try:
        SecretBox("key-two").decrypt(cipher)
    except ValueError:
        return
    raise AssertionError("decryption with the wrong key should fail")
