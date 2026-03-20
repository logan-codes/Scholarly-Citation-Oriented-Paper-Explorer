import os
from sentence_transformers import SentenceTransformer
from core.config import settings
from core.logger import logger

EMBED_BATCH_SIZE = 32
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

_minilm_model = None
_specter2_model = None


def get_minilm():
    global _minilm_model
    if _minilm_model is None:
        logger.info("Loading MiniLM model...")
        local_path = os.path.join(MODELS_DIR, "all-MiniLM-L6-v2")
        if os.path.exists(local_path):
            logger.info(f"Loading MiniLM from local path: {local_path}")
            _minilm_model = SentenceTransformer(local_path)
        else:
            logger.info("Local MiniLM not found, downloading from HF...")
            _minilm_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _minilm_model


def get_specter2():
    global _specter2_model
    if _specter2_model is None:
        logger.info("Loading SPECTER2 model...")
        local_path = os.path.join(MODELS_DIR, "specter2_base")
        if os.path.exists(local_path):
            logger.info(f"Loading SPECTER2 from local path: {local_path}")
            _specter2_model = SentenceTransformer(local_path)
        else:
            logger.info("Local SPECTER2 not found, downloading from HF...")
            _specter2_model = SentenceTransformer("allenai/specter2_base")
    return _specter2_model


def embed_title(title: str) -> list[float]:
    return get_minilm().encode([title])[0].tolist()


def embed_abstract(abstract: str) -> list[float]:
    return get_specter2().encode([abstract])[0].tolist()


def embed_contribution(contribution: str) -> list[float]:
    return get_specter2().encode([contribution])[0].tolist()


def embed_query(query: str) -> dict[str, list[float]]:
    return {
        "title": get_minilm().encode([query])[0].tolist(),
        "abstract": get_specter2().encode([query])[0].tolist(),
        "contribution": get_specter2().encode([query])[0].tolist(),
    }
