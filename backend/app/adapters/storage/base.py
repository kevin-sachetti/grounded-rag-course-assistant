from abc import ABC, abstractmethod


class Storage(ABC):
    """Interface de armazenamento de arquivos.

    Implementações: LocalStorage (disco) agora; S3Storage no futuro.
    A aplicação só conhece esta interface — trocar a implementação não afeta o resto.
    """

    @abstractmethod
    async def save(self, key: str, data: bytes) -> None:
        """Grava os bytes sob a chave informada."""

    @abstractmethod
    def full_path(self, key: str) -> str:
        """Caminho/localização absoluta do arquivo (usado pela ingestão depois)."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove o arquivo, se existir."""
