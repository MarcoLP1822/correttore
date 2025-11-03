# Piano di Implementazione Completo
## Sistema Filtraggio Intelligente + UI Modernization

**Data**: 3 Novembre 2025  
**Obiettivo**: Trasformare applicazione in sistema professionale state-of-the-art  
**Approccio**: Incremental deployment con testing continuo

---

## 📊 Stato Attuale

### ✅ Completato
- [x] Modulo `language_classifier.py` creato
- [x] Integrazione base in `document_analyzer.py`
- [x] Pattern linguistici per 4 lingue (Inglese, Francese, Tedesco, Italiano)
- [x] Sistema di filtraggio intelligente implementato
- [x] Logging avanzato aggiunto

### 🔄 In Corso
- [ ] Test su documento reale
- [ ] Validazione accuracy
- [ ] Fine-tuning soglie confidenza

### ⏳ Da Fare
- [ ] UI modernization
- [ ] Design system
- [ ] Component library
- [ ] Performance optimization

---

## 🎯 FASE 1: Validazione Sistema Filtraggio (Priority: CRITICAL)

**Durata stimata**: 30 minuti  
**Obiettivo**: Verificare funzionamento corretto prima di procedere

### Step 1.1: Test Ambiente Locale ⚡
**Durata**: 5 minuti

```bash
# 1. Verifica import moduli
python -c "from src.correttore.core.language_classifier import ForeignWordFilter; print('✅ Import OK')"

# 2. Verifica integrazione DocumentAnalyzer
python -c "from src.correttore.core.document_analyzer import DocumentAnalyzer; print('✅ DocumentAnalyzer OK')"

# 3. Check errori sintassi
python -m py_compile src/correttore/core/language_classifier.py
python -m py_compile src/correttore/core/document_analyzer.py
```

**Successo**: Tutti i comandi completano senza errori

---

### Step 1.2: Test Classificatore Isolato ⚡
**Durata**: 10 minuti

```python
# File: tests/test_language_classifier.py (NUOVO)

from src.correttore.core.language_classifier import (
    LanguageClassifier, ForeignWordFilter, Language
)

def test_latin_detection():
    """Test rilevamento parole latine"""
    classifier = LanguageClassifier()
    
    test_cases = [
        ("populus", "legislator sive populus", Language.LATIN, 0.6),
        ("civium", "voluntatem civium generaliter", Language.LATIN, 0.6),
        ("cum", "dicimus igitur cum veritate", Language.LATIN, 0.6),
    ]
    
    for word, context, expected_lang, min_conf in test_cases:
        lang, conf = classifier.classify_word(word, context)
        assert lang == expected_lang, f"Expected {expected_lang}, got {lang}"
        assert conf >= min_conf, f"Confidence too low: {conf} < {min_conf}"
    
    print("✅ Latin detection: PASS")

def test_english_detection():
    """Test rilevamento parole inglesi"""
    classifier = LanguageClassifier()
    
    test_cases = [
        ("checks", "sistema di checks and balances", Language.ENGLISH, 0.6),
        ("governance", "La governance multilivello", Language.ENGLISH, 0.5),
        ("should", "justice should lose their names", Language.ENGLISH, 0.7),
    ]
    
    for word, context, expected_lang, min_conf in test_cases:
        lang, conf = classifier.classify_word(word, context)
        assert lang == expected_lang, f"Expected {expected_lang}, got {lang}"
        assert conf >= min_conf, f"Confidence too low: {conf} < {min_conf}"
    
    print("✅ English detection: PASS")

def test_proper_noun_filter():
    """Test filtraggio nomi propri"""
    filter_sys = ForeignWordFilter()
    
    test_cases = [
        ("Poddighe", "Marco Poddighe nato", True, "proper_noun"),
        ("Westfalia", "trattato di Westfalia", True, "proper_noun"),
        ("Weber", "come Weber sosteneva", True, "proper_noun"),
    ]
    
    for word, context, should_filter, expected_reason in test_cases:
        filtered, lang, reason = filter_sys.should_filter_error(word, context)
        assert filtered == should_filter, f"Filter mismatch for {word}"
        assert reason == expected_reason, f"Wrong reason: {reason}"
    
    print("✅ Proper noun filter: PASS")

def test_technical_terms():
    """Test filtraggio termini tecnici"""
    filter_sys = ForeignWordFilter()
    
    technical = ["governance", "asset", "welfare", "blockchain", "smart"]
    
    for term in technical:
        filtered, lang, reason = filter_sys.should_filter_error(term, "")
        assert filtered == True, f"{term} should be filtered"
        assert reason == "technical_term", f"Wrong reason for {term}"
    
    print("✅ Technical terms filter: PASS")

if __name__ == "__main__":
    test_latin_detection()
    test_english_detection()
    test_proper_noun_filter()
    test_technical_terms()
    print("\n🎉 All tests passed!")
```

**Esegui**:
```bash
python tests/test_language_classifier.py
```

**Successo**: Tutti i test passano

---

### Step 1.3: Test Integrazione Documento Reale 🔥
**Durata**: 15 minuti

```bash
# 1. Backup documento test corrente
cp "uploads/ordine-con-note-tascabile_68dbb566217df.docx" "backups/test_document.docx"

# 2. Riavvia server Flask
# Ctrl+C per fermare se già in esecuzione
python main.py

# 3. In browser: http://localhost:5000
# - Carica documento "ordine-con-note-tascabile_68dbb566217df.docx"
# - Clicca "Analizza"
# - Attendi completamento

# 4. Verifica nei logs del terminale:
```

**Log da verificare**:
```
✅ DEVE APPARIRE:
🔍 _analyze_grammar: LanguageTool returned 489 errors
📊 Filtering stats: X filtered, Y reclassified as foreign
📝 Final count: 489 raw errors → Z valid records

DOVE:
X = numero errori filtrati (nomi propri + termini tecnici)
Y = numero errori riclassificati come LINGUE
Z = numero errori reali italiani rimasti

TARGET ATTESO:
X ≈ 150-200 (nomi propri come Poddighe, Weber, etc.)
Y ≈ 250-300 (citazioni latine, inglesi, francesi, tedesche)
Z ≈ 10-40 (errori italiani reali)
```

**Validazione Report**:
1. Apri report HTML generato
2. Verifica sezioni:
   - ✅ "Errori Riconosciuti (X)" → DEVE essere bassa (10-40)
   - ✅ "Lingue (L)" → DEVE contenere parole straniere (250-300)
   - ❌ NON DEVONO APPARIRE: "Poddighe", "Weber", "governance", "asset"

**Se fallisce**: 
- Verifica import in `document_analyzer.py`
- Verifica `self.foreign_word_filter` inizializzato
- Verifica condizione `if category == CorrectionCategory.ERRORI_RICONOSCIUTI`

---

## 🎨 FASE 2: UI Modernization (Priority: HIGH)

**Durata stimata**: 4-6 ore  
**Obiettivo**: Trasformare interfaccia da "infantile" a "professionale"

### Step 2.1: Setup Design System ⚡
**Durata**: 30 minuti

```bash
# 1. Crea struttura cartelle
mkdir -p src/correttore/web/styles
mkdir -p src/correttore/web/components/atoms
mkdir -p src/correttore/web/components/molecules
mkdir -p src/correttore/web/components/templates
```

**File 1**: `src/correttore/web/styles/tokens.css`
```css
/* ========================================
   Design Tokens - Professional System
   ======================================== */

:root {
  /* Typography Scale */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 
               'Helvetica Neue', Arial, sans-serif;
  --font-mono: 'SF Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
  
  --text-xs: 0.75rem;     /* 12px - metadata */
  --text-sm: 0.875rem;    /* 14px - body */
  --text-base: 1rem;      /* 16px - default */
  --text-lg: 1.125rem;    /* 18px - subtitles */
  --text-xl: 1.25rem;     /* 20px - headings */
  --text-2xl: 1.5rem;     /* 24px - page titles */
  
  --line-tight: 1.25;
  --line-normal: 1.5;
  --line-relaxed: 1.75;
  
  /* Color Palette - Professional */
  --color-primary-50: #eff6ff;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  
  --color-success-50: #f0fdf4;
  --color-success-500: #22c55e;
  --color-success-600: #16a34a;
  
  --color-warning-50: #fffbeb;
  --color-warning-500: #f59e0b;
  --color-warning-600: #d97706;
  
  --color-danger-50: #fef2f2;
  --color-danger-500: #ef4444;
  --color-danger-600: #dc2626;
  
  --color-neutral-50: #f9fafb;
  --color-neutral-100: #f3f4f6;
  --color-neutral-200: #e5e7eb;
  --color-neutral-300: #d1d5db;
  --color-neutral-400: #9ca3af;
  --color-neutral-500: #6b7280;
  --color-neutral-600: #4b5563;
  --color-neutral-700: #374151;
  --color-neutral-800: #1f2937;
  --color-neutral-900: #111827;
  
  /* Spacing Scale */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  
  /* Border Radius */
  --radius-sm: 0.25rem;   /* 4px */
  --radius-md: 0.375rem;  /* 6px */
  --radius-lg: 0.5rem;    /* 8px */
  --radius-xl: 0.75rem;   /* 12px */
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  
  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

**File 2**: `src/correttore/web/styles/reset.css`
```css
/* Modern CSS Reset */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  line-height: var(--line-normal);
  color: var(--color-neutral-800);
  background-color: var(--color-neutral-50);
}

h1, h2, h3, h4, h5, h6 {
  font-weight: 600;
  color: var(--color-neutral-900);
  line-height: var(--line-tight);
}

button {
  font-family: inherit;
  cursor: pointer;
}
```

---

### Step 2.2: Refactor HTMLReportGenerator 🔥
**Durata**: 2 ore

**File**: `src/correttore/utils/html_report_generator.py`

**Modifiche da fare**:

1. **Cambia header HTML**:
```python
# PRIMA (da eliminare)
<h1 style="font-size: 32px; color: #FF5722;">ANALISI DOCUMENTO</h1>

# DOPO (nuovo)
<h1 style="font-size: 1.5rem; font-weight: 600; color: #111827; margin-bottom: 1.5rem;">
    Document Analysis Report
</h1>
```

2. **Cambia metrics cards**:
```python
# PRIMA
<div style="background: red; padding: 30px; font-size: 24px;">
    🔴 ERRORI: {error_count}
</div>

# DOPO
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
    <div style="background: white; border: 1px solid #e5e7eb; 
                border-radius: 0.5rem; padding: 1rem;">
        <div style="font-size: 0.875rem; color: #6b7280;">Errors</div>
        <div style="font-size: 1.5rem; font-weight: 600; color: #dc2626;">
            {error_count}
        </div>
    </div>
    <div style="background: white; border: 1px solid #e5e7eb; 
                border-radius: 0.5rem; padding: 1rem;">
        <div style="font-size: 0.875rem; color: #6b7280;">Foreign Words</div>
        <div style="font-size: 1.5rem; font-weight: 600; color: #3b82f6;">
            {foreign_count}
        </div>
    </div>
    <!-- altri metrics -->
</div>
```

3. **Cambia error cards**:
```python
# PRIMA
<div style="border: 3px solid red; padding: 25px; margin: 20px; 
            font-size: 20px; background: #ffebee;">
    <b style="font-size: 24px;">ERRORE ORTOGRAFICO</b>
    <p style="font-size: 22px;">{original_text}</p>
</div>

# DOPO
<div style="border: 1px solid #fecaca; border-left: 3px solid #dc2626;
            border-radius: 0.375rem; padding: 1rem; margin-bottom: 0.75rem;
            background: white;">
    <div style="display: flex; align-items: center; gap: 0.5rem; 
                margin-bottom: 0.5rem;">
        <span style="font-size: 0.75rem; padding: 0.25rem 0.5rem;
                     background: #fef2f2; color: #dc2626; 
                     border-radius: 0.25rem; font-weight: 500;">
            SPELLING
        </span>
        <span style="font-size: 0.875rem; color: #6b7280;">
            Line {line_number}
        </span>
    </div>
    <div style="font-size: 0.875rem; color: #1f2937; margin-bottom: 0.5rem;">
        <span style="background: #fee; padding: 2px 4px; border-radius: 2px;">
            {original_text}
        </span>
        →
        <span style="background: #efe; padding: 2px 4px; border-radius: 2px;">
            {corrected_text}
        </span>
    </div>
    <div style="font-size: 0.75rem; color: #6b7280;">
        {message}
    </div>
</div>
```

**Approccio Incrementale**:
```python
# 1. Crea nuovo metodo _generate_modern_html()
def _generate_modern_html(self, data: Dict) -> str:
    """Generate modern professional HTML report"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Analysis Report</title>
        <link rel="stylesheet" href="/static/styles/tokens.css">
        <link rel="stylesheet" href="/static/styles/reset.css">
        <link rel="stylesheet" href="/static/styles/components.css">
    </head>
    <body>
        {self._render_header(data)}
        {self._render_metrics(data)}
        {self._render_errors(data)}
        {self._render_foreign_language(data)}
    </body>
    </html>
    """

# 2. Aggiungi flag per usare vecchio o nuovo sistema
def generate_report(self, data: Dict, use_modern: bool = True) -> str:
    if use_modern:
        return self._generate_modern_html(data)
    else:
        return self._generate_legacy_html(data)  # Vecchio sistema
```

---

### Step 2.3: Crea Components CSS 🎨
**Durata**: 1 ora

**File**: `src/correttore/web/styles/components.css`

```css
/* ========================================
   Component Library
   ======================================== */

/* Container */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-6);
}

/* Header */
.report-header {
  margin-bottom: var(--space-8);
}

.report-title {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--color-neutral-900);
  margin-bottom: var(--space-2);
}

.report-subtitle {
  font-size: var(--text-sm);
  color: var(--color-neutral-600);
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.metric-card {
  background: white;
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  transition: all var(--transition-base);
}

.metric-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-neutral-300);
}

.metric-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-600);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
  margin-bottom: var(--space-1);
}

.metric-value {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: var(--line-tight);
}

.metric-value.error { color: var(--color-danger-600); }
.metric-value.warning { color: var(--color-warning-600); }
.metric-value.success { color: var(--color-success-600); }
.metric-value.info { color: var(--color-primary-600); }

/* Error Card */
.error-card {
  background: white;
  border: 1px solid var(--color-neutral-200);
  border-left: 3px solid var(--color-danger-500);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  margin-bottom: var(--space-3);
  transition: all var(--transition-base);
}

.error-card:hover {
  box-shadow: var(--shadow-sm);
}

.error-card.warning {
  border-left-color: var(--color-warning-500);
}

.error-card.info {
  border-left-color: var(--color-primary-500);
}

.error-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.error-badge {
  font-size: var(--text-xs);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.error-badge.error {
  background: var(--color-danger-50);
  color: var(--color-danger-700);
}

.error-badge.warning {
  background: var(--color-warning-50);
  color: var(--color-warning-700);
}

.error-location {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

.error-content {
  font-size: var(--text-sm);
  color: var(--color-neutral-800);
  margin-bottom: var(--space-2);
}

.error-text-original {
  background: var(--color-danger-50);
  padding: 2px 4px;
  border-radius: var(--radius-sm);
  text-decoration: line-through;
}

.error-text-corrected {
  background: var(--color-success-50);
  padding: 2px 4px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.error-message {
  font-size: var(--text-xs);
  color: var(--color-neutral-600);
  line-height: var(--line-relaxed);
}

/* Section */
.section {
  margin-bottom: var(--space-10);
}

.section-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-neutral-900);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-2);
  border-bottom: 2px solid var(--color-neutral-200);
}

.section-empty {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
}

/* Foreign Language Group */
.foreign-group {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-200);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  margin-bottom: var(--space-4);
}

.foreign-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.foreign-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-primary-900);
}

.foreign-count {
  font-size: var(--text-xs);
  padding: var(--space-1) var(--space-2);
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.foreign-words {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.foreign-word {
  font-size: var(--text-xs);
  padding: var(--space-1) var(--space-2);
  background: white;
  border: 1px solid var(--color-primary-200);
  border-radius: var(--radius-sm);
  color: var(--color-primary-700);
  font-family: var(--font-mono);
}
```

---

### Step 2.4: Test UI Nuovo Sistema 🧪
**Durata**: 30 minuti

```bash
# 1. Riavvia server
python main.py

# 2. Analizza documento

# 3. Verifica report generato ha:
✅ Font leggibili (14-16px body text)
✅ Colori professionali (grigi, blu, rosso semantico)
✅ Cards compatte con shadow sottili
✅ Spacing consistente
✅ Metrics in grid
✅ Errori in cards moderne

# 4. Test responsive:
# - Ridimensiona finestra browser
# - Verifica metrics grid si adatta
# - Verifica cards mantengono leggibilità
```

---

## 🚀 FASE 3: Ottimizzazione Performance (Priority: MEDIUM)

**Durata stimata**: 2 ore  
**Obiettivo**: < 10s analisi documento 100k caratteri

### Step 3.1: Profiling Attuale
```python
# Aggiungi timing dettagliato in document_analyzer.py
import time

def analyze_document(self, ...):
    start = time.time()
    
    # ... extraction ...
    t1 = time.time()
    logger.info(f"⏱️  Extraction: {t1-start:.2f}s")
    
    # ... grammar ...
    t2 = time.time()
    logger.info(f"⏱️  Grammar: {t2-t1:.2f}s")
    
    # ... filtering ...
    t3 = time.time()
    logger.info(f"⏱️  Filtering: {t3-t2:.2f}s")
    
    # ... readability ...
    t4 = time.time()
    logger.info(f"⏱️  Readability: {t4-t3:.2f}s")
    
    total = time.time() - start
    logger.info(f"⏱️  TOTAL: {total:.2f}s")
```

### Step 3.2: Caching Migliorato
```python
# Implementa cache Redis per classificazioni linguistiche
from functools import lru_cache

class LanguageClassifier:
    @lru_cache(maxsize=10000)
    def classify_word_cached(self, word: str, context_hash: int):
        """Cache results per word+context combination"""
        return self.classify_word(word, context)
```

### Step 3.3: Batch Processing
```python
# Analizza errori in batch invece di uno alla volta
def _analyze_grammar_batch(self, text: str, batch_size: int = 100):
    """Process errors in batches for better performance"""
    lt_errors = self.languagetool_service.check_text(text)
    
    # Group by offset position
    errors_batched = [
        lt_errors[i:i+batch_size] 
        for i in range(0, len(lt_errors), batch_size)
    ]
    
    records = []
    for batch in errors_batched:
        batch_records = self._process_error_batch(batch, text)
        records.extend(batch_records)
    
    return records
```

---

## 📊 FASE 4: Testing e Validazione (Priority: CRITICAL)

**Durata stimata**: 3 ore

### Step 4.1: Unit Tests
```bash
# File: tests/test_document_analyzer.py
pytest tests/test_document_analyzer.py -v
pytest tests/test_language_classifier.py -v
```

### Step 4.2: Integration Tests
```python
# Test end-to-end completo
def test_full_analysis_pipeline():
    """Test completo: documento → analisi → report"""
    analyzer = DocumentAnalyzer()
    result = analyzer.analyze_document("test_doc.docx")
    
    # Verifica filtri applicati
    assert result.errors_count < 50, "Too many false positives"
    assert result.foreign_words_count > 200, "Foreign words not detected"
    
    # Verifica report generato
    assert Path(result.report_path).exists()
```

### Step 4.3: Performance Tests
```python
def test_performance_large_document():
    """Test performance su documento 100k+ chars"""
    import time
    
    analyzer = DocumentAnalyzer()
    start = time.time()
    result = analyzer.analyze_document("large_doc.docx")
    duration = time.time() - start
    
    assert duration < 15.0, f"Too slow: {duration}s"
```

---

## 🎯 Checklist Finale

### Funzionalità Core
- [ ] Sistema filtraggio intelligente attivo
- [ ] Latino rilevato correttamente (>90% accuracy)
- [ ] Inglese rilevato correttamente (>90% accuracy)
- [ ] Nomi propri filtrati
- [ ] Termini tecnici filtrati
- [ ] Falsi positivi < 5%

### UI/UX
- [ ] Font professionali (14-16px body)
- [ ] Colori sobri (neutral + semantici)
- [ ] Cards compatte con spacing consistente
- [ ] Metrics visibili a colpo d'occhio
- [ ] Report carica in < 2s
- [ ] Responsive design

### Performance
- [ ] Analisi < 15s per 100k chars
- [ ] Cache LRU per classificazioni
- [ ] Memory usage < 500MB
- [ ] No memory leaks

### Qualità Codice
- [ ] Type hints completi
- [ ] Docstrings su tutte le funzioni pubbliche
- [ ] Unit tests coverage > 80%
- [ ] Lint errors = 0
- [ ] No code smells (pylint score > 8.5)

---

## 📈 Metriche di Successo

### Prima
```
Tempo analisi: 15-20s
Falsi positivi: 95% (469/489)
UI Score: 3/10 (infantile)
Font size: 24-32px (troppo grande)
User satisfaction: ⭐⭐
```

### Target Dopo
```
Tempo analisi: < 10s
Falsi positivi: < 5% (< 25/489)
UI Score: 9/10 (professionale)
Font size: 14-16px (perfetto)
User satisfaction: ⭐⭐⭐⭐⭐
```

---

## 🚨 Rollback Plan

Se qualcosa va storto:

```bash
# 1. Backup code attuale
git branch backup-before-changes
git checkout -b backup-before-changes
git push origin backup-before-changes

# 2. Se serve rollback:
git checkout main
git reset --hard backup-before-changes

# 3. Restore specifico file:
git checkout backup-before-changes -- src/correttore/core/document_analyzer.py
```

---

## 🎓 Risorse e Documentazione

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Design Tokens](https://css-tricks.com/what-are-design-tokens/)
- [CSS Modern Reset](https://piccalil.li/blog/a-modern-css-reset/)
- [Python Performance](https://docs.python.org/3/library/profile.html)

---

**Next Action**: Eseguire Step 1.1 - Test Ambiente Locale ⚡
