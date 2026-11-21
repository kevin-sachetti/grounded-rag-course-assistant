import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.features.materials.models import Material
from app.infra.config import settings
from app.infra.db import Base

# Ligação muitos-para-muitos: um chat usa vários materiais da biblioteca, e o
# mesmo material pode estar em vários chats. Excluir o chat ou o material
# remove só a ligação; o outro lado continua existindo.
chat_materials = Table(
    "chat_materials",
    Base.metadata,
    Column("chat_id", ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "material_id", ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Chat(Base):
    """Um chatbot criado pelo usuário: nome, materiais e parâmetros próprios.

    Os parâmetros ficam no chat (e não só nas configurações globais) para que
    cada chat possa ser ajustado separadamente na tela "editar chat".
    """

    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))

    # Temperatura do LLM (0 = respostas mais previsíveis).
    temperature: Mapped[float] = mapped_column(Float, default=0.6)
    # Relevância mínima (0 a 1, na escala do re-ranqueador) para um trecho ser usado.
    similarity_threshold: Mapped[float] = mapped_column(
        Float, default=settings.similarity_threshold
    )
    # Quantos trechos sobram no final da busca.
    retrieval_k: Mapped[int] = mapped_column(Integer, default=settings.retrieval_k)
    use_reranker: Mapped[bool] = mapped_column(Boolean, default=settings.use_reranker)
    # Agente ligado por padrão; desligado = fluxo fixo.
    use_agent: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    materials: Mapped[list[Material]] = relationship(
        secondary=chat_materials, lazy="selectin"
    )


class Message(Base):
    """Uma mensagem da conversa de um chat.

    role = "user" para a pergunta e "assistant" para a resposta. Na resposta,
    `details` guarda o que o painel "entender a resposta" mostra: os trechos,
    o material de origem, as notas de cada etapa e as versões da resposta.
    """

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True
    )
    # user | assistant
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    # A resposta foi uma recusa (o material não tem a resposta)?
    refused: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict | None] = mapped_column(JSONB, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
