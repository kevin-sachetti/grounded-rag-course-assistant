"""Datas usadas pelos limites: o "dia" das perguntas e o "mês" do teto de gasto.

Contam no fuso de Brasília, para o limite virar à meia-noite daqui, e não à
meia-noite de Londres.
"""
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.infra.config import settings


def now() -> datetime:
    return datetime.now(UTC)


def iso_now() -> str:
    return now().isoformat()


def local_today() -> str:
    """Ex.: "2026-11-21"."""
    return now().astimezone(ZoneInfo(settings.timezone)).date().isoformat()


def local_month() -> str:
    """Ex.: "2026-11"."""
    return local_today()[:7]
