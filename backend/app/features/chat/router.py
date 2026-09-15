import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.chat import service
from app.features.chat.schemas import ChatRequest, ChatResponse
from app.features.courses import service as courses_service
from app.infra.db import get_session

router = APIRouter(tags=["chat"])


@router.post("/courses/{course_id}/chat", response_model=ChatResponse)
async def chat(
    course_id: uuid.UUID,
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    course = await courses_service.get_course(session, course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não encontrado")

    result = await service.answer_question(course_id, payload.question)
    return ChatResponse(answer=result["answer"], sources=result.get("sources", []))
