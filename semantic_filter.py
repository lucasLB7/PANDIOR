import numpy as np
from fastembed import TextEmbedding

# Initialize lazily so startup remains clean
_embedder = None

def get_embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _embedder


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def filter_relevant_records(
    query: str, items: list[dict], threshold: float = 0.35, top_k: int = 3
) -> list[dict]:
    """Filters out irrelevant text chunks and ranks by semantic similarity."""
    if not items:
        return []

    embedder = get_embedder()
    query_vec = list(embedder.embed([query]))[0]
    texts = [item.get("raw_text") or item.get("headline") or "" for item in items]
    item_vecs = list(embedder.embed(texts))

    scored_items = []
    for item, vec in zip(items, item_vecs):
        score = cosine_similarity(query_vec, vec)
        if score >= threshold:
            item_copy = dict(item)
            item_copy["relevance_score"] = round(score, 3)
            scored_items.append(item_copy)

    scored_items.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_items[:top_k]