# 📘 Fase 5 Completata: Lemmatizzazione e NLP con spaCy

**Data**: 25 Ottobre 2025  
**Stato**: ✅ **COMPLETATA E TESTATA**

---

## 🎯 Obiettivo

Implementare lemmatizzazione e analisi NLP avanzata usando spaCy per:
- Ridurre drasticamente i falsi positivi nel confronto con il Vocabolario di Base
- Riconoscere automaticamente nomi propri, luoghi e organizzazioni
- Fornire analisi linguistica approfondita (POS tagging, lemmatizzazione)

---

## 📦 Componenti Implementati

### 1. **LemmatizationService** 
`src/correttore/services/lemmatization_service.py`

Servizio singleton per lemmatizzazione e analisi NLP con spaCy.

#### Funzionalità principali:

```python
from src.correttore.services.lemmatization_service import LemmatizationService

service = LemmatizationService()

# Lemmatizzazione singola parola
lemma = service.lemmatize_word("mangiato")  # → "mangiare"
lemma = service.lemmatize_word("case")      # → "casa"

# Lemmatizzazione testo completo
lemmas = service.lemmatize("I gatti mangiano i topi")
# → [('I', 'il'), ('gatti', 'gatto'), ('mangiano', 'mangiare'), ('i', 'il'), ('topi', 'topo')]

# POS Tagging (parti del discorso)
pos_tags = service.get_pos_tags("Il gatto nero mangia")
# → [('Il', 'DET', 'Determinante'), 
#    ('gatto', 'NOUN', 'Nome'),
#    ('nero', 'ADJ', 'Aggettivo'),
#    ('mangia', 'VERB', 'Verbo')]

# Named Entity Recognition
entities = service.get_named_entities("Mario Rossi vive a Roma")
# → [NamedEntity(text='Mario Rossi', label='PER', label_description='Persona', ...),
#    NamedEntity(text='Roma', label='LOC', label_description='Luogo', ...)]

# Raggruppamento entità per tipo
entities_by_type = service.get_named_entities_by_type(text)
# → {'PER': ['Mario Rossi', 'Laura Bianchi'],
#    'LOC': ['Roma', 'Milano'],
#    'ORG': ['Microsoft', 'Google']}

# Estrazione nomi propri
proper_nouns = service.get_proper_nouns("Mario e Luigi vanno a Roma")
# → ['Mario', 'Luigi', 'Roma']
```

#### Strutture Dati

**Token**:
```python
@dataclass
class Token:
    text: str          # Parola originale
    lemma: str         # Forma base
    pos: str           # Part of Speech (NOUN, VERB, ADJ, etc.)
    tag: str           # Fine-grained POS tag
    is_stop: bool      # Parola funzionale (il, la, di, ecc.)
    is_alpha: bool     # Solo caratteri alfabetici
```

**NamedEntity**:
```python
@dataclass
class NamedEntity:
    text: str                # Testo dell'entità
    label: str               # PER, LOC, ORG, etc.
    label_description: str   # Descrizione in italiano
    start_char: int          # Posizione inizio
    end_char: int            # Posizione fine
    context: str             # Frase contenente l'entità
```

---

### 2. **Integrazione con VocabularyService**
`services/vocabulary_service.py`

Il VocabularyService è stato esteso per usare la lemmatizzazione nel confronto con il Vocabolario di Base.

#### Nuovi Metodi:

```python
from services.vocabulary_service import VocabularyService

vocab = VocabularyService()

# Verifica con lemmatizzazione
is_in, lemma = vocab.is_in_vocabulary_with_lemma("mangiato")
# → (True, "mangiare")

# Analisi dettagliata con lemma
analysis = vocab.analyze_word_detailed("correvano", use_lemmatization=True)
# → WordAnalysis(word='correvano', in_vdb=True, lemma='correre', ...)

# Analisi testo con lemmatizzazione
stats = vocab.analyze_text(text, use_lemmatization=True)
# → VocabularyStats con copertura VdB migliorata
```

#### Miglioramento Drastico della Copertura

**Esempio pratico** (dal test):

```python
text = "I gatti mangiano velocemente. Le case sono belle. I bambini correvano felici."

# SENZA lemmatizzazione:
# - Parole totali: 12
# - Nel VdB: 4 (33.3%)
# - Fuori VdB: 8
# - Parole difficili: bambini, belle, case, correvano, felici, gatti, mangiano, sono

# CON lemmatizzazione:
# - Parole totali: 12
# - Nel VdB: 12 (100.0%)
# - Fuori VdB: 0

# 📈 Miglioramento: +66.7% di copertura VdB!
```

---

## 🧪 Test Suite Completa

**File**: `test_lemmatization_phase5.py`

### Test Implementati:

1. **Test 1: Lemmatization Service**
   - Lemmatizzazione singole parole (5/5 ✅)
   - Lemmatizzazione testo completo ✅
   - POS Tagging ✅
   - Analisi token completa ✅

2. **Test 2: Named Entity Recognition**
   - Riconoscimento entità base (6 entità trovate) ✅
   - Raggruppamento per tipo ✅
   - Estrazione nomi propri ✅

3. **Test 3: Integrazione Vocabulary + Lemmatization**
   - Confronto con/senza lemmatizzazione ✅
   - Analisi parola dettagliata con lemma ✅
   - Analisi testo completo ✅
   - **Miglioramento copertura VdB: +66.7%** 🎉

4. **Test 4: Analisi Completa Testo**
   - Statistiche complete ✅
   - Distribuzione POS ✅
   - Named entities ✅
   - Lemmi ✅

### Risultato Test:
```
🎉 TUTTI I TEST SONO PASSATI!
✅ Fase 5 implementata con successo!
```

---

## 💡 Casi d'Uso

### 1. Riduzione Falsi Positivi nel VdB

**Prima (Fase 4)**:
```python
# "mangiato" NON viene riconosciuto (solo "mangiare" è nel VdB)
is_in_vdb("mangiato")  # → False ❌
```

**Dopo (Fase 5)**:
```python
# "mangiato" viene lemmatizzato a "mangiare" e riconosciuto
is_in_vdb_with_lemma("mangiato")  # → (True, "mangiare") ✅
```

### 2. Named Entity Recognition per Report "Nomi/Sigle"

```python
text = "Mario Rossi è nato a Roma e lavora per Microsoft"

entities_by_type = lemma_service.get_named_entities_by_type(text)

# Risultato:
# {
#   'PER': ['Mario Rossi'],
#   'LOC': ['Roma'],
#   'ORG': ['Microsoft']
# }

# Può essere usato per:
# - Popolare automaticamente il tab "Nomi/Sigle" del report
# - Ridurre segnalazioni false per nomi propri
# - Creare glossario automatico
```

### 3. Analisi Linguistica Completa

```python
text = "Il gatto nero mangia velocemente"

analysis = lemma_service.analyze_text_complete(text)

# Risultato include:
# - tokens: Lista dettagliata di tutti i token
# - lemmas: Coppie (parola, lemma)
# - pos_tags: Classificazione parti del discorso
# - named_entities: Entità nominate riconosciute
# - statistics: Statistiche complete (token, lemmi unici, frasi, ecc.)
```

### 4. Integrazione nei Report HTML

**Possibile estensione futura**:
```python
# Nel report leggibilità, evidenziare:
# - Nomi propri con colore diverso (non contano come "parole difficili")
# - Termini tecnici identificati tramite POS
# - Copertura VdB più accurata grazie a lemmatizzazione
```

---

## 🔧 Dettagli Tecnici

### Modello spaCy
- **Modello**: `it_core_news_lg` (Large Italian model)
- **Dimensione**: ~568 MB
- **Funzionalità**: Lemmatizzazione, POS tagging, NER, dependency parsing
- **Prestazioni**: Caricamento iniziale ~2-3 secondi, poi cached

### Singleton Pattern
Entrambi i servizi usano il singleton pattern per evitare caricamenti multipli:
```python
service1 = LemmatizationService()
service2 = LemmatizationService()  # Stessa istanza!
# Il modello spaCy viene caricato una sola volta
```

### Import Opzionale
Il VocabularyService funziona anche senza spaCy installato:
```python
try:
    from src.correttore.services.lemmatization_service import get_lemmatization_service
    LEMMATIZATION_AVAILABLE = True
except ImportError:
    LEMMATIZATION_AVAILABLE = False
    # Continua a funzionare senza lemmatizzazione
```

### Etichette Supportate

**POS Tags** (16 tipi principali):
- NOUN (Nome), VERB (Verbo), ADJ (Aggettivo), ADV (Avverbio)
- PRON (Pronome), DET (Determinante), ADP (Preposizione)
- CONJ (Congiunzione), NUM (Numero), PART (Particella)
- INTJ (Interiezione), PROPN (Nome Proprio), AUX (Ausiliare)
- PUNCT (Punteggiatura), SYM (Simbolo), X (Altro)

**Named Entities** (18 tipi):
- PER (Persona), LOC (Luogo), ORG (Organizzazione)
- GPE (Entità Geopolitica), DATE (Data), TIME (Ora)
- MONEY (Denaro), PERCENT (Percentuale), CARDINAL (Numero)
- EVENT (Evento), PRODUCT (Prodotto), WORK_OF_ART (Opera)
- LAW (Legge), LANGUAGE (Lingua), e altri

---

## 📊 Performance e Statistiche

### Test su Testo Reale

**Input**: 171 caratteri, 3 frasi
```
Mario Rossi è nato a Roma nel 1985. 
Ha studiato all'Università La Sapienza e ora lavora per Microsoft.
Il 15 gennaio 2024 ha visitato Parigi con sua moglie Laura Bianchi.
```

**Risultati**:
- ✅ 6 entità nominate riconosciute
- ✅ 2 persone (Mario Rossi, Laura Bianchi)
- ✅ 3 luoghi (Roma, Università La Sapienza, Parigi)
- ✅ 1 organizzazione (Microsoft)
- ✅ 7 nomi propri estratti

### Miglioramento Copertura VdB

| Metrica | Senza Lemma | Con Lemma | Miglioramento |
|---------|-------------|-----------|---------------|
| Copertura VdB | 33.3% | 100.0% | **+66.7%** |
| Falsi positivi | 8/12 | 0/12 | **-100%** |

---

## 🚀 Utilizzo nel Workflow

### 1. Nel Correttore Principale

```python
from src.correttore.services.lemmatization_service import get_lemmatization_service
from services.vocabulary_service import VocabularyService

# Setup
lemma_service = get_lemmatization_service()
vocab_service = VocabularyService()

# Analisi testo
text = "I bambini correvano felici nel parco"

# Con lemmatizzazione automatica
stats = vocab_service.analyze_text(text, use_lemmatization=True)
print(f"Copertura VdB: {stats.percentage_in_nvdb}%")

# Estrazione entità
entities = lemma_service.get_named_entities(text)
```

### 2. Nei Report HTML

```python
from src.correttore.utils.readability_report_generator import ReadabilityReportGenerator

generator = ReadabilityReportGenerator()

# Il vocabulary_service usato nei report ora beneficia automaticamente
# della lemmatizzazione per statistiche più accurate
report_path = generator.generate_report(
    text=text,
    output_path="report.html",
    vocabulary_service=vocab_service,  # Usa lemmatizzazione
    document_title="Analisi Avanzata"
)
```

---

## 📝 File Creati/Modificati

### Nuovi File:
1. `src/correttore/services/lemmatization_service.py` - Servizio lemmatizzazione e NLP
2. `test_lemmatization_phase5.py` - Suite test completa (4 test, tutti ✅)
3. `docs/FASE5_COMPLETATA.md` - Questa documentazione

### File Modificati:
1. `services/vocabulary_service.py` - Aggiunta integrazione lemmatizzazione
   - Nuovo metodo: `is_in_vocabulary_with_lemma()`
   - Parametro `use_lemmatization` in `analyze_text()` e `analyze_word_detailed()`

---

## 🎓 Esempio Completo End-to-End

```python
#!/usr/bin/env python3
"""Esempio completo uso Fase 5"""

from src.correttore.services.lemmatization_service import LemmatizationService
from services.vocabulary_service import VocabularyService

# Setup
lemma_service = LemmatizationService()
vocab_service = VocabularyService()

# Testo da analizzare
text = """
Giuseppe Verdi nacque a Roncole nel 1813.
I suoi capolavori vengono eseguiti nei teatri di tutto il mondo.
"""

# 1. Named Entity Recognition
print("🎭 Entità nominate:")
entities = lemma_service.get_named_entities_by_type(text)
for entity_type, items in entities.items():
    print(f"  {entity_type}: {', '.join(items)}")

# 2. Lemmatizzazione
print("\n📝 Lemmatizzazione:")
lemmas = lemma_service.lemmatize(text)
for word, lemma in lemmas[:10]:
    if word != lemma:
        print(f"  {word} → {lemma}")

# 3. Analisi vocabolario (con lemmatizzazione)
print("\n📊 Copertura Vocabolario di Base:")
stats = vocab_service.analyze_text(text, use_lemmatization=True)
print(f"  Parole totali: {stats.total_words}")
print(f"  Nel VdB: {stats.in_nvdb} ({stats.percentage_in_nvdb}%)")
print(f"  Fuori VdB: {stats.not_in_nvdb}")

# 4. Analisi completa
print("\n🔍 Analisi linguistica completa:")
analysis = lemma_service.analyze_text_complete(text)
print(f"  Lemmi unici: {analysis['statistics']['unique_lemmas']}")
print(f"  Frasi: {analysis['statistics']['sentences']}")
print(f"  Entità nominate: {analysis['statistics']['named_entities_count']}")
```

---

## 🔮 Prossimi Passi

La Fase 5 è completa! Le funzionalità di lemmatizzazione e NER sono pronte per:

### Integrazioni Future (Fase 6+):
1. **Tab "Nomi/Sigle" automatico** nei report HTML
   - Popolato con `get_named_entities_by_type()`
   - Classificazione automatica per tipo

2. **Tab "Lingue" per parole straniere**
   - Riconoscimento automatico con NER
   - Dizionari specifici per lingua

3. **Miglioramento SafeCorrection**
   - Bonus per correzioni che mantengono parole nel VdB
   - Penalità per introduzione parole fuori VdB

4. **Report Leggibilità CT (Terminologia Tecnica)**
   - Identificazione automatica termini tecnici
   - Glossario generato automaticamente

---

## ✅ Checklist Completamento

- [x] Installato spaCy e modello `it_core_news_lg`
- [x] Creato `LemmatizationService` con tutte le funzionalità
- [x] Implementato lemmatizzazione singola parola e testo completo
- [x] Implementato POS tagging
- [x] Implementato Named Entity Recognition
- [x] Integrato lemmatizzazione in `VocabularyService`
- [x] Creata suite test completa (4 test, tutti ✅)
- [x] Verificato miglioramento copertura VdB (+66.7%)
- [x] Creata documentazione completa

---

## 🎉 Conclusione

La **Fase 5** introduce capacità di analisi linguistica avanzata che:

✅ **Riduce drasticamente i falsi positivi** (da 33% a 100% di copertura in alcuni casi)  
✅ **Riconosce automaticamente nomi propri**, luoghi e organizzazioni  
✅ **Fornisce analisi grammaticale completa** (POS tagging)  
✅ **Migliora significativamente l'accuratezza** del confronto con il Vocabolario di Base  

Tutti i test sono passati con successo. Il sistema è pronto per le fasi successive!

---

**Fase successiva**: Fase 6 - Sistema Feedback e Apprendimento (opzionale) o integrazione report HTML avanzati.
