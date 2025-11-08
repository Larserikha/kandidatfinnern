# CV-RAG System - Prosjektplan og Kontekst

## 📋 Bakgrunn og Mål

### Hva vi bygger
Et **lokalt RAG-system** (Retrieval-Augmented Generation) som gir Cursor og Claude Desktop tilgang til å søke i Bekks CV-database via semantisk søk.

### Hvorfor
- **Anbudsarbeid:** Raskt finne relevante kandidater basert på kompetanse, erfaring, teknologier
- **Lokalt først:** CVer skal IKKE lastes opp til sky (GDPR/personvern)
- **Integrert workflow:** Søk direkte fra Cursor/Claude uten å måtte gå til Flowcase

### Brukseksempler
```
Bruker i Cursor: "Finn kandidater med TOGAF og offentlig sektor erfaring"
→ RAG søker i lokal database
→ Returnerer 3-5 mest relevante CV-utdrag
→ Claude kan nå skrive anbudsforslag basert på faktiske CVer
```

---

## 🏗️ Arkitektur - Semi-Manuell Løsning (Valgt tilnærming)

Vi valgte **semi-manuell** fremfor full automatisering for å redusere kompleksitet og risiko.

```
┌─────────────────────────────────────────────────────────────┐
│                    FLOWCASE                                 │
│                (CV-verkøy hos Bekk)                         │
│                                                             │
│  • 150+ CVer                                                │
│  • Har REST API                                             │
│  • Dokumentasjon: https://docs.flowcase.com/                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ ① MANUELL EKSPORT (1 gang/uke)
                       │    Bruker eksporterer CVer fra Flowcase
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              LOKAL DISK (din Mac)                           │
│                                                             │
│  ~/Kodeprosjekter/cv-rag-system/data/cvs/                  │
│  ├── ola-nordmann.md                                        │
│  ├── kari-hansen.md                                         │
│  └── ... (150+ filer)                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ ② INDEKSERING (Python script)
                       │    Når nye CVer legges til
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              CHROMADB (Vector Database)                     │
│                   LOKAL - INGEN SKY                         │
│                                                             │
│  • Embeddings av alle CV-chunks                            │
│  • Chunk-størrelse: 500 ord med 100 ord overlap            │
│  • Lokal embedding-modell (ingen API-kall)                 │
│  • Persistent storage i data/chromadb/                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ ③ MCP SERVER (localhost)
                       │    Eksponerer søkefunksjoner
                       │
          ┌────────────┴────────────┐
          │                         │
          ↓                         ↓
┌──────────────────┐      ┌──────────────────┐
│     CURSOR       │      │  CLAUDE DESKTOP  │
│                  │      │                  │
│ "Finn kandidater │      │ "Hvilke CVer har │
│  med Azure"      │      │  TOGAF erfaring?"│
└──────────────────┘      └──────────────────┘
          │                         │
          │ ④ SEMANTISK SØK         │
          │    via MCP protocol     │
          └────────────┬────────────┘
                       │
                       ↓
        Relevante CV-utdrag returneres
        (3-5 chunks med metadata)
```

---

## 🚨 Risikomomenter vi identifiserte

### 1. **GDPR og Personvern** ⚠️ KRITISK
**Spørsmål som MÅ avklares med Bekk:**
- Har du lov til å lagre CVer lokalt på privat Mac?
- Må CVer krypteres på disk?
- Hva skjer hvis Mac-en blir stjålet?
- Hvem er behandlingsansvarlig?

**Mitigering i arkitekturen:**
- ✅ Alt lokalt (ingen sky-upload)
- ✅ Lokal embedding-modell (ingen data til OpenAI)
- ✅ Kun søkeresultater sendes til Claude (ikke hele CV-basen)
- ⚠️ Disk-kryptering må vurderes

### 2. **Flowcase API - Ukjente begrensninger**
**Vet vi ikke ennå:**
- Hvilket format eksporterer API-et CVer i? (JSON, Markdown, PDF, HTML?)
- Finnes `updated_since` filter for inkrementell sync?
- Hva er rate limits?
- Trenger du admin-tilgang?

**Neste steg:** Teste API-et med noen få CVer først

### 3. **RAG Kvalitet - Vil søket være godt nok?**
**Utfordringer:**
- Synonymer: "EA" vs "Enterprise Architecture" vs "Virksomhetsarkitektur"
- Fuzzy matching: "5 års Azure erfaring" skrevet på mange måter
- Chunk-problem: Relevant info spredt over flere chunks
- Norsk/engelsk blanding i CVer

**Mitigering:**
- Multilingual embedding-modell
- Overlappende chunks (100 ord overlap)
- Metadata-tagging (teknologier, bransjer)
- Hybrid search (semantic + keyword) - fase 2

### 4. **Vedlikehold**
**Ongoing overhead:**
- Ukentlig manuell eksport fra Flowcase (5-10 min)
- Re-indeksering når CVer oppdateres (30-60 sek)
- Python dependencies må oppdateres
- ChromaDB/MCP kan ha breaking changes

**Estimert tid:**
- Oppsett: 10-15 timer
- Vedlikehold: ~1 time/måned

### 5. **Performance**
**Forventet:**
- Søk: 100-300ms ✅ Bra
- Full indeksering første gang: 2-5 minutter (150 CVer)
- Re-indeksering ved oppdatering: 30-60 sekunder

---

## 🎯 Teknisk Stack (Valgt)

### **Embedding-modell**
**Valg 1 (start her):** `all-MiniLM-L6-v2`
- Størrelse: 90 MB
- Hastighet: Veldig rask (~1000 docs/sek)
- Språk: Engelsk primært, OK på norsk
- Dimensjoner: 384

**Valg 2 (hvis kvalitet ikke holder):** `paraphrase-multilingual-MiniLM-L12-v2`
- Størrelse: 420 MB
- Hastighet: Medium (~500 docs/sek)
- Språk: 50+ språk inkl. norsk
- Dimensjoner: 384
- Bedre for norsk/engelsk blanding

**Valg 3 (best kvalitet):** `intfloat/multilingual-e5-base`
- Størrelse: 1.1 GB
- Hastighet: Tregere (~200 docs/sek)
- Språk: 100+ språk
- Dimensjoner: 768
- State-of-the-art multilingual

### **Vector Database**
**ChromaDB** (valgt)
- Enkel å sette opp
- Persistent lokal storage
- God dokumentasjon
- Python-native

### **MCP Server**
**Custom Python MCP server**
- Eksponerer funksjoner til Cursor/Claude
- Kjører lokalt (localhost)
- Funksjoner:
  - `search_cvs(query, n_results=5)`
  - `get_cv(name)`
  - `reindex_all()`
  - `get_stats()`

### **Dependencies**
```txt
chromadb==0.4.22
sentence-transformers==2.3.1
torch>=2.0.0
mcp>=0.1.0  # MCP SDK
```

---

## 📁 Prosjektstruktur

```
cv-rag-system/
├── README.md                 # Brukerdokumentasjon
├── PROSJEKTPLAN.md          # Denne filen
├── requirements.txt          # Python dependencies
├── .env.example             # Eksempel miljøvariabler
├── .gitignore               # Ignore data/ og sensitive files
│
├── config.py                # Konfigurasjon (paths, modell-navn)
├── cv_embeddings.py         # Embedding-wrapper for ChromaDB
├── cv_indexer.py            # ChromaDB indexer klasse
├── mcp_server.py            # MCP server
│
├── scripts/
│   ├── setup.sh             # Initial setup (venv, pip install)
│   ├── index_cvs.py         # Indekser alle CVer i data/cvs/
│   ├── test_search.py       # Test søk fra kommandolinje
│   └── reindex.py           # Re-indekser alt (etter oppdateringer)
│
└── data/                    # GIT-IGNORED
    ├── cvs/                 # CVer legges her (Markdown/tekst)
    │   ├── ola-nordmann.md
    │   └── ...
    └── chromadb/            # ChromaDB storage (automatisk opprettet)
        └── ...
```

---

## 🔧 Teknisk Implementeringsdetaljer

### **Chunking-strategi**
```python
Chunk size: 500 ord
Overlap: 100 ord

Eksempel:
Chunk 1: ord 0-500
Chunk 2: ord 400-900  (100 ord overlap med chunk 1)
Chunk 3: ord 800-1300 (100 ord overlap med chunk 2)
```

**Hvorfor overlap?**
- Unngår at relevant informasjon splittes mellom chunks
- Bedre kontekst for embeddings
- Øker sjansen for å finne riktig informasjon

### **Metadata per chunk**
```json
{
  "source": "ola-nordmann.md",
  "chunk_id": 0,
  "total_chunks": 15,
  "cv_name": "Ola Nordmann",
  "technologies": ["Azure", "TOGAF", "Python"],
  "seniority": "Senior",
  "years_experience": 10
}
```

### **Søkeflow**
```python
1. Bruker: "Finn kandidater med Azure og TOGAF erfaring"
2. MCP server mottar query
3. Generate embedding av query (100ms)
4. ChromaDB søker i vector space (50ms)
5. Returnerer top 5 chunks med metadata
6. MCP sender tilbake til Claude/Cursor
7. Claude bruker chunks til å svare
```

---

## 🚀 Implementeringsplan (Steg-for-steg)

### **Fase 1: Grunnmur (Dag 1-2)**
- [x] Opprett prosjektstruktur
- [ ] Lag `requirements.txt`
- [ ] Lag `setup.sh` for automatisk oppsett
- [ ] Lag `.gitignore` (ignorer data/ og .env)
- [ ] Skriv `config.py` med alle konfigurerbare verdier

### **Fase 2: Embedding og Indexing (Dag 2-3)**
- [ ] Implementer `cv_embeddings.py` (wrapper for sentence-transformers)
- [ ] Implementer `cv_indexer.py` (ChromaDB integrasjon)
- [ ] Test med 2-3 manuelle CV-filer (Markdown)
- [ ] Verifiser at chunks og embeddings fungerer
- [ ] Lag `scripts/index_cvs.py` for batch-indeksering

### **Fase 3: Søk og Testing (Dag 3-4)**
- [ ] Implementer søkefunksjon i `cv_indexer.py`
- [ ] Lag `scripts/test_search.py` for kommandolinje-testing
- [ ] Test med ulike søk:
  - "Senior konsulent Azure"
  - "TOGAF og enterprise architecture"
  - "Offentlig sektor erfaring"
- [ ] Juster chunk-størrelse/overlap ved behov
- [ ] Evaluer om embedding-modell må oppgraderes

### **Fase 4: MCP Server (Dag 4-5)**
- [ ] Implementer `mcp_server.py`
- [ ] Eksponér funksjoner:
  - `search_cvs(query, n_results)`
  - `get_stats()`
  - `reindex_all()`
- [ ] Test MCP server lokalt

### **Fase 5: Integrasjon med Cursor/Claude (Dag 5-6)**
- [ ] Oppdater `~/.cursor/mcp.json`
- [ ] Oppdater `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Test i Cursor: "Finn kandidater med Azure"
- [ ] Test i Claude Desktop: samme query
- [ ] Verifiser at resultater er relevante

### **Fase 6: Flowcase Integrasjon (Dag 6-7)**
- [ ] Få API-nøkkel fra Flowcase
- [ ] Test API-endepunkter:
  - `GET /cvs`
  - `GET /cvs/{id}/export`
- [ ] Eksporter 5-10 CVer manuelt for testing
- [ ] Evaluer om vi vil bygge auto-sync senere

### **Fase 7: Dokumentasjon og Vedlikehold (Dag 7)**
- [ ] Skriv komplett README.md
- [ ] Dokumenter ukentlig workflow
- [ ] Lag troubleshooting-guide
- [ ] Test re-indeksering når CVer oppdateres

---

## 📝 Viktige Notater

### **Alternativer vi diskuterte men IKKE valgte**

#### **1. Full Automatisering med Flowcase API**
**Hvorfor ikke:**
- For komplekst (mange failure points)
- PC-en er ikke alltid på
- Mer vedlikehold
- Flowcase API er fortsatt ukjent

**Kan bygges senere:** Ja, hvis semi-manuell blir tungvint

#### **2. Claude Projects Files**
**Hvorfor ikke:**
- Kun i Claude Desktop (ikke Cursor)
- Begrenset til ~50 filer
- Må re-uploade ved endringer
- Mindre fleksibelt

**Men:** God backup-løsning hvis RAG feiler

#### **3. OpenAI Embeddings**
**Hvorfor ikke:**
- Koster penger (minimalt, men likevel)
- Rate limits
- Sender CV-data til OpenAI (GDPR-bekymring)
- Krever internett

**Kan oppgraderes til:** Ja, hvis lokal embedding ikke er god nok

### **Spørsmål til Bekk (MÅ avklares)**
1. ✅ Har Bekk Flowcase? **JA**
2. ⚠️ Kan jeg lagre CVer lokalt på privat Mac? **AVKLAR**
3. ⚠️ Må CVer krypteres? **AVKLAR**
4. ⚠️ Kan jeg bruke OpenAI embeddings? **AVKLAR**
5. ❓ Hvem kan gi meg Flowcase API-nøkkel? **AVKLAR**
6. ❓ Hvilken tilgang trenger jeg? (read-only til CVer) **AVKLAR**

---

## 🎯 Suksesskriterier

**Minimum Viable Product (MVP):**
- ✅ Kan søke i 150+ CVer lokalt
- ✅ Søkeresultater er relevante (80%+ presisjon)
- ✅ Søk tar < 1 sekund
- ✅ Integrert i både Cursor og Claude Desktop
- ✅ Fungerer offline (ingen internett-avhengighet)

**Nice to Have:**
- Automatisk sync med Flowcase (kan legges til senere)
- Metadata-filtrering (senioritet, teknologier)
- Hybrid search (semantic + keyword)
- Web UI for søk/administrasjon

---

## 🔍 Testing og Validering

### **Testcases for søkekvalitet**
```python
test_queries = [
    # Teknologi-spesifikke
    ("Azure erfaring", ["candidates_with_azure"]),
    ("TOGAF og enterprise architecture", ["EA_certified_candidates"]),
    
    # Bransje
    ("Offentlig sektor", ["public_sector_experience"]),
    ("Helsevesen", ["healthcare_projects"]),
    
    # Rolle
    ("Senior konsulent", ["senior_consultants"]),
    ("Informasjonsarkitekt", ["info_architects"]),
    
    # Kombinasjoner
    ("Senior med TOGAF og offentlig sektor", ["specific_candidates"]),
    
    # Norsk/Engelsk blanding
    ("Data governance og DAMA-DMBOK", ["data_governance_experts"]),
]

# Kjør alle queries og evaluer resultater
for query, expected_topics in test_queries:
    results = indexer.search(query, n_results=5)
    # Manuell validering: Er resultatene relevante?
```

---

## 📚 Ressurser og Lenker

### **Dokumentasjon**
- Flowcase API: https://docs.flowcase.com/
- ChromaDB: https://docs.trychroma.com/
- Sentence Transformers: https://www.sbert.net/
- MCP Protocol: https://modelcontextprotocol.io/

### **Embedding Modeller**
- all-MiniLM-L6-v2: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- paraphrase-multilingual: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- multilingual-e5-base: https://huggingface.co/intfloat/multilingual-e5-base

---

## 🎬 Neste Steg (Umiddelbart)

1. **Åpne nytt prosjekt i Cursor:**
   ```bash
   cd /Users/larsandreassen/Kodeprosjekter/cv-rag-system
   ```

2. **Start ny agent-chat med instruksjoner:**
   ```
   "Les PROSJEKTPLAN.md. Vi skal bygge et CV-RAG system.
   Start med Fase 1: Opprett requirements.txt og setup.sh."
   ```

3. **Før koding - avklar med Bekk:**
   - GDPR-clearance for lokal lagring av CVer
   - Flowcase API-tilgang

4. **Test med dummy-data først:**
   - Lag 2-3 fake CVer (Markdown)
   - Bygg og test hele stacken
   - Så først importer ekte CVer

---

## 💡 Tips til ny agent

- Dette er et **semi-manuelt system** - ikke bygg full automatisering ennå
- Start enkelt, test ofte
- Prioriter **lokal** embedding over OpenAI (GDPR)
- Chunk-størrelse (500 ord) og overlap (100 ord) kan justeres ved behov
- Hvis RAG-kvalitet er dårlig, oppgrader embedding-modell før du endrer arkitektur
- Vedlikehold er viktig - dokumenter alt godt

---

**Opprettet:** 5. november 2025
**Status:** Prosjekt initialisert, klar for implementering
**Estimert tid til MVP:** 30-40 timer over 1-2 uker

