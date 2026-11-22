"""Processamento de um material: texto → trechos → vetores → S3.

Na AWS roda na Lambda de ingestão, chamada pela API sem esperar a resposta.
O progresso vai para o DynamoDB, porque a API, que mostra a barra, é outra
Lambda e não enxerga a memória desta.
"""
import logging
import os
import tempfile

import numpy as np

from app.adapters import storage
from app.adapters.vectorstore import embed_chunks
from app.features import usage
from app.features.materials import service as materials
from app.infra.config import settings
from app.pipeline.ingestion.loader import extract_text
from app.pipeline.ingestion.splitter import split_text

logger = logging.getLogger(__name__)

# Quanto da barra a leitura ocupa; o resto é gerar os vetores.
_READ = {"pdf": ("lendo o PDF", 15), "document": ("lendo o documento", 10), "text": ("lendo o texto", 5)}
_BATCH = 8  # trechos vetorizados por vez (e por atualização da barra)


def ingest_material(user_id: str, material_id: str) -> None:
    material = materials.get_material(user_id, material_id)
    if material is None or material["status"] not in ("pending", "processing"):
        logger.warning("Material %s não está pronto para processar", material_id)
        return

    stage, read_end = _READ.get(material["media_type"], ("lendo o arquivo", 5))
    try:
        materials.set_progress(user_id, material_id, stage, 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, os.path.basename(material["s3_key"]))
            storage.download(material["s3_key"], path)
            text = extract_text(
                material["media_type"], path,
                lambda f: materials.set_progress(user_id, material_id, stage, read_end * f),
            )
        if not text.strip():
            raise ValueError("Nenhum texto encontrado no arquivo")

        materials.set_progress(user_id, material_id, "dividindo em trechos", read_end)
        chunks = split_text(text)

        vectors = []
        for start in range(0, len(chunks), _BATCH):
            vectors.append(embed_chunks(chunks[start:start + _BATCH]))
            done = min(start + _BATCH, len(chunks)) / len(chunks)
            materials.set_progress(
                user_id, material_id, "gerando os vetores", read_end + (100 - read_end) * done
            )

        storage.save_index(user_id, material_id, chunks, np.vstack(vectors))
        materials.finish(user_id, material_id, "done", len(chunks))
        usage.add_cost(len(chunks) * settings.cost_per_chunk_usd)
        logger.info("Material %s processado: %d trechos", material_id, len(chunks))
    except Exception:
        materials.finish(user_id, material_id, "error")
        logger.exception("Falha ao processar o material %s", material_id)
