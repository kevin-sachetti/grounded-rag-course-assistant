import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.courses import service
from app.features.courses.schemas import CourseCreate, CourseRead, CourseUpdate
from app.infra.db import get_session

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseRead])
async def list_courses(session: AsyncSession = Depends(get_session)):
    return await service.list_courses(session)


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate, session: AsyncSession = Depends(get_session)
):
    return await service.create_course(session, data)


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(
    course_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    course = await service.get_course(session, course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não encontrado")
    return course


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: uuid.UUID,
    data: CourseUpdate,
    session: AsyncSession = Depends(get_session),
):
    course = await service.update_course(session, course_id, data)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não encontrado")
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    deleted = await service.delete_course(session, course_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não encontrado")
