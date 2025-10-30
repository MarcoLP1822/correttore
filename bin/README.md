# Bin - Entry Points CLI

Questa cartella contiene **wrapper CLI** per accesso diretto agli strumenti principali del sistema.

---

## 🚀 Script Disponibili

### `correttore.py`

**Entry point principale** per il sistema di correzione.

```bash
# Avvia interfaccia web (default)
python bin/correttore.py

# Avvia CLI
python bin/correttore.py --cli

# Correzione diretta
python bin/correttore.py documento.docx
```

**Features**:
- Auto-detect interfaccia (web o CLI)
- Fallback import path per compatibilità
- Correzione file diretta

---

### `analyze.py`

**Tool di analisi leggibilità** usando indice Gulpease.

```bash
# Analizza documento
python bin/analyze.py documento.docx

# Analizza con export
python bin/analyze.py documento.docx --export report.txt

# Analizza file testo
python bin/analyze.py testo.txt
```

**Features**:
- Analisi Gulpease frase per frase
- Export report dettagliati
- Supporto .docx e .txt

---

## 🎯 Uso Alternativo

Invece di usare `bin/`, puoi anche usare gli **entry point installati**:

```bash
# Dopo pip install -e .
correttore documento.docx
correttore-cli documento.docx
correttore-analyze documento.docx
```

Gli entry point sono definiti in `pyproject.toml`.

---

## 📖 Documentazione

- [docs/QUICKSTART.md](../docs/QUICKSTART.md) - Quick start guide
- [docs/COME_AVVIARE.md](../docs/COME_AVVIARE.md) - Guida dettagliata

---

## 🔧 Note per Sviluppatori

Questi script sono **wrapper** che:
1. Configurano `sys.path` correttamente
2. Importano entry point dal pacchetto `correttore`
3. Forniscono CLI user-friendly

Per modificare la logica, edita: `src/correttore/interfaces/`
