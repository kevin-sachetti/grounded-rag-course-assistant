from functools import lru_cache

from app.adapters.storage.base import Storage
from app.adapters.storage.local import LocalStorage
from app.infra.config import settings


@lru_cache
def get_storage() -> Storage:
    """Retorna a implementação de storage em uso. Trocar aqui para S3 no futuro."""
    return LocalStorage(settings.upload_dir)
