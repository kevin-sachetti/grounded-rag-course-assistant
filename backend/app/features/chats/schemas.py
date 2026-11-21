import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatParams(BaseModel):
    """Parâmetros ajustáveis de um chat. Todos opcionais: o que não vier
    fica com o valor inicial (na criação) ou com o valor atual (na edição)."""

    temperature: float | None = Field(default=None, ge=0, le=2)
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)
    retrieval_k: int | None = Field(default=None, ge=1, le=10)
    use_reranker: bool | None = None
    use_agent: bool | None = None


class ChatCreate(ChatParams):
    name: str = Field(min_length=1, max_length=200)
    material_ids: list[uuid.UUID] = []


class ChatUpdate(ChatParams):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    # None = não mexe nos materiais; lista (mesmo vazia) = substitui.
    material_ids: list[uuid.UUID] | None = None


class ChatMaterial(BaseModel):
    """Resumo de um material dentro de um chat."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    media_type: str
    status: str


class ChatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    temperature: float
    similarity_threshold: float
    retrieval_k: int
    use_reranker: bool
    use_agent: bool
    materials: list[ChatMaterial]
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chat_id: uuid.UUID
    role: str  # user | assistant
    content: str
    refused: bool
    # Só nas respostas: o processamento, para o painel "entender a resposta".
    # Formato descrito em app/pipeline/answer.py.
    details: dict | None
    created_at: datetime


class Exchange(BaseModel):
    """Pergunta e resposta salvas, devolvidas juntas ao enviar uma mensagem."""

    question: MessageRead
    answer: MessageRead
