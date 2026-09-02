import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

def _get_fernet() -> Fernet:
    # Derive a valid 32-byte url-safe base64 key from settings.ENCRYPTION_KEY or SECRET_KEY
    key_material = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    digest = hashlib.sha256(key_material.encode("utf-8")).digest()
    b64_key = base64.urlsafe_b64encode(digest)
    return Fernet(b64_key)

def encrypt_secret(plain_text: str) -> str:
    if not plain_text:
        return ""
    f = _get_fernet()
    encrypted_bytes = f.encrypt(plain_text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_secret(encrypted_text: str) -> str:
    if not encrypted_text:
        return ""
    try:
        f = _get_fernet()
        decrypted_bytes = f.decrypt(encrypted_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        return ""

# Aliases for compatibility
encrypt_string = encrypt_secret
decrypt_string = decrypt_secret

