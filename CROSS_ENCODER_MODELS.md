# Cross-Encoder Modeller - Sammenligning

## Nåværende modell: `BAAI/bge-reranker-base` ✅ (Oppgradert Nov 2025)

**Status:** ✅ Implementert og testet  
**Språkstøtte:** Engelsk og kinesisk (fungerer bedre på norsk enn ms-marco)  
**Størrelse:** ~1.1 GB (278M parametere)  
**Ytelse:** ~5-10x tregere enn bi-encoder (0.1s → 0.3-6s)  
**Kvalitet:** Bedre relevans-scoring, ingen "nan" scores

**Fordeler:**
- ✅ Ingen "nan" scores (fungerer bedre med norsk tekst)
- ✅ Bedre relevans-scoring (0.94+ for relevante dokumenter)
- ✅ Finner relevante kandidater som bi-encoder gikk glipp av
- ✅ Høyere kvalitet enn ms-marco-MiniLM

**Ulemper:**
- Tregere enn ms-marco-MiniLM (større modell)
- Større filstørrelse (1.1 GB vs 90 MB)

---

## Tidligere modell: `cross-encoder/ms-marco-MiniLM-L-6-v2`

**Status:** ❌ Erstattet med BGE-reranker-base  
**Språkstøtte:** Primært engelsk (MS MARCO dataset)  
**Størrelse:** ~90 MB  
**Ytelse:** 2-20x tregere enn bi-encoder (0.1s → 0.1-2s)  
**Kvalitet:** Endrer resultater, men uklart om bedre for norsk tekst

**Problemer:**
- Trente på engelsk data (MS MARCO)
- Noen ganger "nan" scores på norsk tekst
- Ikke optimalt for norsk/engelsk blandet innhold

---

## Alternativer

### 1. `BAAI/bge-reranker-base` ⭐ (Nåværende - Oppgradert Nov 2025)

**Språkstøtte:** Engelsk og kinesisk (kan fungere på norsk)  
**Størrelse:** ~1.1 GB (278M parametere)  
**Utvikler:** Beijing Academy of Artificial Intelligence (BAAI)  
**Status:** ✅ Tilgjengelig på HuggingFace

**Fordeler:**
- Høy kvalitet (toppresultater i sin størrelsesklasse)
- Balanserer nøyaktighet og hastighet
- Trenet på høykvalitets data
- Støtter både engelsk og kinesisk (kan fungere på norsk)

**Ulemper:**
- Større enn ms-marco (1.1 GB vs 90 MB)
- Ikke eksplisitt trent på norsk
- Tregere enn ms-marco-MiniLM

**HuggingFace:** `BAAI/bge-reranker-base`

---

### 2. `BAAI/bge-reranker-large` 

**Språkstøtte:** Engelsk og kinesisk  
**Størrelse:** ~2.2 GB (560M parametere)  
**Utvikler:** Beijing Academy of Artificial Intelligence (BAAI)  
**Status:** ✅ Tilgjengelig på HuggingFace

**Fordeler:**
- Beste nøyaktighet (560M parametere)
- Høy kvalitet

**Ulemper:**
- Mye større (2.2 GB)
- Tregere enn base-varianten
- Ikke eksplisitt trent på norsk

**HuggingFace:** `BAAI/bge-reranker-large`

---

### 3. `jinaai/jina-reranker-v2-base-multilingual`

**Språkstøtte:** Multilingual (inkl. europeiske språk)  
**Størrelse:** Ukjent  
**Utvikler:** Jina AI  
**Status:** ⚠️ Må verifiseres på HuggingFace

**Fordeler:**
- Eksplisitt multilingual
- Kan støtte norsk bedre

**Ulemper:**
- Mindre dokumentasjon
- Ukjent størrelse og ytelse
- Må testes

**HuggingFace:** `jinaai/jina-reranker-v2-base-multilingual` (må verifiseres)

---

### 4. LaBSE (Language-agnostic BERT Sentence Embedding)

**Status:** ❌ IKKE RELEVANT  
**Årsak:** Dette er en **bi-encoder**, ikke en cross-encoder. Kan ikke brukes for re-ranking.

---

## Anbefaling

### Kort sikt (test nå):
**`BAAI/bge-reranker-base`** - Best balanse mellom kvalitet og størrelse

**Grunn:**
- Høy kvalitet (trent på MS MARCO + kinesisk data)
- Rimelig størrelse (1.1 GB)
- Sannsynligvis bedre enn ms-marco-MiniLM for norsk (pga. større modell)
- Enkel å teste (bare bytt modell-navn i config)

### Lang sikt:
1. Test `BAAI/bge-reranker-base` først
2. Hvis ikke godt nok, test `BAAI/bge-reranker-large` (bedre kvalitet, men tregere)
3. Vurder `jina-reranker-v2-base-multilingual` hvis den finnes og er dokumentert

---

## Implementering

For å teste en ny modell, endre i `config.py`:

```python
CROSS_ENCODER_MODEL = "BAAI/bge-reranker-base"  # Eller annen modell
```

Deretter test med:
```bash
python scripts/test_reranking.py
```

---

## Notater

- **Ingen dedikerte norske cross-encoder modeller** funnet
- De fleste cross-encoders er trent på engelsk (MS MARCO) eller engelsk+kinesisk (BGE)
- Multilingual cross-encoders er sjeldne
- BGE-modellene er sannsynligvis beste alternativet for norsk (pga. størrelse og kvalitet)

