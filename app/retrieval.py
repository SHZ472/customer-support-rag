"""Hybrid FAQ retrieval with BM25, BGE, FAISS and reciprocal rank fusion."""

from functools import lru_cache
import os
from pathlib import Path

import course_cache
import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from app.ranking import fuse, tokenize

DATA = Path(__file__).resolve().parents[1] / "data"
MODEL = "BAAI/bge-small-zh-v1.5"
REVISION = "7999e1d3359715c523056ef9478215996d62a620"
QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："


class FaqRetriever:
    def __init__(self, cache_size=256):
        self.chunks = []
        for source in ("shipping.txt", "returns.md"):
            lines = (DATA / source).read_text(encoding="utf-8").splitlines()[1:]
            for number, text in enumerate((line.strip() for line in lines if line.strip()), start=1):
                self.chunks.append({"chunk_id": f"{Path(source).stem}-{number}", "source": source, "text": text})
        self.by_id = {chunk["chunk_id"]: chunk for chunk in self.chunks}
        self.bm25 = BM25Okapi([tokenize(chunk["text"]) for chunk in self.chunks])
        self.model = SentenceTransformer(MODEL, revision=REVISION, device="cpu",
                                         local_files_only=os.getenv("HF_HUB_OFFLINE") == "1")
        self.query_vector = lru_cache(maxsize=cache_size)(self.encode_query)
        vectors = self.encode([chunk["text"] for chunk in self.chunks])
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def encode(self, texts):
        vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.ascontiguousarray(vectors, dtype="float32")

    def encode_query(self, question):
        return self.encode([QUERY_PREFIX + question])

    def search(self, question, top_k=3):
        scores = self.bm25.get_scores(tokenize(question))
        positions = sorted(range(len(self.chunks)), key=lambda i: (-scores[i], i))
        keyword_ids = [self.chunks[i]["chunk_id"] for i in positions if scores[i] > 0][:top_k]
        _, positions = self.index.search(self.query_vector(question), min(top_k, len(self.chunks)))
        vector_ids = [self.chunks[i]["chunk_id"] for i in positions[0]]
        return [{**self.by_id[chunk_id], "rrf_score": score}
                for chunk_id, score in fuse([keyword_ids, vector_ids])[:top_k]]
