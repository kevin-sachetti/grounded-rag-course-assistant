"""Conversões entre o DynamoDB e o Python.

O DynamoDB guarda números como Decimal e não aceita float. Estas funções
convertem nas duas direções, inclusive dentro de dicionários e listas (como
os detalhes de uma resposta, com as notas de cada trecho).
"""
from decimal import Decimal


def to_dynamo(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        # None vira o tipo NULL do DynamoDB e volta como None (ex.: rerank_score
        # de um trecho com o re-ranqueamento desligado).
        return {k: to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_dynamo(v) for v in value]
    return value


def from_dynamo(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: from_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [from_dynamo(v) for v in value]
    return value


def query_all(table, **kwargs) -> list[dict]:
    """Todas as páginas de uma consulta (o DynamoDB devolve no máximo 1 MB por vez)."""
    items, start = [], None
    while True:
        page = table.query(**kwargs, **({"ExclusiveStartKey": start} if start else {}))
        items.extend(page.get("Items", []))
        start = page.get("LastEvaluatedKey")
        if not start:
            return [from_dynamo(i) for i in items]
