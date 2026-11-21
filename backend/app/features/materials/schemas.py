import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaterialRead(BaseModel):
    """Representação de um material da biblioteca retornada pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str | None
    media_type: str
    status: str  # pending | processing | done | error
    chunk_count: int
    # Só enquanto o material é processado: a etapa atual e o percentual (0 a 100).
    stage: str | None = None
    progress: int | None = None
    created_at: datetime
    updated_at: datetime
