from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.infra.config import settings

from app.features.chats.router import router as chats_router
from app.features.materials.router import router as materials_router
from app.infra.db import Base, engine
from app.infra.logging import setup_logging

# Importa os modelos para que fiquem registrados em Base.metadata antes do create_all.
from app.features.chats import models as _chats_models  # noqa: F401
from app.features.materials import models as _materials_models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # TEMPORÁRIO: cria na subida as tabelas que ainda não existem. Não altera
    # tabelas existentes, então mudar o schema exige recriá-las. O projeto
    # ainda não usa ferramenta de migração.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Grounded RAG Assistant",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(materials_router)
app.include_router(chats_router)


@app.get("/")
async def root():
    return {"app": "Grounded RAG Assistant", "docs": "/docs"}


@app.get("/health")
async def health():
    """Verifica se a API está de pé, se conecta no banco e se o pgvector está ativo."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        result = await conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        has_vector = result.first() is not None

    return {
        "status": "ok",
        "database": "connected",
        "pgvector": has_vector,
    }
