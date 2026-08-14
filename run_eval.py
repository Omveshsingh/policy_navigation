

import sys
import os
import numpy as np
from numpy.linalg import norm
from pdf2image import convert_from_path
import pytesseract
import ollama

from vector_store import build_vector_store_faiss, search_similar_faiss
from eval_harness import compare_old_vs_new, TEST_QUESTIONS_KEYWORD

# Same env vars your app already uses
TESSERACT_CMD = os.getenv("TESSERACT_CMD")
POPPLER_PATH = os.getenv("POPPLER_PATH")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def pdf_to_chunks_headless(pdf_path, chunk_size=500, overlap=100):
    """Same logic as pdf_to_word() + chunk_json() in your app, minus the
    Streamlit calls, so it can run from the command line."""
    print(f"Running OCR on {pdf_path} ...")
    pages = convert_from_path(pdf_path, dpi=200, poppler_path=POPPLER_PATH)
    extracted_data = []
    for i, page in enumerate(pages, start=1):
        text = pytesseract.image_to_string(page, lang="eng", config="--psm 6")
        extracted_data.append({"page": i, "text": text})
        print(f"  processed page {i}/{len(pages)}")

    all_chunks = []
    for page in extracted_data:
        start = 0
        page_text = page["text"]
        chunk_id = 1
        while start < len(page_text):
            end = min(start + chunk_size, len(page_text))
            all_chunks.append({"page": page["page"], "chunk_id": chunk_id, "text": page_text[start:end]})
            start += chunk_size - overlap
            chunk_id += 1
    print(f"Total chunks: {len(all_chunks)}")
    return all_chunks


def get_embedding(text):
    """Identical to get_embedding() in your app, minus st.error (uses print)."""
    try:
        resp = ollama.embeddings(model="nomic-embed-text", prompt=text)
        emb = resp.get("embedding") or resp.get("data", [{}])[0].get("embedding")
        return np.array(emb, dtype=np.float32)
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


def build_vector_store_old(chunks):
    """Identical to build_vector_store() in your app — the brute-force version."""
    store = []
    for c in chunks:
        emb = get_embedding(c["text"])
        if emb is None:
            continue
        store.append({"chunk": c, "emb": emb, "norm": norm(emb)})
    return store


def search_similar_old(query, vector_store, top_k=5):
    """Identical to search_similar() in your app — the brute-force loop."""
    q_emb = get_embedding(query)
    if q_emb is None or not vector_store:
        return []
    q_norm = norm(q_emb)
    sims = []
    for item in vector_store:
        score = float(np.dot(q_emb, item["emb"]) / (q_norm * item["norm"] + 1e-12))
        sims.append((score, item["chunk"]))
    sims.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in sims[:top_k]]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_eval.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # 1. OCR + chunk the PDF (same chunks feed both old and new retrievers)
    chunks = pdf_to_chunks_headless(pdf_path)

    # 2. Build the OLD brute-force store (embeds every chunk once)
    print("\nBuilding OLD (brute-force) vector store...")
    old_store = build_vector_store_old(chunks)

    # 3. Build the NEW FAISS store (re-embeds — could optimize to reuse
    #    old_store's embeddings, but kept simple/explicit here)
    print("Building NEW (FAISS) vector store...")
    new_store = build_vector_store_faiss(chunks, get_embedding, dim=768)

    # 4. Run the comparison using the real, verified questions
    compare_old_vs_new(
        old_retrieve_fn=lambda q, k: search_similar_old(q, old_store, k),
        new_retrieve_fn=lambda q, k: search_similar_faiss(q, new_store, get_embedding, k),
        questions=TEST_QUESTIONS_KEYWORD,
        top_k=5,
    )