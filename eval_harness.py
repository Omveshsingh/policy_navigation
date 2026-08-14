import time
import numpy as np

# --- Page-based: fill these in yourself from YOUR own PDF (see docstring) ---
TEST_QUESTIONS = [
    ("What is the maximum claim amount under section 4?", 3)
]

# --- Keyword-based: ready to use right now, verified against the real PDF ---
TEST_QUESTIONS_KEYWORD = [
    ("What is the repatriation benefit maximum payment?", "$2,000"),
    ("How much is the educational benefit paid annually to a qualified student?", "$3,000"),
    ("What is the Dependent Life Insurance scheduled benefit for a spouse?", "$5,000"),
    ("How many days is the grace period for premium payment?", "31 days"),
    ("Within how many days after a loss must written notice of claim be sent?", "20 days"),
    ("Within how many days after a loss must written proof of loss be sent?", "90 days"),
    ("What is the minimum draft amount from the Interest Draft Account?", "$500"),
    ("What percentage of the Scheduled Benefit is paid for accidental loss of life?", "100%"),
    ("What percentage of the Scheduled Benefit applies to a Member age 70 to 75?", "65%"),
    ("What is the maximum dollar amount payable under Accelerated Benefits?", "$250,000"),
    ("How many years after proof of loss can legal action be started at the latest?", "three years"),
    ("What is the Member Life Insurance Scheduled Benefit amount for all members?", "$10,000"),
]


def hit_at_k(retrieved_chunks: list, expected_page: int) -> bool:
    """Page-based hit check. True if the expected page appears anywhere
    in the retrieved chunks."""
    return any(c["page"] == expected_page for c in retrieved_chunks)


def hit_at_k_keyword(retrieved_chunks: list, expected_keyword: str) -> bool:
    """Keyword-based hit check. True if the expected fact/number appears
    (case-insensitive) in the text of any retrieved chunk."""
    kw = expected_keyword.lower()
    return any(kw in c["text"].lower() for c in retrieved_chunks)


def evaluate(retrieve_fn, questions, top_k=5, label="retriever", use_keyword=True):
    """
    retrieve_fn(query, top_k) -> list of chunk dicts
    use_keyword: True to use TEST_QUESTIONS_KEYWORD-style (question, keyword)
                 pairs; False for (question, page) pairs.
    Returns (hit_rate, avg_latency_seconds)
    """
    if not questions:
        print(f"[{label}] No questions provided.")
        return None, None

    hits = 0
    latencies = []
    for question, expected in questions:
        start = time.perf_counter()
        retrieved = retrieve_fn(question, top_k)
        latencies.append(time.perf_counter() - start)
        is_hit = hit_at_k_keyword(retrieved, expected) if use_keyword else hit_at_k(retrieved, expected)
        if is_hit:
            hits += 1

    hit_rate = hits / len(questions)
    avg_latency = sum(latencies) / len(latencies)
    print(f"[{label}] Hit@{top_k}: {hit_rate:.0%}  "
          f"({hits}/{len(questions)})  avg latency: {avg_latency*1000:.1f}ms")
    return hit_rate, avg_latency


def compare_old_vs_new(old_retrieve_fn, new_retrieve_fn, questions, top_k=5, use_keyword=True):
    """
    old_retrieve_fn(query, top_k) -> chunks, using your existing search_similar()
    new_retrieve_fn(query, top_k) -> chunks, using search_similar_faiss()
    """
    print("=" * 60)
    print("RETRIEVAL EVAL — brute-force loop vs FAISS index")
    print("=" * 60)

    old_hit, old_lat = evaluate(old_retrieve_fn, questions, top_k, "OLD (brute-force loop)", use_keyword)
    new_hit, new_lat = evaluate(new_retrieve_fn, questions, top_k, "NEW (FAISS index)", use_keyword)

    if old_hit is not None and new_hit is not None:
        print("-" * 60)
        print(f"Hit@{top_k} change: {old_hit:.0%} -> {new_hit:.0%}")
        if old_lat and new_lat:
            speedup = old_lat / new_lat if new_lat > 0 else float("inf")
            print(f"Latency: {old_lat*1000:.1f}ms -> {new_lat*1000:.1f}ms ({speedup:.1f}x)")
        print("These are the numbers to put on your resume — not before.")


if __name__ == "__main__":
    print(__doc__)
    print(f"TEST_QUESTIONS_KEYWORD has {len(TEST_QUESTIONS_KEYWORD)} real, ready-to-use pairs.")