from core.config import settings
from core.logger import logger

EMBED_BATCH_SIZE = 32

_minilm_model = None
_specter2_model = None


def get_minilm():
    global _minilm_model
    if _minilm_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading MiniLM model...")
        _minilm_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _minilm_model


def get_specter2():
    global _specter2_model
    if _specter2_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SPECTER2 model...")
        _specter2_model = SentenceTransformer("allenai/specter2_base")
    return _specter2_model


def embed_titles(titles: list[str]) -> list[list[float]]:
    return get_minilm().encode(titles, batch_size=EMBED_BATCH_SIZE).tolist()


def embed_abstracts(abstracts: list[str]) -> list[list[float]]:
    return get_specter2().encode(abstracts, batch_size=EMBED_BATCH_SIZE).tolist()


def embed_contributions(contributions: list[str]) -> list[list[float]]:
    return get_specter2().encode(contributions, batch_size=EMBED_BATCH_SIZE).tolist()


def embed_query(query: str) -> dict[str, list[float]]:
    return {
        "title": get_minilm().encode([query])[0].tolist(),
        "abstract": get_specter2().encode([query])[0].tolist(),
        "contribution": get_specter2().encode([query])[0].tolist(),
    }
