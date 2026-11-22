import math
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.infra.config import settings


@lru_cache
def get_reranker() -> CrossEncoder:
    """Cross-encoder usado para reavaliar os candidatos. Carregado uma vez.

    Diferente do modelo de embeddings, ele recebe pergunta e trecho JUNTOS e
    devolve uma nota de relevância — por isso separa muito melhor, mas não dá
    para pré-calcular: roda uma passada por candidato, a cada pergunta.
    """
    return CrossEncoder(settings.reranker_model_name)


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


def score(question: str, texts: list[str]) -> list[float]:
    """Nota de relevância (0 a 1) de cada texto para a pergunta, na mesma ordem.

    Não corta nem reordena: quem chama decide o que fazer com as notas. Assim
    a nota de todos os candidatos fica disponível para o painel da interface.
    """
    if not texts:
        return []
    pairs = [(question, t) for t in texts]
    return _to_relevance(get_reranker().predict(pairs))
