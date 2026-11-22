"""Só para o desenvolvimento no computador: cria as tabelas e o bucket nos
emuladores (DynamoDB Local e moto). Na AWS, quem cria tudo é o template do SAM.
"""
from botocore.exceptions import ClientError

from app.infra.aws import dynamodb, s3
from app.infra.config import settings

# (tabela, chave de partição, chave de ordenação) — as mesmas do template.
TABLES = [
    (settings.table_users, "user_id", None),
    (settings.table_materials, "user_id", "material_id"),
    (settings.table_chats, "user_id", "chat_id"),
    (settings.table_messages, "chat_id", "sort_key"),
    (settings.table_usage, "month", None),
]


def create_local_resources() -> None:
    existing = {t.name for t in dynamodb().tables.all()}
    for name, pk, sk in TABLES:
        if name in existing:
            continue
        keys = [{"AttributeName": pk, "KeyType": "HASH"}]
        attrs = [{"AttributeName": pk, "AttributeType": "S"}]
        if sk:
            keys.append({"AttributeName": sk, "KeyType": "RANGE"})
            attrs.append({"AttributeName": sk, "AttributeType": "S"})
        dynamodb().create_table(
            TableName=name, KeySchema=keys, AttributeDefinitions=attrs,
            BillingMode="PAY_PER_REQUEST",
        )
    try:
        s3().create_bucket(
            Bucket=settings.data_bucket,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise
