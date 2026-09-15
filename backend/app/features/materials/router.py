import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.courses import service as courses_service
from app.features.materials import service
from app.features.materials.schemas import MaterialRead
from app.infra.db import get_session
from app.pipeline.ingestion.service import ingest_material

router = APIRouter(tags=["materials"])


@router.post(
    "/courses/{course_id}/materials",
    response_model=MaterialRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_material(
    course_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    course = await courses_service.get_course(session, course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não encontrado")

    data = await file.read()
    material = await service.create_material(
        session, course_id, file.filename, file.content_type, data
    )

    # Processa o material em segundo plano (transcrição/chunks/embeddings).
    background_tasks.add_task(ingest_material, material.id)
    return material


@router.get("/courses/{course_id}/materials", response_model=list[MaterialRead])
async def list_materials(
    course_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    return await service.list_materials(session, course_id)


@router.get("/materials/{material_id}", response_model=MaterialRead)
async def get_material(
    material_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    material = await service.get_material(session, material_id)
    if material is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material não encontrado")
    return material


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    deleted = await service.delete_material(session, material_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material não encontrado")
