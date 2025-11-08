# Tekniske Valg - Quick Reference

## 🎯 Arkitektur-beslutninger

### Semi-manuell vs. Full Automatisering
**Valg:** ✅ Semi-manuell
**Hvorfor:**
- Enklere (50% mindre kode)
- Færre failure points
- PC er ikke alltid på
- God nok for ukentlig anbudsarbeid

### Lokal vs. Cloud Embeddings
**Valg:** ✅ Lokal (sentence-transformers)
**Hvorfor:**
- GDPR-compliant (ingen data til OpenAI)
- Gratis
- Fungerer offline
- God nok kvalitet for CV-søk

**Kan oppgradere til OpenAI senere hvis nødvendig**

### Embedding-modell
**Start:** `all-MiniLM-L6-v2` (90 MB, rask)
**Upgrade til:** `paraphrase-multilingual-MiniLM-L12-v2` (bedre norsk)
**Best kvalitet:** `intfloat/multilingual-e5-base` (1.1 GB)

### Vector Database
**Valg:** ✅ ChromaDB
**Hvorfor:**
- Enkel setup
- Python-native
- Persistent lokal storage
- God dokumentasjon

**Alternativer vurdert:**
- ❌ Pinecone (cloud-only)
- ❌ Weaviate (overkill)
- ❌ FAISS (bare in-memory)

### Chunking-strategi
```
Chunk size: 500 ord
Overlap: 100 ord
Min chunk size: 50 ord
```

**Hvorfor overlap?**
- Unngår at relevant info splittes
- Bedre kontekst for embeddings

## 🔧 Implementeringsdetaljer

### File Structure
```python
cv_embeddings.py
├── LocalEmbeddingFunction(ChromaDB wrapper)
├── model: SentenceTransformer
└── __call__(): list[str] → list[list[float]]

cv_indexer.py
├── CVIndexer
├── index_cv(file)
├── index_all_cvs()
├── search(query, n_results)
└── _split_into_chunks(text, chunk_size, overlap)

mcp_server.py
├── search_cvs(query, n_results)
├── get_stats()
└── reindex_all()
```

### ChromaDB Setup
```python
client = chromadb.PersistentClient(path="data/chromadb")
collection = client.get_or_create_collection(
    name="cvs",
    embedding_function=LocalEmbeddingFunction(),
    metadata={"description": "CV database"}
)
```

### Metadata per Chunk
```json
{
  "source": "ola-nordmann.md",
  "chunk_id": 0,
  "total_chunks": 15
}
```

**Kan utvides med:**
```json
{
  "cv_name": "Ola Nordmann",
  "technologies": ["Azure", "TOGAF"],
  "seniority": "Senior",
  "years_experience": 10
}
```

## 📊 Performance-mål

### Søk
- Query → Result: < 300ms ✅
- Embedding generation: ~100ms
- ChromaDB search: ~50ms
- Metadata enrichment: ~50ms

### Indeksering
- First-time (150 CVer): 2-5 min
- Re-index (10 CVer): 30-60 sek
- Per CV: ~2 sekunder

### Storage
- ChromaDB: ~50-100 MB for 150 CVer
- Embedding model: 90 MB - 1.1 GB
- Total: < 500 MB

## 🔐 Sikkerhet og GDPR

### Data som Lagres Lokalt
✅ CVer (Markdown/tekst)
✅ Embeddings (vektorer)
✅ Metadata (navn, teknologier)
✅ ChromaDB index

### Data som IKKE Sendes ut
✅ Ingen CVer til OpenAI
✅ Ingen embeddings generert i sky
✅ Kun søkeresultater (chunks) til Claude/Cursor

### Tiltak
- Disk-kryptering (macOS FileVault)
- .gitignore for data/
- Ingen API-keys i kode

## 🧪 Testing

### Unit Tests
```python
# test_embeddings.py
def test_embedding_generation():
    emb = LocalEmbeddingFunction()
    result = emb(["test text"])
    assert len(result) == 1
    assert len(result[0]) == 384  # MiniLM dimensjoner

# test_indexer.py
def test_search():
    indexer = CVIndexer()
    results = indexer.search("Azure")
    assert len(results['documents'][0]) > 0
```

### Integration Tests
```python
# test_search.py (scripts/)
queries = [
    "Senior konsulent med Azure",
    "TOGAF og enterprise architecture",
    "Offentlig sektor erfaring"
]

for query in queries:
    results = indexer.search(query, n_results=5)
    print_results(results)
```

### Manual Testing
```bash
# Test indeksering
python scripts/index_cvs.py

# Test søk
python scripts/test_search.py "Azure erfaring"

# Test MCP
python mcp_server.py
# Fra annen terminal: test MCP-kall
```

## 🚨 Fallback-strategier

### Hvis RAG-kvalitet er dårlig
1. Oppgrader embedding-modell
2. Juster chunk-størrelse (300-700 ord)
3. Legg til metadata-filtrering
4. Implementer hybrid search (semantic + keyword)

### Hvis performance er treg
1. Bruk mindre embedding-modell
2. Reduser chunk overlap (50 ord)
3. Begrens n_results (3 i stedet for 5)
4. Cache ofte-brukte queries

### Hvis vedlikehold blir tungvint
1. Automatiser Flowcase-sync (Fase 8)
2. Bygg web UI for administrasjon
3. Legg til automatisk re-indeksering

## 🔄 Workflow

### Ukentlig Vedlikehold
```bash
# 1. Eksporter CVer fra Flowcase (manuelt)
# 2. Kopier til data/cvs/
cp ~/Downloads/flowcase-export/*.md data/cvs/

# 3. Re-indekser
python scripts/reindex.py

# 4. Ferdig! (tar ~1 minutt)
```

### Daglig Bruk
```
1. Åpne Cursor/Claude Desktop
2. Spør: "Finn kandidater med X erfaring"
3. RAG returnerer relevante CVer
4. Claude/Cursor hjelper med anbudsskriving
```

## 📚 Dependencies Forklart

```txt
chromadb==0.4.22
# Vector database for embeddings
# Persistent lokal storage

sentence-transformers==2.3.1
# Genererer embeddings
# Mange pre-trente modeller

torch>=2.0.0
# PyTorch for ML-modeller
# Kreves av sentence-transformers

mcp>=0.1.0
# Model Context Protocol SDK
# Integrasjon med Cursor/Claude

python-dotenv==1.0.0
# Miljøvariabler (.env file)
# For konfigurasjon
```

## 🎓 Læringsressurser

### RAG Basics
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)

### MCP Protocol
- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP GitHub](https://github.com/anthropics/model-context-protocol)

### Embeddings
- [Hugging Face Models](https://huggingface.co/models?pipeline_tag=sentence-similarity)
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) (embedding kvalitet)

---

**Sist oppdatert:** 5. november 2025
**Vedlikeholdes av:** Lars Andreassen

