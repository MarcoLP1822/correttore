# 🧪 Quick Test Reference - Correttore Automatico

## Comandi Rapidi

### 🚀 Esecuzione Base
```bash
# Tutti i test
pytest tests/

# Con output verbose
pytest tests/ -v

# Con output minimo
pytest tests/ -q
```

### 🎯 Test Specifici per Categoria
```bash
# Solo test unitari
pytest tests/unit/

# Solo test di integrazione  
pytest tests/integration/

# Solo test di performance
pytest tests/performance/

# Test specifico per file
pytest tests/unit/test_correction_engine.py

# Test specifico per funzione
pytest tests/unit/test_correction_engine.py::test_engine_initialization
```

### 📊 Coverage
```bash
# Coverage con report HTML
pytest --cov=correttore --cov-report=html tests/

# Coverage con report nel terminale
pytest --cov=correttore --cov-report=term-missing tests/

# Coverage solo per file specifico
pytest --cov=correttore.core.correction_engine tests/unit/test_correction_engine.py
```

### 🏃 Test Veloci
```bash
# Stop al primo errore
pytest tests/ -x

# Stop dopo N errori
pytest tests/ --maxfail=3

# Solo test non slow
pytest tests/ -m "not slow"

# Solo test senza chiamate API
pytest tests/ -m "not api"
```

### 🔍 Debug e Analisi
```bash
# Con print() visibili
pytest tests/ -s

# Con pdb al primo errore
pytest tests/ --pdb

# Con traceback completo
pytest tests/ --tb=long

# Con traceback minimo
pytest tests/ --tb=short

# Solo mostra quali test verranno eseguiti (senza eseguirli)
pytest tests/ --collect-only
```

### 🎨 Output Personalizzato
```bash
# Output colorato
pytest tests/ --color=yes

# Output in una riga per test
pytest tests/ --tb=line

# Mostra i test più lenti
pytest tests/ --durations=10

# Mostra tutti i test con durata
pytest tests/ --durations=0
```

### 🔄 Ri-esecuzione
```bash
# Ri-esegui solo i test falliti
pytest tests/ --lf

# Ri-esegui prima i test falliti, poi gli altri
pytest tests/ --ff
```

### 🏷️ Markers
```bash
# Solo test unitari (se marcati)
pytest tests/ -m unit

# Solo test di integrazione (se marcati)
pytest tests/ -m integration

# Solo test lenti
pytest tests/ -m slow

# Escludi test lenti
pytest tests/ -m "not slow"

# Combinazioni
pytest tests/ -m "unit and not slow"
```

### 📝 Report
```bash
# Report in formato JUnit XML (per CI/CD)
pytest tests/ --junitxml=report.xml

# Report HTML
pytest tests/ --html=report.html --self-contained-html
```

### 🔧 Script Helper

#### Windows (PowerShell)
```powershell
# Tutti i test
.\run_tests.ps1

# Test unitari
.\run_tests.ps1 unit

# Test integrazione
.\run_tests.ps1 integration

# Test performance
.\run_tests.ps1 performance

# Test con coverage
.\run_tests.ps1 coverage

# Test veloci (no API)
.\run_tests.ps1 fast

# Quick test (stop al primo errore)
.\run_tests.ps1 quick
```

#### Python (Cross-platform)
```bash
# Tutti i test
python run_tests.py

# Test unitari
python run_tests.py unit

# Test integrazione
python run_tests.py integration

# Test performance
python run_tests.py performance

# Test con coverage
python run_tests.py coverage

# Test veloci (no API)
python run_tests.py fast

# Quick test (stop al primo errore)
python run_tests.py quick
```

---

## 📁 Struttura dei Test

```
tests/
├── unit/              # Test unitari (7 file)
│   ├── test_correction.py
│   ├── test_correction_engine.py
│   ├── test_document_handler.py
│   ├── test_gc.py
│   ├── test_quality_assurance.py
│   ├── test_safe_pipeline.py
│   └── test_validation_system.py
│
├── integration/       # Test integrazione (3 file)
│   ├── test_full_pipeline.py
│   ├── test_openai_integration.py
│   └── test_languagetool_manager.py
│
├── performance/       # Test performance (1 file)
│   └── test_safe_pipeline_standalone.py
│
├── fixtures/          # Dati di test
│   └── test_texts.py
│
├── conftest.py        # Configurazione pytest
└── README.md          # Documentazione completa
```

---

## 🎯 Workflow Consigliati

### Sviluppo Locale
```bash
# 1. Prima di committare: test veloci unitari
pytest tests/unit/ -x

# 2. Verifica completa pre-commit
pytest tests/ -x -m "not slow"

# 3. Test completo periodico
pytest tests/
```

### CI/CD
```bash
# 1. Test veloci per ogni push
pytest tests/unit/ --junitxml=report.xml

# 2. Test completi per PR
pytest tests/ --junitxml=report.xml --cov=correttore --cov-report=xml

# 3. Test notturni con performance
pytest tests/ --durations=0 --cov=correttore --cov-report=html
```

### Debug
```bash
# 1. Esegui solo il test problematico
pytest tests/unit/test_correction_engine.py::test_engine_initialization -s

# 2. Aggiungi print() nel test
pytest tests/unit/test_correction_engine.py -s

# 3. Usa debugger se necessario
pytest tests/unit/test_correction_engine.py --pdb
```

---

## 💡 Tips & Tricks

### 1. Test Parametrizzati
```python
@pytest.mark.parametrize("input,expected", [
    ("test", "test"),
    ("Test", "test"),
])
def test_lowercase(input, expected):
    assert input.lower() == expected
```

### 2. Skip Test Condizionali
```python
@pytest.mark.skipif(sys.platform == "win32", reason="Non supportato su Windows")
def test_unix_only():
    pass
```

### 3. Expected Failures
```python
@pytest.mark.xfail(reason="Bug noto #123")
def test_known_bug():
    assert False
```

### 4. Custom Markers
```python
@pytest.mark.slow
def test_long_running():
    pass
```

### 5. Fixtures con Scope
```python
@pytest.fixture(scope="module")
def expensive_resource():
    # Setup una volta per modulo
    yield resource
    # Cleanup
```

---

## 📚 Risorse

- **Documentazione Pytest:** https://docs.pytest.org/
- **README Suite Test:** `tests/README.md`
- **Configurazione:** `pytest.ini`
- **Fixtures Comuni:** `tests/conftest.py`

---

**Last Updated:** 27 Ottobre 2025
