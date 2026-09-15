from pathlib import Path

from app.adapters.storage.base import Storage


class LocalStorage(Storage):
    """Armazena arquivos no disco local, sob um diretório base."""

    def __init__(self, base_dir: str) -> None:
        self.base = Path(base_dir)

    async def save(self, key: str, data: bytes) -> None:
        path = self.base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def full_path(self, key: str) -> str:
        return str(self.base / key)

    async def delete(self, key: str) -> None:
        path = self.base / key
        path.unlink(missing_ok=True)
