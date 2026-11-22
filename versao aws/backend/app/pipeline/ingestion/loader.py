from collections.abc import Callable
from pathlib import Path

from pypdf import PdfReader

Progress = Callable[[float], None]


def extract_text(media_type: str, file_path: str, on_progress: Progress | None = None) -> str:
    """Extrai o texto de um material, conforme o tipo.

    - pdf: texto das páginas, com o pypdf (o mesmo da versão local, já medido)
    - document: Word, PowerPoint e Excel, convertidos pela MarkItDown
    - text: lê o arquivo direto

    `on_progress` recebe a fração concluída (0 a 1), para a barra de progresso.
    """
    if media_type == "pdf":
        return _extract_pdf(file_path, on_progress)
    if media_type == "document":
        from markitdown import MarkItDown

        return MarkItDown().convert(file_path).text_content
    if media_type == "text":
        return Path(file_path).read_text(encoding="utf-8")
    raise ValueError(f"Tipo de material sem suporte para extração: {media_type}")


def _extract_pdf(file_path: str, on_progress: Progress | None) -> str:
    reader = PdfReader(file_path)
    total = len(reader.pages) or 1
    pages = []
    for i, page in enumerate(reader.pages):
        pages.append(page.extract_text() or "")
        if on_progress:
            on_progress((i + 1) / total)
    return "\n".join(pages)
