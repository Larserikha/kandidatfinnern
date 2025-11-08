"""
Test script to compare search results with and without cross-encoder re-ranking

This script helps evaluate whether re-ranking improves search quality.
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cv_indexer import CVIndexer
import logging
import config

# Temporarily enable re-ranking for testing
config.ENABLE_RERANKING = True

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors
    format='%(levelname)s - %(message)s'
)

def format_result(idx, doc, metadata, distance=None, rerank_score=None):
    """Format a single search result for display"""
    name = metadata.get('cv_name', 'Unknown')
    office = metadata.get('office', 'Unknown')
    
    result = f"\n{idx}. {name} | {office}"
    
    if distance is not None:
        result += f" | Distance: {distance:.4f}"
    if rerank_score is not None:
        result += f" | Re-rank: {rerank_score:.4f}"
    
    result += f"\n   {doc[:150]}..."
    
    return result


def compare_search(query: str, n_results: int = 5):
    """
    Compare search results with and without re-ranking
    """
    print("=" * 70)
    print(f"🔍 Testing query: '{query}'")
    print("=" * 70)
    
    indexer = CVIndexer()
    
    # Search WITHOUT re-ranking
    print("\n📊 WITHOUT Re-ranking:")
    print("-" * 70)
    start_time = time.time()
    results_no_rerank = indexer.search(query, n_results=n_results, use_reranking=False)
    time_no_rerank = time.time() - start_time
    
    print(f"⏱️  Time: {time_no_rerank:.3f}s")
    print(f"📈 Found {len(results_no_rerank['documents'])} results\n")
    
    for i, (doc, metadata) in enumerate(zip(
        results_no_rerank['documents'],
        results_no_rerank['metadatas']
    ), 1):
        distance = results_no_rerank['distances'][i-1] if results_no_rerank.get('distances') else None
        print(format_result(i, doc, metadata, distance=distance))
    
    # Search WITH re-ranking
    print("\n\n🎯 WITH Re-ranking:")
    print("-" * 70)
    start_time = time.time()
    results_rerank = indexer.search(query, n_results=n_results, use_reranking=True)
    time_rerank = time.time() - start_time
    
    print(f"⏱️  Time: {time_rerank:.3f}s")
    print(f"📈 Found {len(results_rerank['documents'])} results\n")
    
    for i, (doc, metadata) in enumerate(zip(
        results_rerank['documents'],
        results_rerank['metadatas']
    ), 1):
        distance = results_rerank['distances'][i-1] if results_rerank.get('distances') else None
        rerank_score = results_rerank.get('rerank_scores', [None])[i-1] if results_rerank.get('rerank_scores') else None
        print(format_result(i, doc, metadata, distance=distance, rerank_score=rerank_score))
    
    # Compare results
    print("\n\n📊 Comparison:")
    print("-" * 70)
    print(f"Time difference: {time_rerank - time_no_rerank:.3f}s ({((time_rerank / time_no_rerank) - 1) * 100:.1f}% slower)")
    
    # Check if top results changed
    names_no_rerank = [m.get('cv_name', 'Unknown') for m in results_no_rerank['metadatas']]
    names_rerank = [m.get('cv_name', 'Unknown') for m in results_rerank['metadatas']]
    
    if names_no_rerank == names_rerank:
        print("✅ Top results are identical")
    else:
        print("🔄 Top results changed:")
        print(f"   Without: {names_no_rerank[0] if names_no_rerank else 'N/A'}")
        print(f"   With:    {names_rerank[0] if names_rerank else 'N/A'}")
        
        # Show which candidates moved up/down
        moved_up = [name for name in names_rerank[:3] if name not in names_no_rerank[:3]]
        moved_down = [name for name in names_no_rerank[:3] if name not in names_rerank[:3]]
        
        if moved_up:
            print(f"   ⬆️  Moved up: {', '.join(moved_up)}")
        if moved_down:
            print(f"   ⬇️  Moved down: {', '.join(moved_down)}")
    
    print()


def main():
    """Run comparison tests with different queries"""
    
    print("\n" + "=" * 70)
    print("🧪 Cross-Encoder Re-ranking Test")
    print("=" * 70)
    print("\nThis script compares search results with and without re-ranking.")
    print("Re-ranking is slower but may provide better relevance.\n")
    
    # Test queries
    test_queries = [
        "Senior konsulent med Azure cloud og enterprise architecture erfaring",
        "Kotlin utvikler med Android erfaring",
        "TOGAF og offentlig sektor prosjekter",
        "Python machine learning data science",
    ]
    
    for query in test_queries:
        try:
            compare_search(query, n_results=5)
        except Exception as e:
            print(f"\n❌ Error testing query '{query}': {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print("=" * 70)
    print("\n💡 Tips:")
    print("   - Compare the top results - are they more relevant with re-ranking?")
    print("   - Check the time difference - is it acceptable?")
    print("   - Enable re-ranking in config.py if results are better:")
    print("     ENABLE_RERANKING=true")


if __name__ == "__main__":
    main()

