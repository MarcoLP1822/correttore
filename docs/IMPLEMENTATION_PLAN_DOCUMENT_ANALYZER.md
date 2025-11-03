# 📋 Piano di Implementazione: Document Quality Analyzer

**Data**: 31 Ottobre 2025  
**Obiettivo**: Aggiungere analisi post-correzione per identificare problemi residui nel documento corretto  
**Approccio**: Clean Architecture + Riuso massimo del codice esistente

---

## 🎯 OBIETTIVI

### Funzionalità Principali
1. ✅ Analizzare documento corretto per errori residui
2. ✅ Calcolare metriche di leggibilità finali
3. ✅ Identificare categorie speciali (lingue straniere, nomi, parole sensibili)
4. ✅ Generare report HTML separato per analisi qualità
5. ✅ Supportare analisi standalone su qualsiasi documento

### Requisiti Non Funzionali
- ✅ Riutilizzare 85-90% del codice esistente
- ✅ Architettura pulita e manutenibile
- ✅ Zero impatto su codice esistente (backward compatibility)
- ✅ Production-ready
- ✅ Test coverage >80%

---

## 🏗️ ARCHITETTURA

### Nuovi Componenti

```
src/correttore/
├── core/
│   └── document_analyzer.py        [NUOVO - 250 righe]
├── models/
│   └── analysis_result.py          [NUOVO - 80 righe]
└── utils/
    └── analysis_report_generator.py [NUOVO - 150 righe]
```

### Componenti Riutilizzati (NO modifiche)

```
src/correttore/
├── services/
│   ├── languagetool_service.py     [RIUSO 100%]
│   ├── special_categories_service.py [RIUSO 100%]
│   └── lemmatization_service.py    [RIUSO 100%]
├── utils/
│   ├── readability.py              [RIUSO 100%]
│   └── html_report_generator.py    [RIUSO 90%]
└── core/
    ├── correction_collector.py     [RIUSO 100%]
    └── document_handler.py         [RIUSO 100%]
```

### Componenti da Modificare (modifiche minime)

```
src/correttore/
├── core/
│   └── correction_engine.py        [~15 righe: chiamata analyzer post-save]
├── interfaces/
│   ├── cli.py                      [~40 righe: nuovo comando analyze]
│   └── web_interface.py            [~60 righe: nuovo endpoint /analyze]
└── utils/
    └── html_report_generator.py    [~30 righe: parametro report_type]
```

---

## 📝 STEP-BY-STEP IMPLEMENTATION

---

### **FASE 1: Modelli di Dati** (30 min)

#### Step 1.1: Creare `models/analysis_result.py`

**File**: `src/correttore/models/analysis_result.py`  
**Righe stimate**: ~80  
**Dipendenze**: Nessuna

**Contenuto**:
```python
@dataclass
class DocumentAnalysisResult:
    """Risultato analisi qualità documento"""
    success: bool
    document_path: Path
    analysis_timestamp: datetime
    
    # Errori residui
    total_errors: int
    errors_by_category: Dict[CorrectionCategory, int]
    
    # Leggibilità
    readability_score: float
    readability_level: str
    sentences_analysis: List[SentenceReadability]
    
    # Categorie speciali
    foreign_words: List[CorrectionRecord]
    proper_nouns: List[CorrectionRecord]
    sensitive_words: List[CorrectionRecord]
    
    # Statistiche
    total_words: int
    total_paragraphs: int
    processing_time: float
    
    # Report
    report_path: Optional[Path] = None
```

**Checklist**:
- [ ] Creare file `src/correttore/models/analysis_result.py`
- [ ] Definire `DocumentAnalysisResult` dataclass
- [ ] Aggiungere metodi helper (`to_dict()`, `get_summary()`)
- [ ] Aggiornare `src/correttore/models/__init__.py` per export
- [ ] Verificare import senza errori

---

### **FASE 2: Document Analyzer Core** (2 ore)

#### Step 2.1: Creare `core/document_analyzer.py` - Struttura Base

**File**: `src/correttore/core/document_analyzer.py`  
**Righe stimate**: ~250  
**Dipendenze**: LanguageToolService, ReadabilityAnalyzer, SpecialCategoriesService

**Struttura**:
```python
class DocumentAnalyzer:
    """
    Analizza documenti per identificare problemi di qualità.
    NON applica correzioni, solo analisi.
    """
    
    def __init__(self, enable_languagetool=True, enable_readability=True, 
                 enable_special_categories=True):
        """Inizializza analyzer con servizi configurabili"""
        pass
    
    def analyze_document(self, document_path: Path, 
                        output_report: bool = True) -> DocumentAnalysisResult:
        """
        Analizza un documento completo.
        
        Workflow:
        1. Carica documento
        2. Analisi LanguageTool (errori grammaticali/ortografici)
        3. Analisi leggibilità (Gulpease, parole fuori VdB)
        4. Analisi categorie speciali (lingue, nomi, sensibili)
        5. Genera report HTML
        """
        pass
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analizza un frammento di testo (no report)"""
        pass
    
    # Metodi privati per organizzazione
    def _analyze_grammar(self, text: str) -> List[CorrectionRecord]:
        """LanguageTool analysis"""
        pass
    
    def _analyze_readability(self, text: str) -> Dict[str, Any]:
        """Readability analysis"""
        pass
    
    def _analyze_special_categories(self, text: str) -> Dict[str, List[CorrectionRecord]]:
        """Special categories analysis"""
        pass
    
    def _populate_collector(self, ...):
        """Popola CorrectionCollector per report generation"""
        pass
```

**Checklist Step 2.1**:
- [ ] Creare file `src/correttore/core/document_analyzer.py`
- [ ] Implementare `__init__` con inizializzazione servizi
- [ ] Implementare struttura `analyze_document()` (skeleton)
- [ ] Verificare import dei servizi funzionano
- [ ] Test import: `from correttore.core.document_analyzer import DocumentAnalyzer`

#### Step 2.2: Implementare Analisi LanguageTool

**Metodo**: `_analyze_grammar()`  
**Righe**: ~40

**Implementazione**:
```python
def _analyze_grammar(self, text: str) -> List[CorrectionRecord]:
    """
    Analizza errori grammaticali usando LanguageTool.
    Converte LanguageToolError in CorrectionRecord.
    """
    errors = self.languagetool_service.check_text(text)
    records = []
    
    for error in errors:
        category = self._map_lt_error_to_category(error)
        record = CorrectionRecord(
            category=category,
            source=CorrectionSource.LANGUAGETOOL,
            original_text=error.context[error.offset:error.offset+error.length],
            corrected_text=error.replacements[0] if error.replacements else None,
            context=error.context,
            # ... altri campi
        )
        records.append(record)
    
    return records
```

**Checklist Step 2.2**:
- [ ] Implementare `_analyze_grammar()`
- [ ] Implementare `_map_lt_error_to_category()` helper
- [ ] Test con testo di esempio contenente errori noti
- [ ] Verificare CorrectionRecord creati correttamente

#### Step 2.3: Implementare Analisi Leggibilità

**Metodo**: `_analyze_readability()`  
**Righe**: ~50

**Implementazione**:
```python
def _analyze_readability(self, text: str) -> Dict[str, Any]:
    """
    Analizza leggibilità usando ReadabilityAnalyzer.
    Calcola Gulpease e identifica parole fuori VdB.
    """
    # Calcolo Gulpease
    gulpease = self.readability_analyzer.calculate_gulpease(text)
    
    # Analisi per frase
    sentences = self.readability_analyzer.analyze_by_sentence(
        text, 
        vocabulary_service=self.vocabulary_service
    )
    
    # Parole fuori VdB
    words_not_in_vdb = []
    for sentence in sentences:
        words_not_in_vdb.extend(sentence.words_not_in_vdb)
    
    return {
        'gulpease_score': gulpease,
        'difficulty_level': self._map_gulpease_to_level(gulpease),
        'sentences_analysis': sentences,
        'words_not_in_vdb': list(set(words_not_in_vdb)),
        'total_difficult_words': len(set(words_not_in_vdb))
    }
```

**Checklist Step 2.3**:
- [ ] Implementare `_analyze_readability()`
- [ ] Test con testo di leggibilità mista (facile + difficile)
- [ ] Verificare calcolo Gulpease corretto
- [ ] Verificare identificazione parole fuori VdB

#### Step 2.4: Implementare Analisi Categorie Speciali

**Metodo**: `_analyze_special_categories()`  
**Righe**: ~60

**Implementazione**:
```python
def _analyze_special_categories(self, document) -> Dict[str, List[CorrectionRecord]]:
    """
    Analizza categorie speciali (lingue, nomi, sensibili).
    Riutilizza SpecialCategoriesService.
    """
    results = {
        'foreign_words': [],
        'proper_nouns': [],
        'sensitive_words': []
    }
    
    if not self.special_categories_service:
        return results
    
    # Analisi per paragrafo
    all_paragraphs = self.document_handler.extract_all_paragraphs(document)
    
    for idx, para in enumerate(all_paragraphs):
        text = para.text
        
        # Parole straniere
        foreign = self.special_categories_service.detect_foreign_words(text)
        for word, language in foreign:
            record = CorrectionRecord(
                category=CorrectionCategory.LINGUE,
                source=CorrectionSource.SYSTEM,
                original_text=word,
                context=text,
                paragraph_index=idx,
                additional_info={'language': language}
            )
            results['foreign_words'].append(record)
        
        # Nomi propri (usa lemmatization_service)
        # Parole sensibili
        # ...
    
    return results
```

**Checklist Step 2.4**:
- [ ] Implementare `_analyze_special_categories()`
- [ ] Test rilevamento lingue straniere
- [ ] Test rilevamento nomi propri
- [ ] Test rilevamento parole sensibili

#### Step 2.5: Implementare `analyze_document()` Completo

**Righe**: ~80

**Implementazione**:
```python
def analyze_document(self, document_path: Path, 
                    output_report: bool = True) -> DocumentAnalysisResult:
    """Analisi completa documento"""
    start_time = time.time()
    
    # 1. Carica documento
    document, doc_info = self.document_handler.load_document(document_path)
    
    # 2. Estrai testo completo
    full_text = self._extract_full_text(document)
    
    # 3. Analisi grammaticale
    grammar_errors = []
    if self.enable_languagetool:
        grammar_errors = self._analyze_grammar(full_text)
    
    # 4. Analisi leggibilità
    readability_data = {}
    if self.enable_readability:
        readability_data = self._analyze_readability(full_text)
    
    # 5. Analisi categorie speciali
    special_categories = {}
    if self.enable_special_categories:
        special_categories = self._analyze_special_categories(document)
    
    # 6. Popola collector per report
    self.collector = CorrectionCollector()
    self.collector.start_tracking()
    self._populate_collector(grammar_errors, special_categories)
    self.collector.stop_tracking()
    
    # 7. Genera report HTML
    report_path = None
    if output_report:
        report_path = self._generate_analysis_report(document_path)
    
    # 8. Costruisci risultato
    processing_time = time.time() - start_time
    
    return DocumentAnalysisResult(
        success=True,
        document_path=document_path,
        analysis_timestamp=datetime.now(),
        total_errors=len(grammar_errors),
        errors_by_category=self._count_by_category(grammar_errors),
        readability_score=readability_data.get('gulpease_score', 0),
        readability_level=readability_data.get('difficulty_level', 'unknown'),
        sentences_analysis=readability_data.get('sentences_analysis', []),
        foreign_words=special_categories.get('foreign_words', []),
        proper_nouns=special_categories.get('proper_nouns', []),
        sensitive_words=special_categories.get('sensitive_words', []),
        total_words=len(full_text.split()),
        total_paragraphs=doc_info.total_paragraphs,
        processing_time=processing_time,
        report_path=report_path
    )
```

**Checklist Step 2.5**:
- [ ] Implementare `analyze_document()` completo
- [ ] Implementare helper `_extract_full_text()`
- [ ] Implementare `_populate_collector()`
- [ ] Test con documento reale corretto
- [ ] Verificare tutti i campi di `DocumentAnalysisResult` popolati

---

### **FASE 3: Report Generator** (1 ora)

#### Step 3.1: Modificare `html_report_generator.py`

**File**: `src/correttore/utils/html_report_generator.py`  
**Modifiche**: ~30 righe

**Modifiche necessarie**:
```python
class HTMLReportGenerator:
    def generate_report(
        self,
        collector: CorrectionCollector,
        output_path: str,
        document_name: str = "Documento",
        standalone: bool = True,
        show_feedback_buttons: bool = False,
        report_type: str = 'correction'  # ← NUOVO parametro
    ) -> str:
        """
        Genera report HTML.
        
        Args:
            report_type: 'correction' (durante processo) o 
                        'analysis' (post-correzione)
        """
        # Adatta titoli e descrizioni in base al report_type
        if report_type == 'analysis':
            data['title'] = f"Analisi Qualità - {document_name}"
            data['report_subtitle'] = "Analisi qualità documento corretto"
        else:
            data['title'] = f"Report Correzione - {document_name}"
            data['report_subtitle'] = "Report del processo di correzione"
        
        # ... resto del codice invariato
```

**Checklist Step 3.1**:
- [ ] Aggiungere parametro `report_type` a `generate_report()`
- [ ] Adattare titoli/descrizioni in base a `report_type`
- [ ] Test generazione con `report_type='analysis'`
- [ ] Verificare backward compatibility (default='correction')

#### Step 3.2: Creare Helper `generate_analysis_report()`

**File**: `src/correttore/utils/html_report_generator.py`  
**Aggiunta**: ~20 righe

```python
def generate_analysis_report(
    collector: CorrectionCollector,
    output_path: str,
    document_name: str = "Documento",
    standalone: bool = True
) -> str:
    """
    Shortcut per generare report di analisi qualità.
    Wrapper di generate_report() con report_type='analysis'.
    """
    generator = HTMLReportGenerator()
    return generator.generate_report(
        collector=collector,
        output_path=output_path,
        document_name=document_name,
        standalone=standalone,
        show_feedback_buttons=False,
        report_type='analysis'
    )
```

**Checklist Step 3.2**:
- [ ] Aggiungere funzione `generate_analysis_report()`
- [ ] Aggiornare `__all__` in `__init__.py`
- [ ] Test chiamata da `DocumentAnalyzer`

---

### **FASE 4: Integrazione con Correction Engine** (30 min)

#### Step 4.1: Aggiungere Chiamata Post-Correzione

**File**: `src/correttore/core/correction_engine.py`  
**Modifiche**: ~15 righe  
**Posizione**: Fine del metodo `correct_document()`

**Implementazione**:
```python
class CorrectionEngine:
    def __init__(self, enable_tracking: bool = True, 
                 enable_post_analysis: bool = True):  # ← NUOVO parametro
        # ... codice esistente ...
        self.enable_post_analysis = enable_post_analysis
        
        # Inizializza analyzer se abilitato
        if self.enable_post_analysis:
            from correttore.core.document_analyzer import DocumentAnalyzer
            self.document_analyzer = DocumentAnalyzer()
    
    def correct_document(self, input_path, output_path=None) -> CorrectionResult:
        # ... codice esistente fino al salvataggio ...
        
        # Ferma tracking e genera report processo (esistente)
        if self.collector is not None:
            self.collector.stop_tracking()
            # ... report correzione esistente ...
        
        # NUOVO: Analisi post-correzione
        if self.enable_post_analysis and self.document_analyzer:
            logger.info("🔍 Running post-correction quality analysis...")
            try:
                analysis_result = self.document_analyzer.analyze_document(
                    output_path,
                    output_report=True
                )
                logger.info(f"✅ Quality analysis complete: {analysis_result.total_errors} issues found")
                logger.info(f"📊 Readability score: {analysis_result.readability_score:.1f}")
            except Exception as e:
                logger.warning(f"⚠️  Post-correction analysis failed: {e}")
        
        return CorrectionResult(...)
```

**Checklist Step 4.1**:
- [ ] Aggiungere parametro `enable_post_analysis` a `__init__`
- [ ] Inizializzare `DocumentAnalyzer` se abilitato
- [ ] Aggiungere chiamata post-save in `correct_document()`
- [ ] Test workflow completo: correzione → analisi automatica
- [ ] Verificare gestione errori (graceful degradation)

---

### **FASE 5: Interfaccia CLI** (45 min)

#### Step 5.1: Aggiungere Comando `analyze`

**File**: `src/correttore/interfaces/cli.py`  
**Aggiunta**: ~40 righe

**Implementazione**:
```python
class CorrettoreCLI:
    def analyze_document(self, document_path: Path, output_dir: Optional[Path] = None):
        """
        Analizza un documento senza applicare correzioni.
        Genera solo report di qualità.
        """
        from correttore.core.document_analyzer import DocumentAnalyzer
        
        logger.info(f"🔍 Analyzing document: {document_path}")
        
        analyzer = DocumentAnalyzer(
            enable_languagetool=True,
            enable_readability=True,
            enable_special_categories=True
        )
        
        result = analyzer.analyze_document(document_path, output_report=True)
        
        if result.success:
            logger.info("✅ Analysis complete!")
            logger.info(f"   • Total issues found: {result.total_errors}")
            logger.info(f"   • Readability score: {result.readability_score:.1f}")
            logger.info(f"   • Report: {result.report_path}")
            return result
        else:
            logger.error("❌ Analysis failed")
            return None

def main():
    parser = argparse.ArgumentParser(...)
    
    # Aggiungi subparser per analyze
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Comando correct (esistente)
    correct_parser = subparsers.add_parser('correct', help='Correct a document')
    correct_parser.add_argument('input_file', ...)
    # ... altri argomenti ...
    
    # NUOVO: Comando analyze
    analyze_parser = subparsers.add_parser('analyze', 
                                           help='Analyze document quality')
    analyze_parser.add_argument('input_file', type=str, 
                               help='Document to analyze')
    analyze_parser.add_argument('--output-dir', type=str,
                               help='Output directory for report')
    
    args = parser.parse_args()
    
    cli = CorrettoreCLI()
    
    if args.command == 'analyze':
        cli.analyze_document(Path(args.input_file), 
                           output_dir=Path(args.output_dir) if args.output_dir else None)
    elif args.command == 'correct' or not args.command:
        # ... codice esistente ...
```

**Checklist Step 5.1**:
- [ ] Aggiungere metodo `analyze_document()` a `CorrettoreCLI`
- [ ] Aggiungere subparser `analyze` al CLI
- [ ] Test comando: `python -m correttore analyze documento.docx`
- [ ] Verificare report generato correttamente
- [ ] Test con `--output-dir` personalizzato

---

### **FASE 6: Interfaccia Web** (1 ora)

#### Step 6.1: Aggiungere Endpoint `/analyze`

**File**: `src/correttore/interfaces/web_interface.py`  
**Aggiunta**: ~60 righe

**Implementazione**:
```python
@app.route('/analyze', methods=['POST'])
def analyze_document():
    """
    Endpoint per analisi documento senza correzione.
    Upload → Analisi → Report HTML
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Salva file
    filename = secure_filename(file.filename)
    input_path = app.config['UPLOAD_FOLDER'] / filename
    file.save(str(input_path))
    
    # Genera job ID
    global job_counter
    job_counter += 1
    job_id = f"analyze_{job_counter}_{int(time.time())}"
    
    # Inizializza job status
    job_status[job_id] = {
        'status': 'pending',
        'progress': 0,
        'filename': filename,
        'job_type': 'analysis',
        'created_at': datetime.now().isoformat()
    }
    
    # Avvia analisi in background
    thread = Thread(target=analyze_document_async, args=(job_id, input_path))
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': 'Analysis started'
    })

def analyze_document_async(job_id: str, input_path: Path):
    """Analizza documento in background"""
    global job_status
    
    try:
        job_status[job_id]['status'] = 'processing'
        job_status[job_id]['progress'] = 10
        
        from correttore.core.document_analyzer import DocumentAnalyzer
        
        analyzer = DocumentAnalyzer()
        
        job_status[job_id]['progress'] = 30
        
        # Output path per report
        report_path = app.config['OUTPUT_FOLDER'] / f"{input_path.stem}_analysis_report.html"
        
        result = analyzer.analyze_document(input_path, output_report=True)
        
        job_status[job_id]['progress'] = 90
        
        if result.success and result.report_path:
            job_status[job_id]['status'] = 'completed'
            job_status[job_id]['report_url'] = f"/download/{result.report_path.name}"
            job_status[job_id]['analysis_summary'] = {
                'total_errors': result.total_errors,
                'readability_score': result.readability_score,
                'readability_level': result.readability_level
            }
        else:
            job_status[job_id]['status'] = 'failed'
            job_status[job_id]['error'] = 'Analysis failed'
        
        job_status[job_id]['progress'] = 100
        job_status[job_id]['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        job_status[job_id]['status'] = 'failed'
        job_status[job_id]['error'] = str(e)
        logger.error(f"❌ Analysis failed: {e}")
```

**Checklist Step 6.1**:
- [ ] Aggiungere route `/analyze` (POST)
- [ ] Implementare `analyze_document_async()`
- [ ] Test upload e analisi via web
- [ ] Verificare job status tracking
- [ ] Test download report generato

#### Step 6.2: Aggiungere UI per Analisi

**File**: `templates/index.html` (o equivalente)  
**Aggiunta**: ~50 righe HTML

**Implementazione**:
```html
<!-- Aggiungere tab "Analizza" accanto a "Correggi" -->
<div class="tabs">
    <button class="tab-button active" onclick="showTab('correct')">
        📝 Correggi Documento
    </button>
    <button class="tab-button" onclick="showTab('analyze')">
        🔍 Analizza Qualità
    </button>
</div>

<!-- Tab Analizza (nuovo) -->
<div id="analyze-tab" class="tab-content" style="display:none;">
    <h2>🔍 Analisi Qualità Documento</h2>
    <p>Analizza un documento senza applicare correzioni.</p>
    
    <form id="analyze-form" enctype="multipart/form-data">
        <div class="upload-area" id="analyze-upload-area">
            <input type="file" id="analyze-file-input" name="file" 
                   accept=".docx,.doc,.odt" hidden>
            <label for="analyze-file-input" class="upload-label">
                📄 Clicca o trascina per caricare documento
            </label>
        </div>
        
        <button type="submit" class="btn-primary">
            🔍 Avvia Analisi
        </button>
    </form>
    
    <div id="analyze-progress" style="display:none;">
        <!-- Progress bar e status -->
    </div>
</div>

<script>
function showTab(tabName) {
    // Nascondi tutti i tab
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Mostra tab selezionato
    document.getElementById(tabName + '-tab').style.display = 'block';
    
    // Aggiorna stile pulsanti
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

// Handler submit form analisi
document.getElementById('analyze-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.job_id) {
            // Mostra progress e inizia polling
            showAnalysisProgress(data.job_id);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Errore durante analisi');
    }
});

function showAnalysisProgress(jobId) {
    // Implementazione polling status (simile a correzione)
    // ...
}
</script>
```

**Checklist Step 6.2**:
- [ ] Aggiungere tab "Analizza" nella UI
- [ ] Implementare form upload per analisi
- [ ] Implementare JavaScript per chiamata `/analyze`
- [ ] Implementare polling status job
- [ ] Test workflow completo via browser

---

### **FASE 7: Testing** (1.5 ore)

#### Step 7.1: Unit Tests - DocumentAnalyzer

**File**: `tests/unit/test_document_analyzer.py`  
**Righe**: ~200

**Test da implementare**:
```python
class TestDocumentAnalyzer(unittest.TestCase):
    
    def test_analyzer_initialization(self):
        """Test inizializzazione con configurazioni diverse"""
        pass
    
    def test_analyze_text_with_errors(self):
        """Test analisi testo con errori noti"""
        pass
    
    def test_analyze_text_clean(self):
        """Test analisi testo pulito (no errori)"""
        pass
    
    def test_readability_analysis(self):
        """Test calcolo leggibilità"""
        pass
    
    def test_special_categories_detection(self):
        """Test rilevamento lingue/nomi/sensibili"""
        pass
    
    def test_analyze_document_full_workflow(self):
        """Test workflow completo su documento reale"""
        pass
    
    def test_report_generation(self):
        """Test generazione report HTML"""
        pass
    
    def test_error_handling(self):
        """Test gestione errori (file invalido, etc)"""
        pass
```

**Checklist Step 7.1**:
- [ ] Creare `tests/unit/test_document_analyzer.py`
- [ ] Implementare tutti i test unitari
- [ ] Test coverage >80%
- [ ] Tutti i test passano

#### Step 7.2: Integration Tests

**File**: `tests/integration/test_analysis_workflow.py`  
**Righe**: ~150

**Test da implementare**:
```python
class TestAnalysisWorkflow(unittest.TestCase):
    
    def test_correction_then_analysis(self):
        """Test workflow: correzione → analisi automatica"""
        pass
    
    def test_standalone_analysis(self):
        """Test analisi standalone senza correzione"""
        pass
    
    def test_cli_analyze_command(self):
        """Test comando CLI analyze"""
        pass
    
    def test_web_analyze_endpoint(self):
        """Test endpoint web /analyze"""
        pass
```

**Checklist Step 7.2**:
- [ ] Creare `tests/integration/test_analysis_workflow.py`
- [ ] Implementare test integrazione
- [ ] Test con documenti reali
- [ ] Verificare report generati corretti

#### Step 7.3: End-to-End Tests

**Checklist**:
- [ ] Test CLI: `correttore correct test.docx` → verifica analisi automatica
- [ ] Test CLI: `correttore analyze test.docx` → verifica standalone
- [ ] Test Web: upload → correzione → verifica report analisi
- [ ] Test Web: upload → solo analisi → verifica report
- [ ] Verifica report HTML visualizzabili correttamente

---

### **FASE 8: Documentazione** (30 min)

#### Step 8.1: Aggiornare README

**File**: `README.md`  
**Aggiunta**: sezione nuova funzionalità

```markdown
### Analisi Qualità Documento

Oltre alla correzione, il sistema può analizzare la qualità di un documento:

```bash
# Analisi standalone
correttore analyze documento.docx

# Analisi automatica dopo correzione (default)
correttore correct documento.docx  # genera anche report analisi

# Disabilitare analisi post-correzione
correttore correct documento.docx --no-post-analysis
```

Il report di analisi mostra:
- ❌ Errori grammaticali/ortografici residui
- 📊 Indice di leggibilità (Gulpease)
- 🌐 Parole in lingue straniere
- 👤 Nomi propri e sigle
- 😳 Parole potenzialmente sensibili
```

**Checklist Step 8.1**:
- [ ] Aggiornare README.md
- [ ] Aggiungere esempi uso
- [ ] Aggiornare sezione Features
- [ ] Screenshots report analisi (opzionale)

#### Step 8.2: Creare Guida Utente

**File**: `docs/USER_GUIDE_ANALYSIS.md`  
**Righe**: ~150

**Contenuto**:
- Differenza tra report correzione e report analisi
- Quando usare analisi standalone
- Interpretazione risultati analisi
- FAQ

**Checklist Step 8.2**:
- [ ] Creare `docs/USER_GUIDE_ANALYSIS.md`
- [ ] Esempi pratici
- [ ] Screenshots

#### Step 8.3: Docstrings e Commenti

**Checklist**:
- [ ] Verificare docstrings complete in `document_analyzer.py`
- [ ] Commenti inline dove necessario
- [ ] Type hints completi
- [ ] Esempi uso nelle docstrings

---

### **FASE 9: Ottimizzazione e Refactoring** (1 ora)

#### Step 9.1: Performance Optimization

**Checklist**:
- [ ] Profiling `analyze_document()` su file grande (>100 pagine)
- [ ] Ottimizzare colli di bottiglia se presenti
- [ ] Cache risultati LanguageTool se ripetuti
- [ ] Parallel processing se applicabile

#### Step 9.2: Code Quality

**Checklist**:
- [ ] Lint code: `pylint src/correttore/core/document_analyzer.py`
- [ ] Format code: `black src/correttore/`
- [ ] Type check: `mypy src/correttore/core/document_analyzer.py`
- [ ] Rimuovere codice dead/commented
- [ ] Verificare naming consistente

#### Step 9.3: Error Handling

**Checklist**:
- [ ] Gestione graceful errori LanguageTool non disponibile
- [ ] Gestione file corrotto/non leggibile
- [ ] Timeout su operazioni lunghe
- [ ] Logging appropriato (info/warning/error)
- [ ] Messaggi utente chiari

---

### **FASE 10: Deploy e Validazione Finale** (30 min)

#### Step 10.1: Pre-deploy Checklist

**Checklist**:
- [ ] Tutti i test passano (unit + integration + e2e)
- [ ] Coverage >80%
- [ ] Documentazione completa
- [ ] No warning in lint/type checking
- [ ] Verificato su Python 3.8, 3.9, 3.10, 3.11

#### Step 10.2: Release Notes

**File**: `CHANGELOG.md`  
**Aggiunta**: nuova versione

```markdown
## [2.1.0] - 2025-10-31

### Added
- 🆕 **Document Quality Analyzer**: Analisi post-correzione per identificare problemi residui
- 🔍 Comando CLI `analyze` per analisi standalone
- 📊 Report HTML separato per analisi qualità
- 🌐 Endpoint web `/analyze` per analisi via interfaccia

### Changed
- CorrectionEngine ora esegue analisi automatica post-correzione (disabilitabile)
- HTMLReportGenerator supporta report_type='analysis' per report qualità

### Technical
- Nuovo modulo `core/document_analyzer.py` (~250 righe)
- Riuso 85% codice esistente (LanguageTool, Readability, SpecialCategories)
- Test coverage: 82%
- Zero breaking changes
```

**Checklist Step 10.2**:
- [ ] Aggiornare CHANGELOG.md
- [ ] Aggiornare version in `pyproject.toml`
- [ ] Git tag nuova versione
- [ ] Preparare release notes

#### Step 10.3: Validazione Finale

**Checklist**:
- [ ] Test su 5 documenti reali diversi
- [ ] Verificare report generati corretti e leggibili
- [ ] Test workflow completo: correzione → analisi
- [ ] Test analisi standalone su documento già corretto
- [ ] Performance accettabile (<2 min per 100 pagine)
- [ ] Memory usage ragionevole

---

## 📊 METRICHE DI SUCCESSO

### Quantitative
- [ ] Test coverage ≥ 80%
- [ ] Riuso codice ≥ 85%
- [ ] Nuove righe codice ≤ 500
- [ ] Performance: analisi <2 min per 100 pagine
- [ ] Zero breaking changes

### Qualitative
- [ ] Architettura pulita e manutenibile
- [ ] Documentazione completa
- [ ] User experience intuitiva
- [ ] Report chiari e informativi

---

## 🚀 STIMA TEMPI

| Fase | Tempo Stimato | Completamento |
|------|---------------|---------------|
| **FASE 1**: Modelli | 30 min | [ ] |
| **FASE 2**: Analyzer Core | 2 ore | [ ] |
| **FASE 3**: Report Generator | 1 ora | [ ] |
| **FASE 4**: Integration Engine | 30 min | [ ] |
| **FASE 5**: CLI Interface | 45 min | [ ] |
| **FASE 6**: Web Interface | 1 ora | [ ] |
| **FASE 7**: Testing | 1.5 ore | [ ] |
| **FASE 8**: Documentazione | 30 min | [ ] |
| **FASE 9**: Optimization | 1 ora | [ ] |
| **FASE 10**: Deploy | 30 min | [ ] |
| **TOTALE** | **~9.5 ore** | [ ] |

---

## 🎯 PRIORITÀ

### Must Have (P0)
- [x] DocumentAnalyzer con analisi completa
- [x] Report HTML analisi qualità
- [x] Integrazione automatica post-correzione
- [x] Test coverage base

### Should Have (P1)
- [x] Comando CLI analyze
- [x] Endpoint web /analyze
- [x] UI web per analisi
- [x] Documentazione completa

### Nice to Have (P2)
- [ ] Export report in PDF
- [ ] Confronto tra documenti (prima/dopo)
- [ ] Analisi batch multipli documenti
- [ ] Dashboard statistiche aggregate

---

## 🔧 CONFIGURAZIONE

### Variabili Ambiente (opzionali)
```bash
# Disabilita analisi post-correzione
CORRETTORE_DISABLE_POST_ANALYSIS=true

# Abilita solo alcuni analyzer
CORRETTORE_ENABLE_LANGUAGETOOL=true
CORRETTORE_ENABLE_READABILITY=true
CORRETTORE_ENABLE_SPECIAL_CATEGORIES=false
```

### File Config (config.yaml)
```yaml
analysis:
  enabled: true
  auto_after_correction: true
  components:
    languagetool: true
    readability: true
    special_categories: true
  report:
    format: html
    standalone: true
```

---

## 📝 NOTE IMPLEMENTATIVE

### Riuso Componenti Esistenti

1. **LanguageToolService** → analisi grammaticale
   - Metodo: `check_text(text: str)`
   - Output: `List[LanguageToolError]`
   - Conversione: `LanguageToolError` → `CorrectionRecord`

2. **ReadabilityAnalyzer** → analisi leggibilità
   - Metodi: `calculate_gulpease()`, `analyze_by_sentence()`
   - Output: punteggio + breakdown frasi
   - Conversione: diretta a `DocumentAnalysisResult`

3. **SpecialCategoriesService** → categorie speciali
   - Metodi: `detect_foreign_words()`, `detect_sensitive_words()`
   - Output: liste parole per categoria
   - Conversione: parole → `CorrectionRecord`

4. **CorrectionCollector** → organizzazione risultati
   - Usato per aggregare tutte le analisi
   - Alimenta `HTMLReportGenerator`

5. **HTMLReportGenerator** → generazione report
   - Riuso template esistente
   - Parametro `report_type` per adattare contenuto

### Differenze Chiave: Correction vs Analysis

| Aspetto | Correction Engine | Document Analyzer |
|---------|------------------|-------------------|
| **Input** | Documento originale | Documento qualsiasi |
| **Output** | Documento corretto | Solo report |
| **Applica modifiche** | ✅ Sì | ❌ No |
| **Tracker** | `is_applied`/`is_ignored` | Solo rilevamenti |
| **Report** | "Cosa ho fatto" | "Cosa resta da fare" |
| **Use case** | Correzione testi | Quality check |

---

## 🐛 POTENZIALI PROBLEMI E SOLUZIONI

### Problema 1: LanguageTool non disponibile
**Soluzione**: Graceful degradation, continua con altre analisi

### Problema 2: Performance su file grandi
**Soluzione**: Chunking del testo, analisi parallela

### Problema 3: Memory usage elevato
**Soluzione**: Processing streaming, cleanup dopo analisi

### Problema 4: Report troppo lungo
**Soluzione**: Paginazione, filtri, top N errori

---

## ✅ CRITERIO DI ACCETTAZIONE

L'implementazione è completa quando:

1. ✅ `DocumentAnalyzer` analizza documento completo
2. ✅ Report HTML generato correttamente
3. ✅ Analisi automatica post-correzione funziona
4. ✅ Comando CLI `analyze` funziona
5. ✅ Endpoint web `/analyze` funziona
6. ✅ Test coverage ≥ 80%
7. ✅ Zero breaking changes
8. ✅ Documentazione completa
9. ✅ Validato su 5+ documenti reali
10. ✅ Performance accettabile

---

**Fine del Piano di Implementazione**

*Prossimo step*: Iniziare FASE 1 - Creazione modelli di dati
