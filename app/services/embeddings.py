import logging
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

_embeddings = None
_lock = threading.Lock()


def get_embeddings():
    """
    Lazily load the HuggingFace sentence-transformer embedding model.
    The first call downloads weights (cached afterwards), so we defer
    until actually needed to keep app startup fast.
    """
    global _embeddings
    if _embeddings is not None:
        return _embeddings
    with _lock:
        if _embeddings is not None:
            return _embeddings
        from langchain_huggingface import HuggingFaceEmbeddings

        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model ready")
        return _embeddings
