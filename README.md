# 🎯 Correttore - Enterprise Italian Text Correction System

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sistema enterprise di correzione testi italiani con AI, grammar checking e analisi di leggibilità.

## ✨ Features

- 🤖 **AI-Powered Corrections**: OpenAI GPT per correzioni intelligenti
- 📝 **Grammar Checking**: Integrazione LanguageTool
- 📊 **Readability Analysis**: Indice Gulpease per leggibilità
- 📋 **Report HTML Interattivi**: Report dettagliati simili a Corrige.it (NUOVO!)
- 🏛️ **Historical Italian**: Supporto testi storici
- 🎯 **Quality Assurance**: Validazione enterprise-grade
- 🚀 **Performance**: Caching intelligente e processing parallelo
- 🌐 **Web Interface**: Dashboard moderna e user-friendly

## 🎉 100% COMPLETATO! 🎊

**Tutte le 7 Fasi del Sistema Avanzato sono state implementate:**

- ✅ **FASE 1-2**: Sistema Tracking + Report HTML Interattivi
- ✅ **FASE 3**: Analisi Leggibilità GULPEASE frase per frase
- ✅ **FASE 4**: Vocabolario di Base (7.245 parole NVdB 2016)
- ✅ **FASE 5**: Lemmatizzazione e NER con spaCy
- ✅ **FASE 6**: Sistema Feedback Auto-Learning con Dashboard
- ✅ **FASE 7**: Categorie Speciali (lingue straniere + parole sensibili) 🆕

**📚 Vedi [docs/PROGETTO_100_COMPLETO.md](docs/PROGETTO_100_COMPLETO.md) per il riepilogo completo!**

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
from correttore.utils.html_report_generator import generate_orthography_report

# Inizializza
engine = CorrectionEngine()
handler = DocumentHandler()

# Carica e correggi documento
doc = handler.load_document("input.docx")
result = engine.correct_document(doc)

# Salva risultato
handler.save_document(result, "output.docx")

# Genera report HTML (NUOVO!)
if hasattr(engine, 'collector'):
    generate_orthography_report(
        engine.collector,
        "output_report.html",
        "Il Mio Documento"
    )
```

## 📚 Documentazione

La documentazione completa è disponibile nella cartella [`docs/`](docs/):

- **[PROGETTO 100% COMPLETO](docs/PROGETTO_100_COMPLETO.md)** - 🌟 Riepilogo finale tutte le fasi
- **[Quick Start](docs/QUICKSTART.md)** - Inizia in 5 minuti
- **[Come Avviare](docs/COME_AVVIARE.md)** - Setup completo e primo uso
- **[Documentazione Completa](docs/README.md)** - Indice completo guide

### Implementazioni per Fase
- [FASE 3 - Leggibilità](docs/FASE3_COMPLETATA.md)
- [FASE 5 - Lemmatizzazione](docs/FASE5_COMPLETATA.md)
- [FASE 6 - Sistema Feedback](docs/FASE6_COMPLETE.md)
- [FASE 7 - Categorie Speciali](docs/FASE7_COMPLETATA.md) 🆕
- ⚙️ [Configurazione](docs/MODIFICHE_SOGLIE.md) - Personalizzazione soglie
- 🔄 [Migration v2.0](docs/MIGRATION_REPORT.md) - Report migrazione Clean Architecture
- 📋 [Piano Implementazione](docs/IMPLEMENTATION_PLAN_REPORT_SYSTEM.md) - Roadmap completa
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
