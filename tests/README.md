# Suite di Test - Correttore Automatico

## Struttura della Suite di Test

La suite di test è organizzata per tipologia e livello di integrazione.

### 📁 tests/unit/
**Test unitari per componenti individuali**

- `test_correction.py` - Test base delle funzionalità di correzione
- `test_correction_engine.py` - Test del motore di correzione (CorrectionEngine)
- `test_document_handler.py` - Test gestione documenti Word (DocumentHandler)
- `test_gc.py` - Test integrazione Grammar Check
- `test_quality_assurance.py` - Test sistema di Quality Assurance
- `test_safe_pipeline.py` - Test pipeline di correzione sicura
- `test_validation_system.py` - Test sistema di validazione

**Copertura:** Componenti core, logica business, validazioni

### 📁 tests/integration/
**Test di integrazione tra componenti**

- `test_full_pipeline.py` - Test pipeline completa end-to-end
- `test_openai_integration.py` - Test integrazione con OpenAI API
- `test_languagetool_manager.py` - Test integrazione LanguageTool

**Copertura:** Orchestrazione componenti, workflow completi, interazioni esterne

### 📁 tests/performance/
**Test di performance e ottimizzazione**

- `test_safe_pipeline_standalone.py` - Test performance pipeline sicura

**Copertura:** Metriche di performance, ottimizzazioni, scalabilità

### 📁 tests/ (root)
**Test specifici e validazioni**

- `test_readability.py` - Test completo analisi leggibilità (Gulpease)
- `test_validation_fixes.py` - Test validazione correzioni
- `test_performance.py` - Test metriche di performance
- `test_fase4_optimization.py` - Test cache intelligente e parallelizzazione

### 📁 tools/
**Test di integrazione tool esterni**

- `test_vocabulary_integration.py` - Test integrazione servizio vocabolario

### 📁 examples/
**Script dimostrativi e esempi**

- `test_report_generator.py` - Esempio generazione report HTML

---

## Come Eseguire i Test

### Tutti i test
```bash
pytest tests/
```

### Test unitari
```bash
pytest tests/unit/
```

### Test di integrazione
```bash
pytest tests/integration/
```

### Test di performance
```bash
pytest tests/performance/
```

### Test specifico
```bash
pytest tests/unit/test_correction_engine.py
```

### Con coverage
```bash
pytest --cov=correttore --cov-report=html tests/
```

---

## Convenzioni

### Naming
- `test_*.py` - File di test
- `Test*` - Classi di test
- `test_*` - Metodi di test

### Struttura
- **Arrange** - Preparazione dati e mock
- **Act** - Esecuzione della funzione testata
- **Assert** - Verifica dei risultati

### Mock
- Utilizzare `unittest.mock` per dipendenze esterne
- Mock di API esterne (OpenAI, LanguageTool)
- Mock di I/O (file system, database)

---

## Copertura Attuale

La suite di test copre:

✅ **Core Engine**
- Motore di correzione
- Gestione documenti
- Quality Assurance
- Sistema di validazione

✅ **Servizi**
- OpenAI Service
- LanguageTool Service
- Vocabulary Service

✅ **Pipeline**
- Pipeline completa end-to-end
- Pipeline sicura anti-regressione
- Cache intelligente
- Parallelizzazione

✅ **Analisi**
- Leggibilità (Gulpease)
- Performance metrics
- Validazione correzioni

✅ **Integrazione**
- Workflow completi
- Interazioni tra componenti
- API esterne

---

## Manutenzione

### Quando aggiungere test
- ✅ Nuove funzionalità
- ✅ Bug fix (regression test)
- ✅ Refactoring significativi
- ✅ Nuove integrazioni

### Quando rimuovere test
- ❌ Test duplicati
- ❌ Test obsoleti (funzionalità rimossa)
- ❌ Test legacy di sprint/fasi precedenti
- ❌ Test manuali sostituiti da automatici

### Best Practices
1. Un test = un concetto
2. Test indipendenti (no dipendenze tra test)
3. Test deterministici (stesso input = stesso output)
4. Test veloci per unit, possono essere lenti per integration
5. Mock intelligente (non over-mocking)

---

## Note sulla Pulizia (Ottobre 2025)

### File Rimossi
**Root (16 file):**
- test_classificazione_livelli.py
- test_correction_collector.py
- test_correction_tracking.py
- test_dashboard_feedback.py
- test_feedback_integration.py
- test_feedback_unit.py
- test_feedback_system.py
- test_lemmatization_phase5.py
- test_readability_phase3.py
- test_readability_vocab_sprint2.py
- test_report_completo.py
- test_special_categories_phase7.py
- test_tracking_end_to_end.py
- test_tracking_languagetool.py
- test_vocabulary_phase4.py
- test_vocabulary_quality.py
- test_workflow_complete.py

**tests/ (15 file):**
- test_has_errors.py
- test_simple_has_errors.py
- test_endtoend.py
- test_simulazione_pipeline.py
- test_step3_pipeline_analysis.py
- test_step3_safecorrector_analysis.py
- test_scoring_only.py
- test_quick_corrections.py
- test_openai_direct.py
- test_local_fixes.py
- test_pipeline_inversion.py
- test_regressione.py
- test_api_readability.py
- test_corrections.py
- test_analisi_paragrafi.py

**Motivi:**
- Duplicazione funzionalità
- Test legacy di sprint/fasi precedenti
- Sostituiti da test migliori in tests/unit o tests/integration
- Test manuali sostituiti da automatici

### File Spostati
- `test_report_generator.py` → `examples/` (script dimostrativo)

### Risultato
Da ~50 file di test a ~15 file essenziali, mantenendo copertura completa con test più organizzati e manutenibili.
