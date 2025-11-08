#!/usr/bin/env python3
"""
Index all CVs in the data/cvs/ directory
Run this script whenever you add new CVs or want to rebuild the index
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from cv_indexer import CVIndexer


def main():
    """Index all CVs"""
    print("=" * 60)
    print("CV Indexing Script")
    print("=" * 60)
    print()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT
    )
    
    # Check if CVs directory exists and has files
    if not config.CVS_DIR.exists():
        print(f"❌ Error: CVs directory not found: {config.CVS_DIR}")
        print(f"   Please create it and add CV files")
        return 1
    
    # Find all CV files based on supported formats
    cv_files = []
    for ext in config.SUPPORTED_CV_FORMATS:
        cv_files.extend(config.CVS_DIR.glob(f"*{ext}"))
    
    if not cv_files:
        print(f"❌ Error: No CV files found in {config.CVS_DIR}")
        print(f"   Supported formats: {config.SUPPORTED_CV_FORMATS}")
        print()
        print("To get started:")
        print("  1. Add CV files to data/cvs/")
        print("  2. Run this script again")
        return 1
    
    print(f"📂 CVs directory: {config.CVS_DIR}")
    print(f"📊 Found {len(cv_files)} CV files")
    print(f"🤖 Using embedding model: {config.EMBEDDING_MODEL}")
    print()
    
    # Ask for confirmation
    response = input("Do you want to index these CVs? (y/n): ")
    if response.lower() not in ['y', 'yes']:
        print("Cancelled.")
        return 0
    
    print()
    print("Starting indexing...")
    print("-" * 60)
    
    # Initialize indexer (without reset - will add to existing index)
    indexer = CVIndexer(reset=False)
    
    # Show current state
    current_stats = indexer.get_stats()
    print(f"Current index state:")
    print(f"  - Total chunks: {current_stats['total_chunks']}")
    print(f"  - Unique CVs: {current_stats['unique_cvs']}")
    print()
    
    # Index all CVs
    print("Indexing CVs...")
    stats = indexer.index_all_cvs()
    
    print()
    print("-" * 60)
    print("✅ Indexing complete!")
    print()
    print("Results:")
    print(f"  - Files processed: {stats['success']}/{stats['total_files']}")
    print(f"  - Total chunks created: {stats['total_chunks']}")
    if stats['failed'] > 0:
        print(f"  - Failed: {stats['failed']}")
    
    # Show new state
    new_stats = indexer.get_stats()
    print()
    print("New index state:")
    print(f"  - Total chunks: {new_stats['total_chunks']}")
    print(f"  - Unique CVs: {new_stats['unique_cvs']}")
    print()
    
    print("Next steps:")
    print("  1. Test search: python scripts/test_search.py 'your query'")
    print("  2. Start MCP server: python mcp_server.py")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())



