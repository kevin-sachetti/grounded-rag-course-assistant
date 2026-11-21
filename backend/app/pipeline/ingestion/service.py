import asyncio
import logging
from uuid import UUID

from app.adapters.embeddings import get_embeddings
from app.adapters.storage import get_storage
from app.adapters.vectorstore import add_chunks, delete_chunks
from app.features.materials.models import Material
from app.infra.db import SessionLocal
from app.pipeline.ingestion.loader import extract_text
from app.pipeline.ingestion.progress import Range, clear_progress, set_progress
from app.pipeline.ingestion.splitter import split_text

logger = logging.getLogger(__name__)

# Quanto da barra cada etapa ocupa, por tipo de material. A extração pesa
# muito mais quando é transcrição; nos demais, o grosso é gerar os vetores.
_EXTRACT = {
    "audio": ("transcrevendo o áudio", 80),
    "video": ("transcrevendo o vídeo", 80),
    "pdf": ("lendo o PDF", 15),
    "text": ("lendo o texto", 5),
}


async def ingest_material(material_id: UUID) -> None:
    """Processa um material de ponta a ponta, em sessão própria (roda em background).

    Fluxo: extrai texto → quebra em chunks → gera embeddings → guarda no índice.
    O status acompanha o processo: processing → done (ou error), e o
    progresso de cada etapa fica em `progress`, para a barra da interface.
    """
    async with SessionLocal() as session:
        material = await session.get(Material, material_id)
        if material is None:
            logger.warning("Material %s não encontrado para ingestão", material_id)
            return

        material.status = "processing"
        await session.commit()

        try:
            stage, extract_end = _EXTRACT.get(material.media_type, ("lendo o arquivo", 5))
            set_progress(material.id, stage, 0)

            # Reprocessamento: limpa os vetores antigos antes, senão os chunks
            # da execução anterior ficariam duplicados no índice.
            await delete_chunks(material.id, material.chunk_count)

            path = get_storage().full_path(material.storage_key)

            # extract_text e split_text são trabalho pesado e SÍNCRONO — a
            # transcrição de um vídeo longo leva minutos. Rodando direto aqui,
            # travariam o laço de eventos e a API inteira pararia de responder
            # enquanto isso. Por isso vão para uma thread separada.
            text = await asyncio.to_thread(
                extract_text, material.media_type, path, Range(material.id, stage, 0, extract_end)
            )
            if not text.strip():
                raise ValueError("Nenhum texto encontrado no arquivo")

            set_progress(material.id, "dividindo em trechos", extract_end)
            chunks = await asyncio.to_thread(split_text, text)

            # Na primeira vez, carregar o modelo inclui baixá-lo (~2 GB).
            set_progress(material.id, "carregando o modelo de busca", extract_end)
            await asyncio.to_thread(get_embeddings)

            await add_chunks(
                material.id, chunks, Range(material.id, "gerando os vetores", extract_end, 100)
            )

            material.text = text
            material.chunk_count = len(chunks)
            material.status = "done"
            await session.commit()
            logger.info("Material %s ingerido: %d chunks", material.id, len(chunks))
        except Exception:
            material.status = "error"
            await session.commit()
            logger.exception("Falha ao ingerir material %s", material.id)
        finally:
            clear_progress(material.id)
