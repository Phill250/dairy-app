import uuid
from datetime import datetime
from pydantic import BaseModel


class AdminUserSummary(BaseModel):
    """
    Deliberately excludes name and email -- admin visibility stays
    non-identifying, consistent with the aggregate-only design used
    throughout the rest of the admin role (see MetricsRead).
    """
    id: uuid.UUID
    created_at: datetime | None
    cow_count: int
    log_count: int