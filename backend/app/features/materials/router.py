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

from app.features.materials import service
from app.features.materials.schemas import MaterialRead
from app.infra.db import get_session
from app.pipeline.ingestion.service import ingest_material

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
async def upload_material(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    data = await file.read()
    material = await service.create_material(
        session, file.filename, file.content_type, data
    )
    # Processa o material em segundo plano (transcrição/chunks/embeddings).
    background_tasks.add_task(ingest_material, material.id)
    return material


@router.get("", response_model=list[MaterialRead])
async def list_materials(session: AsyncSession = Depends(get_session)):
    return await service.list_materials(session)


@router.get("/{material_id}", response_model=MaterialRead)
async def get_material(
    material_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    material = await service.get_material(session, material_id)
    if material is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material não encontrado")
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    deleted = await service.delete_material(session, material_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material não encontrado")
