"""Usuários: o registro de uso de cada um, os limites e a exclusão dos dados.

Tabela `usuarios`, chave `user_id` (o id do Cognito). O e-mail não fica aqui.
"""
from datetime import timedelta

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr, Key

from app.adapters import storage, vectorstore
from app.infra.aws import cognito, table
from app.infra.clock import iso_now, local_today, now
from app.infra.config import settings
from app.infra.dynamo import from_dynamo, query_all

# Grava o último acesso no máximo uma vez por hora, para não escrever no
# banco a cada pedido.
_TOUCH_EVERY = timedelta(hours=1)


class QuotaExceeded(Exception):
    """Limite do usuário atingido (perguntas do dia ou espaço)."""


def _users():
    return table(settings.table_users)


def _conditional_failed(e: ClientError) -> bool:
    return e.response["Error"]["Code"] == "ConditionalCheckFailedException"


def get_or_create(user_id: str) -> dict:
    """O registro do usuário; cria na primeira vez que ele usa o sistema."""
    item = _users().get_item(Key={"user_id": user_id}).get("Item")
    if item:
        return from_dynamo(item)
    created = {
        "user_id": user_id,
        "created_at": iso_now(),
        "last_seen_at": iso_now(),
        "storage_bytes": 0,
        "questions_date": "",
        "questions_today": 0,
    }
    try:
        _users().put_item(Item=created, ConditionExpression=Attr("user_id").not_exists())
    except ClientError as e:
        if not _conditional_failed(e):
            raise
        return from_dynamo(_users().get_item(Key={"user_id": user_id})["Item"])
    return created


def touch(user: dict) -> None:
    """Atualiza o último acesso (é dele que depende a limpeza de 30 dias)."""
    last = user.get("last_seen_at", "")
    if last and now().isoformat() < _plus(last, _TOUCH_EVERY):
        return
    _users().update_item(
        Key={"user_id": user["user_id"]},
        UpdateExpression="SET last_seen_at = :t",
        ExpressionAttributeValues={":t": iso_now()},
    )


def _plus(iso: str, delta: timedelta) -> str:
    from datetime import datetime

    return (datetime.fromisoformat(iso) + delta).isoformat()


def accept_terms(user_id: str) -> None:
    _users().update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET terms_accepted_at = :t",
        ExpressionAttributeValues={":t": iso_now()},
    )


def storage_limit_bytes() -> int:
    return settings.storage_limit_mb * 1024 * 1024


def questions_today(user: dict) -> int:
    return user.get("questions_today", 0) if user.get("questions_date") == local_today() else 0


def consume_question(user_id: str) -> None:
    """Conta uma pergunta do dia, ou recusa se o limite já foi atingido.

    Atômico: duas perguntas ao mesmo tempo não passam do limite.
    """
    today = local_today()
    try:
        # Já perguntou hoje: soma 1, desde que esteja abaixo do limite.
        _users().update_item(
            Key={"user_id": user_id},
            UpdateExpression="ADD questions_today :one",
            ConditionExpression=Attr("questions_date").eq(today)
            & Attr("questions_today").lt(settings.questions_per_day),
            ExpressionAttributeValues={":one": 1},
        )
        return
    except ClientError as e:
        if not _conditional_failed(e):
            raise
    try:
        # Primeira pergunta do dia: recomeça a contagem.
        _users().update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET questions_date = :d, questions_today = :one",
            ConditionExpression=Attr("questions_date").ne(today),
            ExpressionAttributeValues={":d": today, ":one": 1},
        )
    except ClientError as e:
        if not _conditional_failed(e):
            raise
        raise QuotaExceeded(
            f"Você já fez as {settings.questions_per_day} perguntas de hoje. "
            "O limite renova à meia-noite."
        )


def reserve_storage(user_id: str, size: int) -> None:
    """Reserva espaço para um arquivo, ou recusa se não couber."""
    try:
        _users().update_item(
            Key={"user_id": user_id},
            UpdateExpression="ADD storage_bytes :s",
            ConditionExpression=Attr("storage_bytes").lte(storage_limit_bytes() - size),
            ExpressionAttributeValues={":s": size},
        )
    except ClientError as e:
        if not _conditional_failed(e):
            raise
        raise QuotaExceeded(
            f"O arquivo não cabe no seu espaço de {settings.storage_limit_mb} MB. "
            "Exclua algum material para liberar espaço."
        )


def release_storage(user_id: str, size: int) -> None:
    if size > 0:
        _users().update_item(
            Key={"user_id": user_id},
            UpdateExpression="ADD storage_bytes :s",
            ExpressionAttributeValues={":s": -size},
        )


def wipe_data(user_id: str) -> None:
    """Apaga chats, mensagens, materiais e arquivos do usuário. A conta fica.

    Usado pela exclusão da conta e pela limpeza de 30 dias sem uso.
    """
    chats = table(settings.table_chats)
    messages = table(settings.table_messages)
    materials = table(settings.table_materials)

    for chat in query_all(chats, KeyConditionExpression=Key("user_id").eq(user_id)):
        for m in query_all(messages, KeyConditionExpression=Key("chat_id").eq(chat["chat_id"])):
            messages.delete_item(Key={"chat_id": m["chat_id"], "sort_key": m["sort_key"]})
        chats.delete_item(Key={"user_id": user_id, "chat_id": chat["chat_id"]})

    for material in query_all(materials, KeyConditionExpression=Key("user_id").eq(user_id)):
        vectorstore.forget(user_id, material["material_id"])
        materials.delete_item(Key={"user_id": user_id, "material_id": material["material_id"]})

    storage.delete_prefix(storage.user_prefix(user_id))
    _users().update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET storage_bytes = :z",
        ExpressionAttributeValues={":z": 0},
    )


def delete_account(user_id: str) -> None:
    """Apaga tudo do usuário, inclusive a conta no Cognito."""
    wipe_data(user_id)
    _users().delete_item(Key={"user_id": user_id})
    if settings.cognito_user_pool_id:
        # No Cognito, o "username" do pool é o próprio sub quando o login é por e-mail.
        cognito().admin_delete_user(UserPoolId=settings.cognito_user_pool_id, Username=user_id)


def inactive_users() -> list[str]:
    """Usuários sem entrar há mais de `inactivity_days` e com algum dado guardado."""
    limit = (now() - timedelta(days=settings.inactivity_days)).isoformat()
    found, start = [], None
    while True:
        page = _users().scan(
            FilterExpression=Attr("last_seen_at").lt(limit),
            ProjectionExpression="user_id",
            **({"ExclusiveStartKey": start} if start else {}),
        )
        found.extend(i["user_id"] for i in page.get("Items", []))
        start = page.get("LastEvaluatedKey")
        if not start:
            return found
