from services.vectorstore import add_chunks
from docling.document import Document

def build_docling_document(paper):
    text = f"""
# {paper['title']}

**Authors:** {', '.join(paper['authors'])}
**Year:** {paper.get('year', '')}
**Source:** {paper['source']}

## Abstract
{paper['abstract']}
"""

    return Document(
        text=text,
        metadata={
            "source": paper["source"],
            "title": paper["title"],
            "authors": paper["authors"],
            "year": paper.get("year"),
            "doi": paper.get("doi"),
            "url": paper.get("url")
        }
    )

from docling.chunking import HybridChunker
from transformers import AutoTokenizer

# Load tokenizer once (important for performance)
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# Initialize hybrid chunker
chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=256,     # Good for embedding models
    overlap=40          # Small overlap for context retention
)

def hybrid_chunk_document(doc):
    chunks = chunker.chunk(doc)

    structured_chunks = []

    for i, chunk in enumerate(chunks):
        structured_chunks.append({
            "chunk_id": i,
            "text": chunk.text,
            "metadata": doc.metadata
        })

    return structured_chunks

def process_paper_with_hybrid_chunking(paper):
    # 1. Build structured Docling document
    doc = build_docling_document(paper)

    # 2. Apply Hybrid Chunking
    chunks = hybrid_chunk_document(doc)

    return chunks

def process_query_results(papers):
    for paper in papers:
        chunks = process_paper_with_hybrid_chunking(paper)

        add_chunks(chunks)   # 🔥 THIS connects to Chroma

    print("Ingestion completed.")