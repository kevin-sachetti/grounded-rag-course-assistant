"""Progresso da ingestão, para a barra da biblioteca de materiais.

Fica em memória, e não no banco, de propósito: o processamento roda dentro
do próprio processo da API, então o progresso só existe enquanto ela está de
pé. Se a API reiniciar no meio, o processamento também para, e guardar um
número no banco só mostraria um progresso que não avança mais.

Cada material em processamento tem uma etapa (texto para a interface) e um
percentual de 0 a 100 do processamento inteiro.
"""

from threading import Lock
from uuid import UUID

_lock = Lock()
_state: dict[UUID, dict] = {}


def set_progress(material_id: UUID, stage: str, percent: float) -> None:
    with _lock:
        _state[material_id] = {"stage": stage, "progress": max(0, min(100, round(percent)))}


def get_progress(material_id: UUID) -> dict:
    """{"stage": ..., "progress": ...} ou {} se o material não está sendo processado."""
    with _lock:
        return dict(_state.get(material_id, {}))


def clear_progress(material_id: UUID) -> None:
    with _lock:
        _state.pop(material_id, None)


class Range:
    """Uma faixa do percentual total reservada a uma etapa.

    Ex.: a transcrição ocupa de 0 a 80%. Quando ela informa 50% do próprio
    trabalho, a barra mostra 40% do total.
    """

    def __init__(self, material_id: UUID, stage: str, start: float, end: float) -> None:
        self.material_id, self.stage, self.start, self.end = material_id, stage, start, end

    def __call__(self, fraction: float) -> None:
        fraction = max(0.0, min(1.0, fraction))
        set_progress(self.material_id, self.stage, self.start + (self.end - self.start) * fraction)
