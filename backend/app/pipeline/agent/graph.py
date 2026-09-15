from uuid import UUID

from langchain_core.messages import SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.adapters.llm import get_llm
from app.pipeline.agent.prompts import SYSTEM_PROMPT
from app.pipeline.agent.tools import build_tools


def build_agent(course_id: UUID) -> tuple[object, list[dict]]:
    """Monta o agente para um curso e devolve (grafo, coletor de fontes).

    O grafo é montado por requisição — de propósito. As ferramentas ficam
    presas ao curso e a um coletor de fontes próprio, então uma requisição
    nunca enxerga o material ou as fontes de outra. Montar é barato: os
    modelos pesados ficam em cache separado, fora daqui.

    Fluxo (é aqui que está a autonomia):

        agente ─┬─ decide usar ferramenta → ferramentas ─┐
                │                                        │
                │        ←───── volta pro agente ────────┘
                └─ decide que já pode responder → fim

    O agente escolhe QUAL ferramenta usar, pode chamar várias, e repete o
    ciclo até se dar por satisfeito. Nenhuma ferramenta enxerga nada além
    do material do curso — a autonomia é de estratégia, não de fonte.
    """
    sources: list[dict] = []
    tools = build_tools(course_id, sources)
    llm = get_llm().bind_tools(tools)

    async def agent(state: MessagesState) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = await llm.ainvoke(messages)
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "agent")
    # tools_condition: se o modelo pediu ferramenta vai para "tools",
    # senão encerra.
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    return builder.compile(), sources
