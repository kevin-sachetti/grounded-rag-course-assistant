"""Teto de gasto do mês, somando todos os usuários (US$ 10).

Cada pergunta e cada trecho vetorizado somam um custo estimado no contador
do mês. Quando o contador chega no teto, ou quando o AWS Budgets avisa que o
gasto real chegou, o mês fica bloqueado: ninguém pergunta, envia arquivo ou
cria conta até o mês virar.
"""
from decimal import Decimal

from app.infra.aws import table
from app.infra.clock import local_month
from app.infra.config import settings
from app.infra.dynamo import from_dynamo


def _usage():
    return table(settings.table_usage)


def month_status() -> dict:
    """{"month", "spent_usd", "blocked"} do mês atual."""
    month = local_month()
    item = from_dynamo(_usage().get_item(Key={"month": month}).get("Item", {}))
    spent = float(item.get("spent_usd", 0))
    blocked = bool(item.get("blocked")) or spent >= settings.monthly_budget_usd
    return {"month": month, "spent_usd": round(spent, 4), "blocked": blocked}


def is_blocked() -> bool:
    return month_status()["blocked"]


def add_cost(amount_usd: float, questions: int = 0) -> None:
    """Soma um custo estimado ao contador do mês (operação atômica)."""
    _usage().update_item(
        Key={"month": local_month()},
        UpdateExpression="ADD spent_usd :c, questions :q",
        ExpressionAttributeValues={":c": Decimal(str(amount_usd)), ":q": questions},
    )


def block_month() -> None:
    """Chamado quando o AWS Budgets avisa que o gasto real chegou no teto."""
    _usage().update_item(
        Key={"month": local_month()},
        UpdateExpression="SET blocked = :t",
        ExpressionAttributeValues={":t": True},
    )


BLOCKED_MESSAGE = (
    "O limite de uso da demonstração deste mês foi atingido. "
    "Você ainda pode ver seus chats e materiais, mas novas perguntas e envios "
    "voltam no próximo mês. Para usar sem limites, instale a versão local: "
    "https://github.com/kevin-sachetti/grounded-rag-course-assistant"
)
