import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.features.chats import service
from app.features.chats.schemas import (
    ChatCreate,
    ChatRead,
    ChatUpdate,
    Exchange,
    MessageCreate,
    MessageRead,
)
from app.features.users.router import active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])

_NOT_FOUND = "Chat não encontrado"
_BAD_MATERIALS = "Algum dos materiais não existe na biblioteca"


def _owned(user: dict, chat_id: str) -> dict:
    chat = service.get_chat(user["user_id"], chat_id)
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    return chat


@router.get("", response_model=list[ChatRead])
def list_chats(user: dict = Depends(active_user)):
    library = service.library_of(user["user_id"])
    return [service.to_read(c, library) for c in service.list_chats(user["user_id"])]


@router.post("", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
def create_chat(payload: ChatCreate, user: dict = Depends(active_user)):
    try:
        chat = service.create_chat(user["user_id"], payload)
    except service.UnknownMaterials:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _BAD_MATERIALS)
    return service.to_read(chat, service.library_of(user["user_id"]))


@router.get("/{chat_id}", response_model=ChatRead)
def get_chat(chat_id: str, user: dict = Depends(active_user)):
    return service.to_read(_owned(user, chat_id), service.library_of(user["user_id"]))


@router.patch("/{chat_id}", response_model=ChatRead)
def update_chat(chat_id: str, payload: ChatUpdate, user: dict = Depends(active_user)):
    try:
        chat = service.update_chat(user["user_id"], chat_id, payload)
    except service.UnknownMaterials:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, _BAD_MATERIALS)
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    return service.to_read(chat, service.library_of(user["user_id"]))


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: str, user: dict = Depends(active_user)):
    if not service.delete_chat(user["user_id"], chat_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)


@router.get("/{chat_id}/messages", response_model=list[MessageRead])
def list_messages(chat_id: str, user: dict = Depends(active_user)):
    _owned(user, chat_id)
    return service.list_messages(chat_id)


@router.post("/{chat_id}/messages", response_model=Exchange)
async def send_message(chat_id: str, payload: MessageCreate, user: dict = Depends(active_user)):
    chat = _owned(user, chat_id)
    try:
        question, answer = await service.send_message(user["user_id"], chat, payload.content)
    except service.Blocked as e:
        raise HTTPException(e.status, str(e))
    except Exception:
        # Ex.: o Bedrock fora do ar. A conversa não é alterada.
        logger.exception("Falha ao responder no chat %s", chat_id)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Não foi possível gerar a resposta agora. Tente novamente.",
        )
    return Exchange(question=question, answer=answer)
