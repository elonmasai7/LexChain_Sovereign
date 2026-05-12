"""Enterprise security implementation for LexChain Sovereign."""
import secrets
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
fernet = Fernet(settings.ENCRYPTION_KEY.encode())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> tuple[str, str]:
    """Create a refresh token and its hash for secure storage."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    token_hash = hash_token(token)
    return token, token_hash


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")


def rotate_tokens(refresh_token: str) -> tuple[str, str, str]:
    """Rotate tokens using a valid refresh token. Returns (new_access, new_refresh, old_hash)."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token payload")

    old_hash = hash_token(refresh_token)
    new_access = create_access_token({"sub": user_id, "email": payload.get("email"), "role": payload.get("role")})
    new_refresh, new_hash = create_refresh_token({"sub": user_id, "email": payload.get("email"), "role": payload.get("role")})

    return new_access, new_refresh, old_hash


def generate_csrf_token() -> str:
    """Generate a secure CSRF token."""
    return secrets.token_urlsafe(64)


def validate_csrf_token(token: str, stored_token: Optional[str] = None) -> bool:
    """Validate a CSRF token against stored token."""
    if not token or not stored_token:
        return False
    return hmac.compare_digest(token, stored_token)


def encrypt_data(data: str) -> bytes:
    """Encrypt data using Fernet symmetric encryption."""
    if isinstance(data, str):
        data = data.encode()
    return fernet.encrypt(data)


def decrypt_data(encrypted_data: bytes) -> str:
    """Decrypt Fernet-encrypted data."""
    try:
        decrypted = fernet.decrypt(encrypted_data)
        return decrypted.decode()
    except InvalidToken:
        raise ValueError("Invalid encrypted data")


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_api_key() -> tuple[str, str]:
    """Generate an API key and its hash."""
    key = f"lcs_{secrets.token_urlsafe(48)}"
    hashed = hashlib.sha256(key.encode()).hexdigest()
    return key, hashed


def hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


_brute_force_store: dict[str, tuple[int, float]] = {}


def record_login_attempt(user_id: str, success: bool) -> dict:
    """Record a login attempt for brute force protection."""
    global _brute_force_store
    key = f"login:{user_id}"
    current_time = time.time()

    if key in _brute_force_store:
        attempts, first_attempt_time = _brute_force_store[key]
        if current_time - first_attempt_time > 900:
            attempts = 0
            first_attempt_time = current_time
    else:
        attempts = 0
        first_attempt_time = current_time

    if success:
        if key in _brute_force_store:
            del _brute_force_store[key]
    else:
        attempts += 1
        _brute_force_store[key] = (attempts, first_attempt_time)

    return {
        "attempts": attempts,
        "locked": attempts >= 5,
        "lock_until": datetime.fromtimestamp(first_attempt_time + 900, tz=timezone.utc) if attempts >= 5 else None
    }


def is_account_locked(user_id: str) -> bool:
    """Check if an account is currently locked due to failed attempts."""
    key = f"login:{user_id}"
    if key not in _brute_force_store:
        return False

    attempts, first_attempt_time = _brute_force_store[key]
    if time.time() - first_attempt_time > 900:
        del _brute_force_store[key]
        return False

    return attempts >= 5


def get_login_attempts(user_id: str, window_minutes: int = 15) -> int:
    """Get the number of login attempts within the window."""
    key = f"login:{user_id}"
    if key not in _brute_force_store:
        return 0

    attempts, first_attempt_time = _brute_force_store[key]
    if time.time() - first_attempt_time > window_minutes * 60:
        return 0

    return attempts


def sanitize_input(value: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not value:
        return ""
    replacements = {
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;"
    }
    result = value
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    return result


def sanitize_html(value: str) -> str:
    """Remove HTML tags from input."""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', value)


def rate_limit_key_user(user_id: str) -> str:
    """Generate rate limit key for a user."""
    return f"ratelimit:user:{user_id}"


def rate_limit_key_ip(ip_address: str) -> str:
    """Generate rate limit key for an IP address."""
    return f"ratelimit:ip:{ip_address}"


def rate_limit_key_endpoint(user_id: str, endpoint: str) -> str:
    """Generate rate limit key for endpoint per user."""
    return f"ratelimit:endpoint:{user_id}:{endpoint}"


def generate_session_id() -> str:
    """Generate a unique session identifier."""
    return f"sess_{secrets.token_urlsafe(48)}"


def hash_file_content(content: bytes) -> str:
    """Generate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()