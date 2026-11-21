import importlib
import threading
from collections.abc import Callable
from functools import lru_cache

import whisper

from app.infra.config import settings

# O módulo, e não a função: `whisper.transcribe` também é o nome da função
# exportada pelo pacote, então o import comum devolveria a função.
_whisper_transcribe = importlib.import_module("whisper.transcribe")

# Uma transcrição por vez: duas ao mesmo tempo disputariam o processador e
# ficariam mais lentas que em sequência. A trava também protege o gancho de
# progresso abaixo, que é instalado no módulo do Whisper durante a chamada.
_lock = threading.Lock()


@lru_cache
def _model():
    """Carrega o modelo Whisper uma única vez (fica em cache na memória)."""
    return whisper.load_model(settings.whisper_model_size)


class _ProgressBar:
    """Substitui a barra de progresso do terminal que o Whisper usa (tqdm).

    O Whisper avança essa barra conforme processa o áudio, em quadros. Em vez
    de desenhar no terminal, ela repassa a fração concluída para `on_progress`.
    """

    def __init__(self, on_progress: Callable[[float], None]) -> None:
        self.on_progress = on_progress

    def __call__(self, total=None, **_kwargs):
        self.total, self.done = total or 0, 0
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def update(self, n: int) -> None:
        self.done += n
        if self.total:
            self.on_progress(self.done / self.total)


class _TqdmModule:
    def __init__(self, bar: _ProgressBar) -> None:
        self.tqdm = bar


def transcribe(file_path: str, on_progress: Callable[[float], None] | None = None) -> str:
    """Transcreve um arquivo de áudio ou vídeo para texto usando o Whisper."""
    with _lock:
        model = _model()
        original = _whisper_transcribe.tqdm
        if on_progress:
            # verbose=False é o que liga a barra interna do Whisper.
            _whisper_transcribe.tqdm = _TqdmModule(_ProgressBar(on_progress))
        try:
            result = model.transcribe(file_path, verbose=False if on_progress else None)
        finally:
            _whisper_transcribe.tqdm = original
    return result["text"].strip()
