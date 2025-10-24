# 🤝 Contributing to Correttore

Grazie per l'interesse nel contribuire a Correttore! Questo documento fornisce linee guida per contribuire al progetto.

## 📋 Indice

- [Code of Conduct](#code-of-conduct)
- [Come Contribuire](#come-contribuire)
- [Setup Sviluppo](#setup-sviluppo)
- [Architettura](#architettura)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## 📜 Code of Conduct

Questo progetto aderisce a un Code of Conduct. Partecipando, ti impegni a rispettarlo.

### Principi Base

- 🤝 Sii rispettoso e inclusivo
- 💬 Comunicazione costruttiva
- 🎯 Focus su ciò che è meglio per la community
- 🌟 Mostra empatia verso altri membri

## 🚀 Come Contribuire

### Tipi di Contributi Benvenuti

1. **🐛 Bug Reports**
   - Usa GitHub Issues
   - Include passi per riprodurre
   - Specifica versione Python e OS

2. **✨ Feature Requests**
   - Discuti prima nelle Issues
   - Spiega use case
   - Proponi implementazione

3. **📝 Documentation**
   - Fix typos
   - Migliora chiarezza
   - Aggiungi esempi

4. **💻 Code Contributions**
   - Bug fixes
   - Nuove features
   - Performance improvements

5. **🧪 Testing**
   - Aggiungi test cases
   - Migliora coverage
   - Test integration

## 🛠️ Setup Sviluppo

### 1. Fork e Clone

```bash
# Fork su GitHub
# Poi clona il tuo fork
git clone https://github.com/TUO_USERNAME/correttore.git
cd correttore

# Aggiungi upstream remote
git remote add upstream https://github.com/MarcoLP1822/correttore.git
```

### 2. Setup Ambiente

```bash
# Crea virtual environment
python -m venv .venv

# Attiva
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Installa in modalità dev
pip install -e ".[dev]"

# Installa pre-commit hooks
pip install pre-commit
pre-commit install
```

### 3. Setup LanguageTool

```bash
python scripts/install_languagetool.py
```

### 4. Configura Ambiente

```bash
# Copia .env.example
cp .env.example .env

# Configura chiave OpenAI per testing
# Usa una chiave di test o mock
```

## 🏗️ Architettura

Il progetto segue **Clean Architecture**:

```
src/correttore/
├── core/           # Business Logic (NO dipendenze esterne)
│   ├── correttore.py         # Main correction engine
│   ├── safe_correction.py    # Safe correction system
│   ├── validation.py         # Validation logic
│   └── ...
│
├── services/       # External Services (dipendono da core)
│   ├── openai_service.py     # OpenAI integration
│   ├── languagetool_service.py
│   ├── intelligent_cache.py
│   └── ...
│
├── interfaces/     # User Interfaces (dipendono da tutto)
│   ├── cli.py                # Command line
│   ├── web_interface.py      # Web UI
│   └── dashboard.py          # Dashboard
│
├── utils/          # Shared Utilities
│   ├── readability.py
│   ├── text_processing.py
│   └── ...
│
├── models/         # Data Models
│   └── ...
│
└── config/         # Configuration
    └── settings.py
```

### Dependency Rule

**Fondamentale**: Le dipendenze vanno **solo verso l'interno**

```
interfaces → services → core
     ↓          ↓         ↓
   utils ← ← ← ← ← ← ← ←
```

- ✅ `interfaces` può importare da `core`, `services`, `utils`
- ✅ `services` può importare da `core`, `utils`
- ✅ `core` può importare solo da `utils`
- ❌ `core` NON può importare da `services` o `interfaces`

## 📏 Coding Standards

### Style Guide

Seguiamo **PEP 8** con alcune personalizzazioni:

```python
# Line length: 100 caratteri
# Usa Black per formatting automatico
black src/

# Type hints dove sensato
def process_text(text: str, mode: str = "balanced") -> CorrectionResult:
    pass

# Docstrings Google Style
def complex_function(param1: str, param2: int) -> bool:
    """
    Breve descrizione su una riga.
    
    Descrizione più dettagliata se necessaria.
    Può essere su più righe.
    
    Args:
        param1: Descrizione parametro 1
        param2: Descrizione parametro 2
        
    Returns:
        True se successo, False altrimenti
        
    Raises:
        ValueError: Se param1 è vuoto
    """
    pass
```

### Import Order

```python
# 1. Standard library
import os
import sys
from pathlib import Path

# 2. Third party
import yaml
from openai import OpenAI

# 3. Local application
from correttore.core.correttore import process_doc
from correttore.services.openai_service import OpenAIService
```

### Naming Conventions

```python
# Classes: PascalCase
class CorrectionEngine:
    pass

# Functions/variables: snake_case
def process_document(file_path):
    correction_result = ...
    
# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_TIMEOUT = 30

# Private: _leading_underscore
def _internal_helper():
    pass
```

## 🧪 Testing

### Running Tests

```bash
# Tutti i test
pytest

# Con coverage
pytest --cov=correttore --cov-report=html

# Test specifici
pytest tests/unit/
pytest tests/integration/
pytest tests/test_readability.py

# Test singolo
pytest tests/unit/test_correction_engine.py::TestCorrectionEngine::test_basic_correction
```

### Writing Tests

```python
# tests/unit/test_my_feature.py
import pytest
from correttore.core.my_module import MyClass

class TestMyClass:
    """Test suite per MyClass"""
    
    def setup_method(self):
        """Setup eseguito prima di ogni test"""
        self.instance = MyClass()
    
    def test_basic_functionality(self):
        """Test funzionalità base"""
        result = self.instance.do_something("input")
        assert result == "expected"
    
    def test_error_handling(self):
        """Test gestione errori"""
        with pytest.raises(ValueError):
            self.instance.do_something(None)
    
    @pytest.mark.parametrize("input,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test casi multipli"""
        assert self.instance.do_something(input) == expected
```

### Test Coverage

Miriamo a:
- **Overall**: >80%
- **Core modules**: >90%
- **Critical paths**: 100%

## 📤 Pull Request Process

### 1. Crea Feature Branch

```bash
# Aggiorna main
git checkout main
git pull upstream main

# Crea branch
git checkout -b feature/my-new-feature
# o
git checkout -b fix/bug-description
```

### 2. Sviluppa

```bash
# Fai modifiche
# Testa localmente
pytest

# Commit frequenti
git add .
git commit -m "feat: add new feature X"

# Usa Conventional Commits
# feat: nuova feature
# fix: bug fix
# docs: documentazione
# test: aggiunta test
# refactor: refactoring
# perf: performance improvement
```

### 3. Push e PR

```bash
# Push al tuo fork
git push origin feature/my-new-feature

# Apri PR su GitHub
# - Descrizione chiara
# - Riferimenti a issues
# - Screenshot se UI
```

### 4. Code Review

- ✅ Rispondi ai commenti
- ✅ Fai modifiche richieste
- ✅ Mantieni PR aggiornata con main

```bash
# Aggiorna con upstream
git fetch upstream
git rebase upstream/main
git push --force-with-lease
```

### PR Checklist

- [ ] Test passano localmente
- [ ] Nuovi test aggiunti per nuove feature
- [ ] Documentazione aggiornata
- [ ] Changelog aggiornato (se applicabile)
- [ ] Code segue style guide
- [ ] No breaking changes (o ben documentati)
- [ ] Commits seguono Conventional Commits

## 📝 Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: Nuova feature
- `fix`: Bug fix
- `docs`: Solo documentazione
- `style`: Formatting, no code change
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Aggiunta test
- `chore`: Build, config, etc

### Esempi

```
feat(core): add support for PDF documents

Implement PDF text extraction and correction.
Supports both text-based and OCR PDFs.

Closes #123
```

```
fix(services): handle OpenAI rate limits

Add exponential backoff for rate limit errors.
Improves reliability under high load.
```

## 🐛 Bug Reports

Template per bug report:

```markdown
**Descrizione**
Breve descrizione del bug.

**Come Riprodurre**
1. Vai a '...'
2. Esegui '....'
3. Vedi errore

**Comportamento Atteso**
Cosa dovrebbe succedere.

**Comportamento Attuale**
Cosa succede invece.

**Screenshots**
Se applicabile.

**Ambiente**
- OS: [Windows 11 / Ubuntu 22.04 / macOS 13]
- Python: [3.10.5]
- Versione Correttore: [2.0.0]

**Log/Errori**
```
Paste error logs here
```

**Contesto Aggiuntivo**
Altre informazioni utili.
```

## ✨ Feature Requests

Template per feature request:

```markdown
**Feature Richiesta**
Breve descrizione della feature.

**Problema da Risolvere**
Quale problema risolve questa feature?

**Soluzione Proposta**
Come dovrebbe funzionare?

**Alternative Considerate**
Altre soluzioni possibili?

**Use Case**
Esempi concreti di utilizzo.

**Priorità**
Low / Medium / High
```

## 📚 Risorse Utili

### Documentazione

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [PEP 8](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [pytest docs](https://docs.pytest.org/)

### Tools

- [Black](https://black.readthedocs.io/) - Code formatting
- [mypy](https://mypy.readthedocs.io/) - Type checking
- [flake8](https://flake8.pycqa.org/) - Linting
- [pre-commit](https://pre-commit.com/) - Git hooks

## 🙏 Grazie!

Ogni contributo è prezioso, grande o piccolo. Grazie per aiutarci a migliorare Correttore!

## 📞 Contatti

- **Issues**: [GitHub Issues](https://github.com/MarcoLP1822/correttore/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MarcoLP1822/correttore/discussions)
- **Email**: your.email@example.com

---

**Happy Coding! 🚀**
