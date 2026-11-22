import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.features.materials import service
from app.features.materials.schemas import MaterialRead, UploadRequest, UploadTicket
from app.features.users.router import active_user
from app.infra.aws import lambda_client
from app.infra.config import settings
from app.pipeline.ingestion.service import ingest_material

router = APIRouter(prefix="/materials", tags=["materiais"])


def _dispatch(user_id: str, material_id: str, background: BackgroundTasks) -> None:
    """Dispara o processamento: na AWS, na Lambda de ingestão; no computador, aqui mesmo."""
    if settings.ingest_function:
        lambda_client().invoke(
            FunctionName=settings.ingest_function,
            InvocationType="Event",  # não espera terminar
            Payload=json.dumps({"user_id": user_id, "material_id": material_id}).encode(),
        )
    else:
        background.add_task(ingest_material, user_id, material_id)


@router.post("/upload", response_model=UploadTicket, status_code=status.HTTP_201_CREATED)
def start_upload(payload: UploadRequest, user: dict = Depends(active_user)):
    """1ª etapa do envio: registra o material e devolve o endereço de envio ao S3."""
    try:
        material, form = service.start_upload(user, payload.filename, payload.size)
    except service.UploadError as e:
        raise HTTPException(e.status, str(e))
    return UploadTicket(material=service.to_read(material), url=form["url"], fields=form["fields"])


@router.post("/{material_id}/confirm", response_model=MaterialRead)
def confirm_upload(
    material_id: str, background: BackgroundTasks, user: dict = Depends(active_user)
):
    """2ª etapa do envio: o arquivo chegou ao S3; reserva o espaço e processa."""
    try:
        material = service.confirm_upload(user["user_id"], material_id)
    except service.UploadError as e:
        raise HTTPException(e.status, str(e))
    if material["status"] == "pending":
        _dispatch(user["user_id"], material_id, background)
    return service.to_read(material)


@router.get("", response_model=list[MaterialRead])
def list_materials(user: dict = Depends(active_user)):
    return [service.to_read(m) for m in service.list_materials(user["user_id"])]


@router.get("/{material_id}", response_model=MaterialRead)
def get_material(material_id: str, user: dict = Depends(active_user)):
    material = service.get_material(user["user_id"], material_id)
    if material is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material não encontrado")
    return service.to_read(material)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(material_id: str, user: dict = Depends(active_user)):
    if not service.delete_material(user["user_id"], material_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material não encontrado")
