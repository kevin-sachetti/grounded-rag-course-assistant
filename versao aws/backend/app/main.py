from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.features.chats.router import router as chats_router
from app.features.materials.router import router as materials_router
from app.features.users.router import router as users_router
from app.infra.config import settings
from app.infra.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # No computador, cria as tabelas e o bucket nos emuladores. Na AWS quem
    # cria tudo é o template do SAM.
    if settings.local_dev:
        from app.infra.local_setup import create_local_resources

        create_local_resources()
    yield


app = FastAPI(title="Grounded RAG Assistant (AWS)", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(materials_router)
app.include_router(chats_router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Carrega os modelos de busca na inicialização da Lambda, e não na primeira pergunta.
if settings.preload_models:
    from app.adapters.embeddings import get_embeddings
    from app.adapters.reranker import get_reranker

    get_embeddings()
    get_reranker()

# O Mangum traduz o pedido da Function URL para o FastAPI. `lifespan="off"`
# porque na AWS não há o que preparar na subida.
_http = Mangum(app, lifespan="off", api_gateway_base_path=settings.api_base_path)


def handler(event, context):
    """Ponto de entrada da Lambda da API.

    O agendamento manda {"warmup": true} a cada 5 minutos só para manter a
    Lambda carregada, com os modelos na memória; esse pedido não faz nada.
    """
    if isinstance(event, dict) and event.get("warmup"):
        return {"warm": True}
    return _http(event, context)
