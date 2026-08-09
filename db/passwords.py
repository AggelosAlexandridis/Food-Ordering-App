import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260_000
SALT_BYTES = 16


def hash_password(plain_password):
    salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(plain_password, stored_password):
    """True if plain_password matches stored_password.

    Accepts a legacy plaintext stored_password (no '$' segments) so old,
    not-yet-migrated rows still work: falls back to a direct compare.
    """
    parts = stored_password.split("$") if stored_password else []
    if len(parts) != 4 or parts[0] != ALGORITHM:
        return hmac.compare_digest(plain_password, stored_password or "")

    _, iterations, salt_hex, hash_hex = parts
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        iterations = int(iterations)
    except ValueError:
        return False

    actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def is_hashed(stored_password):
    parts = stored_password.split("$") if stored_password else []
    return len(parts) == 4 and parts[0] == ALGORITHM
