from datetime import UTC, datetime, timedelta
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_bytes, token_urlsafe

from otm_workbench.config import get_settings

PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
    if algorithm != "pbkdf2_sha256":
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    actual = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
    return compare_digest(actual, expected)


def new_session_token() -> str:
    return token_urlsafe(32)


def session_expiry() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) + timedelta(
        minutes=get_settings().session_ttl_minutes
    )
