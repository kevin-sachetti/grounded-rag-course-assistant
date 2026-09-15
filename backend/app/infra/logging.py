import logging

from app.infra.config import settings


def setup_logging() -> None:
    """Configura o logging básico da aplicação."""
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
