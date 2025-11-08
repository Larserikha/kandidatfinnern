#!/usr/bin/env python3
"""
Re-index CVs with AI-generated summaries

This script adds summary chunks to the RAG index to improve search quality.
Each CV gets a special "summary" chunk that provides high-level overview.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from cv_indexer import CVIndexer


def reindex_with_summaries():
    """
    Re-index all CVs and include their summaries as special chunks
    """
    cv_dir = config.CV_DIR
    summaries_dir = config.BASE_DIR / "data" / "cv_summaries"
    
    if not summaries_dir.exists():
        print("❌ Ingen sammendrag funnet!")
        print()
        print("Kjør først:")
        print("  python scripts/generate_cv_summaries.py")
        sys.exit(1)
    
    print("🔧 Initialiserer CV indexer...")
    indexer = CVIndexer()
    
    # Clear existing index
    print("🗑️  Sletter gammel index...")
    indexer.collection.delete()
    
    print()
    print("📚 Re-indekserer CVer med sammendrag...")
    print()
    
    cv_files = list(cv_dir.glob("*.json"))
    total_chunks = 0
    cvs_with_summaries = 0
    
    for i, cv_file in enumerate(cv_files, 1):
        cv_name = cv_file.stem
        summary_file = summaries_dir / f"{cv_name}_summary.txt"
        
        # Index the full CV
        print(f"[{i}/{len(cv_files)}] 📄 Indekserer {cv_file.name}...")
        chunks = indexer.index_cv(cv_file)
        total_chunks += chunks
        
        # Add summary as a special high-priority chunk if available
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = f.read().strip()
            
            if summary:
                # Read CV metadata
                import json
                with open(cv_file, 'r', encoding='utf-8') as f:
                    cv_data = json.load(f)
                
                user_meta = cv_data.get('_user_metadata', {})
                
                # Create metadata for summary chunk
                summary_metadata = {
                    "source": cv_file.name,
                    "file_path": str(cv_file),
                    "cv_name": cv_data.get('name', cv_name.replace("-", " ").title()),
                    "office": user_meta.get('office_name', ''),
                    "chunk_id": 0,  # Summary is always chunk 0
                    "total_chunks": chunks + 1,
                    "is_summary": True  # Special flag
                }
                
                # Prepend "SAMMENDRAG:" to make it clear
                summary_text = f"SAMMENDRAG: {summary}"
                
                # Generate embedding and add to collection
                embedding = indexer.embeddings.embed([summary_text])[0]
                
                indexer.collection.add(
                    ids=[f"{cv_file.stem}_summary"],
                    embeddings=[embedding],
                    documents=[summary_text],
                    metadatas=[summary_metadata]
                )
                
                print(f"             ✅ + sammendrag ({len(summary)} tegn)")
                total_chunks += 1
                cvs_with_summaries += 1
    
    print()
    print("=" * 80)
    print(f"✨ Ferdig re-indeksert!")
    print(f"   CVer: {len(cv_files)}")
    print(f"   CVer med sammendrag: {cvs_with_summaries}")
    print(f"   Totale chunks: {total_chunks}")
    print()
    print("🎉 Claude Desktop og Cursor har nå bedre oversikt!")
    print()
    print("💡 Restart Cursor/Claude Desktop for å aktivere endringene.")


if __name__ == "__main__":
    reindex_with_summaries()




