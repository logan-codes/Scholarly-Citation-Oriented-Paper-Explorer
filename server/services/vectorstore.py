import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


# 🔥 Chroma embedding function (auto-embeds)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# 🔥 Persistent client
chroma_client = chromadb.Client(
    Settings(
        persist_directory="./chroma_storage",
        anonymized_telemetry=False
    )
)

# 🔥 Collection
collection = chroma_client.get_or_create_collection(
    name="research_papers",
    embedding_function=sentence_transformer_ef,
    metadata={"hnsw:space": "cosine"}
)


# ✅ Add chunks
def add_chunks(chunks):
    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )


# ✅ Semantic search
def semantic_search(query, top_k=5):
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    return results


# ✅ Delete by IDs
def delete_by_ids(ids):
    collection.delete(ids=ids)


# ✅ Clear collection
def clear_collection():
    chroma_client.delete_collection("research_papers")