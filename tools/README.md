# Tools - Utility per Gestione Vocabolario

Questa cartella contiene **tool specifici** per la gestione e manutenzione del Nuovo Vocabolario di Base (NVdB).

---

## 📚 Script Vocabolario

### Gestione Parole

- **`add_functional_words.py`** - Aggiunge parole funzionali al vocabolario
- **`add_missing_verbs.py`** - Identifica e aggiunge verbi mancanti
- **`merge_user_txt.py`** - Merge di vocabolari utente personalizzati

### Classificazione

- **`classify_nvdb.py`** - Classifica parole per livello di disponibilità/uso
- **`extract_nvdb.py`** - Estrae subset del vocabolario per analisi

### Analisi e Verifica

- **`check_verbs.py`** - Verifica coniugazioni e forme verbali
- **`search_words.py`** - Ricerca parole nel vocabolario

### Testing

- **`test_vocabulary_integration.py`** - Test integrazione vocabolario nel sistema

### Test Runner

- **`advanced_test_runner.py`** - Test runner avanzato con report colorati
  - Test suite completa con configurazione
  - Output colorato e verbosity levels
  - Timing e performance metrics

---

## 🎯 Uso

### Esempio: Aggiungere Verbi

```bash
python tools/add_missing_verbs.py
```

### Esempio: Classificare Vocabolario

```bash
python tools/classify_nvdb.py data/vocabolario/nvdb_completo.json
```

### Esempio: Cercare Parola

```bash
python tools/search_words.py "esempio"
```

### Esempio: Test Runner Avanzato

```bash
python tools/advanced_test_runner.py --verbose --timing
```

---

## 📖 Documentazione

Per maggiori dettagli sull'integrazione del vocabolario:
- [docs/features/vocabulary.md](../docs/features/vocabulary.md)
- [docs/features/nvdb.md](../docs/features/nvdb.md)

---

## 🔧 Note per Sviluppatori

Questi tool sono **utility standalone** per manutenzione dati, non fanno parte della pipeline di correzione principale.

Per script generici del progetto, vedi: `scripts/`
