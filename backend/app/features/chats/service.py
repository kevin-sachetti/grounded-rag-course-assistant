import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.chats.models import Chat, Message
from app.features.chats.schemas import ChatCreate, ChatUpdate
from app.features.materials.service import get_materials
from app.infra.config import settings
from app.pipeline.answer import answer_question
from app.pipeline.params import AnswerParams

_PARAM_FIELDS = ("temperature", "similarity_threshold", "retrieval_k", "use_reranker", "use_agent")


class UnknownMaterials(Exception):
    """Algum material_id enviado não existe na biblioteca."""


async def _resolve_materials(session: AsyncSession, material_ids: list[uuid.UUID]):
    unique = list(dict.fromkeys(material_ids))
    materials = await get_materials(session, unique)
    if len(materials) != len(unique):
        raise UnknownMaterials()
    return materials


async def list_chats(session: AsyncSession) -> list[Chat]:
    result = await session.execute(select(Chat).order_by(Chat.updated_at.desc()))
    return list(result.scalars().all())


async def get_chat(session: AsyncSession, chat_id: uuid.UUID) -> Chat | None:
    return await session.get(Chat, chat_id)


async def create_chat(session: AsyncSession, data: ChatCreate) -> Chat:
    chat = Chat(name=data.name)
    for field in _PARAM_FIELDS:
        value = getattr(data, field)
        if value is not None:
            setattr(chat, field, value)
    chat.materials = await _resolve_materials(session, data.material_ids)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


async def update_chat(
    session: AsyncSession, chat_id: uuid.UUID, data: ChatUpdate
) -> Chat | None:
    chat = await session.get(Chat, chat_id)
    if chat is None:
        return None
    if data.name is not None:
        chat.name = data.name
    for field in _PARAM_FIELDS:
        value = getattr(data, field)
        if value is not None:
            setattr(chat, field, value)
    if data.material_ids is not None:
        chat.materials = await _resolve_materials(session, data.material_ids)
    chat.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(chat)
    return chat


async def delete_chat(session: AsyncSession, chat_id: uuid.UUID) -> bool:
    """Apaga o chat e, em cascata, as mensagens. Os materiais continuam na biblioteca."""
    chat = await session.get(Chat, chat_id)
    if chat is None:
        return False
    await session.delete(chat)
    await session.commit()
    return True


async def list_messages(session: AsyncSession, chat_id: uuid.UUID) -> list[Message]:
    result = await session.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )
    return list(result.scalars().all())


async def _recent_history(session: AsyncSession, chat_id: uuid.UUID) -> list[tuple[str, str]]:
    """As últimas mensagens do chat, da mais antiga para a mais recente."""
    result = await session.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(settings.chat_history_messages)
    )
    return [(m.role, m.content) for m in reversed(result.scalars().all())]


def _add_material_names(details: dict, names: dict[str, str]) -> None:
    """Põe o nome do arquivo em cada trecho, para o painel mostrar a origem."""
    for search in details["searches"]:
        for c in search["candidates"]:
            c["material_name"] = names.get(c["material_id"])


async def send_message(
    session: AsyncSession, chat: Chat, content: str
) -> tuple[Message, Message]:
    """Responde a pergunta com os materiais e parâmetros do chat e salva as duas mensagens.

    As duas só vão para o banco depois que a resposta fica pronta: se a
    geração falhar, a conversa não fica com uma pergunta sem resposta.
    """
    asked_at = datetime.now(UTC)
    params = AnswerParams(
        temperature=chat.temperature,
        similarity_threshold=chat.similarity_threshold,
        retrieval_k=chat.retrieval_k,
        use_reranker=chat.use_reranker,
    )
    material_ids = [m.id for m in chat.materials]
    history = await _recent_history(session, chat.id)
    result = await answer_question(material_ids, content, params, chat.use_agent, history)
    _add_material_names(result["details"], {str(m.id): m.filename for m in chat.materials})

    question = Message(chat_id=chat.id, role="user", content=content, created_at=asked_at)
    answer = Message(
        chat_id=chat.id,
        role="assistant",
        content=result["answer"],
        refused=result["refused"],
        details=result["details"],
        created_at=datetime.now(UTC),
    )
    session.add_all([question, answer])
    # A conversa mais recente sobe no menu lateral.
    chat.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(question)
    await session.refresh(answer)
    return question, answer
