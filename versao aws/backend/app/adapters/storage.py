"""Arquivos no S3: os originais enviados e os trechos e vetores de cada material.

Estrutura no bucket de dados (privado):

    usuarios/{user_id}/materiais/{material_id}/original.{ext}
    usuarios/{user_id}/materiais/{material_id}/trechos.json
    usuarios/{user_id}/materiais/{material_id}/vetores.npy
"""
import io
import json

import numpy as np
from botocore.exceptions import ClientError

from app.infra.aws import s3, s3_public
from app.infra.config import settings


def user_prefix(user_id: str) -> str:
    return f"usuarios/{user_id}/"


def material_prefix(user_id: str, material_id: str) -> str:
    return f"{user_prefix(user_id)}materiais/{material_id}/"


def original_key(user_id: str, material_id: str, extension: str) -> str:
    return f"{material_prefix(user_id, material_id)}original.{extension}"


def upload_form(key: str, max_bytes: int) -> dict:
    """Endereço temporário para o navegador enviar o arquivo direto ao S3.

    O próprio S3 recusa o envio se passar de `max_bytes` (o espaço que o
    usuário ainda tem), então o limite não depende do navegador.
    """
    return s3_public().generate_presigned_post(
        Bucket=settings.data_bucket,
        Key=key,
        Conditions=[["content-length-range", 1, max_bytes]],
        ExpiresIn=settings.upload_url_seconds,
    )


def object_size(key: str) -> int | None:
    """Tamanho do arquivo no S3, ou None se ele não existe."""
    try:
        return s3().head_object(Bucket=settings.data_bucket, Key=key)["ContentLength"]
    except ClientError:
        return None


def download(key: str, path: str) -> None:
    s3().download_file(settings.data_bucket, key, path)


def save_index(user_id: str, material_id: str, chunks: list[str], vectors: np.ndarray) -> None:
    prefix = material_prefix(user_id, material_id)
    s3().put_object(
        Bucket=settings.data_bucket,
        Key=f"{prefix}trechos.json",
        Body=json.dumps(chunks, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
    buffer = io.BytesIO()
    np.save(buffer, vectors.astype(np.float32))
    s3().put_object(Bucket=settings.data_bucket, Key=f"{prefix}vetores.npy", Body=buffer.getvalue())


def load_index(user_id: str, material_id: str) -> tuple[list[str], np.ndarray]:
    prefix = material_prefix(user_id, material_id)
    body = s3().get_object(Bucket=settings.data_bucket, Key=f"{prefix}trechos.json")["Body"].read()
    chunks = json.loads(body)
    raw = s3().get_object(Bucket=settings.data_bucket, Key=f"{prefix}vetores.npy")["Body"].read()
    return chunks, np.load(io.BytesIO(raw))


def delete_prefix(prefix: str) -> None:
    """Apaga tudo o que está sob o prefixo (um material ou um usuário inteiro)."""
    paginator = s3().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=settings.data_bucket, Prefix=prefix):
        keys = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if keys:
            s3().delete_objects(Bucket=settings.data_bucket, Delete={"Objects": keys})
