"""
Cross-Encoder Reranker for CV-RAG System
Uses cross-encoder models to re-rank search results for better relevance

Cross-encoders score query-document pairs directly, providing more accurate
relevance scores than bi-encoder similarity alone.
"""
import os
from sentence_transformers import CrossEncoder
from typing import List, Dict, Tuple
import logging
import config

# Prevent HuggingFace from trying to contact their servers
# Model is cached locally, so we don't need network access
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Re-ranks search results using a cross-encoder model
    
    Cross-encoders take query and document as input together and output
    a relevance score directly, providing better accuracy than bi-encoder
    similarity scores alone.
    """
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize the cross-encoder model
        
        Args:
            model_name: Name of the cross-encoder model
                       Defaults to config.CROSS_ENCODER_MODEL
            device: Device to run on ('cpu' or 'cuda')
                   Defaults to config.EMBEDDING_DEVICE
        """
        self.model_name = model_name or getattr(config, 'CROSS_ENCODER_MODEL', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.device = device or config.EMBEDDING_DEVICE
        
        logger.info(f"Loading cross-encoder model: {self.model_name} on {self.device}")
        
        try:
            # CrossEncoder loads from local cache (HF_HUB_OFFLINE env var is set)
            self.model = CrossEncoder(self.model_name, device=self.device)
            logger.info(f"Cross-encoder model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            raise
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = None
    ) -> List[Tuple[int, float]]:
        """
        Re-rank documents based on query relevance
        
        Args:
            query: Search query
            documents: List of document texts to re-rank
            top_k: Number of top results to return (None = return all)
            
        Returns:
            List of tuples (index, score) sorted by score (highest first)
            Score is typically 0-1 range, higher = more relevant
        """
        if not documents:
            return []
        
        # Create query-document pairs for cross-encoder
        pairs = [[query, doc] for doc in documents]
        
        # Get relevance scores from cross-encoder
        # Returns array of scores (one per pair)
        scores = self.model.predict(pairs)
        
        # Convert to list of (index, score) tuples
        scored_indices = [(i, float(score)) for i, score in enumerate(scores)]
        
        # Sort by score (highest first)
        scored_indices.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k if specified
        if top_k:
            return scored_indices[:top_k]
        
        return scored_indices
    
    def rerank_search_results(
        self,
        query: str,
        search_results: Dict,
        top_k: int = None
    ) -> Dict:
        """
        Re-rank ChromaDB search results and return re-ordered results
        
        Args:
            query: Search query
            search_results: Dictionary from cv_indexer.search() containing:
                - documents: List of document texts
                - metadatas: List of metadata dicts
                - ids: List of chunk IDs
                - distances: List of distance scores
            top_k: Number of top results to return after re-ranking
            
        Returns:
            Same structure as search_results, but re-ordered by cross-encoder scores
        """
        if not search_results.get('documents'):
            return search_results
        
        documents = search_results['documents']
        
        # Re-rank documents
        reranked_indices = self.rerank(query, documents, top_k=top_k)
        
        # Re-order all result lists based on re-ranking
        reranked_results = {
            'ids': [search_results['ids'][idx] for idx, _ in reranked_indices],
            'documents': [search_results['documents'][idx] for idx, _ in reranked_indices],
            'metadatas': [search_results['metadatas'][idx] for idx, _ in reranked_indices],
            'distances': [search_results['distances'][idx] if search_results.get('distances') else None 
                         for idx, _ in reranked_indices],
            'rerank_scores': [score for _, score in reranked_indices]  # Add cross-encoder scores
        }
        
        return reranked_results


def test_reranker():
    """
    Test the cross-encoder reranker with sample queries
    """
    print("Testing Cross-Encoder Reranker")
    print("=" * 50)
    
    # Initialize
    reranker = CrossEncoderReranker()
    print(f"\nModel: {reranker.model_name}")
    
    # Sample query and documents
    query = "Senior konsulent med Azure cloud og enterprise architecture erfaring"
    
    documents = [
        "Junior utvikler med 2 års erfaring i Python og Django",
        "Senior konsulent med 10 års erfaring i Azure cloud, enterprise architecture, og TOGAF",
        "Utvikler med React og TypeScript erfaring",
        "Informasjonsarkitekt med kompetanse i TOGAF, enterprise architecture, og Azure cloud services",
        "Designer med UX/UI erfaring"
    ]
    
    print(f"\nQuery: '{query}'")
    print(f"\nRe-ranking {len(documents)} documents...")
    
    # Re-rank
    reranked = reranker.rerank(query, documents, top_k=3)
    
    print("\nTop 3 results (after re-ranking):")
    for rank, (idx, score) in enumerate(reranked, 1):
        print(f"\n{rank}. Score: {score:.4f}")
        print(f"   {documents[idx][:80]}...")
    
    print("\n✅ Re-ranking test complete!")


if __name__ == "__main__":
    import os
    # Prevent HuggingFace from trying to contact their servers
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT
    )
    
    test_reranker()

