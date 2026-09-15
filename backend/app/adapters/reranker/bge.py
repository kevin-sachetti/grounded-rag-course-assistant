import math
from functools import lru_cache

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from app.infra.config import settings


@lru_cache
def get_reranker() -> CrossEncoder:
    """Cross-encoder usado para reordenar os candidatos. Carregado uma vez.

    Diferente do modelo de embeddings, ele recebe pergunta e trecho JUNTOS e
    devolve uma nota de relevância — por isso separa muito melhor, mas não dá
    para pré-calcular: roda uma passada por candidato, a cada pergunta.
    """
    return CrossEncoder(
        settings.reranker_model_name,
        trust_remote_code=settings.reranker_trust_remote_code,
    )


def _to_relevance(raw_scores) -> list[float]:
    """Normaliza as notas para a faixa 0–1.

    O bge-reranker devolve logits (podem ser negativos ou > 1). Dependendo da
    versão, o sentence-transformers já aplica a sigmoide — então só aplicamos
    quando os valores estiverem fora da faixa, evitando aplicar duas vezes.
    """
    scores = [float(s) for s in raw_scores]
    if all(0.0 <= s <= 1.0 for s in scores):
        return scores
    return [1.0 / (1.0 + math.exp(-s)) for s in scores]


def rerank(
    question: str, documents: list[Document], top_k: int
) -> tuple[list[Document], list[float]]:
    """Reordena os documentos por relevância à pergunta e devolve os top_k."""
    if not documents:
        return [], []

    pairs = [(question, doc.page_content) for doc in documents]
    scores = _to_relevance(get_reranker().predict(pairs))

    ranked = sorted(zip(documents, scores), key=lambda ds: ds[1], reverse=True)
    best = ranked[:top_k]
    return [doc for doc, _ in best], [score for _, score in best]
