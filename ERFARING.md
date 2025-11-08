# Erfaring (Years of Experience)

CV-dataen blir automatisk beriket med antall års erfaring fra en ekstern CSV-fil.

## 📁 CSV-Format

Fil: `data/employee_experience.csv`

```csv
Ansatt-ID;Erfaring totalt
1626;3,3
943;9,3
6;33,3
```

- **Separator:** Semikolon (`;`)
- **Desimal:** Norsk komma (`,`)
- **Encoding:** UTF-8 (med eller uten BOM)

## 🔄 Hvordan det fungerer

### 1. Automatisk berikelse ved sync

Når du kjører `sync-cv`, skjer følgende:

```
1. Les CSV-fil med erfaring
2. Last ned CV fra Flowcase
3. Match ansatt-ID (external_unique_id)
4. Legg til "years_of_experience" i JSON
5. Lagre berikede CVer
6. Indekser med erfaring i metadata
```

**Viktig:** Erfaringsdata blir **permanent lagret** i CV-JSON-filene, så den ikke forsvinner ved re-sync!

### 2. I ChromaDB-metadata

Erfaringsdata blir indeksert som metadata:

```python
{
    "cv_name": "Kandidatnavn",
    "office": "Trondheim",
    "years_of_experience": 9.3,
    "source": "kandidat.json",
    ...
}
```

### 3. Søk på erfaring

Du kan filtrere søk basert på erfaring:

```python
# Finn kandidater med 5+ års erfaring
results = indexer.search(
    "React utvikler", 
    n_results=10,
    filter_metadata={"years_of_experience": {"$gte": 5}}
)
```

## 📥 Oppdatere erfaringsdata

### Manuell oppdatering

1. **Eksporter ny CSV** fra HR-system
2. **Kopier til riktig plassering:**
   ```bash
   cp ~/Downloads/ansattliste_eksport.csv data/employee_experience.csv
   ```
3. **Kjør full re-sync:**
   ```bash
   sync-cv --full
   ```

### Automatisk oppdatering (fremtidig)

Man kan utvide `sync_flowcase.py` til å:
- Hente erfaringsdata fra et API
- Automatisk oppdatere CSV-filen før sync
- Logge endringer i erfaring

## 🔍 Verifisering

Test at berikelse fungerer:

```python
from experience_enrichment import ExperienceEnricher

enricher = ExperienceEnricher()
print(f"Loaded {len(enricher.experience_map)} employees")

# Test et ansatt-ID
exp = enricher.get_experience("943")
print(f"Employee 943: {exp} years")
```

Sjekk at en CV har erfaring:

```bash
jq '.years_of_experience' data/cvs/kandidat-navn.json
```

## 🛠️ Feilsøking

### Ingen erfaring i CVer

**Symptom:** `years_of_experience` mangler i JSON-filer

**Løsninger:**
1. Sjekk at CSV-filen eksisterer: `ls -la data/employee_experience.csv`
2. Sjekk format: `head -5 data/employee_experience.csv`
3. Kjør full re-sync: `sync-cv --full`

### Feil i CSV-parsing

**Symptom:** "Loaded 0 employees" i logger

**Løsninger:**
- Sjekk encoding (skal være UTF-8)
- Sjekk separator (skal være `;`)
- Sjekk header-navn: `Ansatt-ID` og `Erfaring totalt`

### Manglende match

**Symptom:** Noen CVer får ikke erfaring

**Årsaker:**
- Ansatt-ID mangler i CSV
- Ansatt-ID i Flowcase matcher ikke CSV
- Ansatt har `NaN` i CSV (håndteres automatisk)

**Sjekk match:**
```bash
# Hent ansatt-ID fra en CV
jq '.external_unique_id' data/cvs/kandidat.json

# Søk i CSV
grep "^1234" data/employee_experience.csv
```

## 📊 Statistikk

Etter sync, sjekk coverage:

```python
from cv_indexer import CVIndexer

indexer = CVIndexer()
stats = indexer.get_stats()

# Tell hvor mange CVer som har erfaring
results = indexer.collection.get()
with_experience = sum(1 for m in results['metadatas'] if 'years_of_experience' in m)

print(f"Total CVs: {stats['unique_cvs']}")
print(f"With experience: {with_experience}")
print(f"Coverage: {with_experience/stats['unique_cvs']*100:.1f}%")
```

## 🔐 GDPR

**Erfaring er IKKE persondata** - det er OK å lagre og indeksere.

- ✅ Antall års erfaring (aggregert tall)
- ❌ Fødselsdato, alder
- ❌ Ansettelsesdato, sluttdato

Vi lagrer kun **totalt antall års erfaring** som et tall, ikke sensitive datoer.

