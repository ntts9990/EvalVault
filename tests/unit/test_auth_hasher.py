"""Tests for the Argon2 password hasher (EvalVault Auth P1.1)."""

from __future__ import annotations

from evalvault.adapters.outbound.auth.argon2_hasher import Argon2PasswordHasher


def test_hash_is_not_plaintext_and_uses_argon2() -> None:
    hashed = Argon2PasswordHasher().hash("s3cret-pw")
    assert hashed != "s3cret-pw"
    assert hashed.startswith("$argon2")


def test_verify_accepts_correct_and_rejects_wrong() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("s3cret-pw")
    assert hasher.verify("s3cret-pw", hashed) is True
    assert hasher.verify("wrong-pw", hashed) is False


def test_hashes_are_salted_and_differ() -> None:
    hasher = Argon2PasswordHasher()
    assert hasher.hash("same") != hasher.hash("same")


def test_verify_works_across_instances() -> None:
    hashed = Argon2PasswordHasher().hash("portable")
    assert Argon2PasswordHasher().verify("portable", hashed) is True
