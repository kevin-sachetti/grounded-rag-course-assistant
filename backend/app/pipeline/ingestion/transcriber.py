from functools import lru_cache

import whisper

from app.infra.config import settings


@lru_cache
def _model():
    """Carrega o modelo Whisper uma única vez (fica em cache na memória)."""
    return whisper.load_model(settings.whisper_model_size)


def transcribe(file_path: str) -> str:
    """Transcreve um arquivo de áudio ou vídeo para texto usando o Whisper."""
    result = _model().transcribe(file_path)
    return result["text"].strip()
