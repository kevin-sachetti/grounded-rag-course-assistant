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
from app.features.materials.models import Material
from app.features.materials.schemas import MaterialRead
from app.infra.config import settings
from app.infra.db import get_session
from app.pipeline.ingestion.progress import get_progress
from app.pipeline.ingestion.service import ingest_material

_CHUNK = 1024 * 1024  # lê o envio em blocos de 1 MB


def _read(material: Material) -> MaterialRead:
    """Material + etapa e percentual do processamento, quando houver."""
    return MaterialRead.model_validate(material).model_copy(update=get_progress(material.id))

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
async def upload_material(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    filename = service.clean_filename(file.filename)
    try:
        service.validate_upload(filename)
        if await service.name_in_use(session, filename):
            raise service.UploadError(
                409, f"Já existe um material chamado “{filename}” na biblioteca."
            )
        # Lê em blocos para recusar arquivos grandes demais sem esperar o fim.
        limit = settings.max_upload_mb * 1024 * 1024
        data = bytearray()
        while block := await file.read(_CHUNK):
            data.extend(block)
            if len(data) > limit:
                raise service.UploadError(
                    413, f"O arquivo passa do limite de {settings.max_upload_mb} MB."
                )
        if not data:
            raise service.UploadError(422, "O arquivo está vazio.")
    except service.UploadError as e:
        raise HTTPException(e.status, str(e))

    material = await service.create_material(
        session, filename, file.content_type, bytes(data)
    )
    # Processa o material em segundo plano (transcrição/chunks/embeddings).
    background_tasks.add_task(ingest_material, material.id)
    return _read(material)


@router.get("", response_model=list[MaterialRead])
async def list_materials(session: AsyncSession = Depends(get_session)):
    return [_read(m) for m in await service.list_materials(session)]


@router.get("/{material_id}", response_model=MaterialRead)
async def get_material(
    material_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    material = await service.get_material(session, material_id)
    if material is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material não encontrado")
    return _read(material)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    deleted = await service.delete_material(session, material_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material não encontrado")
