import os
from sentence_transformers import SentenceTransformer
from core.logger import logger

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

def download_models():
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        logger.info(f"Created models directory at {MODELS_DIR}")

    # MiniLM
    minilm_path = os.path.join(MODELS_DIR, "all-MiniLM-L6-v2")
    if not os.path.exists(minilm_path):
        logger.info("Downloading all-MiniLM-L6-v2...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        model.save(minilm_path)
        logger.info(f"Saved MiniLM to {minilm_path}")
    else:
        logger.info("MiniLM already exists locally.")

    # SPECTER2
    specter2_path = os.path.join(MODELS_DIR, "specter2_base")
    if not os.path.exists(specter2_path):
        logger.info("Downloading specter2_base...")
        model = SentenceTransformer("allenai/specter2_base")
        model.save(specter2_path)
        logger.info(f"Saved SPECTER2 to {specter2_path}")
    else:
        logger.info("SPECTER2 already exists locally.")

if __name__ == "__main__":
    download_models()
