# Integrazione Vocabolario di Base - Guida Tecnica

## 📦 Componenti Integrati

### 1. **VocabularyService** (`src/correttore/services/vocabulary_service.py`)
Servizio singleton per gestione del Nuovo Vocabolario di Base (NVdB).

**Caratteristiche:**
- Caricamento lazy del vocabolario (7.245 parole)
- Pattern Singleton per evitare caricamenti multipli
- Cache in memoria per performance ottimali
- Supporto livelli: fondamentale, alto_uso, alta_disponibilita

**Utilizzo:**
```python
from correttore.services.vocabulary_service import get_vocabulary_service

vocab = get_vocabulary_service()

# Verifica presenza parola
if vocab.is_in_vocabulary("casa"):
    print("Parola nel vocabolario")

# Info dettagliate
info = vocab.get_word_info("casa")
print(f"Livello: {info.level}")
print(f"Difficoltà: {info.difficulty_score}")

# Analisi testo completo
stats = vocab.analyze_text("Il sole brilla nel cielo...")
print(f"Copertura: {stats.percentage_in_nvdb}%")
print(f"Parole difficili: {stats.difficult_words}")
```

### 2. **ReadabilityAnalyzer** (aggiornato in `src/correttore/utils/readability.py`)
Analizzatore leggibilità ora integra GULPEASE + analisi vocabolario.

**Novità:**
- Parametro `use_vocabulary=True` per abilitare analisi NVdB
- Metrica `vocabulary` nei risultati
- Calcolo qualità lessicale automatico

**Utilizzo:**
```python
from correttore.utils.readability import ReadabilityAnalyzer

analyzer = ReadabilityAnalyzer(use_vocabulary=True)
result = analyzer.analyze(text)

# Metriche tradizionali
print(f"Gulpease: {result['gulpease']}")
print(f"Parole: {result['words']}")

# Nuove metriche vocabolario
if result['vocabulary']:
    vocab = result['vocabulary']
    print(f"Copertura NVdB: {vocab['coverage_percentage']}%")
    print(f"Qualità: {vocab['lexical_quality']}")
    print(f"Parole difficili: {', '.join(vocab['difficult_words_sample'][:10])}")
```

## 🔧 Configurazione

### File Vocabolario
Posizione: `data/vocabolario/`

- **nvdb_completo.json**: Struttura completa con metadata e livelli
- **nvdb_parole.json**: Lista semplice per uso rapido
- **nvdb_parole.txt**: Formato testo (una parola per riga)

### Lazy Loading
Il vocabolario viene caricato automaticamente al primo utilizzo del servizio.
Non richiede configurazione esplicita.

## 📊 Metriche Disponibili

### Analisi Vocabolario (`VocabularyStats`)
```python
{
    'total_words': 100,           # Parole totali analizzate
    'in_nvdb': 85,               # Parole nel vocabolario
    'not_in_nvdb': 15,           # Parole fuori vocabolario
    'percentage_in_nvdb': 85.0,  # % copertura
    'difficult_words': [...]     # Lista parole difficili
}
```

### Qualità Lessicale
Scala automatica basata su copertura NVdB:
- **>= 95%**: Eccellente (molto accessibile)
- **>= 90%**: Ottima (accessibile)
- **>= 85%**: Buona (mediamente accessibile)
- **>= 80%**: Sufficiente (richiede attenzione)
- **>= 70%**: Moderata (testo specialistico)
- **< 70%**: Bassa (testo molto tecnico)

## 🚀 Integrazione nel Correttore

### Uso nel CorrectionEngine
Il vocabolario può essere usato per:

1. **Validazione ortografica migliorata**
```python
from services.vocabulary_service import get_vocabulary_service

vocab = get_vocabulary_service()

def is_likely_correct(word: str) -> bool:
    """Parola nel NVdB = probabilmente corretta"""
    return vocab.is_in_vocabulary(word)
```

2. **Analisi qualità output**
```python
def analyze_correction_quality(original: str, corrected: str):
    """Confronta qualità lessicale prima/dopo correzione"""
    vocab = get_vocabulary_service()
    
    stats_before = vocab.analyze_text(original)
    stats_after = vocab.analyze_text(corrected)
    
    return {
        'coverage_improvement': stats_after.percentage_in_nvdb - stats_before.percentage_in_nvdb,
        'difficult_words_removed': len(stats_before.difficult_words) - len(stats_after.difficult_words)
    }
```

3. **Suggerimenti intelligenti**
```python
def flag_difficult_words(text: str) -> List[str]:
    """Evidenzia parole che potrebbero confondere lettori"""
    vocab = get_vocabulary_service()
    stats = vocab.analyze_text(text)
    return stats.difficult_words
```

### Uso in Quality Assurance
```python
from correttore.core.quality_assurance import QualityAssurance
from correttore.services.vocabulary_service import get_vocabulary_service

class EnhancedQA(QualityAssurance):
    def __init__(self):
        super().__init__()
        self.vocab = get_vocabulary_service()
    
    def check_readability(self, text: str) -> Dict:
        """Check leggibilità con vocabolario"""
        analyzer = ReadabilityAnalyzer(use_vocabulary=True)
        result = analyzer.analyze(text)
        
        issues = []
        if result['vocabulary']:
            coverage = result['vocabulary']['coverage_percentage']
            if coverage < 80:
                issues.append({
                    'type': 'readability',
                    'severity': 'warning',
                    'message': f'Bassa copertura vocabolario ({coverage:.1f}%)',
                    'suggestion': 'Considerare semplificazione lessico'
                })
        
        return {'issues': issues}
```

## 🧪 Testing

Script di test disponibile:
```bash
python tools/test_vocabulary_integration.py
```

Testa:
- Caricamento vocabolario
- Verifica presenza parole
- Analisi testi semplici/complessi
- Metriche di qualità

## 📈 Performance

- **Caricamento vocabolario**: ~50ms (una volta)
- **Lookup parola**: O(1) - set lookup
- **Analisi testo**: O(n) dove n = numero parole
- **Memoria**: ~2MB per vocabolario in RAM

## 🔄 Manutenzione

### Aggiornare Vocabolario
```bash
# Ri-estrai da PDF
python tools/extract_nvdb.py

# Merge con TXT utente
python tools/merge_user_txt.py

# Aggiungi parole funzionali
python tools/add_functional_words.py
```

### Classificare Parole
```bash
# Statistiche
python tools/classify_nvdb.py stats

# Classificazione interattiva
python tools/classify_nvdb.py interactive

# Import da file
python tools/classify_nvdb.py import classificazioni.txt
```

## 🎯 Vantaggi Competitivi

1. **Vocabolario più moderno di Corrige** (2016 vs 1997)
2. **7.245 parole** vs ~7.000 di Corrige
3. **Integrazione nativa** senza dipendenze esterne
4. **Analisi lessicale scientifica** basata su De Mauro
5. **Performance ottimizzate** con singleton pattern

## 📚 Riferimenti

- De Mauro, T. (2016). Nuovo Vocabolario di Base della lingua italiana
- Lucisano-Piemontese (1988). GULPEASE: formula per la predizione della difficoltà
- Corrige.it: https://pro.corrige.it/ortografia/vocabolario-di-base/

## ✅ Checklist Integrazione Completata

- [x] Servizio vocabolario (Singleton pattern)
- [x] Integrazione ReadabilityAnalyzer
- [x] 7.245 parole caricate (incluse funzionali)
- [x] Test suite funzionante
- [x] Documentazione tecnica
- [x] Clean architecture rispettata
- [x] Zero breaking changes su codice esistente
