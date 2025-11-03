# 📚 Documentazione Correttore

Benvenuto nella documentazione completa di **Correttore v2.0** - Sistema Enterprise di Correzione Testi Italiani.

---

## 🚀 Per Iniziare

### Nuovi Utenti
- **[Getting Started](GETTING_STARTED.md)** - Guida completa per iniziare ⚡
- **[Progetto 100% Completo](PROGETTO_100_COMPLETO.md)** - Overview completo del sistema

### Utenti Esistenti
- **[Guida Migrazione](development/migrations/migration_report.md)** - Migrazione a v2.0 (Clean Architecture)

---

## 📖 Funzionalità

Documentazione delle principali funzionalità del sistema:

### [📁 features/](features/)
- **[Document Quality Analyzer](features/document_analyzer.md)** - 🆕 Analisi qualità senza correzioni
- **[Quality Metrics Guide](features/quality_metrics.md)** - 🆕 Metriche Gulpease e Quality Rating
- **[Sistema Report](features/report_system.md)** - Sistema avanzato di reporting HTML
- **[Vocabolario (NVdB)](features/nvdb.md)** - Integrazione Nuovo Vocabolario di Base
- **[Integrazione Vocabolario](features/vocabulary.md)** - Guida tecnica sviluppatori

### Analisi Leggibilità
Sistema di analisi basato sull'**Indice Gulpease**, formula calibrata per l'italiano:

| Punteggio | Livello | Target |
|-----------|---------|--------|
| 📗 **80-100** | Molto facile | Scuola elementare |
| 📘 **60-79** | Facile | Scuola media |
| 📙 **40-59** | Difficile | Scuola superiore |
| 📕 **0-39** | Molto difficile | Università |

**🆕 Novità v2.2**: Ora puoi analizzare la qualità del documento **senza applicare correzioni**!
- Comando CLI: `correttore analyze documento.docx`
- Web UI: Button "🔍 Analizza Qualità"
- API Python: `DocumentAnalyzer().analyze_document()`

---

## 🏗️ Documentazione Tecnica

### [📁 development/](development/)

Risorse per sviluppatori:

- **[Configurazione](development/configuration.md)** - Configurazione soglie e parametri
- **[Piani Implementazione](development/implementation_plans/)** - Piani tecnici features
- **[Report Migrazioni](development/migrations/)** - Storico migrazioni e refactoring

### Architettura v2.0 (Clean Architecture)
```
src/correttore/
├── core/           # Business logic (correction engine, document handler)
├── services/       # Servizi esterni (OpenAI, LanguageTool, cache)
├── interfaces/     # CLI & Web (Flask app, CLI commands)
├── utils/          # Utilities (readability, reports, database)
├── models/         # Data models (correction tracking, feedback)
└── config/         # Configurazione (settings, env)
```

### Contribuire
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Linee guida contributi
- **[CHANGELOG.md](../CHANGELOG.md)** - Storia completa modifiche

---

## 📋 Storico Sviluppo

### [📁 changelog/](changelog/)

Cronologia completa dello sviluppo del progetto:

- **[Fase 3](changelog/fase_3.md)** - Integrazione sistema report HTML
- **[Fase 5](changelog/fase_5.md)** - Ottimizzazioni performance
- **[Fase 6](changelog/fase_6.md)** - Miglioramenti interfaccia
- **[Fase 7](changelog/fase_7.md)** - Completamento features enterprise

---

## 🎯 Stato Progetto

**Status**: ✅ 100% Completo - Sistema Enterprise Production-Ready

Per dettagli completi sullo stato del progetto e tutte le funzionalità implementate, consulta:
- **[PROGETTO 100% COMPLETO](PROGETTO_100_COMPLETO.md)** - 🎉 Riepilogo finale

---

## 🎯 Guide per Casi d'Uso

### Correzione Documenti

```bash
# Correzione base
python -m correttore documento.docx

# Con opzioni avanzate
python -m correttore documento.docx --mode balanced --backup
```

**Modalità disponibili:**
- `conservative` - Sicura, solo correzioni certe
- `balanced` - Equilibrata (default)
- `aggressive` - Massima correzione
- `historical` - Per testi storici

### Analisi Leggibilità

```bash
# Analizza documento
python bin/analyze.py documento.docx

# Con export
python bin/analyze.py documento.docx --export report.txt
```

### Interfaccia Web

```bash
# Avvia web interface
python -m correttore

# Accedi a: http://localhost:5000
```

Features web:
- 📤 Upload drag & drop
- 📊 Dashboard real-time
- 📈 Grafici leggibilità
- 💾 Download risultati

---

## 🔧 Configurazione

### File di Configurazione

- **config.yaml** - Configurazione principale
- **.env** - Variabili ambiente (API keys)
- **data/glossari/** - Glossari custom
- **data/corrections/** - Correzioni personalizzate

### Variabili Ambiente

```bash
# .env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4
MAX_TOKENS=2000
```

---

## 🧪 Testing

```bash
# Tutti i test
pytest

# Con coverage
pytest --cov=correttore

# Test specifici
pytest tests/unit/
```

---

## 📊 Indice Gulpease

### Formula

```
Gulpease = 89 + (300 × N_frasi - 10 × N_lettere) / N_parole
```

Dove:
- **N_frasi**: Numero di frasi
- **N_lettere**: Numero di lettere
- **N_parole**: Numero di parole

### Consigli per Migliorare

- ✍️ Usa frasi più corte
- 📝 Preferisci parole semplici
- 🎯 Evita subordinate complesse
- 💡 Dividi periodi lunghi

---

## 🔍 Troubleshooting

### Problemi Comuni

**LanguageTool non si avvia**
```bash
python scripts/install_languagetool.py --force
```

**Errore API OpenAI**
```bash
# Verifica chiave
echo $OPENAI_API_KEY
```

**Import errors**
```bash
pip install -e . --force-reinstall
```

### Log e Debug

```bash
# Verbose mode
python -m correttore documento.docx --verbose

# Check logs
cat migration.log
```

---

## 📞 Supporto

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/MarcoLP1822/correttore/issues)
- 💬 **Discussioni**: [GitHub Discussions](https://github.com/MarcoLP1822/correttore/discussions)

---

## 🗺️ Roadmap

### v2.1 (Prossimo)
- [ ] Supporto PDF
- [ ] API REST
- [ ] Plugin VSCode
- [ ] Batch processing avanzato

### v2.2 (Futuro)
- [ ] Machine Learning custom
- [ ] Multi-lingua
- [ ] Cloud deployment
- [ ] Mobile app

---

## 📚 Risorse Esterne

### Python & Packaging
- [Python.org](https://www.python.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 517/518](https://peps.python.org/pep-0517/)

### Clean Architecture
- [Clean Architecture Blog](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Architecting Modern Python](https://www.amazon.com/dp/1800207315)

### NLP & Linguistica
- [LanguageTool](https://languagetool.org/)
- [OpenAI Documentation](https://platform.openai.com/docs)
- [Indice Gulpease](https://it.wikipedia.org/wiki/Indice_Gulpease)

## 🏆 Credits

Sviluppato da **Marco LP** e contributors.

### Tecnologie Usate
- Python 3.8+
- OpenAI GPT
- LanguageTool
- Flask
- pytest

---

**Ultima modifica**: 24 Ottobre 2025  
**Versione**: 2.0.0

Per tornare alla [documentazione principale](../README.md)
