#!/usr/bin/env python3
"""
Test semantic search on indexed CVs
Usage: python scripts/test_search.py "your search query"
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from cv_indexer import CVIndexer


def print_search_results(query: str, results: dict):
    """Pretty print search results"""
    print(f"🔍 Query: '{query}'")
    print(f"📊 Found {len(results['documents'])} results")
    print("=" * 80)
    print()
    
    if not results['documents']:
        print("No results found. Try a different query or index more CVs.")
        return
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'],
        results['metadatas'],
        results.get('distances', [0] * len(results['documents']))
    )):
        print(f"Result #{i+1}")
        print(f"{'─' * 80}")
        print(f"Source: {metadata.get('cv_name', 'Unknown')} ({metadata.get('source', 'unknown')})")
        print(f"Chunk: {metadata.get('chunk_id', '?')}/{metadata.get('total_chunks', '?')}")
        print(f"Similarity score: {1 - distance:.3f}" if distance else "N/A")
        print()
        
        # Print document with truncation if too long
        doc_preview = doc if len(doc) <= 500 else doc[:500] + "..."
        print(doc_preview)
        print()
        print()


def main():
    """Run search test"""
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,  # Less verbose for interactive use
        format=config.LOG_FORMAT
    )
    
    # Get query from command line or prompt
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("CV Search Test")
        print("=" * 80)
        print()
        query = input("Enter your search query: ").strip()
    
    if not query:
        print("Error: No query provided")
        print("Usage: python scripts/test_search.py 'your search query'")
        return 1
    
    print()
    
    # Initialize indexer
    try:
        indexer = CVIndexer()
    except Exception as e:
        print(f"❌ Error initializing indexer: {e}")
        print()
        print("Have you run 'python scripts/index_cvs.py' yet?")
        return 1
    
    # Check if index has data
    stats = indexer.get_stats()
    if stats['total_chunks'] == 0:
        print("❌ Error: No CVs indexed yet")
        print()
        print("Please run: python scripts/index_cvs.py")
        return 1
    
    print(f"📚 Index stats: {stats['total_chunks']} chunks from {stats['unique_cvs']} CVs")
    print()
    
    # Perform search
    try:
        results = indexer.search(query, n_results=5)
        print_search_results(query, results)
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return 1
    
    # Interactive mode - allow multiple searches
    while True:
        print()
        next_query = input("Enter another query (or press Enter to quit): ").strip()
        if not next_query:
            break
        
        print()
        results = indexer.search(next_query, n_results=5)
        print_search_results(next_query, results)
    
    print()
    print("Done! 👋")
    return 0


if __name__ == "__main__":
    sys.exit(main())



