"""Handler da prova de conceito.

VARIANT=fp32 usa os modelos originais com PyTorch (iguais aos da versão local);
VARIANT=int8 usa as versões ONNX quantizadas, só com o onnxruntime.

Eventos:
  {"action": "ingest"}            vetoriza o fotossintese.txt (como a ingestão)
  {"action": "ask", "q": "..."}   busca em dois estágios: 7 candidatos -> re-ranqueamento
"""
import os
import resource
import time

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

VARIANT = os.environ.get("VARIANT", "fp32")
T0 = time.perf_counter()


def _sigmoid_if_needed(scores: np.ndarray) -> np.ndarray:
    """Mesma regra da versão local: sigmoide só se a nota vier fora de 0 a 1."""
    if ((scores >= 0) & (scores <= 1)).all():
        return scores
    return 1 / (1 + np.exp(-scores))


if VARIANT == "int8":
    import onnxruntime as ort
    from tokenizers import Tokenizer

    def _session(path: str):
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = os.cpu_count() or 1
        return ort.InferenceSession(f"{path}/onnx/model_qint8_avx2.onnx", opts)

    def _tokenizer(path: str):
        tok = Tokenizer.from_file(f"{path}/tokenizer.json")
        tok.enable_truncation(512)
        tok.enable_padding()
        return tok

    _E5, _E5_TOK = _session("/opt/onnx/e5"), _tokenizer("/opt/onnx/e5")
    _BGE, _BGE_TOK = _session("/opt/onnx/bge"), _tokenizer("/opt/onnx/bge")

    def _feeds(session, encodings):
        ids = np.array([e.ids for e in encodings], dtype=np.int64)
        mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        names = {i.name for i in session.get_inputs()}
        feeds = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in names:
            feeds["token_type_ids"] = np.zeros_like(ids)
        return {k: v for k, v in feeds.items() if k in names}, mask

    def embed(texts: list[str], batch: int = 8) -> np.ndarray:
        """Média dos tokens (mean pooling) e normalização, como o e5 pede."""
        out = []
        for i in range(0, len(texts), batch):
            feeds, mask = _feeds(_E5, _E5_TOK.encode_batch(texts[i:i + batch]))
            hidden = _E5.run(None, feeds)[0]
            summed = (hidden * mask[..., None]).sum(axis=1)
            vec = summed / mask.sum(axis=1, keepdims=True)
            out.append(vec / np.linalg.norm(vec, axis=1, keepdims=True))
        return np.vstack(out)

    def rerank(question: str, texts: list[str]) -> np.ndarray:
        feeds, _ = _feeds(_BGE, _BGE_TOK.encode_batch([(question, t) for t in texts]))
        logits = _BGE.run(None, feeds)[0].reshape(-1)
        return _sigmoid_if_needed(logits.astype(float))

else:
    from sentence_transformers import CrossEncoder, SentenceTransformer

    _E5 = SentenceTransformer("intfloat/multilingual-e5-large")
    _BGE = CrossEncoder("BAAI/bge-reranker-v2-m3")

    def embed(texts: list[str]) -> np.ndarray:
        return _E5.encode(texts, normalize_embeddings=True)

    def rerank(question: str, texts: list[str]) -> np.ndarray:
        return _sigmoid_if_needed(np.asarray(_BGE.predict([(question, t) for t in texts]), dtype=float))


INIT_SECONDS = round(time.perf_counter() - T0, 2)
CHUNKS: list[str] = []
VECTORS = None


def _peak_mb() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024


def handler(event, _context):
    global CHUNKS, VECTORS
    t = time.perf_counter()
    action = event.get("action")

    if action == "ingest":
        text = open("fotossintese.txt", encoding="utf-8").read()
        CHUNKS = RecursiveCharacterTextSplitter(chunk_size=1400, chunk_overlap=200).split_text(text)
        VECTORS = embed([f"passage: {c}" for c in CHUNKS])
        result = {"chunks": len(CHUNKS)}

    elif action == "ask":
        q = embed([f"query: {event['q']}"])[0]
        sims = VECTORS @ q  # similaridade do cosseno (vetores normalizados)
        top = np.argsort(-sims)[:7]
        scores = rerank(event["q"], [CHUNKS[i] for i in top])
        order = np.argsort(-scores)
        result = {
            "best": [{"chunk": int(top[i]), "vector": round(float(sims[top[i]]), 4),
                      "rerank": round(float(scores[i]), 4)} for i in order[:3]],
        }
    else:
        result = {}

    return {
        "variant": VARIANT,
        "init_seconds": INIT_SECONDS,
        "seconds": round(time.perf_counter() - t, 2),
        "peak_memory_mb": _peak_mb(),
        **result,
    }
