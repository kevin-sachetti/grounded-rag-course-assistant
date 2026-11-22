from langgraph.graph import END, START, StateGraph

from app.pipeline.rag.nodes import generate, refuse, rerank, respond_raw, retrieve
from app.pipeline.rag.state import RagState
from app.pipeline.retrieval import kept


def _answer_node(state: RagState) -> str:
    """Recusa se nenhum trecho foi aceito; senão, resposta com ou sem LLM."""
    if not kept(state.get("candidates", [])):
        return "refuse"
    # Na versão AWS a resposta é sempre redigida pelo Nova Lite.
    return "generate"


def _after_retrieve(state: RagState) -> str:
    """Passa pelo re-ranqueamento (2º estágio) ou vai direto responder."""
    return "rerank" if state["params"].use_reranker else _answer_node(state)


def _build_graph():
    """Fluxo fixo: recuperar → (reordenar) → recusar ou responder.

    retrieve     1º estágio, busca vetorial ampla (rápida, pouco precisa)
    rerank       2º estágio, cross-encoder reordena (preciso, mais lento)
    refuse       nenhum trecho atingiu o limiar de relevância
    generate     resposta reformulada pelo LLM
    respond_raw  resposta extrativa, sem LLM
    """
    builder = StateGraph(RagState)

    builder.add_node("retrieve", retrieve)
    builder.add_node("rerank", rerank)
    builder.add_node("refuse", refuse)
    builder.add_node("respond_raw", respond_raw)
    builder.add_node("generate", generate)

    builder.add_edge(START, "retrieve")

    answer_paths = {"refuse": "refuse", "generate": "generate", "respond_raw": "respond_raw"}
    builder.add_conditional_edges(
        "retrieve", _after_retrieve, {"rerank": "rerank", **answer_paths}
    )
    builder.add_conditional_edges("rerank", _answer_node, answer_paths)

    builder.add_edge("refuse", END)
    builder.add_edge("respond_raw", END)
    builder.add_edge("generate", END)

    return builder.compile()


graph = _build_graph()
