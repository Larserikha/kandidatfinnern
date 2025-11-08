"""
Configuration file for CV-RAG System
All paths and settings are defined here for easy customization
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Data directories
DATA_DIR = BASE_DIR / "data"
CVS_DIR = DATA_DIR / "cvs"
CHROMADB_DIR = DATA_DIR / "chromadb"

# Ensure directories exist
CVS_DIR.mkdir(parents=True, exist_ok=True)
CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

# Embedding model configuration
# Using multilingual-e5-large for Norwegian/multilingual support
EMBEDDING_MODEL_OPTIONS = {
    "fast": "all-MiniLM-L6-v2",           # 90 MB, very fast, English-focused
    "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",  # 420 MB, better Norwegian
    "good": "intfloat/multilingual-e5-base",  # 1.1 GB, 768D
    "best": "intfloat/multilingual-e5-large"  # 2.2 GB, 1024D (current default)
}

# Default embedding model (can be overridden with env var)
# Using "best" (e5-large) for optimal Norwegian CV search
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL_OPTIONS["best"])
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")  # "cpu" or "cuda"

# ChromaDB configuration
CHROMADB_COLLECTION_NAME = "cvs"
CHROMADB_DISTANCE_METRIC = "cosine"  # cosine, l2, or ip (inner product)

# Chunking strategy
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))  # words
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))  # words
MIN_CHUNK_SIZE = int(os.getenv("MIN_CHUNK_SIZE", "50"))  # words

# Search configuration
# Increased from 5 to 12 for better overview of candidates
DEFAULT_SEARCH_RESULTS = int(os.getenv("DEFAULT_SEARCH_RESULTS", "12"))
MAX_SEARCH_RESULTS = 20

# MCP Server configuration
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "3000"))

# Flowcase API configuration (when available)
FLOWCASE_API_KEY = os.getenv("FLOWCASE_API_KEY", "")
FLOWCASE_API_URL = os.getenv("FLOWCASE_API_URL", "https://api.flowcase.com")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File formats supported for CV import
SUPPORTED_CV_FORMATS = [".json", ".md", ".txt", ".markdown"]

# Performance settings
BATCH_SIZE = 32  # For batch embedding generation
CACHE_SIZE = 100  # Number of queries to cache

# Cross-encoder re-ranking configuration
# Cross-encoder provides better relevance scoring but is slower (~5-10x)
# Upgraded to BGE-reranker-base for better multilingual support (Nov 2025)
# Re-ranking is enabled by default for better search quality
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "BAAI/bge-reranker-base")
ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "true").lower() == "true"  # Enabled by default
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "50"))  # Number of candidates to re-rank

def get_config_summary():
    """Return a summary of current configuration"""
    return {
        "embedding_model": EMBEDDING_MODEL,
        "device": EMBEDDING_DEVICE,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "chromadb_path": str(CHROMADB_DIR),
        "cvs_path": str(CVS_DIR),
        "default_search_results": DEFAULT_SEARCH_RESULTS,
    }

if __name__ == "__main__":
    # Print configuration when run directly
    print("CV-RAG System Configuration")
    print("=" * 50)
    for key, value in get_config_summary().items():
        print(f"{key:.<30} {value}")

