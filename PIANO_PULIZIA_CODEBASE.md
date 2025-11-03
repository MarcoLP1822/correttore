# 🧹 PIANO DI PULIZIA E REFACTORING CODEBASE
## Analisi Completa e Roadmap di Implementazione

**Data Analisi:** 3 Novembre 2025  
**Obiettivo:** Trasformare la codebase in un'applicazione production-grade con clean architecture e DRY principles

---

## 📊 EXECUTIVE SUMMARY

### Stato Attuale
- **216 file Python** nel progetto
- **Cartella `_legacy/`** con codice duplicato obsoleto
- **Molteplici generatori di report** con funzionalità sovrapposte
- **Configurazione frammentata** (config.yaml, settings.py, pyproject.toml, requirements.txt)
- **Test duplicati e obsoleti**
- **Documentazione ridondante e obsoleta**

### Problemi Critici Identificati
🔴 **CRITICI (P0)** - Da risolvere immediatamente
🟡 **IMPORTANTI (P1)** - Da risolvare a breve termine
🟢 **MIGLIORAMENTI (P2)** - Ottimizzazioni future

---

## 🔴 PROBLEMI CRITICI (P0)

### 1. CARTELLA `_legacy/` COMPLETAMENTE DUPLICATA
**Problema:** Intera struttura parallela con codice obsoleto

```
_legacy/
├── src_core/           # Duplica src/correttore/core/
├── src_services/       # Duplica src/correttore/services/
├── src_models/         # Duplica src/correttore/models/
├── src_interfaces/     # Duplica src/correttore/interfaces/
├── src_utils/          # Duplica src/correttore/utils/
├── core_root/          # Codice legacy non utilizzato
├── services_root/      # Codice legacy non utilizzato
├── utils_root/         # Codice legacy non utilizzato
```

**Azione:**
- ✅ Verificare che nessun file attivo importi da `_legacy/`
- ✅ Creare backup completo
- 🗑️ **ELIMINARE COMPLETAMENTE** la cartella `_legacy/`

**Impatto:** Libera ~30% del codice, elimina confusione

---

### 2. FILE DUPLICATI NELLA ROOT

**Problema:** Molteplici script nella root che fanno cose simili

#### Script Debug Duplicati
```
debug_collector.py
debug_documento.py
debug_extraction.py
debug_languagetool.py
```
**Azione:** Consolidare in `tools/debug/` oppure eliminare se non più usati

#### Script LanguageTool Duplicati
```
start_languagetool.py (root)
stop_languagetool.py (root)
start_lt.bat
start_lt_temp.bat
```
**Azione:** 
- Mantenere solo gli script Python nella root
- Eliminare `.bat` files obsoleti
- Consolidare logica in `src/correttore/services/languagetool_manager.py`

#### Script Test Duplicati
```
run_tests.py (root)
scripts/run_tests.py
tools/advanced_test_runner.py
```
**Azione:** Mantenere solo `scripts/run_tests.py`, eliminare gli altri

---

### 3. GENERATORI DI REPORT MULTIPLI

**Problema:** 4 diversi moduli per generare report con funzionalità sovrapposte

```python
src/correttore/utils/report_generator.py          # 530+ righe
src/correttore/utils/reports.py                   # Report semplici
src/correttore/utils/html_report_generator.py     # 880+ righe - HTML
src/correttore/utils/readability_report_generator.py  # 1552+ righe
```

**Analisi Sovrapposizioni:**
- `report_generator.py` e `reports.py` hanno logica simile per diff/markdown
- Tutti generano statistiche di correzione in modi diversi
- Codice per formattazione markdown/HTML ripetuto

**Azione:** 
1. **Creare architettura unificata:**
   ```
   src/correttore/reporting/
   ├── __init__.py
   ├── base.py              # Abstract base classes
   ├── statistics.py        # Logica statistiche condivisa
   ├── formatters/
   │   ├── __init__.py
   │   ├── markdown.py
   │   ├── html.py
   │   └── json.py
   └── generators/
       ├── __init__.py
       ├── correction_report.py
       └── readability_report.py
   ```

2. **Eliminare duplicazioni:**
   - Estrarre logica comune in `statistics.py`
   - Template pattern per formatters
   - Strategy pattern per generators

**Impatto:** Riduzione ~40% codice report, manutenibilità ++

---

### 4. SERVIZI OPENAI DUPLICATI

**Problema:** Due moduli per gestire OpenAI con funzionalità sovrapposte

```python
src/correttore/services/openai_service.py    # Service completo
src/correttore/utils/utils_openai.py         # Funzioni utility duplicate
```

**Duplicazioni Trovate:**
- `_strip_fences()` presente in entrambi
- Logica retry/backoff duplicata
- Parsing response duplicato

**Azione:**
- Consolidare tutto in `openai_service.py`
- Eliminare `utils_openai.py`
- Migrare eventuali chiamate residue

---

### 5. CACHE DUPLICATI

**Problema:** Due sistemi di cache separati

```python
src/correttore/services/intelligent_cache.py  # Cache sofisticata con TTL
src/correttore/services/cache_llm.py         # Cache semplice JSON
```

**Azione:**
- Migrare `cache_llm.py` a usare `intelligent_cache.py`
- Deprecare e rimuovere `cache_llm.py`
- Update imports in tutti i file

---

## 🟡 PROBLEMI IMPORTANTI (P1)

### 6. CONFIGURAZIONE FRAMMENTATA

**Problema:** 4+ posti dove è definita la configurazione

```
config.yaml              # Config runtime
pyproject.toml          # Packaging e metadata
requirements.txt        # Dipendenze (DUPLICATO con pyproject.toml)
src/correttore/config/settings.py  # Config hardcoded
.env (se esiste)        # Secrets
```

**Inconsistenze Trovate:**
- `requirements.txt` ha dipendenze non in `pyproject.toml`
- `settings.py` ha valori hardcoded che dovrebbero essere in `config.yaml`
- Flask/Werkzeug versions diverse

**Azione:**
1. **Eliminare** `requirements.txt` completamente
2. **Usare solo** `pyproject.toml` per dipendenze:
   ```toml
   dependencies = [
       "openai>=1.84.0",
       "python-docx>=1.1.2",
       "pyyaml>=6.0.2",
       "flask>=3.0.0",
       "tiktoken>=0.9.0",
       "language_tool_python>=2.9.4",
       ...
   ]
   ```
3. **Refactor** `settings.py`:
   - Leggere tutto da `config.yaml`
   - Usare `pydantic.BaseSettings` per validazione
   - Supporto `.env` per secrets

---

### 7. INTERFACES DUPLICATE

**Problema:** CLI implementato in multipli posti

```python
src/correttore/interfaces/cli.py       # CLI principale
bin/correttore.py                      # Entry point
bin/analyze.py                         # Altro entry point
```

**Azione:**
- Mantenere solo `interfaces/cli.py` per logica
- `bin/correttore.py` → solo shim a cli.py
- Eliminare `bin/analyze.py`, integrare funzionalità in CLI principale

---

### 8. SCRIPT TOOLS DISORGANIZZATI

**Problema:** 10+ script in `tools/` senza organizzazione

```
tools/
├── add_functional_words.py
├── add_missing_verbs.py
├── check_verbs.py
├── classify_nvdb.py
├── extract_nvdb.py
├── merge_user_txt.py
├── search_words.py
├── test_vocabulary_integration.py
└── advanced_test_runner.py
```

**Azione:**
Organizzare per funzione:
```
tools/
├── vocabulary/
│   ├── add_functional_words.py
│   ├── add_missing_verbs.py
│   └── merge_user_txt.py
├── nvdb/
│   ├── extract_nvdb.py
│   └── classify_nvdb.py
├── testing/
│   └── advanced_test_runner.py → eliminare, usare pytest
└── utils/
    ├── check_verbs.py
    └── search_words.py
```

---

### 9. TEST DUPLICATI E OBSOLETI

**Problema:** Test con nomi simili e funzionalità sovrapposte

```python
tests/test_document_analyzer.py
tests/unit/test_document_analyzer_unit.py
tests/integration/test_analysis_workflow.py
```

**Azione:**
1. Audit completo test coverage
2. Eliminare test obsoleti
3. Consolidare test simili
4. Standardizzare naming: `test_<feature>_<scenario>.py`

---

### 10. DOCUMENTAZIONE OBSOLETA

**Problema:** Doc multipli e contraddittori

```
docs/
├── PROGETTO_100_COMPLETO.md     # Obsoleto?
├── QUICKSTART.md
├── COME_AVVIARE.md               # Duplicato di QUICKSTART?
├── archive/
│   └── migrate_to_clean_architecture.py  # File Python in docs?!
```

**Azione:**
1. **Eliminare** `archive/migrate_to_clean_architecture.py`
2. **Consolidare** QUICKSTART.md e COME_AVVIARE.md
3. **Verificare** se PROGETTO_100_COMPLETO.md è ancora attuale
4. **Creare** documentazione API con Sphinx/MkDocs

---

## 🟢 MIGLIORAMENTI (P2)

### 11. BEST PRACTICES E CODE QUALITY

#### Type Hints Mancanti
**Problema:** Inconsistenza type hints (~60% copertura)

**Azione:**
- Aggiungere type hints a tutte le funzioni pubbliche
- Usare `mypy --strict` per validazione
- Aggiungere `py.typed` marker

#### Error Handling Inconsistente
**Problema:** Mix di approcci error handling

**Azione:**
- Standardizzare su eccezioni custom da `error_handling.py`
- Logging strutturato consistente
- Circuit breaker pattern per API calls

#### Logging Non Strutturato
**Problema:** Mix di `print()` e `logging`

**Azione:**
- Sostituire tutti `print()` con `logging`
- Configurazione centralizzata logging
- Structured logging (JSON) per production

---

### 12. ARCHITETTURA E DESIGN PATTERNS

#### Dependency Injection Mancante
**Problema:** Molte dipendenze hardcoded

**Azione:**
- Implementare DI container
- Factory pattern per servizi
- Facilitare testing con mock

#### Service Layer Incompleto
**Problema:** Logica business mista con infrastruttura

**Azione:**
- Separation of concerns rigoroso
- Repository pattern per data access
- Service layer puro senza dipendenze infra

---

### 13. PERFORMANCE E SCALABILITÀ

#### Caching Non Ottimizzato
**Azione:**
- Strategia cache multi-livello
- LRU cache per funzioni pure
- Redis per cache distribuito (futuro)

#### Async/Await Inconsistente
**Azione:**
- Convertire operazioni I/O-bound a async
- Pool connections per HTTP clients
- Async context managers

---

## 📋 ROADMAP DI IMPLEMENTAZIONE

### FASE 1: PULIZIA IMMEDIATA (1-2 giorni)
**Obiettivo:** Rimuovere codice inutile e duplicati evidenti

#### Step 1.1: Eliminazione File Obsoleti
```bash
# Backup prima di tutto
git checkout -b refactor/cleanup-phase1

# 1. Eliminare _legacy/
rm -rf _legacy/

# 2. Eliminare debug scripts
rm debug_*.py

# 3. Eliminare batch files
rm start_lt*.bat

# 4. Consolidare test runners
rm run_tests.py
rm tools/advanced_test_runner.py

# 5. Commit
git add -A
git commit -m "Phase 1.1: Remove obsolete files and _legacy folder"
```

#### Step 1.2: Consolidare Configurazione
1. Eliminare `requirements.txt`
2. Consolidare tutto in `pyproject.toml`
3. Generare `requirements.txt` da pyproject:
   ```bash
   pip-compile pyproject.toml
   ```

#### Step 1.3: Verificare Build
```bash
pytest tests/
python -m correttore --help
```

**Deliverable:** Codebase ridotto ~30%, build funzionante

---

### FASE 2: CONSOLIDAMENTO SERVIZI (2-3 giorni)
**Obiettivo:** Eliminare duplicazioni in servizi e utilities

#### Step 2.1: Consolidare OpenAI Services
1. Migrare logica da `utils_openai.py` a `openai_service.py`
2. Update imports in tutti i file
3. Eliminare `utils_openai.py`
4. Test regressione

#### Step 2.2: Unificare Cache
1. Deprecare `cache_llm.py`
2. Migrare a `intelligent_cache.py`
3. Update imports
4. Test performance

#### Step 2.3: Refactor Report Generators
1. Creare `src/correttore/reporting/` package
2. Estrarre logica comune
3. Implementare base classes
4. Migrare generatori uno a uno
5. Update imports
6. Eliminare file vecchi

**Deliverable:** 4 → 1 sistema cache, 4 → 2 report generators

---

### FASE 3: ARCHITETTURA CLEAN (3-4 giorni)
**Obiettivo:** Clean architecture e best practices

#### Step 3.1: Dependency Injection
1. Implementare DI container
2. Factory functions per servizi
3. Refactor core per usare DI

#### Step 3.2: Type Hints e Mypy
1. Aggiungere type hints completi
2. Configurare mypy strict
3. Fix errori mypy progressivamente

#### Step 3.3: Error Handling Unificato
1. Audit tutti i try/except
2. Standardizzare su eccezioni custom
3. Implementare circuit breaker pattern

#### Step 3.4: Logging Strutturato
1. Configurazione centralizzata
2. Sostituire print() con logging
3. Structured logging JSON

**Deliverable:** Type safe, error handling robusto, logging production-ready

---

### FASE 4: DOCUMENTAZIONE E TEST (2-3 giorni)
**Obiettivo:** Doc aggiornata e test coverage >80%

#### Step 4.1: Consolidare Documentazione
1. Eliminare doc obsoleti
2. Unificare QUICKSTART
3. Creare API docs con Sphinx

#### Step 4.2: Test Coverage
1. Audit test esistenti
2. Eliminare test obsoleti
3. Aggiungere test mancanti
4. Target: >80% coverage

#### Step 4.3: CI/CD
1. GitHub Actions per test
2. Linting automatico
3. Coverage reports

**Deliverable:** Doc completa, test coverage >80%, CI/CD attivo

---

### FASE 5: OTTIMIZZAZIONI (2-3 giorni)
**Obiettivo:** Performance e scalabilità

#### Step 5.1: Profiling
1. Identificare bottleneck
2. Profiling con cProfile
3. Memory profiling

#### Step 5.2: Async Migration
1. Convertire I/O operations ad async
2. Connection pooling
3. Concurrent processing

#### Step 5.3: Caching Avanzato
1. Multi-level cache
2. Cache warming
3. Cache invalidation strategy

**Deliverable:** Performance +30%, memoria -20%

---

## 📊 METRICHE DI SUCCESSO

### Quantitative
- ✅ **-30%** linee di codice totali
- ✅ **-50%** duplicazioni (da rilevare con tool)
- ✅ **>80%** test coverage
- ✅ **0** errori mypy strict
- ✅ **<5** warning linting
- ✅ **+30%** performance

### Qualitative
- ✅ Architettura clean e modulare
- ✅ Codice type-safe
- ✅ Documentazione completa e aggiornata
- ✅ Deployment pronto per production
- ✅ Manutenibilità alta

---

## 🛠️ TOOLS E TECNICHE

### Static Analysis
```bash
# Duplicazioni
pylint --duplicate-code src/

# Complessità
radon cc src/ -a -nb

# Maintainability
radon mi src/ -nb

# Type checking
mypy --strict src/
```

### Coverage
```bash
pytest --cov=src/correttore --cov-report=html --cov-report=term
```

### Performance
```bash
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
```

---

## ⚠️ RISCHI E MITIGAZIONI

### Rischio 1: Breaking Changes
**Mitigazione:**
- Branch separato per ogni fase
- Test regressione dopo ogni step
- Deploy graduale

### Rischio 2: Perdita Funzionalità
**Mitigazione:**
- Audit completo prima eliminazioni
- Git history per recovery
- Feature flags per nuovo codice

### Rischio 3: Tempo Stimato Inaccurato
**Mitigazione:**
- Buffer 20% su stime
- Review dopo ogni fase
- Priorità flessibili

---

## 📝 CHECKLIST FASE 1 (QUICK WIN)

Puoi iniziare subito con questi quick wins:

- [ ] Backup completo progetto
- [ ] Eliminare cartella `_legacy/`
- [ ] Eliminare `debug_*.py` dalla root
- [ ] Eliminare `.bat` files
- [ ] Eliminare `requirements.txt`, usare solo `pyproject.toml`
- [ ] Eliminare `run_tests.py` dalla root
- [ ] Eliminare `tools/advanced_test_runner.py`
- [ ] Eliminare `docs/archive/migrate_to_clean_architecture.py`
- [ ] Consolidare `QUICKSTART.md` e `COME_AVVIARE.md`
- [ ] Run test suite per verificare nulla è rotto
- [ ] Commit: "🧹 Phase 1: Remove obsolete code and duplicates"

**Tempo stimato:** 2-3 ore  
**Impatto:** Codebase -30%, chiarezza +100%

---

## 🎯 PROSSIMI PASSI

1. **Review questo piano** con il team
2. **Approval** per procedere
3. **Iniziare Fase 1** (quick wins)
4. **Daily standup** per monitorare progresso
5. **Retrospettiva** dopo ogni fase

---

**Nota Finale:** Questo piano è ambizioso ma realizzabile. L'approccio incrementale permette di mantenere la stabilità mentre miglioriamo sistematicamente la qualità del codice. Ogni fase è indipendente e delivera valore tangibile.

**Domande? Pronto ad iniziare quando vuoi!** 🚀
