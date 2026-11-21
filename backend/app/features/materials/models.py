import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db import Base


class Material(Base):
    """Um material enviado pelo usuário para a biblioteca.

    O material não pertence a um chat: fica na biblioteca e pode ser usado por
    vários chats ao mesmo tempo (ligação em app/features/chats/models.py).
    O arquivo em si fica no storage; aqui guardamos só os metadados + a chave.
    O campo `status` acompanha o processamento da ingestão (transcrição/embeddings).
    """

    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(150), default=None)
    # audio | video | pdf | text | other
    media_type: Mapped[str] = mapped_column(String(20))
    storage_key: Mapped[str] = mapped_column(String(700))
    # Texto extraído na ingestão (transcrição, PDF ou arquivo de texto).
    # Guardado inteiro para a ferramenta de resumo — os chunks ficam no
    # vector store, mas resumir exige o material completo.
    text: Mapped[str | None] = mapped_column(Text, default=None)
    # Quantos chunks este material gerou. Necessário para recalcular os ids
    # dos vetores e poder removê-los do índice.
    chunk_count: Mapped[int] = mapped_column(default=0)
    # pending | processing | done | error
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
