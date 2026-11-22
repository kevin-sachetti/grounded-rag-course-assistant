from pydantic import BaseModel, Field


class ChatParams(BaseModel):
    """Parâmetros ajustáveis de um chat. Todos opcionais: o que não vier
    fica com o valor inicial (na criação) ou com o valor atual (na edição).

    Na versão AWS não há a chave do agente: toda resposta usa o fluxo fixo.
    """

    temperature: float | None = Field(default=None, ge=0, le=1)
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)
    retrieval_k: int | None = Field(default=None, ge=1, le=10)
    use_reranker: bool | None = None


class ChatCreate(ChatParams):
    name: str = Field(min_length=1, max_length=200)
    material_ids: list[str] = Field(min_length=1)


class ChatUpdate(ChatParams):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    # None = não mexe nos materiais; lista = substitui (com pelo menos um).
    material_ids: list[str] | None = Field(default=None, min_length=1)


class ChatMaterial(BaseModel):
    """Resumo de um material dentro de um chat."""

    id: str
    filename: str
    media_type: str
    status: str


class ChatRead(BaseModel):
    id: str
    name: str
    temperature: float
    similarity_threshold: float
    retrieval_k: int
    use_reranker: bool
    materials: list[ChatMaterial]
    created_at: str
    updated_at: str


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageRead(BaseModel):
    id: str
    chat_id: str
    role: str  # user | assistant
    content: str
    refused: bool
    # Só nas respostas: o processamento, para o painel "entender a resposta".
    # Formato descrito em app/pipeline/answer.py.
    details: dict | None = None
    created_at: str


class Exchange(BaseModel):
    """Pergunta e resposta salvas, devolvidas juntas ao enviar uma mensagem."""

    question: MessageRead
    answer: MessageRead
