import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def derive_key(master_password: str, salt: bytes) -> bytes:
    password_bytes = master_password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    key = kdf.derive(password_bytes)
    return base64.urlsafe_b64encode(key)


def generate_salt() -> bytes:
    return os.urandom(16)


def encrypt(key: bytes, plaintext: str) -> bytes:
    if plaintext is None:
        return b""
    f = Fernet(key)
    token = f.encrypt(plaintext.encode("utf-8"))
    return token


def decrypt(key: bytes, ciphertext: bytes) -> str:
    if not ciphertext:
        return ""
    f = Fernet(key)
    text = f.decrypt(ciphertext).decode("utf-8")
    return text


def wipe_string(value: str):
    """
    Best-effort memory wipe for Python strings (symbolic).
    """
    value = None
    return None
