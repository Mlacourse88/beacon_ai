"""
Shared Utilities for BEACON_AI Project
Provides logging, configuration, and common functions.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Any
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings # Import Embeddings base class

# Conditional import for sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

# Load environment variables
load_dotenv()

# ========================= CONFIGURATION =========================

PROJECT_ROOT = Path(__file__).parent
FAISS_INDEX_PATH = PROJECT_ROOT / "faiss_indexes"
BIBLICAL_PDF_PATH = PROJECT_ROOT / "biblical_ai" / "PDFs_Raw_Text"
GENERAL_KB_PATH = PROJECT_ROOT / "general_ai" / "knowledge_base"

# Global Embedding Model Configuration
DEFAULT_EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini").lower() # 'gemini' or 'huggingface'
DEFAULT_GEMINI_MODEL_NAME = "models/text-embedding-004"
DEFAULT_HF_MODEL_NAME = "all-MiniLM-L6-v2"

# ========================= LOGGING =========================

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for a module.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logging(__name__)

# ========================= API & PATHS =========================

def get_project_root() -> Path:
    """Returns the project root directory."""
    return PROJECT_ROOT

def get_api_key() -> str:
    """
    Retrieve Google API key from environment.
    
    Returns:
        str: The API key.
    
    Raises:
        ValueError: If API key is not found.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        logger.error("GOOGLE_API_KEY not found in environment variables.")
        raise ValueError(
            "GOOGLE_API_KEY not found in environment. "
            "Please set it in your .env file or environment variables."
        )
    
    return api_key

# ========================= EMBEDDING HELPERS =========================

class HuggingFaceEmbeddingsWrapper(Embeddings):
    """
    Wrapper for SentenceTransformer to match LangChain's Embeddings interface.
    """
    def __init__(self, model_name: str):
        if not HUGGINGFACE_AVAILABLE:
            raise ImportError("sentence-transformers not installed. Please run 'pip install sentence-transformers'")
        logger.info(f"Loading SentenceTransformer model: {model_name}...")
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of texts."""
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embeds a single query."""
        embedding = self.model.encode(text, show_progress_bar=False, convert_to_numpy=True)
        return embedding.tolist()

def get_embedding_model(
    provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> Embeddings:
    """
    Instantiates and returns the appropriate embedding model.
    """
    provider = provider or DEFAULT_EMBEDDING_PROVIDER
    
    if provider == "huggingface":
        name = model_name or DEFAULT_HF_MODEL_NAME
        return HuggingFaceEmbeddingsWrapper(name)
    elif provider == "gemini":
        name = model_name or DEFAULT_GEMINI_MODEL_NAME
        return GoogleGenerativeAIEmbeddings(
            model=name,
            google_api_key=get_api_key()
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


# ========================= FAISS UTILS =========================

def load_faiss_index(embeddings_instance: Embeddings, index_name: str = "beacon_index") -> Optional[FAISS]:
    """
    Loads a FAISS index from disk.
    
    Args:
        index_name (str): The name of the folder containing the index (inside faiss_indexes/).
        embeddings_instance (Embeddings): An instantiated embedding model compatible with the index.
        
    Returns:
        FAISS: The loaded vector store, or None if not found.
    """
    index_path = FAISS_INDEX_PATH / index_name
    
    if not index_path.exists():
        logger.warning(f"FAISS index not found at {index_path}")
        return None
        
    try:
        vector_store = FAISS.load_local(
            str(index_path), 
            embeddings_instance, 
            allow_dangerous_deserialization=True
        )
        logger.info(f"Successfully loaded FAISS index '{index_name}' from {index_path}")
        return vector_store
    except Exception as e:
        logger.error(f"Failed to load FAISS index '{index_name}': {e}")
        return None


def query_knowledge_base(query: str, vector_store: FAISS, k: int = 5) -> List[Any]: # List[Document] but Any for broader compatibility
    """
    Queries the knowledge base for relevant documents.
    
    Args:
        query (str): The search query.
        vector_store (FAISS): The loaded vector store.
        k (int): Number of results to return.
        
    Returns:
        List[Document]: Top k matching documents.
    """
    if not vector_store:
        logger.error("Vector store is None. Cannot query.")
        return []
    
    try:
        results = vector_store.similarity_search(query, k=k)
        return results
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return []