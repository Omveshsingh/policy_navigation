import numpy as np
import faiss


class FaissVectorStore:
    """
    Thin wrapper around a FAISS IndexFlatIP (inner product) index.
    Vectors are L2-normalized before insertion/search, so inner product
    becomes equivalent to cosine similarity — same math as the original
    build_vector_store/search_similar, just with a real index instead of
    a Python loop.
    """

    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.chunks = []  # parallel list: chunks[i] <-> vector at row i

    @staticmethod
    def _normalize(vecs: np.ndarray) -> np.ndarray:
        vecs = vecs.astype("float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1e-12
        return vecs / norms

    def add(self, chunks: list, embeddings: np.ndarray):
        """
        chunks: list of chunk dicts (same shape as the original code's
                {"page":..., "chunk_id":..., "text":...})
        embeddings: (n, dim) float array, same order as chunks
        """
        vecs = self._normalize(np.asarray(embeddings))
        self.index.add(vecs)
        self.chunks.extend(chunks)

    def search(self, query_embedding: np.ndarray, top_k: int = 5):
        if self.index.ntotal == 0:
            return []
        q = self._normalize(np.asarray([query_embedding]))
        scores, idxs = self.index.search(q, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append((float(score), self.chunks[idx]))
        return results


def build_vector_store_faiss(chunks: list, get_embedding_fn, dim: int = 768):
    store = FaissVectorStore(dim=dim)
    embeddings, kept_chunks = [], []
    for c in chunks:
        emb = get_embedding_fn(c["text"])
        if emb is None:
            continue
        embeddings.append(emb)
        kept_chunks.append(c)
    if embeddings:
        store.add(kept_chunks, np.vstack(embeddings))
    return store


def search_similar_faiss(query: str, store: FaissVectorStore, get_embedding_fn, top_k: int = 5):
    q_emb = get_embedding_fn(query)
    if q_emb is None:
        return []
    results = store.search(q_emb, top_k=top_k)
    return [chunk for score, chunk in results]