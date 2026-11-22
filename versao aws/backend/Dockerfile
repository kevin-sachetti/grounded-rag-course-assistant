# Imagem das Lambdas da versão AWS (API, ingestão, cadastro, limpeza e alerta).
# A mesma imagem serve a todas; o template do SAM escolhe a função de cada uma.
FROM public.ecr.aws/lambda/python:3.14

ENV PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf

# Torch só para processador: o pacote padrão traz bibliotecas de placa de
# vídeo (vários GB) que a Lambda não usa.
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch

COPY pyproject.toml ./
COPY app ./app
RUN pip install ".[dev]"

# Os modelos de busca vão dentro da imagem: na Lambda o disco é só de leitura
# (fora o /tmp), e baixar a cada partida seria lento.
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('intfloat/multilingual-e5-large'); CrossEncoder('BAAI/bge-reranker-v2-m3')"

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    PRELOAD_MODELS=true

# Função padrão: a API. As outras Lambdas trocam pelo template (ImageConfig).
CMD ["app.main.handler"]
