#!/usr/bin/env python3
"""
Sync CVs from Flowcase and re-index
Workflow:
1. Download CVs from Flowcase API
2. Save as individual markdown files
3. Re-index in ChromaDB
"""
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from flowcase_api import FlowcaseAPI
from cv_indexer import CVIndexer


def main():
    """Sync CVs from Flowcase and re-index"""
    # Default offices to sync
    DEFAULT_OFFICES = ["Teknologi", "Design", "Trondheim", "Management Consulting", "Oppdrag"]
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Sync CVs from Flowcase')
    parser.add_argument('--auto', action='store_true', help='Run without interactive prompts')
    parser.add_argument('--mode', choices=['incremental', 'full', 'test'], default='incremental',
                       help='Sync mode: incremental (default), full, or test')
    parser.add_argument('--offices', type=str, help='Comma-separated list of offices (e.g., "Teknologi,Design")')
    parser.add_argument('--all-offices', action='store_true', help='Include all offices (overrides --offices)')
    parser.add_argument('--no-reindex', action='store_true', help='Skip re-indexing after sync')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Flowcase CV Sync")
    print("=" * 60)
    print()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT
    )
    
    limit = None
    updated_since = None
    offices = None
    
    # Determine which offices to sync
    if args.all_offices:
        offices = None  # None means all offices
        print("Syncing all offices")
    elif args.offices:
        offices = [o.strip() for o in args.offices.split(',')]
        print(f"Syncing offices: {', '.join(offices)}")
    else:
        offices = DEFAULT_OFFICES
        print(f"Syncing default offices: {', '.join(offices)}")
    
    # Determine mode
    if args.auto:
        # Automatic mode - use command line args
        if args.mode == 'incremental':
            # Incremental mode now checks per-CV timestamps instead of fixed date
            # Set updated_since to None to enable per-CV timestamp checking
            updated_since = None
        elif args.mode == 'test':
            limit = 5
    else:
        # Interactive mode
        print()
        print("Select sync mode:")
        print("1. Default offices (Teknologi, Design, Trondheim, Management Consulting, Oppdrag)")
        print("2. All offices")
        print("3. Incremental sync (checks each CV individually for updates)")
        print("4. Test (download 5 CVs)")
        print()
        
        choice = input("Choice (1/2/3/4): ").strip()
        
        if choice == '1':
            offices = DEFAULT_OFFICES
            print(f"Syncing CVs from: {', '.join(offices)}")
        elif choice == '2':
            offices = None
            print("Full sync: downloading all CVs from all offices")
        elif choice == '3':
            # Incremental mode - checks per-CV timestamps
            updated_since = None
            print("Incremental sync: checking each CV individually for updates")
        elif choice == '4':
            limit = 5
            print("Test mode: downloading 5 CVs")
        else:
            print("Invalid choice, defaulting to default offices")
            offices = DEFAULT_OFFICES
    
    print()
    
    # Initialize Flowcase API
    try:
        api = FlowcaseAPI()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print()
        print("Please set FLOWCASE_API_KEY in .env file")
        return 1
    
    # Test connection
    print("Testing API connection...")
    if not api.test_connection():
        print("❌ Connection failed. Check API key and URL.")
        return 1
    
    print("✅ Connected to Flowcase API")
    print()
    
    # Download CVs
    print()
    print("Downloading CVs...")
    print("-" * 60)
    
    stats = api.download_all_cvs(
        output_dir=config.CVS_DIR,
        limit=limit,
        updated_since=updated_since,
        offices=offices
    )
    
    print()
    print("-" * 60)
    print("Download complete!")
    print(f"  ✅ Success: {stats['success']}")
    print(f"  ⏭️  Skipped: {stats['skipped']}")
    print(f"  ❌ Failed: {stats['failed']}")
    if stats.get('removed', 0) > 0:
        print(f"  🗑️  Removed: {stats['removed']} (external/deactivated)")
    print()
    
    if stats['success'] == 0 and stats['failed'] == 0:
        print("No new CVs to index.")
        return 0
    
    # Ask to re-index
    if args.auto:
        should_reindex = not args.no_reindex
    else:
        response = input("Re-index CVs now? (y/n): ").strip().lower()
        should_reindex = (response in ['y', 'yes'])
    
    if not should_reindex:
        print("Skipping re-indexing.")
        print()
        print("To index later, run:")
        print("  python scripts/reindex.py")
        return 0
    
    print()
    print("Re-indexing CVs...")
    print("-" * 60)
    
    # Re-index with reset
    indexer = CVIndexer(reset=True)
    index_stats = indexer.index_all_cvs()
    
    print()
    print("-" * 60)
    print("✅ Re-indexing complete!")
    print()
    print("Results:")
    print(f"  - Files processed: {index_stats['success']}/{index_stats['total_files']}")
    print(f"  - Total chunks: {index_stats['total_chunks']}")
    if index_stats['failed'] > 0:
        print(f"  - Failed: {index_stats['failed']}")
    
    # Show final stats
    final_stats = indexer.get_stats()
    print()
    print("Index statistics:")
    print(f"  - Total chunks: {final_stats['total_chunks']}")
    print(f"  - Unique CVs: {final_stats['unique_cvs']}")
    print(f"  - Embedding model: {final_stats['embedding_model']}")
    print()
    
    print("✅ Sync complete!")
    print()
    print("Test search:")
    print("  python scripts/test_search.py 'Azure erfaring'")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

