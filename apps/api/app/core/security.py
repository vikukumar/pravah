import hashlib
import hmac
import os
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import jwt, JWTError
from app.core.config import settings

ALGORITHM = "HS256"

def get_password_hash(password: str) -> str:
    salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}${pwd_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or '$' not in hashed_password:
        return False
    salt, stored_hash = hashed_password.split('$', 1)
    computed_hash = hashlib.pbkdf2_hmac(
        'sha256',
        plain_password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hmac.compare_digest(stored_hash, computed_hash)

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    if extra_claims:
        to_encode.update(extra_claims)
        
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

def generate_random_token(length: int = 32) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_recovery_codes(count: int = 8, length: int = 10) -> list[str]:
    codes = []
    for _ in range(count):
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
        formatted = f"{code[:5]}-{code[5:]}"
        codes.append(formatted)
    return codes
