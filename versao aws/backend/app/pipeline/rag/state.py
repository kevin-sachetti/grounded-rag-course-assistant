from typing import TypedDict

from app.pipeline.params import AnswerParams


class RagState(TypedDict, total=False):
    """Estado que passa de nó em nó no grafo do fluxo fixo.

    total=False: a entrada inicial só precisa de user_id, material_ids, question e
    params; os demais campos vão sendo preenchidos pelos nós.
    """

    user_id: str  # dono do chat (id do Cognito)
    material_ids: list[str]  # materiais do chat
    question: str
    params: AnswerParams
    candidates: list[dict]  # trechos com as notas de cada etapa (ver retrieval.py)
    extractive: str  # versão extrativa: os trechos usados, como estão no material
    answer: str  # a resposta final
    refused: bool  # nenhum trecho atingiu o limiar
