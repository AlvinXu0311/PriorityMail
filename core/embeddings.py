"""
Email Embedding Generator

Generates semantic embeddings for emails using various embedding models.
"""

import numpy as np
import logging
from typing import List, Optional, Union
import os

logger = logging.getLogger(__name__)


class EmailEmbedder:
    """Generate embeddings for email text."""

    def __init__(self, provider: str = "ollama",
                 model: str = None):
        """
        Initialize embedder.

        Args:
            provider: 'ollama' (default), 'openai', or 'sentence-transformers'
            model: Model name (defaults to qwen3-embedding:latest for ollama)
        """
        # Default to Qwen embedding model
        if model is None:
            if provider == "ollama":
                model = "qwen3-embedding:latest"
            elif provider == "openai":
                import os
                model = os.getenv('OPENAI_MODEL', 'text-embedding-3-small')
            else:
                raise ValueError("model must be specified for sentence-transformers")

        self.provider = provider
        self.model_name = model
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the embedding model based on provider."""
        if self.provider == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("SentenceTransformer loaded successfully")
            except ImportError:
                logger.error("sentence-transformers not installed. Install: pip install sentence-transformers")
                raise
            except Exception as e:
                logger.error(f"Error loading SentenceTransformer: {e}")
                raise

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY must be set in .env")
                self.model = OpenAI(api_key=api_key)
                logger.info(f"OpenAI embeddings initialized: {self.model_name}")
            except ImportError:
                logger.error("openai not installed. Install: pip install openai")
                raise

        elif self.provider == "ollama":
            import requests
            self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            # Test connection
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info(f"Ollama embeddings initialized: {self.model_name}")
                else:
                    logger.warning("Ollama not responding, embeddings may fail")
            except Exception as e:
                logger.warning(f"Could not connect to Ollama: {e}")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector as numpy array
        """
        if not text or text.strip() == "":
            # Return zero vector for empty text
            return np.zeros(self._get_embedding_dim())

        if self.provider == "sentence-transformers":
            return self.model.encode(text, show_progress_bar=False)

        elif self.provider == "openai":
            try:
                response = self.model.embeddings.create(
                    input=text[:8000],  # OpenAI limit
                    model=self.model_name
                )
                return np.array(response.data[0].embedding)
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")
                return np.zeros(self._get_embedding_dim())

        elif self.provider == "ollama":
            import requests
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text[:2000]
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    return np.array(response.json()['embedding'])
                else:
                    logger.error(f"Ollama embedding error: {response.status_code}")
                    return np.zeros(self._get_embedding_dim())
            except Exception as e:
                logger.error(f"Ollama embedding error: {e}")
                return np.zeros(self._get_embedding_dim())

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            Array of embeddings (n_texts, embedding_dim)
        """
        if self.provider == "sentence-transformers":
            return self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )

        else:
            # Process one by one for OpenAI/Ollama
            embeddings = []
            for text in texts:
                embeddings.append(self.embed_text(text))
            return np.array(embeddings)

    def _get_embedding_dim(self) -> int:
        """Get embedding dimension based on model."""
        dims = {
            # Ollama embedding models (RECOMMENDED)
            "qwen3-embedding": 768,
            "mxbai-embed-large": 1024,
            "snowflake-arctic-embed": 1024,
            "all-minilm": 384,
            # OpenAI
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
            # Sentence Transformers
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
        }
        return dims.get(self.model_name, 768)  # Default to qwen3-embedding dim


def create_email_embeddings(df, embedder: EmailEmbedder,
                            subject_weight: float = 0.3,
                            body_weight: float = 0.7) -> np.ndarray:
    """
    Create weighted embeddings from email subject and body.

    Args:
        df: DataFrame with 'subject' and 'body' columns
        embedder: EmailEmbedder instance
        subject_weight: Weight for subject embedding
        body_weight: Weight for body embedding

    Returns:
        Array of combined embeddings
    """
    logger.info(f"Generating embeddings for {len(df)} emails...")

    # Combine subject and body with weights
    combined_texts = []
    for _, row in df.iterrows():
        subject = str(row.get('subject', ''))
        body = str(row.get('body', ''))[:1000]  # Limit body length

        # Weight subject more by repeating it
        combined = f"{subject} {subject} {body}"
        combined_texts.append(combined)

    # Generate embeddings
    embeddings = embedder.embed_batch(combined_texts)

    logger.info(f"Generated embeddings with shape: {embeddings.shape}")
    return embeddings
