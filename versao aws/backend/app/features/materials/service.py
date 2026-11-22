"""Biblioteca de materiais de cada usuário.

Tabela `materiais`, chave `user_id` + `material_id`. O arquivo e o índice
(trechos e vetores) ficam no S3, em usuarios/{user_id}/materiais/{material_id}/.

O envio tem duas etapas, porque a Lambda só aceita pedidos de até 6 MB:
1. `start_upload` valida o pedido, registra o material e devolve um endereço
   para o navegador enviar o arquivo direto ao S3;
2. `confirm_upload` confere que o arquivo chegou, reserva o espaço e dispara
   o processamento.
"""
import uuid
from pathlib import PurePosixPath, PureWindowsPath

from boto3.dynamodb.conditions import Key

from app.adapters import storage, vectorstore
from app.features import usage
from app.features.users import service as users
from app.infra.aws import table
from app.infra.clock import iso_now
from app.infra.config import settings
from app.infra.dynamo import from_dynamo, query_all, to_dynamo

# Na versão AWS só documentos: áudio e vídeo ficam para a versão local.
TEXT_EXT = {"txt", "md"}
DOCUMENT_EXT = {"docx", "pptx", "xlsx"}  # lidos pela MarkItDown
SUPPORTED_EXT = TEXT_EXT | DOCUMENT_EXT | {"pdf"}


class UploadError(Exception):
    """Envio recusado. `status` é o código HTTP; a mensagem vai para o usuário."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _materials():
    return table(settings.table_materials)


def clean_filename(filename: str | None) -> str:
    """Só o nome do arquivo, sem pastas, como o usuário vê."""
    return PureWindowsPath(PurePosixPath(filename or "").name).name.strip()


def extension(filename: str) -> str:
    return filename.lower().rsplit(".", 1)[-1] if "." in filename else ""


def media_type(filename: str) -> str:
    ext = extension(filename)
    if ext == "pdf":
        return "pdf"
    if ext in DOCUMENT_EXT:
        return "document"
    return "text"


def list_materials(user_id: str) -> list[dict]:
    items = query_all(_materials(), KeyConditionExpression=Key("user_id").eq(user_id))
    return sorted(items, key=lambda m: m["created_at"], reverse=True)


def get_material(user_id: str, material_id: str) -> dict | None:
    item = _materials().get_item(Key={"user_id": user_id, "material_id": material_id}).get("Item")
    return from_dynamo(item) if item else None


def start_upload(user: dict, raw_filename: str, size: int) -> tuple[dict, dict]:
    """Valida o pedido e devolve (material, formulário de envio ao S3)."""
    if usage.is_blocked():
        raise UploadError(403, usage.BLOCKED_MESSAGE)

    filename = clean_filename(raw_filename)
    if not filename:
        raise UploadError(422, "O arquivo precisa ter um nome.")
    if extension(filename) not in SUPPORTED_EXT:
        raise UploadError(
            415,
            "Formato não suportado. Envie texto (.txt, .md), PDF, Word (.docx), "
            "PowerPoint (.pptx) ou Excel (.xlsx). Áudio e vídeo só na versão local: https://github.com/kevin-sachetti/grounded-rag-course-assistant",
        )
    user_id = user["user_id"]
    if any(m["filename"].lower() == filename.lower() for m in list_materials(user_id)):
        raise UploadError(409, f"Já existe um material chamado “{filename}” na biblioteca.")
    free = users.storage_limit_bytes() - user.get("storage_bytes", 0)
    if size > free:
        raise UploadError(
            413,
            f"O arquivo não cabe no seu espaço de {settings.storage_limit_mb} MB. "
            "Exclua algum material para liberar espaço.",
        )

    material_id = str(uuid.uuid4())
    key = storage.original_key(user_id, material_id, extension(filename))
    material = {
        "user_id": user_id,
        "material_id": material_id,
        "filename": filename,
        "media_type": media_type(filename),
        "s3_key": key,
        "size_bytes": 0,  # só conta depois que o arquivo chega
        "declared_size": size,
        "status": "uploading",
        "chunk_count": 0,
        "created_at": iso_now(),
        "updated_at": iso_now(),
    }
    _materials().put_item(Item=to_dynamo(material))
    # O S3 recusa sozinho um arquivo maior que o declarado.
    return material, storage.upload_form(key, size)


def confirm_upload(user_id: str, material_id: str) -> dict:
    """Confere o arquivo no S3, reserva o espaço e marca o material para processar."""
    material = get_material(user_id, material_id)
    if material is None:
        raise UploadError(404, "Material não encontrado.")
    if material["status"] != "uploading":
        return material  # confirmação repetida: nada a fazer

    size = storage.object_size(material["s3_key"])
    if size is None:
        raise UploadError(422, "O arquivo ainda não chegou. Tente enviar de novo.")
    try:
        users.reserve_storage(user_id, size)
    except users.QuotaExceeded as e:
        delete_material(user_id, material_id)
        raise UploadError(413, str(e))

    _materials().update_item(
        Key={"user_id": user_id, "material_id": material_id},
        UpdateExpression="SET #s = :s, size_bytes = :b, updated_at = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "pending", ":b": size, ":t": iso_now()},
    )
    return {**material, "status": "pending", "size_bytes": size}


def set_progress(user_id: str, material_id: str, stage: str, percent: float) -> None:
    """Etapa e percentual do processamento, para a barra da interface."""
    _materials().update_item(
        Key={"user_id": user_id, "material_id": material_id},
        UpdateExpression="SET #s = :s, stage = :st, progress = :p, updated_at = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "processing", ":st": stage,
            ":p": max(0, min(100, round(percent))), ":t": iso_now(),
        },
    )


def finish(user_id: str, material_id: str, status: str, chunk_count: int = 0) -> None:
    """Fim do processamento: pronto ou com erro. Some com a etapa e o percentual."""
    _materials().update_item(
        Key={"user_id": user_id, "material_id": material_id},
        UpdateExpression="SET #s = :s, chunk_count = :c, updated_at = :t REMOVE stage, progress",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status, ":c": chunk_count, ":t": iso_now()},
    )


def delete_material(user_id: str, material_id: str) -> bool:
    """Apaga o arquivo, os trechos e os vetores, libera o espaço e tira o material dos chats."""
    material = get_material(user_id, material_id)
    if material is None:
        return False
    storage.delete_prefix(storage.material_prefix(user_id, material_id))
    vectorstore.forget(user_id, material_id)
    users.release_storage(user_id, material.get("size_bytes", 0))

    chats = table(settings.table_chats)
    for chat in query_all(chats, KeyConditionExpression=Key("user_id").eq(user_id)):
        if material_id in chat.get("material_ids", []):
            chats.update_item(
                Key={"user_id": user_id, "chat_id": chat["chat_id"]},
                UpdateExpression="SET material_ids = :m",
                ExpressionAttributeValues={
                    ":m": [m for m in chat["material_ids"] if m != material_id]
                },
            )
    _materials().delete_item(Key={"user_id": user_id, "material_id": material_id})
    return True


def to_read(material: dict) -> dict:
    """Formato da API (MaterialRead)."""
    return {
        "id": material["material_id"],
        "filename": material["filename"],
        "media_type": material["media_type"],
        "size_bytes": material.get("size_bytes", 0),
        "status": material["status"],
        "chunk_count": material.get("chunk_count", 0),
        "stage": material.get("stage"),
        "progress": material.get("progress"),
        "created_at": material["created_at"],
        "updated_at": material["updated_at"],
    }

