"""Input validation utilities."""
import re
from typing import Optional
from eth_utils import is_address, to_checksum_address
from app.core.config import settings


class InputValidator:
    """Validation utilities for user inputs."""

    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email or len(email) > 255:
            return False
        return bool(InputValidator.EMAIL_REGEX.match(email))

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength. Returns (is_valid, message)."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        if len(password) > 128:
            return False, "Password must be less than 128 characters"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, "Password is valid"

    @staticmethod
    def validate_wallet_address(address: str, chain: str = 'evm') -> bool:
        """Validate blockchain wallet address."""
        if not address:
            return False

        if chain.lower() == 'evm':
            try:
                return is_address(address)
            except Exception:
                return False

        return len(address) > 20

    @staticmethod
    def validate_did(did: str) -> bool:
        """Validate W3C DID format."""
        if not did:
            return False

        patterns = [
            r'^did:ethr:0x[a-fA-F0-9]{40}$',
            r'^did:web:[a-zA-Z0-9._~/-]+$',
            r'^did:key:z[a-zA-Z0-9]+$'
        ]

        return any(re.match(pattern, did) for pattern in patterns)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        if not filename:
            return "unnamed"

        filename = re.sub(r'[^\w\s.-]', '', filename)
        filename = re.sub(r'[\s]+', '_', filename)
        filename = filename[:255]

        dangerous = ['..', '/', '\\', '\x00', '..']
        for pattern in dangerous:
            filename = filename.replace(pattern, '')

        return filename or "unnamed"

    @staticmethod
    def validate_file_type(filename: str, allowed_types: list[str]) -> bool:
        """Validate file extension against allowed types."""
        if not filename or not allowed_types:
            return False

        extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return extension in [ext.lower().lstrip('.') for ext in allowed_types]

    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
        """Validate file size against maximum."""
        max_bytes = max_size_mb * 1024 * 1024
        return 0 < file_size <= max_bytes

    @staticmethod
    def validate_json_structure(data: dict, schema: dict) -> tuple[bool, str]:
        """Validate JSON data against a simple schema."""
        try:
            for field, rules in schema.items():
                if rules.get('required', False) and field not in data:
                    return False, f"Missing required field: {field}"

                if field in data:
                    value = data[field]
                    field_type = rules.get('type')

                    if field_type == 'string' and not isinstance(value, str):
                        return False, f"{field} must be a string"
                    elif field_type == 'number' and not isinstance(value, (int, float)):
                        return False, f"{field} must be a number"
                    elif field_type == 'boolean' and not isinstance(value, bool):
                        return False, f"{field} must be a boolean"
                    elif field_type == 'array' and not isinstance(value, list):
                        return False, f"{field} must be an array"
                    elif field_type == 'object' and not isinstance(value, dict):
                        return False, f"{field} must be an object"

                    min_len = rules.get('min_length')
                    if min_len and isinstance(value, str) and len(value) < min_len:
                        return False, f"{field} must be at least {min_len} characters"

                    max_len = rules.get('max_length')
                    if max_len and isinstance(value, str) and len(value) > max_len:
                        return False, f"{field} must be at most {max_len} characters"

            return True, "Valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """Validate username format."""
        if not username:
            return False, "Username is required"

        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if len(username) > 50:
            return False, "Username must be less than 50 characters"

        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens"

        return True, "Valid"

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        url_regex = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_regex.match(url))