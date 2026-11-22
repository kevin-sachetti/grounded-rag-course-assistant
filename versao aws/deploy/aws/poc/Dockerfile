# Prova de conceito, variante original (fp32): os modelos de busca (e5 + bge)
# com PyTorch, nas mesmas versões da versão local. Serve de referência.
FROM public.ecr.aws/lambda/python:3.14

ENV PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf

RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.15.0 \
    && pip install "sentence-transformers==6.3.0" "transformers==5.24.0" "numpy==2.5.5" \
        langchain-text-splitters

# Modelos baixados no build: na Lambda o disco é só de leitura (fora o /tmp).
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('intfloat/multilingual-e5-large'); CrossEncoder('BAAI/bge-reranker-v2-m3')"

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    VARIANT=fp32

COPY handler.py fotossintese.txt ./
CMD ["handler.handler"]
