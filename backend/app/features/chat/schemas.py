from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class Source(BaseModel):
    material_id: str | None = None
    chunk_index: int | None = None
    score: float | None = None  # relevância (0 a 1) — para calibrar o corte


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = []
