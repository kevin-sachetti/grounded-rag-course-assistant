from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.infra.config import settings


def split_text(text: str) -> list[str]:
    """Quebra um texto longo em pedaços (chunks) com sobreposição.

    O RecursiveCharacterTextSplitter tenta cortar em fronteiras naturais
    (parágrafo → linha → frase), preservando o sentido de cada pedaço.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return splitter.split_text(text)
