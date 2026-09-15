import asyncio
import logging
from uuid import UUID

from app.adapters.storage import get_storage
from app.adapters.vectorstore import add_chunks, delete_chunks
from app.features.materials.models import Material
from app.infra.db import SessionLocal
from app.pipeline.ingestion.loader import extract_text
from app.pipeline.ingestion.splitter import split_text

logger = logging.getLogger(__name__)


async def ingest_material(material_id: UUID) -> None:
    """Processa um material de ponta a ponta, em sessão própria (roda em background).

    Fluxo: extrai texto → quebra em chunks → gera embeddings → guarda no índice.
    O status acompanha o processo: processing → done (ou error).
    """
    async with SessionLocal() as session:
        material = await session.get(Material, material_id)
        if material is None:
            logger.warning("Material %s não encontrado para ingestão", material_id)
            return

        material.status = "processing"
        await session.commit()

        try:
            # Reprocessamento: limpa os vetores antigos antes, senão os chunks
            # da execução anterior ficariam duplicados no índice.
            await delete_chunks(material.id, material.chunk_count)

            path = get_storage().full_path(material.storage_key)

            # extract_text e split_text são trabalho pesado e SÍNCRONO — a
            # transcrição de um vídeo longo leva minutos. Rodando direto aqui,
            # travariam o laço de eventos e a API inteira pararia de responder
            # enquanto isso. Por isso vão para uma thread separada.
            text = await asyncio.to_thread(extract_text, material.media_type, path)
            chunks = await asyncio.to_thread(split_text, text)

            await add_chunks(material.course_id, material.id, chunks)

            material.text = text
            material.chunk_count = len(chunks)
            material.status = "done"
            await session.commit()
            logger.info("Material %s ingerido: %d chunks", material.id, len(chunks))
        except Exception:
            material.status = "error"
            await session.commit()
            logger.exception("Falha ao ingerir material %s", material.id)
