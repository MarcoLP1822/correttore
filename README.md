# 🎯 Correttore - Enterprise Italian Text Correction System

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sistema enterprise di correzione testi italiani con AI, grammar checking e analisi di leggibilità.

## ✨ Features

- 🤖 **AI-Powered Corrections**: OpenAI GPT per correzioni intelligenti
- 📝 **Grammar Checking**: Integrazione LanguageTool
- 📊 **Readability Analysis**: Indice Gulpease per leggibilità
- 🏛️ **Historical Italian**: Supporto testi storici
- 🎯 **Quality Assurance**: Validazione enterprise-grade
- 🚀 **Performance**: Caching intelligente e processing parallelo
- 🌐 **Web Interface**: Dashboard moderna e user-friendly

## 🚀 Quick Start

### Installazione

```bash
# Clone repository
git clone https://github.com/MarcoLP1822/correttore.git
cd correttore

# Crea virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Installa pacchetto
pip install -e .

# Setup LanguageTool
python scripts/install_languagetool.py
```

### Uso Base

```bash
# Interfaccia Web (consigliato)
python -m correttore

# CLI
correttore documento.docx

# Analisi leggibilità
correttore-analyze documento.docx
```

### Uso Programmatico

```python
from correttore import CorrectionEngine, DocumentHandler

# Inizializza
engine = CorrectionEngine()
handler = DocumentHandler()

# Carica e correggi documento
doc = handler.load_document("input.docx")
result = engine.correct_document(doc)

# Salva risultato
handler.save_document(result, "output.docx")
```

## 📚 Documentazione

Documentazione completa disponibile in [`docs/`](docs/):

- 🚀 [Quick Start](docs/QUICKSTART.md) - Inizia in 5 minuti
- 📖 [Come Avviare](docs/COME_AVVIARE.md) - Guida installazione dettagliata
- 🌐 [Interfaccia Web](docs/IMPLEMENTAZIONE_WEB_LEGGIBILITA.md) - Web dashboard
- ⚙️ [Configurazione](docs/MODIFICHE_SOGLIE.md) - Personalizzazione soglie
- 🔄 [Migration v2.0](docs/MIGRATION_REPORT.md) - Report migrazione Clean Architecture
- 📋 [Indice Docs](docs/README.md) - Indice completo documentazione

## 🏗️ Architettura

Progetto organizzato secondo **Clean Architecture**:

```
correttore/
├── src/correttore/          # Package principale
│   ├── core/               # Business logic
│   ├── services/           # Servizi esterni (OpenAI, LanguageTool)
│   ├── interfaces/         # CLI, Web UI
│   ├── utils/              # Utilities
│   ├── models/             # Data models
│   └── config/             # Configurazione
├── scripts/                # Setup e utility scripts
├── tests/                  # Test suite completa
├── docs/                   # Documentazione
├── data/                   # Glossari e configurazioni
└── examples/               # File di esempio
```

## 🧪 Testing

```bash
# Tutti i test
pytest

# Con coverage
pytest --cov=correttore --cov-report=html

# Test specifici
pytest tests/unit/
pytest tests/integration/
```

## 🛠️ Development

```bash
# Installa dipendenze dev
pip install -e ".[dev]"

# Code formatting
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## 📊 Performance

- ⚡ Cache intelligente per riduzioni fino al 80% dei tempi
- 🔄 Processing parallelo per documenti grandi
- 💾 Gestione efficiente memoria
- 🎯 Quality scoring real-time

## 🤝 Contributing

Contributi benvenuti! Vedi [CONTRIBUTING.md](CONTRIBUTING.md) per dettagli.

## 📄 License

MIT License - vedi [LICENSE](LICENSE) per dettagli.

## 👥 Authors

- **Marco LP** - [GitHub](https://github.com/MarcoLP1822)

## 🙏 Acknowledgments

- OpenAI per le API GPT
- LanguageTool per grammar checking
- Comunità Python per le librerie open source

---

**Nota**: Questo è un progetto in attivo sviluppo. Per bug report e feature requests, apri una [issue](https://github.com/MarcoLP1822/correttore/issues).
