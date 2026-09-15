from typing import TypedDict
from uuid import UUID

from langchain_core.documents import Document


class RagState(TypedDict, total=False):
    """Estado que passa de nó em nó no grafo do RAG.

    total=False: a entrada inicial só precisa de course_id + question;
    os demais campos vão sendo preenchidos pelos nós ao longo do caminho.
    """

    course_id: UUID
    question: str
    documents: list[Document]  # trechos recuperados
    scores: list[float]  # relevância de cada trecho (0 a 1, maior = melhor)
    answer: str  # a resposta final
    sources: list[dict]  # de quais trechos a resposta veio
