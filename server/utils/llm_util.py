from core.config import settings
from core.logger import logger
from langchain_groq import ChatGroq

GROQ_MODEL = "llama-3.1-8b-instant"

_groq_llm = None


def get_groq_llm() -> ChatGroq:
    global _groq_llm
    if _groq_llm is None:
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        _groq_llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0.1,
            groq_api_key=api_key,
        )
        logger.info("Groq LLM initialised (%s)", GROQ_MODEL)
    return _groq_llm
