# 🔄 Oppdatering av CVer

## Manuell Synkronisering (Anbefalt)

### Super Enkel Måte (Anbefalt):
```bash
sync-cv
```
Kjør fra hvor som helst! 🎯

### Alternativ (hvis du er i prosjektmappen):
```bash
cd /Users/larsandreassen/Kodeprosjekter/cv-rag-system
./sync.sh
```

Dette vil:
1. ✅ Hente CVer oppdatert siste 7 dager fra Flowcase
2. ✅ Lagre som JSON (uten persondata)
3. ✅ Re-indeksere automatisk i ChromaDB
4. ✅ Gjøre dem tilgjengelig for Cursor/Claude

## Sync-Alternativer

```bash
./sync.sh              # Incremental (siste 7 dager) - STANDARD
./sync.sh --full       # Full sync (standard offices: 798 CVer)
./sync.sh --all        # Full sync (ALLE avdelinger inkl. Salg & Admin)
./sync.sh --test       # Test med 5 CVer
```

## Manual Re-indeksering

Hvis du bare vil re-indeksere uten å laste ned nye CVer:

```bash
source venv/bin/activate
python scripts/reindex.py
```

## CLI-Bruk (Avansert)

```bash
# Incremental sync uten prompts (standard offices)
python scripts/sync_flowcase.py --auto --mode incremental

# Full sync uten re-indeksering (standard offices)
python scripts/sync_flowcase.py --auto --mode full --no-reindex

# Kun spesifikke avdelinger
python scripts/sync_flowcase.py --auto --offices "Teknologi,Design"

# Alle avdelinger (inkl. Salg & Admin)
python scripts/sync_flowcase.py --auto --all-offices

# Test med 5 CVer
python scripts/sync_flowcase.py --auto --mode test
```

## Flowcase Data

- **Standard Offices:** Teknologi, Design, Trondheim, Management Consulting, Oppdrag (798 CVer totalt)
- **Format:** JSON (opptil 1 MB per CV)
- **Persondata:** Kun navn og avdeling (GDPR-vennlig)
- **Innhold:** Teknologier, erfaring, utdanning, key qualifications

## Når bør du synkronisere?

✅ **Før du starter anbudsarbeid** - Få siste endringer  
✅ **Ukentlig** - Hold databasen oppdatert  
✅ **Etter store CV-oppdateringer i Flowcase**

❌ **Ikke nødvendig daglig** - Incremental sync er rask og effektiv

