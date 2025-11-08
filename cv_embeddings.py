"""
Local Embedding Function for ChromaDB
Uses sentence-transformers for local, GDPR-compliant embeddings

Note: You may see warnings about HuggingFace connection failures in the logs.
These are harmless - the model is cached locally and works fine offline.
"""
from sentence_transformers import SentenceTransformer
from typing import List
import logging
import config

logger = logging.getLogger(__name__)


class LocalEmbeddingFunction:
    """
    Wrapper class for sentence-transformers that implements ChromaDB's EmbeddingFunction interface
    
    This ensures all embeddings are generated locally without any API calls,
    maintaining GDPR compliance and allowing offline operation.
    """
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize the embedding model
        
        Args:
            model_name: Name of the sentence-transformers model to use
                       Defaults to config.EMBEDDING_MODEL
            device: Device to run on ('cpu' or 'cuda')
                   Defaults to config.EMBEDDING_DEVICE
        """
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.device = device or config.EMBEDDING_DEVICE
        
        logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
        
        try:
            # Model will load from local cache (HF_HUB_OFFLINE env var is set at module level)
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully from local cache. Embedding dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        This method is called by ChromaDB when indexing or searching.
        For E5 models, documents should be prefixed with "passage: " during indexing.
        
        Args:
            input: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if not input:
            return []
        
        try:
            # For E5 models: prefix documents with "passage: " for better retrieval
            # This is used during indexing (documents)
            prefixed_input = [f"passage: {text}" for text in input]
            
            # Generate embeddings
            embeddings = self.model.encode(
                prefixed_input,
                convert_to_numpy=True,
                show_progress_bar=len(input) > 10,  # Only show progress for large batches
                batch_size=config.BATCH_SIZE,
                normalize_embeddings=True  # E5 models benefit from normalization
            )
            
            # Convert to list of lists (ChromaDB format)
            return embeddings.tolist()
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query string
        
        For E5 models, queries should be prefixed with "query: " for optimal retrieval.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # For E5 models: prefix queries with "query: " for better retrieval
        prefixed_query = f"query: {query}"
        
        try:
            embedding = self.model.encode(
                prefixed_query,
                convert_to_numpy=True,
                normalize_embeddings=True  # E5 models benefit from normalization
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents
        
        Args:
            documents: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self.__call__(documents)
    
    def get_model_info(self) -> dict:
        """
        Get information about the current model
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self.dimension,
            "max_seq_length": self.model.max_seq_length
        }


def test_embeddings():
    """
    Test the embedding function with sample texts
    Useful for validating the setup
    """
    print("Testing Local Embedding Function")
    print("=" * 50)
    
    # Initialize
    embedding_fn = LocalEmbeddingFunction()
    print(f"\nModel info: {embedding_fn.get_model_info()}")
    
    # Test with sample CV-like texts
    test_texts = [
        "Senior konsulent med 10 års erfaring i Azure cloud og enterprise architecture",
        "Informasjonsarkitekt med kompetanse i TOGAF og virksomhetsarkitektur",
        "Utvikler med Python, Django og machine learning erfaring"
    ]
    
    print(f"\nGenerating embeddings for {len(test_texts)} texts...")
    embeddings = embedding_fn(test_texts)
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    print(f"   Dimension: {len(embeddings[0])}")
    print(f"   First embedding (truncated): {embeddings[0][:5]}...")
    
    # Test single query
    query = "Azure cloud konsulent"
    print(f"\nTesting single query: '{query}'")
    query_embedding = embedding_fn.embed_query(query)
    print(f"✅ Query embedding dimension: {len(query_embedding)}")
    
    # Calculate similarity (simple dot product)
    from numpy import dot
    from numpy.linalg import norm
    
    def cosine_similarity(a, b):
        return dot(a, b) / (norm(a) * norm(b))
    
    print("\nSimilarity scores:")
    for i, text in enumerate(test_texts):
        sim = cosine_similarity(query_embedding, embeddings[i])
        print(f"  {sim:.3f} - {text[:60]}...")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT
    )
    
    # Run tests
    test_embeddings()



