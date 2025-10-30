"""
Authentication helpers using Argon2 for secure password hashing.

Adds convenience functions:
- hash_password(password: str) -> str
- verify_password(hash: str, password: str) -> bool
- needs_rehash(hash: str) -> bool
- generate_token(nbytes: int = 32) -> str

NOTE: This module requires the `argon2-cffi` package. Add it to your
project requirements (e.g. `pip install argon2-cffi`) or add
`argon2-cffi>=21.3.0` to `requirements.txt`.
"""
from __future__ import annotations

import secrets
from typing import Optional

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash
except Exception as e:  # pragma: no cover - runtime dependency check
    raise RuntimeError("argon2-cffi is required for auth_utils.py; install with 'pip install argon2-cffi'")

# Tuning: time_cost, memory_cost (KB), parallelism. These are reasonable defaults
# for many applications but should be tuned per deployment environment.
_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2, hash_len=32)


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id and return the encoded hash string.

    Inputs:
    - password: cleartext password (must be a str)

    Output:
    - encoded Argon2 hash string (store this in the database)

    Raises:
    - TypeError if password is not a string.
    """
    if not isinstance(password, str):
        raise TypeError("password must be a str")
    return _ph.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify a password against a stored Argon2 hash.

    Returns True for a match, False otherwise. If the stored hash uses weaker
    parameters and needs re-hashing, this function will return True and callers
    may choose to re-hash the password and update the DB.
    """
    try:
        ok = _ph.verify(stored_hash, password)
        # Optionally check if the hash needs upgrading
        try:
            if _ph.check_needs_rehash(stored_hash):
                # Caller can re-hash and store the new value on next successful login
                pass
        except Exception:
            # Older versions of argon2-cffi use `needs_rehash` name or may not
            # expose the method; ignore gracefully.
            pass
        return bool(ok)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False


def needs_rehash(stored_hash: str) -> bool:
    """Return True if the stored hash should be re-hashed with current params."""
    try:
        return _ph.check_needs_rehash(stored_hash)
    except Exception:
        return False


def generate_token(nbytes: int = 32) -> str:
    """Generate a secure URL-safe token for password resets or session tokens."""
    return secrets.token_urlsafe(nbytes)
