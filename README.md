# CV-RAG System 🔍

Lokalt RAG-system for semantisk søk i CV-database. Integrerer med Cursor og Claude Desktop via MCP.

## 🚀 Setup og Installasjon

### Systemkrav

- **Python:** 3.8 eller høyere
- **Diskplass:** ~5 GB (for embedding-modeller og CV-data)
- **Minne:** 4 GB RAM minimum (8 GB anbefalt for bedre ytelse)
- **OS:** macOS, Linux eller Windows (med WSL)

### Steg-for-steg installasjon

#### 1. Klon repositoriet

```bash
git clone https://github.com/Larserikha/kandidatfinnern.git
cd kandidatfinnern
```

#### 2. Kjør setup-script

```bash
./scripts/setup.sh
```

Dette scriptet:
- ✅ Oppretter virtual environment
- ✅ Installerer alle Python-avhengigheter
- ✅ Laster ned embedding-modellen (`multilingual-e5-large`, ~2.2 GB) automatisk
- ✅ Laster ned re-ranking-modellen (`BGE-reranker-base`) automatisk
- ✅ Oppretter nødvendige mapper

**Merk:** Første gang kan ta 10-15 minutter pga. nedlasting av modeller.

#### 3. Konfigurer Flowcase API

**Du må selv skaffe Flowcase API-nøkkel:**
1. Logg inn på Flowcase
2. Gå til API-innstillinger
3. Generer en API-nøkkel
4. Kopier nøkkelen

**Opprett `.env` fil:**
```bash
# Kopier eksempel-filen (hvis den finnes) eller opprett manuelt
cat > .env << EOF
FLOWCASE_API_KEY=din_api_nøkkel_her
FLOWCASE_API_URL=https://bekk.flowcase.com/api
EOF
```

**Viktig:** `.env` filen er allerede i `.gitignore` og vil ikke bli committet.

#### 4. (Valgfritt) Sett opp alias for enkel synkronisering

```bash
./setup-alias.sh
source ~/.zshrc  # eller ~/.bashrc på Linux
```

Dette lar deg kjøre `sync-cv` fra hvor som helst i terminalen.

#### 5. Synkroniser CVer fra Flowcase

```bash
# Hvis du satte opp alias:
sync-cv

# Eller manuelt:
./sync.sh --full
```

Dette vil:
- Hente alle aktive konsulenter fra Flowcase
- Lagre CV-er lokalt i `data/cvs/`
- Indeksere dem i ChromaDB for søk

#### 6. Konfigurer MCP i Claude Desktop / ChatGPT Desktop

**Automatisk oppsett (anbefalt):**
```bash
python scripts/setup_mcp.py
```

Dette scriptet:
- ✅ Finner automatisk MCP-konfigurasjonsfiler for Claude Desktop og ChatGPT Desktop
- ✅ Legger til cv-rag server-konfigurasjonen automatisk
- ✅ Oppretter backup hvis det trengs
- ✅ Fungerer på macOS, Linux og Windows

**Manuelt oppsett (hvis automatisk ikke fungerer):**

**For Claude Desktop:**
1. Åpne MCP-konfigurasjonsfilen:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Legg til følgende konfigurasjon (juster stien til ditt prosjekt):

```json
{
  "mcpServers": {
    "cv-rag": {
      "command": "/full/path/til/cv-rag-system/venv/bin/python",
      "args": [
        "/full/path/til/cv-rag-system/mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

**For Cursor:**
1. Åpne Cursor Settings
2. Gå til "Features" → "Model Context Protocol"
3. Legg til samme konfigurasjon som over

**Eksempel-konfigurasjoner:** Se `mcp_config_examples/` mappen for eksempler.

#### 7. Test at alt fungerer

```bash
# Test at MCP-serveren kan starte
source venv/bin/activate
python mcp_server.py
```

Hvis det fungerer, kan du nå bruke systemet i Cursor/Claude Desktop!

## Quick Start (etter første setup)

```bash
# Oppdater CVer (fra hvor som helst hvis du satte opp alias)
sync-cv

# Eller manuelt:
cd /path/til/cv-rag-system
./sync.sh
```

## 🔄 Oppdatere CVer

**Før du starter anbudsarbeid:**
```bash
sync-cv
```
Det er alt! ✨

## Hva er dette?

Et system som lar deg søke i Bekks CV-database direkte fra Cursor eller Claude Desktop:

```
Du i Cursor: "Finn kandidater med TOGAF og offentlig sektor erfaring"
→ RAG søker i 798 CVer lokalt (fra 5 avdelinger)
→ Returnerer relevante kandidater med erfaring og senioritet
→ Claude skriver anbudsforslag basert på faktiske CVer
```

**Inkluderer:**
- 📄 Full CV-tekst (teknologier, prosjekter, utdanning, nøkkelkvalifikasjoner)
- 👤 Metadata (navn, avdeling/kontor)
- ⏱️ **Antall års erfaring** (automatisk berikelse fra HR-data)

**Standard avdelinger:**
- Teknologi (517 personer)
- Design (91 personer)
- Trondheim (84 personer)
- Management Consulting (60 personer)
- Oppdrag (46 personer)

## Hvorfor lokalt?

- ✅ **GDPR-compliant:** Ingen CVer i skyen
- ✅ **Offline:** Fungerer uten internett
- ✅ **Raskt:** Søk < 300ms
- ✅ **Integrert:** Søk direkte i Cursor/Claude workflow

## Arkitektur (Semi-manuell)

```
CVer (Flowcase) 
   → Eksporter manuelt 1x/uke
   → data/cvs/ (lokal disk)
   → ChromaDB indexing (lokal vector database)
   → MCP Server (localhost)
   → Cursor + Claude Desktop
```

**Dokumentasjon:**
- [PROSJEKTPLAN.md](./PROSJEKTPLAN.md) - Full prosjektplan og arkitektur
- [ERFARING.md](./ERFARING.md) - Hvordan erfaringsdata håndteres

## Tech Stack

- **Vector DB:** ChromaDB (lokal, persistent)
- **Embeddings:** multilingual-e5-large (lokal, 1024D, ~2.2 GB, lastes ned automatisk)
- **Re-ranking:** BGE-reranker-base (cross-encoder, lastes ned automatisk)
- **MCP Server:** Python
- **Clients:** Cursor + Claude Desktop

**Modeller lastes ned automatisk:**
- Embedding-modellen lastes ned første gang `setup.sh` kjører
- Re-ranking-modellen lastes ned første gang den brukes
- Modeller lagres lokalt i HuggingFace cache (vanligvis `~/.cache/huggingface/`)

## Status

- [x] Prosjektstruktur opprettet
- [x] Dependencies installert (multilingual-e5-large for Norwegian)
- [x] Embedding + indexing implementert og testet
- [x] MCP server implementert
- [x] Integrert med Cursor & Claude Desktop
- [x] Flowcase API-integrasjon fullført
- [x] 74 Trondheim-CVer indeksert (full innhold fra JSON)
- [x] **Rike CV-data:** 200+ teknologier, detaljerte prosjekter, key qualifications
- [x] **Cross-encoder re-ranking:** BGE-reranker-base aktivert for bedre søkekvalitet
- [x] **Optimalisert output:** Truncated chunks (400 tegn) for bedre LLM-performance
- [x] **AI-sammendrag support:** Klart for Claude API-genererte sammendrag (valgfritt)

## 💬 Bruk i Cursor/Claude

**I Cursor eller Claude Desktop:**

```
Finn kandidater med Azure erfaring
Hvem har jobbet med React og TypeScript?
Senior konsulenter med erfaring fra offentlig sektor
```

MCP-serveren starter automatisk i bakgrunnen! 🎉

### 💡 Tips for beste resultater:

**Workflow Claude følger:**
1. `list_all_candidates()` → Oversikt over alle 74 kandidater
2. `search_cvs("teknologi domene", n_results=15)` → Korte utdrag (400 tegn)
3. `get_cv_by_name("kandidat.json")` → Full CV for de mest relevante

**Husk:** Søkeresultater er korte utdrag for effektivitet. For anbudsforslag ber du Claude om å hente full CV for utvalgte kandidater.

**Mer info:** Se `.cursorrules` for detaljerte instruksjoner Claude følger.

## 📚 Dokumentasjon

- **[OPPDATERING.md](./OPPDATERING.md)** - Hvordan oppdatere CVer
- **[AI_SUMMARIES.md](./AI_SUMMARIES.md)** - AI-genererte sammendrag (valgfritt)
- **[PROSJEKTPLAN.md](./docs/PROSJEKTPLAN.md)** - Full prosjektplan og arkitektur

## Neste Steg

Se [PROSJEKTPLAN.md](./docs/PROSJEKTPLAN.md) → Implementeringsplan (Fase 1-7)

