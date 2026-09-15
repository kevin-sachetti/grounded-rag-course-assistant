import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.storage import get_storage
from app.adapters.vectorstore import delete_chunks
from app.features.materials.models import Material

_AUDIO_EXT = {"mp3", "wav", "m4a", "ogg", "flac", "aac"}
_VIDEO_EXT = {"mp4", "mov", "mkv", "avi", "webm"}


def _detect_media_type(filename: str, content_type: str | None) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    ct = content_type or ""
    if ext in _AUDIO_EXT or ct.startswith("audio"):
        return "audio"
    if ext in _VIDEO_EXT or ct.startswith("video"):
        return "video"
    if ext == "pdf" or ct == "application/pdf":
        return "pdf"
    if ext in {"txt", "md"} or ct.startswith("text"):
        return "text"
    return "other"


async def create_material(
    session: AsyncSession,
    course_id: uuid.UUID,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> Material:
    material_id = uuid.uuid4()
    storage = get_storage()
    key = f"{course_id}/{material_id}_{filename}"
    await storage.save(key, data)

    material = Material(
        id=material_id,
        course_id=course_id,
        filename=filename,
        content_type=content_type,
        media_type=_detect_media_type(filename, content_type),
        storage_key=key,
        status="pending",
    )
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return material


async def list_materials(
    session: AsyncSession, course_id: uuid.UUID
) -> list[Material]:
    result = await session.execute(
        select(Material)
        .where(Material.course_id == course_id)
        .order_by(Material.created_at.desc())
    )
    return list(result.scalars().all())


async def get_material(
    session: AsyncSession, material_id: uuid.UUID
) -> Material | None:
    return await session.get(Material, material_id)


async def purge_material_resources(material: Material) -> None:
    """Remove o que o material tem fora do banco: os vetores e o arquivo.

    O registro no banco não é tocado aqui — quem chama decide como apagá-lo.
    """
    await delete_chunks(material.id, material.chunk_count)
    await get_storage().delete(material.storage_key)


async def delete_material(session: AsyncSession, material_id: uuid.UUID) -> bool:
    material = await session.get(Material, material_id)
    if material is None:
        return False
    await purge_material_resources(material)
    await session.delete(material)
    await session.commit()
    return True
