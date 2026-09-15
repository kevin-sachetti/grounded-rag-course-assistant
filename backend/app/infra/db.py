from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.infra.config import settings

# Engine assíncrono (usa o driver psycopg 3).
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

# Fábrica de sessões.
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM (tabelas)."""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependência do FastAPI que fornece uma sessão de banco por requisição."""
    async with SessionLocal() as session:
        yield session
