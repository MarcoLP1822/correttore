# 📚 Documentazione Correttore

Benvenuto nella documentazione completa di Correttore v2.0!

## 🚀 Per Iniziare

### Nuovi Utenti
- **[Quick Start Guide](QUICKSTART.md)** - Inizia in 5 minuti! ⚡
- **[Come Avviare](COME_AVVIARE.md)** - Guida dettagliata installazione e primo uso

### Utenti Esistenti
- **[Migration Report](MIGRATION_REPORT.md)** - Guida migrazione a v2.0 (Clean Architecture)

## 📖 Guide Utente

### Funzionalità Principali
- **[Implementazione Web Leggibilità](IMPLEMENTAZIONE_WEB_LEGGIBILITA.md)** - Interfaccia web e dashboard
- **[Modifiche Soglie](MODIFICHE_SOGLIE.md)** - Configurazione soglie correzione
- **[Changelog Gulpease](CHANGELOG_GULPEASE.md)** - Storia funzionalità Gulpease

### Analisi Leggibilità
La funzionalità di analisi leggibilità usa l'**Indice Gulpease**, formula tarata per l'italiano.

**Quick Reference Gulpease:**
- 📗 **80-100**: Molto facile (scuola elementare)
- 📘 **60-79**: Facile (scuola media)
- 📙 **40-59**: Difficile (scuola superiore)
- 📕 **0-39**: Molto difficile (università)

## 🏗️ Architettura

### Per Developer
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Come contribuire al progetto
- **[CHANGELOG.md](../CHANGELOG.md)** - Storia completa modifiche

### Struttura v2.0 (Clean Architecture)
```
src/correttore/
├── core/           # Business logic
├── services/       # Servizi esterni
├── interfaces/     # CLI & Web
├── utils/          # Utilities
└── config/         # Configurazione
```

## 📋 Documenti di Riferimento

### File nella Directory `docs/`

| File | Descrizione |
|------|-------------|
| **QUICKSTART.md** | 🚀 Guida rapida 5 minuti |
| **COME_AVVIARE.md** | 📖 Guida completa setup |
| **IMPLEMENTAZIONE_WEB_LEGGIBILITA.md** | 🌐 Web interface e dashboard |
| **MODIFICHE_SOGLIE.md** | ⚙️ Configurazione soglie |
| **CHANGELOG_GULPEASE.md** | 📝 Storia Gulpease |
| **MIGRATION_REPORT.md** | 🔄 Report migrazione v2.0 |
| **README_OLD.md** | 📜 README precedente (backup) |

### File nella Root del Progetto

| File | Descrizione |
|------|-------------|
| **README.md** | 🏠 Documentazione principale |
| **CHANGELOG.md** | 📋 Changelog completo |
| **CONTRIBUTING.md** | 🤝 Guida contributi |

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

## 🧪 Testing

```bash
# Tutti i test
pytest

# Con coverage
pytest --cov=correttore

# Test specifici
pytest tests/unit/
```

## 📊 Indice Gulpease

### Formula

```
Gulpease = 89 + (300 × N_frasi - 10 × N_lettere) / N_parole
```

Dove:
- **N_frasi**: Numero di frasi
- **N_lettere**: Numero di lettere
- **N_parole**: Numero di parole

### Interpretazione

| Punteggio | Difficoltà | Target |
|-----------|------------|--------|
| 80-100 | Molto facile | Licenza elementare |
| 60-79 | Facile | Licenza media |
| 40-59 | Difficile | Diploma superiore |
| 0-39 | Molto difficile | Laurea |

### Consigli per Migliorare

- ✍️ Usa frasi più corte
- 📝 Preferisci parole semplici
- 🎯 Evita subordinate complesse
- 💡 Dividi periodi lunghi

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

## 📞 Supporto

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/MarcoLP1822/correttore/issues)
- 💬 **Discussioni**: [GitHub Discussions](https://github.com/MarcoLP1822/correttore/discussions)
- 📧 **Email**: your.email@example.com

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
