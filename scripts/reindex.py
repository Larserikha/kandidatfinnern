#!/usr/bin/env python3
"""
Re-index all CVs (deletes existing index and rebuilds from scratch)
Use this when:
- CVs have been significantly updated
- You want to change chunk size or other indexing parameters
- Index seems corrupted
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from cv_indexer import CVIndexer


def main():
    """Re-index all CVs"""
    print("=" * 60)
    print("CV Re-Indexing Script")
    print("=" * 60)
    print()
    
    print("⚠️  WARNING: This will delete the existing index and rebuild from scratch.")
    print()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT
    )
    
    # Show current config
    print("Configuration:")
    for key, value in config.get_config_summary().items():
        print(f"  {key}: {value}")
    print()
    
    # Ask for confirmation
    response = input("Are you sure you want to re-index? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return 0
    
    print()
    print("Starting re-indexing...")
    print("-" * 60)
    
    # Initialize indexer with reset=True
    indexer = CVIndexer(reset=True)
    
    # Index all CVs
    print()
    stats = indexer.index_all_cvs()
    
    print()
    print("-" * 60)
    print("✅ Re-indexing complete!")
    print()
    print("Results:")
    print(f"  - Files processed: {stats['success']}/{stats['total_files']}")
    print(f"  - Total chunks created: {stats['total_chunks']}")
    if stats['failed'] > 0:
        print(f"  - Failed: {stats['failed']}")
    
    # Show final state
    final_stats = indexer.get_stats()
    print()
    print("Final index state:")
    print(f"  - Total chunks: {final_stats['total_chunks']}")
    print(f"  - Unique CVs: {final_stats['unique_cvs']}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())



