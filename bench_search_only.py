

import sys
import time
import numpy as np
from numpy.linalg import norm

from run_eval import pdf_to_chunks_headless, get_embedding, build_vector_store_old, search_similar_old
from vector_store import build_vector_store_faiss

N_TRIALS = 200  # repeat the search many times to get a stable average


def bench_old_search_only(query_emb, vector_store, top_k=5, n_trials=N_TRIALS):
    q_norm = norm(query_emb)
    times = []
    for _ in range(n_trials):
        start = time.perf_counter()
        sims = []
        for item in vector_store:
            score = float(np.dot(query_emb, item["emb"]) / (q_norm * item["norm"] + 1e-12))
            sims.append((score, item["chunk"]))
        sims.sort(key=lambda x: x[0], reverse=True)
        _ = sims[:top_k]
        times.append(time.perf_counter() - start)
    return sum(times) / len(times)


def bench_new_search_only(query_emb, store, top_k=5, n_trials=N_TRIALS):
    times = []
    for _ in range(n_trials):
        start = time.perf_counter()
        _ = store.search(query_emb, top_k=top_k)
        times.append(time.perf_counter() - start)
    return sum(times) / len(times)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bench_search_only.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    chunks = pdf_to_chunks_headless(pdf_path)

    print("\nEmbedding all chunks for OLD store...")
    old_store = build_vector_store_old(chunks)
    print("Embedding all chunks for NEW (FAISS) store...")
    new_store = build_vector_store_faiss(chunks, get_embedding, dim=768)

    query_emb = get_embedding("What is the grace period for premium payment?")

    print(f"\nRunning {N_TRIALS} trials of search only (no embedding call)...")
    old_avg = bench_old_search_only(query_emb, old_store)
    new_avg = bench_new_search_only(query_emb, new_store)

    print("=" * 60)
    print("SEARCH-ONLY LATENCY (embedding call excluded)")
    print("=" * 60)
    print(f"OLD (brute-force loop, {len(old_store)} chunks): {old_avg*1000:.3f}ms")
    print(f"NEW (FAISS index, {len(new_store.chunks)} chunks):     {new_avg*1000:.3f}ms")
    if new_avg > 0:
        print(f"Speedup: {old_avg/new_avg:.1f}x")
    print("\nThis is the number that actually reflects the FAISS swap —")
    print("not the run_eval.py number, which includes Ollama API latency.")