import base64
import json
import os
from typing import Any, Final, cast

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

_NONCE_BYTES: Final[int] = 12


class CryptoError(ValueError):
    pass


def _load_key() -> bytes:
    if not settings.OAUTH_TOKEN_ENCRYPTION_KEY:
        raise CryptoError("OAUTH_TOKEN_ENCRYPTION_KEY must be configured")
    try:
        key = base64.urlsafe_b64decode(settings.OAUTH_TOKEN_ENCRYPTION_KEY.encode("utf-8"))
    except ValueError as exc:
        raise CryptoError("Invalid OAUTH_TOKEN_ENCRYPTION_KEY encoding") from exc
    if len(key) != 32:
        raise CryptoError("OAUTH_TOKEN_ENCRYPTION_KEY must decode to 32 bytes")
    return key


def encrypt_secret(plaintext: str) -> str:
    key = _load_key()
    nonce = os.urandom(_NONCE_BYTES)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = {
        "n": base64.urlsafe_b64encode(nonce).decode("utf-8"),
        "c": base64.urlsafe_b64encode(ciphertext).decode("utf-8"),
    }
    return json.dumps(payload, separators=(",", ":"))


def decrypt_secret(token: str) -> str:
    key = _load_key()
    try:
        payload = cast(dict[str, Any], json.loads(token))
        nonce = base64.urlsafe_b64decode(payload["n"].encode("utf-8"))
        ciphertext = base64.urlsafe_b64decode(payload["c"].encode("utf-8"))
    except (KeyError, ValueError, TypeError) as exc:
        raise CryptoError("Invalid encrypted token payload") from exc
    aesgcm = AESGCM(key)
    try:
        plaintext = cast(bytes, aesgcm.decrypt(nonce, ciphertext, None))
    except Exception as exc:  # pragma: no cover
        raise CryptoError("Unable to decrypt token") from exc
    return plaintext.decode("utf-8")
