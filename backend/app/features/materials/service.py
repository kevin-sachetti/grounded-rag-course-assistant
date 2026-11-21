import re
import uuid
from pathlib import PurePosixPath, PureWindowsPath

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.storage import get_storage
from app.adapters.vectorstore import delete_chunks
from app.features.materials.models import Material

_AUDIO_EXT = {"mp3", "wav", "m4a", "ogg", "flac", "aac"}
_VIDEO_EXT = {"mp4", "mov", "mkv", "avi", "webm"}
_TEXT_EXT = {"txt", "md"}
SUPPORTED_EXT = _AUDIO_EXT | _VIDEO_EXT | _TEXT_EXT | {"pdf"}


class UploadError(Exception):
    """Envio recusado. `status` é o código HTTP; a mensagem vai para o usuário."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def clean_filename(filename: str | None) -> str:
    """Só o nome do arquivo, sem pastas, como o usuário vê.

    O navegador manda só o nome, mas um cliente qualquer pode mandar um
    caminho ("../../algo"). Tirar as pastas impede gravar fora da pasta de envios.
    """
    name = PureWindowsPath(PurePosixPath(filename or "").name).name
    return name.strip()


def _extension(filename: str) -> str:
    return filename.lower().rsplit(".", 1)[-1] if "." in filename else ""


def _detect_media_type(filename: str) -> str:
    ext = _extension(filename)
    if ext in _AUDIO_EXT:
        return "audio"
    if ext in _VIDEO_EXT:
        return "video"
    if ext == "pdf":
        return "pdf"
    if ext in _TEXT_EXT:
        return "text"
    return "other"


def validate_upload(filename: str) -> None:
    """Recusa nome vazio e formato sem suporte antes de receber o arquivo inteiro."""
    if not filename:
        raise UploadError(422, "O arquivo precisa ter um nome.")
    if _extension(filename) not in SUPPORTED_EXT:
        raise UploadError(
            415,
            "Formato não suportado. Envie texto (.txt, .md), PDF, áudio "
            "(.mp3, .wav, .m4a, .ogg, .flac, .aac) ou vídeo (.mp4, .mov, .mkv, .avi, .webm).",
        )


async def name_in_use(session: AsyncSession, filename: str) -> bool:
    """Já existe um material com esse nome? Sem diferenciar maiúsculas de minúsculas."""
    result = await session.execute(
        select(Material.id).where(func.lower(Material.filename) == filename.lower()).limit(1)
    )
    return result.first() is not None


async def create_material(
    session: AsyncSession,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> Material:
    material_id = uuid.uuid4()
    # A chave no disco não usa o nome do usuário além do necessário: só
    # letras, números, ponto, hífen e sublinhado.
    safe = re.sub(r"[^\w.-]", "_", filename)[:150]
    key = f"{material_id}_{safe}"
    await get_storage().save(key, data)

    material = Material(
        id=material_id,
        filename=filename,
        content_type=content_type,
        media_type=_detect_media_type(filename),
        storage_key=key,
        status="pending",
    )
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return material


async def list_materials(session: AsyncSession) -> list[Material]:
    result = await session.execute(select(Material).order_by(Material.created_at.desc()))
    return list(result.scalars().all())


async def get_material(session: AsyncSession, material_id: uuid.UUID) -> Material | None:
    return await session.get(Material, material_id)


async def get_materials(
    session: AsyncSession, material_ids: list[uuid.UUID]
) -> list[Material]:
    if not material_ids:
        return []
    result = await session.execute(select(Material).where(Material.id.in_(material_ids)))
    return list(result.scalars().all())


async def delete_material(session: AsyncSession, material_id: uuid.UUID) -> bool:
    """Apaga o material: vetores, arquivo e registro.

    O banco remove sozinho a ligação com os chats que o usavam (ON DELETE CASCADE).
    """
    material = await session.get(Material, material_id)
    if material is None:
        return False
    await delete_chunks(material.id, material.chunk_count)
    await get_storage().delete(material.storage_key)
    await session.delete(material)
    await session.commit()
    return True
