from uuid import UUID

from langchain_core.messages import SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.adapters.llm import get_llm
from app.pipeline.agent.prompts import SYSTEM_PROMPT
from app.pipeline.agent.tools import build_tools
from app.pipeline.params import AnswerParams


def build_agent(material_ids: list[UUID], params: AnswerParams) -> tuple[object, dict]:
    """Monta o agente para um chat e devolve (grafo, registro do processamento).

    O grafo é montado por requisição — de propósito. As ferramentas ficam
    presas aos materiais do chat e a um registro próprio, então uma requisição
    nunca enxerga o material ou o processamento de outra. Montar é barato: os
    modelos pesados ficam em cache separado, fora daqui.

    Fluxo (é aqui que está a autonomia):

        agente ─┬─ decide usar ferramenta → ferramentas ─┐
                │                                        │
                │        ←───── volta pro agente ────────┘
                └─ decide que já pode responder → fim

    O agente escolhe QUAL ferramenta usar, pode chamar várias, e repete o
    ciclo até se dar por satisfeito. Nenhuma ferramenta enxerga nada além
    dos materiais do chat — a autonomia é de estratégia, não de fonte.
    """
    trace: dict = {"steps": [], "searches": []}
    tools = build_tools(material_ids, params, trace)
    llm = get_llm(params.temperature).bind_tools(tools)

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

    return builder.compile(), trace
