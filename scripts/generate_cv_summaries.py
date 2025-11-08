#!/usr/bin/env python3
"""
Generate AI summaries of CVs for better RAG performance

This script uses Claude API to generate concise summaries of each CV,
which are then added to the RAG index to give the LLM better overview.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List
import anthropic

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from cv_indexer import CVIndexer


SUMMARY_PROMPT = """Du er en CV-oppsummerer for Bekk Consulting. Din oppgave er å lage et kort, søkbart sammendrag av en CV.

Inkluder i sammendraget:
1. Navn og avdeling
2. Senioritetsnivå (junior/konsulent/senior/principal)
3. Hovedkompetanser (topp 5-7 teknologier/plattformer)
4. Roller/spesialiseringer (f.eks. "systemutvikler", "arkitekt", "DevOps")
5. Bransjeerfaring (f.eks. "offentlig sektor", "finans", "helse")
6. Nøkkelprosjekter (1-3 viktigste)

Skriv sammendraget i 3. person, som en pitch til et anbud.
Maks 200 ord.
Bruk norsk.

---

CV:
{cv_content}

---

SAMMENDRAG:"""


def generate_summary(cv_content: str, api_key: str) -> str:
    """
    Generate a concise summary of a CV using Claude API
    
    Args:
        cv_content: Full text content of the CV
        api_key: Anthropic API key
        
    Returns:
        Generated summary text
    """
    client = anthropic.Anthropic(api_key=api_key)
    
    # Truncate if CV is extremely long to save costs
    MAX_CV_LENGTH = 20000  # chars
    if len(cv_content) > MAX_CV_LENGTH:
        cv_content = cv_content[:MAX_CV_LENGTH] + "\n\n[...truncated for length...]"
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",  # Fast and accurate
        max_tokens=400,  # ~200 words
        temperature=0.3,  # Focused and consistent
        messages=[{
            "role": "user",
            "content": SUMMARY_PROMPT.format(cv_content=cv_content)
        }]
    )
    
    return message.content[0].text.strip()


def generate_all_summaries(indexer: CVIndexer, api_key: str, overwrite: bool = False):
    """
    Generate summaries for all CVs in the data/cvs directory
    
    Args:
        indexer: CVIndexer instance
        api_key: Anthropic API key
        overwrite: Whether to regenerate existing summaries
    """
    cv_dir = config.CV_DIR
    summaries_dir = config.BASE_DIR / "data" / "cv_summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    
    cv_files = list(cv_dir.glob("*.json"))
    
    print(f"📄 Fant {len(cv_files)} CV-er")
    print(f"📁 Sammendrag lagres i: {summaries_dir}")
    print()
    
    processed = 0
    skipped = 0
    errors = 0
    
    for i, cv_file in enumerate(cv_files, 1):
        cv_name = cv_file.stem
        summary_file = summaries_dir / f"{cv_name}_summary.txt"
        
        # Skip if summary exists and overwrite is False
        if summary_file.exists() and not overwrite:
            print(f"[{i}/{len(cv_files)}] ⏭️  Hopper over {cv_name} (eksisterer)")
            skipped += 1
            continue
        
        try:
            # Read CV
            with open(cv_file, 'r', encoding='utf-8') as f:
                cv_data = json.load(f)
            
            # Extract text using the indexer's method
            cv_text = indexer._extract_text_from_json(cv_data)
            
            print(f"[{i}/{len(cv_files)}] 🤖 Genererer sammendrag for {cv_name}...")
            
            # Generate summary
            summary = generate_summary(cv_text, api_key)
            
            # Save summary
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            print(f"             ✅ Lagret ({len(summary)} tegn)")
            processed += 1
            
        except Exception as e:
            print(f"             ❌ Feil: {e}")
            errors += 1
            continue
    
    print()
    print("=" * 80)
    print(f"✨ Ferdig!")
    print(f"   Prosessert: {processed}")
    print(f"   Hoppet over: {skipped}")
    print(f"   Feil: {errors}")
    print()
    print("💡 Neste steg: Kjør re-indexing for å legge til sammendragene i RAG:")
    print("   python scripts/reindex_with_summaries.py")


def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate AI summaries of CVs')
    parser.add_argument('--overwrite', action='store_true', 
                       help='Regenerate existing summaries')
    parser.add_argument('--api-key', type=str,
                       help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ Ingen API-nøkkel funnet!")
        print()
        print("Sett miljøvariabel:")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'")
        print()
        print("Eller bruk --api-key:")
        print("  python scripts/generate_cv_summaries.py --api-key 'sk-ant-...'")
        print()
        print("💡 Få API-nøkkel fra: https://console.anthropic.com/")
        sys.exit(1)
    
    # Initialize indexer
    print("🔧 Initialiserer CV indexer...")
    indexer = CVIndexer()
    print()
    
    # Generate summaries
    generate_all_summaries(indexer, api_key, overwrite=args.overwrite)


if __name__ == "__main__":
    main()




