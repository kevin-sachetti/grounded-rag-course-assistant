import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaterialRead(BaseModel):
    """Representação de um material retornada pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    filename: str
    content_type: str | None
    media_type: str
    status: str
    created_at: datetime
    updated_at: datetime
