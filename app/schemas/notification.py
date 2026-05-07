from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class UserNotification(BaseModel):
    telegram_chat_id: Optional[str] = None
    user_id: UUID
    tasks: dict


class PendingNotificationsResponse(BaseModel):
    users: List[UserNotification]
    current_time: str
