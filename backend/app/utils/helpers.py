"""Helper utilities."""
import uuid
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def hash_data(data: str, algorithm: str = "sha256") -> str:
    """Hash data using specified algorithm."""
    if algorithm == "sha256":
        return hashlib.sha256(data.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(data.encode()).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(data.encode()).hexdigest()
    return hashlib.sha256(data.encode()).hexdigest()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string."""
    if not dt:
        return ""
    return dt.strftime(format_str)


def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_input(value: str) -> str:
    """Sanitize user input."""
    if not value:
        return ""
    import re
    value = re.sub(r'[<>"\';]', '', value)
    return value.strip()


async def paginate_query(
    db: AsyncSession,
    query: select,
    page: int = 1,
    page_size: int = 20
) -> Tuple[list, int]:
    """Paginate a SQLAlchemy query."""
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return items, total


def calculate_expiry(seconds: int) -> datetime:
    """Calculate expiry datetime."""
    return datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(seconds=seconds)


from datetime import timedelta