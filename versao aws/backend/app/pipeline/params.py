from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AnswerParams:
    """Parâmetros de um chat que influenciam a resposta.

    Vêm do chat (tela "editar chat") e acompanham a pergunta pelo fluxo fixo. Ficam também nos detalhes da resposta, para o painel
    mostrar com quais parâmetros ela foi gerada.
    """

    temperature: float
    similarity_threshold: float  # relevância mínima (0 a 1) para um trecho ser usado
    retrieval_k: int  # trechos que sobram no final da busca
    use_reranker: bool

    def as_dict(self) -> dict:
        return asdict(self)
