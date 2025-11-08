# 🤖 AI-Genererte CV-Sammendrag

## Hvorfor?

**Problem:** Claude Desktop får for mye data og cutter chatten for tidlig.

**Løsning:** Generer AI-sammendrag av hver CV (200 ord) som legges i RAG. Dette gir Claude bedre oversikt uten å overbelaste konteksten.

## Fordeler

✅ **Bedre oversikt:** 200 ord vs 2000+ ord per CV  
✅ **Raskere matching:** Sammendrag er optimalisert for søk  
✅ **Komprimert kontekst:** Claude Desktop får ikke cutoff  
✅ **Høyere kvalitet:** AI trekker ut nøkkelinfo strukturert  
✅ **GDPR OK:** Anthropic har DPA, data sendes kryptert

## Slik fungerer det

1. **Generering:** Claude API lager 200-ords sammendrag av hver CV
   - Navn, avdeling, senioritet
   - Topp 5-7 teknologier
   - Roller og spesialiseringer
   - Bransjeerfaring
   - Nøkkelprosjekter

2. **Lagring:** Sammendrag lagres i `data/cv_summaries/`

3. **Indeksering:** Sammendrag legges som "chunk 0" i RAG med spesiell flagging

4. **Søk:** Når Claude søker får den først sammendragene, deretter full CV hvis nødvendig

## 🚀 Bruk

### Steg 1: Installer Anthropic SDK

```bash
cd /Users/larsandreassen/Kodeprosjekter/cv-rag-system
source venv/bin/activate
pip install anthropic
```

### Steg 2: Sett API-nøkkel

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

💡 **Få API-nøkkel:** https://console.anthropic.com/settings/keys

### Steg 3: Generer sammendrag

```bash
python scripts/generate_cv_summaries.py
```

Dette vil:
- Lese alle 74 CV-er
- Generere sammendrag med Claude API (~$2-3 totalt)
- Lagre i `data/cv_summaries/`

**Første gang:** ~5-10 minutter (74 CVer × 5 sekunder)  
**Senere:** Kun nye/endrede CVer prosesseres

### Steg 4: Re-indekser med sammendrag

```bash
python scripts/reindex_with_summaries.py
```

Dette vil:
- Slette gammel index
- Re-indeksere alle CVer
- Legge til sammendrag som chunk 0

### Steg 5: Restart Claude/Cursor

```bash
# Restart Cursor eller Claude Desktop
```

## 📊 Eksempel på sammendrag

**Input (12000 tegn):**
```
# Øystein Grande Jaren
**Avdeling:** Trondheim

## Technologies
HTML, CSS, React, Java, .NET Core, OpenID Connect...
[... 12000 tegn mer ...]
```

**Output (200 ord):**
```
SAMMENDRAG: Øystein Grande Jaren er en senior systemutvikler og 
rådgiver ved Bekk Trondheim med bred ekspertkompetanse innen både 
Java og .NET. Han har spesialisert seg på moderne autentiserings-
løsninger basert på OpenID Connect, SAML og WS-Federation, samt 
frontend-utvikling med React og TypeScript.

Øystein har lang erfaring fra offentlig sektor, inkludert store 
prosjekter for Statens Vegvesen, Domstoladministrasjonen og 
Miljødirektoratet. Han har ledet utviklingen av bl.a. Vegbilder 
(React/Leaflet), API-plattform på Kubernetes (ArgoCD, Istio), og 
Aktørportalen (ASP.NET, OpenID Connect).

Hans nøkkelkompetanser inkluderer: Java, Spring Boot, .NET Core, 
React, TypeScript, OpenID Connect, Kubernetes, Docker, Azure og 
OpenShift. Han er spesielt opptatt av informasjonssikkerhet og 
clean code.
```

## 🔄 Oppdatere sammendrag

Når CVer endres i Flowcase:

```bash
# 1. Synkroniser CVer fra Flowcase
sync-cv

# 2. Generer nye sammendrag (hopper over eksisterende)
python scripts/generate_cv_summaries.py

# 3. Eller regenerer ALT
python scripts/generate_cv_summaries.py --overwrite

# 4. Re-indekser
python scripts/reindex_with_summaries.py
```

## 💰 Kostnader

**Claude 3.5 Sonnet priser:**
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Estimat for 74 CVer:**
- Input: 74 CVer × ~3000 tokens = ~222k tokens = **$0.67**
- Output: 74 × ~250 tokens = ~18.5k tokens = **$0.28**
- **Total: ~$0.95**

Veldig rimelig! 🎉

## 🔒 GDPR

✅ **Anthropic har Data Processing Agreement (DPA)**  
✅ **Data sendes kryptert (TLS)**  
✅ **Anthropic logger ikke input/output for API-bruk**  
✅ **Data lagres ikke hos Anthropic**  
✅ **EU/EEA databehandling tilgjengelig**

Mer info: https://www.anthropic.com/legal/data-processing-addendum

## 🎯 Resultater

**Før sammendrag:**
```
Bruker: "Finn kandidater med Azure erfaring"
→ Claude får 12 chunks × 500 ord = 6000 ord
→ Claude Desktop cutter chatten
→ Får bare første 3-4 kandidater
```

**Etter sammendrag:**
```
Bruker: "Finn kandidater med Azure erfaring"  
→ Claude får 12 sammendrag × 200 ord = 2400 ord
→ God oversikt over alle kandidater
→ Kan be om full CV for utvalgte kandidater
```

## 🛠️ Avansert: Custom prompts

Du kan tilpasse sammendrags-prompten i `scripts/generate_cv_summaries.py`:

```python
SUMMARY_PROMPT = """Din custom prompt her..."""
```

For eksempel:
- Fokus på spesifikke teknologier (cloud, frontend, etc.)
- Inkluder sertifiseringer
- Fremhev ledererfaring
- osv.

## 📝 Tips

1. **Generer sammendrag etter større Flowcase-synk**
   ```bash
   sync-cv && python scripts/generate_cv_summaries.py
   ```

2. **Test sammendragene før re-indexing**
   ```bash
   ls -lh data/cv_summaries/
   cat data/cv_summaries/ola-nordmann_summary.txt
   ```

3. **Kombiner med list_all_candidates()**
   - Claude bruker først `list_all_candidates()` for oversikt
   - Deretter `search_cvs()` som returnerer sammendrag
   - Til slutt `get_cv_by_name()` for full detalj

---

**Spørsmål?** Se `README.md` eller `.cursorrules` for mer info.




