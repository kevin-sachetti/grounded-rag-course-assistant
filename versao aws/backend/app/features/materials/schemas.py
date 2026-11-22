from pydantic import BaseModel, Field


class MaterialRead(BaseModel):
    """Um material da biblioteca do usuário."""

    id: str
    filename: str
    media_type: str  # text | pdf | document
    size_bytes: int
    status: str  # uploading | pending | processing | done | error
    chunk_count: int
    # Só enquanto o material é processado: a etapa atual e o percentual (0 a 100).
    stage: str | None = None
    progress: int | None = None
    created_at: str
    updated_at: str


class UploadRequest(BaseModel):
    """Pedido de envio: o nome e o tamanho do arquivo, antes de mandá-lo."""

    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(gt=0)


class UploadTicket(BaseModel):
    """O material registrado e o endereço para o navegador enviar o arquivo ao S3.

    O navegador faz um POST em `url` com os campos de `fields` e o arquivo por
    último, no campo "file". Depois avisa a API em /materials/{id}/confirm.
    """

    material: MaterialRead
    url: str
    fields: dict[str, str]
