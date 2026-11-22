"""Pontos de entrada das Lambdas que não são a API.

Todas usam a mesma imagem da API; o template do SAM escolhe a função de cada uma.

    ingest     processa um material enviado (chamada pela API, sem esperar)
    presignup  gatilho do Cognito antes do cadastro: recusa se o teto do mês foi atingido
    cleanup    agendada uma vez por dia: apaga os dados de quem está 30 dias sem entrar
    budget     recebe o alerta do AWS Budgets e bloqueia o mês
"""
import logging

from app.infra.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def ingest(event, _context):
    from app.pipeline.ingestion.service import ingest_material

    ingest_material(event["user_id"], event["material_id"])


def presignup(event, _context):
    """O Cognito mostra a mensagem da exceção na tela de cadastro."""
    from app.features import usage

    if usage.is_blocked():
        raise Exception(
            "Novos cadastros estão pausados até o próximo mês: o limite de uso da "
            "demonstração foi atingido. Para usar sem limites, instale a versão "
            "local: https://github.com/kevin-sachetti/grounded-rag-course-assistant"
        )
    return event


def cleanup(_event, _context):
    from app.features.users import service as users

    inactive = users.inactive_users()
    for user_id in inactive:
        users.wipe_data(user_id)
    logger.info("Limpeza: dados de %d usuário(s) inativo(s) apagados", len(inactive))
    return {"wiped": len(inactive)}


def budget(_event, _context):
    """O AWS Budgets publica no SNS quando o gasto real passa do limite."""
    from app.features import usage

    usage.block_month()
    logger.warning("Teto de gasto atingido pelo AWS Budgets: mês bloqueado")
