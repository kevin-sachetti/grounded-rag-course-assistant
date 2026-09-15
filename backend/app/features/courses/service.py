import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.courses.models import Course
from app.features.courses.schemas import CourseCreate, CourseUpdate
from app.features.materials.models import Material
from app.features.materials.service import purge_material_resources


async def list_courses(session: AsyncSession) -> list[Course]:
    result = await session.execute(select(Course).order_by(Course.created_at.desc()))
    return list(result.scalars().all())


async def get_course(session: AsyncSession, course_id: uuid.UUID) -> Course | None:
    return await session.get(Course, course_id)


async def create_course(session: AsyncSession, data: CourseCreate) -> Course:
    course = Course(name=data.name, description=data.description)
    session.add(course)
    await session.commit()
    await session.refresh(course)
    return course


async def update_course(
    session: AsyncSession, course_id: uuid.UUID, data: CourseUpdate
) -> Course | None:
    course = await session.get(Course, course_id)
    if course is None:
        return None

    # exclude_unset: só altera os campos que vieram no corpo da requisição.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    await session.commit()
    await session.refresh(course)
    return course


async def delete_course(session: AsyncSession, course_id: uuid.UUID) -> bool:
    course = await session.get(Course, course_id)
    if course is None:
        return False

    # O banco apaga os materiais em cascata (ON DELETE CASCADE), mas os vetores
    # e os arquivos ficam fora do banco. Sem esta limpeza eles sobrariam órfãos,
    # e o conteúdo do curso apagado continuaria no índice.
    result = await session.execute(
        select(Material).where(Material.course_id == course_id)
    )
    for material in result.scalars().all():
        await purge_material_resources(material)

    await session.delete(course)
    await session.commit()
    return True
