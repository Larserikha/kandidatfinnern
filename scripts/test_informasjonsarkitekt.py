"""
Test script for Informasjonsarkitekt søk - med og uten re-ranking
Basert på minimumskrav og evalueringskrav fra anbud
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cv_indexer import CVIndexer
import logging
import config

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors
    format='%(levelname)s - %(message)s'
)

def format_result(idx, doc, metadata, distance=None, rerank_score=None):
    """Format a single search result for display"""
    name = metadata.get('cv_name', 'Unknown')
    office = metadata.get('office', 'Unknown')
    years_exp = metadata.get('years_of_experience', 'N/A')
    
    result = f"\n{idx}. {name} | {office}"
    if years_exp != 'N/A':
        result += f" | {years_exp} års erfaring"
    
    if distance is not None:
        result += f" | Distance: {distance:.4f}"
    if rerank_score is not None:
        result += f" | Re-rank: {rerank_score:.4f}"
    
    result += f"\n   {doc[:200]}..."
    
    return result


def test_informasjonsarkitekt():
    """
    Test søk for Informasjonsarkitekt med omfattende krav
    """
    # Omfattende søk som dekker alle minimumskrav og evalueringskrav
    query = (
        "Informasjonsarkitekt med minst 3 års erfaring fra informasjonsarkitektur "
        "i offentlig sektor eller komplekse organisasjoner. Sterk forretningsforståelse "
        "og formidlingskompetanse, erfaring med å jobbe i krysningspunktet mellom IT og forretning. "
        "Ekspert på modellering av informasjonsstrukturer, taksonomier og metadata i komplekse organisasjoner. "
        "Erfaring med brukerorientert tjenesteutvikling, strukturere informasjon med tanke på brukeropplevelse "
        "og tilgjengelighet. Prosjektledelse eller prosessledelse. Dokumentere verdikjeder og få verdikjeder til å virke. "
        "BIM og digital infrastrukturmodell digital tvilling. Begrepsarbeid i større organisasjoner. "
        "Oppdatert innen informasjonsarkitektur. Svært god muntlig og skriftlig fremstillingsevne på norsk."
    )
    
    print("=" * 80)
    print("🔍 Søk: Informasjonsarkitekt")
    print("=" * 80)
    print(f"\nQuery: {query[:150]}...\n")
    
    indexer = CVIndexer()
    
    # Test 1: Uten re-ranking
    print("\n" + "=" * 80)
    print("📊 UTEN Re-ranking (Standard bi-encoder)")
    print("=" * 80)
    start_time = time.time()
    results_no_rerank = indexer.search(query, n_results=10, use_reranking=False)
    time_no_rerank = time.time() - start_time
    
    print(f"⏱️  Tid: {time_no_rerank:.3f}s")
    print(f"📈 Fant {len(results_no_rerank['documents'])} resultater\n")
    
    # Vis top 5
    print("🏆 TOP 5 KANDIDATER (uten re-ranking):")
    print("-" * 80)
    for i, (doc, metadata) in enumerate(zip(
        results_no_rerank['documents'][:5],
        results_no_rerank['metadatas'][:5]
    ), 1):
        distance = results_no_rerank['distances'][i-1] if results_no_rerank.get('distances') else None
        print(format_result(i, doc, metadata, distance=distance))
    
    # Test 2: Med re-ranking
    print("\n\n" + "=" * 80)
    print("🎯 MED Re-ranking (BGE-reranker-base)")
    print("=" * 80)
    
    # Aktiver re-ranking for denne testen
    original_reranking = config.ENABLE_RERANKING
    config.ENABLE_RERANKING = True
    
    start_time = time.time()
    results_rerank = indexer.search(query, n_results=10, use_reranking=True)
    time_rerank = time.time() - start_time
    
    # Restore original setting
    config.ENABLE_RERANKING = original_reranking
    
    print(f"⏱️  Tid: {time_rerank:.3f}s")
    print(f"📈 Fant {len(results_rerank['documents'])} resultater\n")
    
    # Vis top 5
    print("🏆 TOP 5 KANDIDATER (med re-ranking):")
    print("-" * 80)
    for i, (doc, metadata) in enumerate(zip(
        results_rerank['documents'][:5],
        results_rerank['metadatas'][:5]
    ), 1):
        distance = results_rerank['distances'][i-1] if results_rerank.get('distances') else None
        rerank_score = results_rerank.get('rerank_scores', [None])[i-1] if results_rerank.get('rerank_scores') else None
        print(format_result(i, doc, metadata, distance=distance, rerank_score=rerank_score))
    
    # Sammenligning
    print("\n\n" + "=" * 80)
    print("📊 SAMMENLIGNING")
    print("=" * 80)
    print(f"Tidsforskjell: {time_rerank - time_no_rerank:.3f}s ({((time_rerank / time_no_rerank) - 1) * 100:.1f}% tregere med re-ranking)")
    
    # Sjekk om beste kandidat endret seg
    best_no_rerank = results_no_rerank['metadatas'][0].get('cv_name', 'Unknown') if results_no_rerank['metadatas'] else 'N/A'
    best_rerank = results_rerank['metadatas'][0].get('cv_name', 'Unknown') if results_rerank['metadatas'] else 'N/A'
    
    print(f"\n🏆 Beste kandidat UTEN re-ranking: {best_no_rerank}")
    print(f"🏆 Beste kandidat MED re-ranking: {best_rerank}")
    
    if best_no_rerank != best_rerank:
        print(f"\n🔄 Re-ranking endret beste kandidat!")
        print(f"   ⬆️  Ny topp: {best_rerank}")
        print(f"   ⬇️  Tidligere topp: {best_no_rerank}")
    
    # Vis beste kandidat med full info
    print("\n\n" + "=" * 80)
    print("⭐ BESTE KANDIDAT (med re-ranking)")
    print("=" * 80)
    if results_rerank['documents']:
        best_doc = results_rerank['documents'][0]
        best_meta = results_rerank['metadatas'][0]
        best_score = results_rerank.get('rerank_scores', [None])[0] if results_rerank.get('rerank_scores') else None
        
        print(f"\n👤 Navn: {best_meta.get('cv_name', 'Unknown')}")
        print(f"📍 Kontor: {best_meta.get('office', 'Unknown')}")
        if best_meta.get('years_of_experience'):
            print(f"⏱️  Erfaring: {best_meta.get('years_of_experience')} år")
        if best_score:
            print(f"🎯 Re-ranking score: {best_score:.4f}")
        print(f"\n📄 Relevante CV-utdrag:")
        print(f"{best_doc[:500]}...")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_informasjonsarkitekt()

