"""Argon2 password hasher (pwdlib) — implements ``PasswordHasherPort``.

pwdlib is the maintained successor to passlib (which breaks on Python 3.13+);
Argon2 is the current recommended password-hashing algorithm.
"""

from __future__ import annotations

from pwdlib import PasswordHash


class Argon2PasswordHasher:
    """Hash/verify passwords using Argon2 via pwdlib's recommended config."""

    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._hasher.verify(password, hashed)
