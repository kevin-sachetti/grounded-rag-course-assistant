import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.chats import service
from app.features.chats.schemas import (
    ChatCreate,
    ChatRead,
    ChatUpdate,
    Exchange,
    MessageCreate,
    MessageRead,
)
from app.infra.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])

_NOT_FOUND = "Chat não encontrado"
_BAD_MATERIALS = "Algum dos materiais escolhidos não existe na biblioteca"


@router.get("", response_model=list[ChatRead])
async def list_chats(session: AsyncSession = Depends(get_session)):
    return await service.list_chats(session)


@router.post("", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
async def create_chat(data: ChatCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await service.create_chat(session, data)
    except service.UnknownMaterials:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _BAD_MATERIALS)


@router.get("/{chat_id}", response_model=ChatRead)
async def get_chat(chat_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    chat = await service.get_chat(session, chat_id)
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    return chat


@router.patch("/{chat_id}", response_model=ChatRead)
async def update_chat(
    chat_id: uuid.UUID, data: ChatUpdate, session: AsyncSession = Depends(get_session)
):
    try:
        chat = await service.update_chat(session, chat_id, data)
    except service.UnknownMaterials:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _BAD_MATERIALS)
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    if not await service.delete_chat(session, chat_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)


@router.get("/{chat_id}/messages", response_model=list[MessageRead])
async def list_messages(chat_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    if await service.get_chat(session, chat_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    return await service.list_messages(session, chat_id)


@router.post("/{chat_id}/messages", response_model=Exchange)
async def send_message(
    chat_id: uuid.UUID, payload: MessageCreate, session: AsyncSession = Depends(get_session)
):
    chat = await service.get_chat(session, chat_id)
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    try:
        question, answer = await service.send_message(session, chat, payload.content)
    except Exception:
        # Ex.: o Ollama fora do ar. A conversa não é alterada.
        logger.exception("Falha ao responder no chat %s", chat_id)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Não foi possível gerar a resposta agora. Tente novamente.",
        )
    return Exchange(question=question, answer=answer)
