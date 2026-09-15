from pathlib import Path

from pypdf import PdfReader

from app.pipeline.ingestion.transcriber import transcribe


def extract_text(media_type: str, file_path: str) -> str:
    """Extrai o texto de um material, conforme o tipo.

    - audio/video: transcreve com o Whisper
    - pdf: extrai o texto das páginas
    - text: lê o arquivo direto
    """
    if media_type in ("audio", "video"):
        return transcribe(file_path)
    if media_type == "pdf":
        return _extract_pdf(file_path)
    if media_type == "text":
        return Path(file_path).read_text(encoding="utf-8")
    raise ValueError(f"Tipo de material sem suporte para extração: {media_type}")


def _extract_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)
