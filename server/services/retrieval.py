from typing import List, Dict, TypedDict, Tuple
from collections import defaultdict

from langchain_core.documents import Document
from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, END

# Initialize the embedding model
embedding_model = SentenceTransformer(model_name="all-MiniLM-L6-v2")

# Connect to the Chroma vector store
vector_store = Chroma(
    collection_name="documents",
    embedding_function=embedding_model,
    persist_directory="./chroma_db",
)


class RetrievalState(TypedDict):
    query: str
    k: int
    expanded_k: int
    k_docs: int
    retrieved_chunks: List[Tuple[Document, float]]  # (chunk, distance)
    documents: Dict[str, List[Tuple[Document, float]]]


def initial_retrieval(state: RetrievalState):
    """Initial vector search"""
    chunks = vector_store.similarity_search_with_score(state["query"], state["k"])
    return {"retrieved_chunks": chunks}


def expand_k(state: RetrievalState):
    """
    Simple k expansion.
    Replace with LLM-based rewriting later if needed.
    """
    expanded = state["k"] + 25
    return {"expanded_k": expanded}


def expanded_retrieval(state: RetrievalState):
    """Second retrieval using expanded query"""
    new_chunks = vector_store.similarity_search_with_score(
        state["query"], state["expanded_k"]
    )
    combined_chunks = state["retrieved_chunks"] + new_chunks
    return {"retrieved_chunks": combined_chunks}


def aggregate_documents(state: RetrievalState):
    """
    Convert chunk-level retrieval into document-level retrieval
    using doc_id metadata.
    """
    doc_map = defaultdict(list)

    for chunk, score in state["retrieved_chunks"]:
        doc_id = chunk.metadata.get("doc_id", "unknown")
        doc_map[doc_id].append(chunk, score)

    return {"documents": doc_map}


def should_expand(state: RetrievalState) -> str:
    """
    Decide whether query expansion is needed.
    """
    unique_docs = {
        chunk.metadata.get("doc_id") for chunk, _ in state["retrieved_chunks"]
    }

    if len(unique_docs) < state["k_docs"]:
        return "expand"
    return "enough"


graph = StateGraph(RetrievalState)

graph.add_node("initial_retrieval", initial_retrieval)
graph.add_node("expand_k", expand_k)
graph.add_node("expanded_retrieval", expanded_retrieval)
graph.add_node("aggregate_documents", aggregate_documents)

graph.set_entry_point("initial_retrieval")

graph.add_conditional_edges(
    "initial_retrieval",
    should_expand,
    {
        "expand": "expand_k",
        "enough": "aggregate_documents",
    },
)

graph.add_edge("expand_k", "expanded_retrieval")
graph.add_conditional_edges(
    "expanded_retrieval",
    should_expand,
    {
        "expand": "expand_k",
        "enough": "aggregate_documents",
    },
)
graph.add_edge("aggregate_documents", END)

retrieval_graph = graph.compile()


def rrf_score(
    ranked_lists: List[List[str]],
    k: int = 60,
) -> Dict[str, float]:
    """
    Reciprocal Rank Fusion.
    ranked_lists: list of ranked doc_id lists
    """
    scores = defaultdict(float)

    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] += 1 / (k + rank)

    return scores


def retrieval_service(
    query: str, k_docs: int = 50, k_chunks: int = 250, rrf_k: int = 60
):
    """
    Retrieval Service

    This service takes the user's query and retrieves k relevant document not chunks from the chroma vector store. It uses langgraph to repeatedly call the vector store until k documents are retrieved and ranks them based on relevance to the query.
    """

    # Invoke the LangGraph retrieval workflow
    result = retrieval_graph.invoke({"query": query, "k": k_chunks, "k_docs": k_docs})

    documents = result["documents"]

    # Rank documents by number of relevant chunks
    ranked_docs_by_count = sorted(
        documents.items(), key=lambda x: len(x[1]), reverse=True
    )

    # Rank documents by best chunk score
    ranked_docs_by_best_score = sorted(
        documents.items(), key=lambda x: min(score for _, score in x[1])
    )
    ranked_lists = [
        [doc_id for doc_id, _ in ranked_docs_by_count],
        [doc_id for doc_id, _ in ranked_docs_by_best_score],
    ]

    rrf_scores = rrf_score(ranked_lists, k=rrf_k)

    final_ranking = sorted(
        documents.items(),
        key=lambda x: rrf_scores[x[0]],
        reverse=True,
    )

    return final_ranking[:k_docs]


if __name__ == "__main__":
    query = "graph neural networks for citation analysis"
    top_docs = retrieval_service(query)

    for doc_id, chunks in top_docs:
        print(f"\nDocument ID: {doc_id}")
        print(f"RRF score: {len(chunks)}")
        print(f"Relevant chunks: {len(chunks)}")
        print("Sample text:", chunks[0][0].page_content[:200])
