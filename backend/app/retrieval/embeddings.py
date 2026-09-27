"""
retrieval/embeddings.py – Embedding model factory.
Supports sentence-transformers (local) and can be extended for OpenAI/Gemini embeddings.
"""

from __future__ import annotations
import logging
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model():
    """Return a cached embedding model instance."""
    settings = get_settings()
    model_name = settings.embedding_model
    logger.info("Loading embedding model: %s", model_name)
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
