import logging

logging.basicConfig(level=logging.INFO,filename="app.log")
logger = logging.getLogger(__name__)

# Silence noisy libraries
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
