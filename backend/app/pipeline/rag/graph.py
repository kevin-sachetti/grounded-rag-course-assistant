from langgraph.graph import END, START, StateGraph

from app.infra.config import settings
from app.pipeline.rag.nodes import generate, rerank, respond_raw, retrieve
from app.pipeline.rag.state import RagState


def _after_retrieve(state: RagState) -> str:
    """Passa pelo re-ranking (2º estágio) ou vai direto responder."""
    return "rerank" if settings.use_reranker else _answer_node()


def _answer_node(state: RagState | None = None) -> str:
    """Resposta reformulada pelo LLM ou os trechos crus."""
    return "generate" if settings.use_llm_reformulation else "respond_raw"


def _build_graph():
    """Fluxo: recuperar → (reordenar) → responder.

    retrieve  1º estágio, busca vetorial ampla (rápida, pouco precisa)
    rerank    2º estágio, cross-encoder reordena (preciso, mais lento)
    generate  resposta reformulada pelo LLM
    respond_raw  resposta extrativa, sem LLM

    A recusa por baixa similaridade (settings.similarity_threshold) entra
    depois, usando a nota do re-ranker — que separa bem melhor que a do e5.
    """
    builder = StateGraph(RagState)

    builder.add_node("retrieve", retrieve)
    builder.add_node("rerank", rerank)
    builder.add_node("respond_raw", respond_raw)
    builder.add_node("generate", generate)

    builder.add_edge(START, "retrieve")

    answer_paths = {"generate": "generate", "respond_raw": "respond_raw"}
    builder.add_conditional_edges(
        "retrieve", _after_retrieve, {"rerank": "rerank", **answer_paths}
    )
    builder.add_conditional_edges("rerank", _answer_node, answer_paths)

    builder.add_edge("respond_raw", END)
    builder.add_edge("generate", END)

    return builder.compile()


graph = _build_graph()
