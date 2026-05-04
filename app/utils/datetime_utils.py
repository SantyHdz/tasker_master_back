from datetime import datetime, timezone
from typing import Optional

def ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware, convert to UTC if naive."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def get_current_utc() -> datetime:
    """Get current time in UTC."""
    return datetime.now(timezone.utc)