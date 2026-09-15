import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    """Dados para criar um curso."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class CourseUpdate(BaseModel):
    """Dados para atualizar um curso (todos opcionais — atualização parcial)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class CourseRead(BaseModel):
    """Representação de um curso retornada pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
