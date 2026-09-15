from app.adapters.storage.base import Storage
from app.adapters.storage.factory import get_storage
from app.adapters.storage.local import LocalStorage

__all__ = ["LocalStorage", "Storage", "get_storage"]
