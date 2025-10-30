# Changelog - Correttore

Tutte le modifiche importanti al progetto sono documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e il progetto aderisce a [Semantic Versioning](https://semver.org/lang/it/).

## [2.1.0] - 2025-10-27

### 🎉 FASE 7: Categorie Speciali - COMPLETATA

**100% Feature Complete** - Tutte le 7 fasi implementate e testate!

### Aggiunte

- ✨ **SpecialCategoriesService**: Rilevamento categorie speciali
  - 385 parole straniere in 7 lingue (english, latin, french, german, spanish, japanese, other)
  - 210 parole sensibili in 9 categorie (anatomia, funzioni_corporali, insulti_leggeri, parolacce, sessualità, violenza, discriminazione, volgare, doppi_sensi)
  - Integrazione NER per nomi propri automatici (Persona, Luogo, Organizzazione)
- ✨ Dizionari JSON: `data/foreign_words/common_foreign.json` e `data/sensitive_words/imbarazzanti.json`
- ✨ Popolamento automatico tabs LINGUE, IMBARAZZANTI, NOMI_SIGLE nel report HTML
- ✨ Test suite completa: `test_special_categories_phase7.py` (6/6 test passed)
- ✨ Documentazione completa: `docs/FASE7_COMPLETATA.md`

### Documentazione

- 📚 **PROGETTO_100_COMPLETO.md**: Documento master con riepilogo completo tutte le 7 fasi
- 🧹 **Pulizia documentazione**: Rimossi 10 documenti obsoleti/duplicati (-38%)
  - Eliminati: stati intermedi, riepiloghi parziali, analisi obsolete
  - Mantenuti: solo documenti essenziali e guide tecniche
-  Aggiornato `docs/README.md` con nuova struttura organizzata
- 🔄 Aggiornato `README.md` principale con link a PROGETTO_100_COMPLETO.md

### Struttura Finale Documentazione (16 file)

```
docs/
├── PROGETTO_100_COMPLETO.md          ⭐ Master document
├── Fasi: FASE3/5/6/7_COMPLETATA.md
├── Guide: QUICKSTART, COME_AVVIARE, NVDB_USAGE, etc.
└── Setup: MIGRATION_REPORT, MODIFICHE_SOGLIE
```

## [2.0.0] - 2025-10-24

### 🎯 Migrazione a Clean Architecture

Riorganizzazione completa del progetto secondo i principi di Clean Architecture.

### Aggiunte

- ✨ Struttura package moderna `src/correttore/`
- ✨ Setup completo con `setup.py` e `pyproject.toml`
- ✨ Entry point CLI: `python -m correttore`
- ✨ Lazy imports per performance migliori
- ✨ Script `bin/correttore.py` e `bin/analyze.py`
- ✨ Documentazione consolidata in `docs/`
- ✨ README.md principale rinnovato
- ✨ Migration script automatico con backup
- ✨ Cartella `examples/` per file di test
- ✨ Package installabile: `pip install -e .`

### Modifiche

- 🔄 **BREAKING**: Import path cambiano da `from src.core.*` a `from correttore.core.*`
- 🔄 Riorganizzazione completa file e directory
- 🔄 Core business logic → `src/correttore/core/`
- 🔄 Servizi esterni → `src/correttore/services/`
- 🔄 Interfacce → `src/correttore/interfaces/`
- 🔄 Utilities → `src/correttore/utils/`
- 🔄 Configurazione → `src/correttore/config/`
- 🔄 Scripts → `scripts/` (da `tools/`)
- 🔄 Documentazione → `docs/` (centralizzata)
- 🔄 Esempi → `examples/` (da `correttore files/`)

### Miglioramenti

- ⚡ Lazy loading moduli pesanti
- ⚡ Import consistenti e puliti
- ⚡ Struttura modulare migliorata
- ⚡ Dependency management chiaro
- ⚡ Testabilità aumentata
- ⚡ Manutenibilità migliorata

### Architettura

```
src/correttore/
├── core/           # Business Logic (indipendente)
├── services/       # External Services (OpenAI, LanguageTool)
├── interfaces/     # User Interfaces (CLI, Web)
├── utils/          # Shared Utilities
├── models/         # Data Models
└── config/         # Configuration
```

### Deprecato

- ⚠️ Import diretti da `core.*`, `services.*`, `utils.*` (usare `correttore.*`)
- ⚠️ `main.py` nella root (usare `bin/correttore.py` o `python -m correttore`)
- ⚠️ `analyze_readability.py` nella root (usare `bin/analyze.py`)

### Rimossi (dopo migrazione)

- ❌ Duplicazioni di `core/`, `services/`, `utils/`, `config/` nella root
- ❌ Cartella `tools/` (migrata in `scripts/`)
- ❌ "correttore files/" (migrata in `examples/`)

### Sicurezza

- 🔒 Backup automatico pre-migrazione
- 🔒 Migration log dettagliato
- 🔒 Rollback supportato

### Migration Guide

```bash
# 1. Aggiorna import nel tuo codice
# Prima:
from src.core.correttore import process_doc
from services.openai_service import OpenAIService

# Dopo:
from correttore.core.correttore import process_doc
from correttore.services.openai_service import OpenAIService

# 2. Installa il package
pip install -e .

# 3. Usa i nuovi entry point
python -m correttore documento.docx
# oppure
bin/correttore.py documento.docx
```

---

## [1.x.x] - Pre-2.0.0

Versioni precedenti alla riorganizzazione Clean Architecture.
Vedi `docs/CHANGELOG_GULPEASE.md` per dettagli su feature specifiche.

### Features principali pre-2.0.0

- Correzione automatica documenti Word
- Integrazione OpenAI GPT
- LanguageTool per grammar checking
- Analisi leggibilità (Gulpease)
- Supporto testi storici
- Web interface con dashboard
- Quality assurance system
- Intelligent caching
- Parallel processing
- Backup automatici
- Report dettagliati

---

## Formato del Changelog

### Tipi di modifiche

- **Aggiunte** - Nuove features
- **Modifiche** - Cambiamenti a features esistenti
- **Deprecato** - Features che saranno rimosse
- **Rimossi** - Features rimosse
- **Risolti** - Bug fixes
- **Sicurezza** - Vulnerabilità risolte

### Emoji Guide

- ✨ Nuove features
- 🔄 Breaking changes
- ⚡ Performance improvements
- 🐛 Bug fixes
- 📚 Documentazione
- 🔒 Sicurezza
- ⚠️ Deprecazioni
- ❌ Rimozioni

[2.0.0]: https://github.com/MarcoLP1822/correttore/releases/tag/v2.0.0
