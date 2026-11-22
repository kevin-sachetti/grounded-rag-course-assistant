"""Chats e mensagens de cada usuário.

Tabela `chats`, chave `user_id` + `chat_id`: nome, materiais e parâmetros.
Tabela `mensagens`, chave `chat_id` + `sort_key` (data e hora + id, para
ficarem em ordem): pergunta ou resposta, e os detalhes do painel.
"""
import asyncio
import uuid

from boto3.dynamodb.conditions import Key

from app.features import usage
from app.features.materials import service as materials
from app.features.users import service as users
from app.infra.aws import table
from app.infra.clock import iso_now
from app.infra.config import settings
from app.infra.dynamo import from_dynamo, query_all, to_dynamo
from app.pipeline.answer import answer_question
from app.pipeline.params import AnswerParams

_PARAM_FIELDS = ("temperature", "similarity_threshold", "retrieval_k", "use_reranker")
_DEFAULTS = {
    "temperature": 0.6,
    "similarity_threshold": settings.similarity_threshold,
    "retrieval_k": settings.retrieval_k,
    "use_reranker": settings.use_reranker,
}


class UnknownMaterials(Exception):
    """Algum material enviado não existe na biblioteca do usuário."""


class Blocked(Exception):
    """Pergunta recusada pelo teto do mês ou pelo limite do usuário."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _chats():
    return table(settings.table_chats)


def _messages():
    return table(settings.table_messages)


def _check_materials(user_id: str, material_ids: list[str]) -> list[str]:
    unique = list(dict.fromkeys(material_ids))
    mine = {m["material_id"] for m in materials.list_materials(user_id)}
    if not set(unique) <= mine:
        raise UnknownMaterials()
    return unique


def to_read(chat: dict, library: dict[str, dict]) -> dict:
    """Formato da API (ChatRead), com o resumo de cada material."""
    return {
        "id": chat["chat_id"],
        "name": chat["name"],
        **{f: chat[f] for f in _PARAM_FIELDS},
        "materials": [
            {
                "id": m["material_id"],
                "filename": m["filename"],
                "media_type": m["media_type"],
                "status": m["status"],
            }
            for mid in chat.get("material_ids", [])
            if (m := library.get(mid))
        ],
        "created_at": chat["created_at"],
        "updated_at": chat["updated_at"],
    }


def library_of(user_id: str) -> dict[str, dict]:
    return {m["material_id"]: m for m in materials.list_materials(user_id)}


def list_chats(user_id: str) -> list[dict]:
    items = query_all(_chats(), KeyConditionExpression=Key("user_id").eq(user_id))
    return sorted(items, key=lambda c: c["updated_at"], reverse=True)


def get_chat(user_id: str, chat_id: str) -> dict | None:
    item = _chats().get_item(Key={"user_id": user_id, "chat_id": chat_id}).get("Item")
    return from_dynamo(item) if item else None


def create_chat(user_id: str, data) -> dict:
    chat = {
        "user_id": user_id,
        "chat_id": str(uuid.uuid4()),
        "name": data.name,
        "material_ids": _check_materials(user_id, data.material_ids),
        "created_at": iso_now(),
        "updated_at": iso_now(),
    }
    for field in _PARAM_FIELDS:
        value = getattr(data, field)
        chat[field] = _DEFAULTS[field] if value is None else value
    _chats().put_item(Item=to_dynamo(chat))
    return chat


def update_chat(user_id: str, chat_id: str, data) -> dict | None:
    chat = get_chat(user_id, chat_id)
    if chat is None:
        return None
    if data.name is not None:
        chat["name"] = data.name
    for field in _PARAM_FIELDS:
        value = getattr(data, field)
        if value is not None:
            chat[field] = value
    if data.material_ids is not None:
        chat["material_ids"] = _check_materials(user_id, data.material_ids)
    chat["updated_at"] = iso_now()
    _chats().put_item(Item=to_dynamo(chat))
    return chat


def delete_chat(user_id: str, chat_id: str) -> bool:
    """Apaga o chat e as mensagens dele. Os materiais continuam na biblioteca."""
    if get_chat(user_id, chat_id) is None:
        return False
    for m in query_all(_messages(), KeyConditionExpression=Key("chat_id").eq(chat_id)):
        _messages().delete_item(Key={"chat_id": chat_id, "sort_key": m["sort_key"]})
    _chats().delete_item(Key={"user_id": user_id, "chat_id": chat_id})
    return True


def list_messages(chat_id: str) -> list[dict]:
    items = query_all(_messages(), KeyConditionExpression=Key("chat_id").eq(chat_id))
    return [_message_read(m) for m in items]


def _message_read(m: dict) -> dict:
    return {
        "id": m["message_id"],
        "chat_id": m["chat_id"],
        "role": m["role"],
        "content": m["content"],
        "refused": bool(m.get("refused")),
        "details": m.get("details"),
        "created_at": m["created_at"],
    }


def _save_message(chat_id: str, role: str, content: str, refused=False, details=None) -> dict:
    created = iso_now()
    message_id = str(uuid.uuid4())
    item = {
        "chat_id": chat_id,
        "sort_key": f"{created}#{message_id}",
        "message_id": message_id,
        "role": role,
        "content": content,
        "refused": refused,
        "details": details,
        "created_at": created,
    }
    _messages().put_item(Item=to_dynamo(item))
    return _message_read(item)


def _add_material_names(details: dict, library: dict[str, dict]) -> None:
    """Põe o nome do arquivo em cada trecho, para o painel mostrar a origem."""
    for search in details["searches"]:
        for c in search["candidates"]:
            m = library.get(c["material_id"])
            c["material_name"] = m["filename"] if m else None


async def send_message(user_id: str, chat: dict, content: str) -> tuple[dict, dict]:
    """Responde a pergunta com os materiais e parâmetros do chat e salva as duas mensagens.

    Antes de responder, confere o teto do mês e o limite de perguntas do dia.
    As duas mensagens só vão para o banco depois que a resposta fica pronta.
    """
    if await asyncio.to_thread(usage.is_blocked):
        raise Blocked(403, usage.BLOCKED_MESSAGE)
    try:
        await asyncio.to_thread(users.consume_question, user_id)
    except users.QuotaExceeded as e:
        raise Blocked(429, str(e))

    library = await asyncio.to_thread(library_of, user_id)
    ready = [m for m in chat.get("material_ids", []) if library.get(m, {}).get("status") == "done"]
    params = AnswerParams(**{f: chat[f] for f in _PARAM_FIELDS})
    result = await answer_question(user_id, ready, content, params)
    _add_material_names(result["details"], library)

    question = await asyncio.to_thread(_save_message, chat["chat_id"], "user", content)
    answer = await asyncio.to_thread(
        _save_message, chat["chat_id"], "assistant", result["answer"],
        result["refused"], result["details"],
    )
    chat["updated_at"] = iso_now()
    await asyncio.to_thread(_chats().put_item, Item=to_dynamo(chat))
    await asyncio.to_thread(usage.add_cost, settings.cost_per_question_usd, 1)
    return question, answer
