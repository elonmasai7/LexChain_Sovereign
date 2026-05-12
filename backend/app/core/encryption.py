"""Encryption service for sensitive data at rest."""
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self, key: str | None = None):
        if key:
            key_bytes = key.encode() if isinstance(key, str) else key
            key_hash = hashlib.sha256(key_bytes).digest()
            self.fernet = Fernet(base64.urlsafe_b64encode(key_hash))
        else:
            self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())

    def encrypt(self, data: str | bytes) -> bytes:
        """Encrypt data using Fernet symmetric encryption."""
        if isinstance(data, str):
            data = data.encode()
        return self.fernet.encrypt(data)

    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt Fernet-encrypted data."""
        try:
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted.decode()
        except InvalidToken:
            raise ValueError("Invalid encrypted data or key")

    def encrypt_json(self, data: dict) -> bytes:
        """Encrypt a JSON-serializable dictionary."""
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_json(self, encrypted: bytes) -> dict:
        """Decrypt to a JSON-serializable dictionary."""
        import json
        decrypted = self.decrypt(encrypted)
        return json.loads(decrypted)

    def hash_file(self, file_content: bytes) -> str:
        """Generate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    async def hash_file_chunked(self, file_path: str, chunk_size: int = 8192) -> str:
        """Generate SHA-256 hash of a large file in chunks."""
        sha256_hash = hashlib.sha256()

        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet-compatible encryption key."""
        return Fernet.generate_key().decode()

    def rotate_key(self, old_key: str, new_key: str, data: bytes) -> bytes:
        """Re-encrypt data with a new key."""
        old_service = EncryptionService(old_key)
        decrypted = old_service.decrypt(data)
        return self.encrypt(decrypted)


encryption_service = EncryptionService()


import aiofiles