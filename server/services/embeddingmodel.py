from sentence_transformers import SentenceTransformer
import numpy as np

# Load once globally
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

[
    {"chunk_id": 0, "text": "...", "metadata": {...}},
    {"chunk_id": 1, "text": "...", "metadata": {...}}
]
def embed_chunks(chunks):
    texts = [chunk["text"] for chunk in chunks]

    # Batch encoding (fast)
    embeddings = embedding_model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Attach embeddings back
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i]

    return chunks

{
    "chunk_id": 0,
    "text": "...",
    "metadata": {...},
    "embedding": [0.023, -0.441, ... 384 values]
}

def process_and_embed_paper(paper):
    doc = build_docling_document(paper)
    chunks = hybrid_chunk_document(doc)
    embedded_chunks = embed_chunks(chunks)
    return embedded_chunks

def embed_query(query):
    return embedding_model.encode(query, convert_to_numpy=True)

from numpy.linalg import norm

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))


def search(query, embedded_chunks, top_k=5):
    query_vector = embed_query(query)

    scored_chunks = []

    for chunk in embedded_chunks:
        score = cosine_similarity(query_vector, chunk["embedding"])
        scored_chunks.append((score, chunk))

    scored_chunks.sort(reverse=True, key=lambda x: x[0])

    return scored_chunks[:top_k]