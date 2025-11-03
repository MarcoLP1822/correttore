# 🚀 Getting Started - Correttore v2.0

Guida completa per iniziare con il sistema di correzione testi italiano.

---

## ⚡ Setup Veloce (5 minuti)

### 1. Requisiti

- **Python >= 3.8**
- **Java >= 8** (per LanguageTool)
- **OpenAI API Key** (per correzioni avanzate)

### 2. Installazione

```bash
# Verifica Python
python --version

# Naviga nella directory del progetto
cd correttore

# Attiva virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Oppure creane uno nuovo se necessario
python -m venv .venv
.venv\Scripts\activate  # Windows

# Installa il package con tutte le dipendenze
pip install -e .

# Per sviluppatori (include pytest, mypy, ecc.)
pip install -e ".[dev]"
```

### 3. Configurazione

```bash
# Copia il file di esempio (se esiste)
cp .env.example .env

# Modifica .env con il tuo editor
nano .env
```

Aggiungi la tua **OpenAI API Key**:
```env
OPENAI_API_KEY=sk-your-key-here
```

### 4. Avvia LanguageTool

```bash
# Avvio automatico (raccomandato)
python start_languagetool.py

# Verifica che sia attivo
curl http://localhost:8081/v2/languages
```

---

## 📋 Modalità di Utilizzo

### 1. 🖥️ **Interfaccia CLI** (Linea di Comando)

#### Correzione Base
```bash
# Correzione documento singolo
python -m correttore documento.docx
# oppure (se installato)
correttore documento.docx
```

#### Opzioni Avanzate
```bash
# Con soglia qualità personalizzata
correttore documento.docx --quality-threshold 0.9

# Preview senza modifiche (dry-run)
correttore documento.docx --preview --dry-run

# Modalità specifica
correttore documento.docx --mode balanced  # fast|balanced|thorough

# Abilitare backup automatico
correttore documento.docx --backup

# Modalità batch per più documenti
correttore *.docx --batch
```

#### Help Completo
```bash
correttore --help
```

---

### 2. 🌐 **Interfaccia Web** (Raccomandato)

L'interfaccia web offre:
- ✅ Upload documenti drag & drop
- ✅ Monitoraggio in tempo reale
- ✅ Visualizzazione report interattivi
- ✅ Gestione LanguageTool integrata

#### Avvio
```bash
# Avvia il server web
python -m correttore.interfaces.web_interface
# oppure
correttore-web

# Apri nel browser
# http://localhost:5000
```

#### Funzionalità
- **Dashboard**: Overview statistiche e job attivi
- **Upload**: Carica documenti Word (.docx)
- **Analisi**: Analisi leggibilità senza correzioni
- **Correzione**: Modalità fast/balanced/thorough
- **Report**: Visualizzazione diff e statistiche
- **LanguageTool**: Start/Stop server integrato

---

### 3. 📊 **Analisi Leggibilità**

Analizza un documento senza apportare correzioni:

```bash
# CLI
correttore-analyze documento.docx

# Oppure
python -m correttore.utils.readability documento.docx
```

**Output:**
- Indice Gulpease
- Statistiche parole/frasi
- Parole difficili/rare
- Report HTML interattivo

---

### 4. 🐍 **API Python**

Usa il correttore programmaticamente:

```python
from pathlib import Path
from correttore.core.correction_engine import create_correction_engine

# Crea engine
engine = create_correction_engine()

# Correggi documento
input_path = Path("documento.docx")
output_path = Path("documento_corretto.docx")

result = engine.correct_document(
    input_path=input_path,
    output_path=output_path,
    quality_threshold=0.85
)

# Accedi ai risultati
print(f"Correzioni: {result.corrections_count}")
print(f"Quality score: {result.quality_score}")
print(f"Warnings: {result.warnings}")
```

---

## 🎯 Pipeline di Correzione

Il sistema segue questa pipeline:

```
1. Normalize → Pulizia e normalizzazione testo
2. LanguageTool → Controllo grammaticale base
3. LLM (GPT-4) → Correzione intelligente contestuale
4. LanguageTool → Verifica finale
5. Validation → Quality assurance
```

**Configurabile in** `config.yaml`:
```yaml
correction:
  pipeline: normalize_lt_llm_lt  # Pipeline attiva
  min_paragraph_length: 3
  chunk_max_tokens: 1800
  
openai:
  temperature: 0.0  # Deterministico
  max_tokens: 1200
```

---

## 🛠️ Troubleshooting

### LanguageTool non si avvia
```bash
# Verifica Java
java -version

# Verifica porta
netstat -an | findstr 8081  # Windows
lsof -i :8081               # Linux/Mac

# Kill processo se bloccato
python stop_languagetool.py
```

### Errori OpenAI
```bash
# Verifica API key
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"

# Test connessione
python -c "from openai import OpenAI; print(OpenAI().models.list())"
```

### Dipendenze mancanti
```bash
# Re-installa tutto
pip install -e . --force-reinstall

# Verifica installazione
pip list | grep -E "openai|docx|flask"
```

---

## 📚 Ulteriori Risorse

- **README.md** - Panoramica generale del progetto
- **docs/features/** - Documentazione feature specifiche
- **docs/development/** - Guide per sviluppatori
- **CHANGELOG.md** - Storia delle modifiche
- **CONTRIBUTING.md** - Come contribuire

---

## 🆘 Supporto

- **Issues**: [GitHub Issues](https://github.com/MarcoLP1822/correttore/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MarcoLP1822/correttore/discussions)
- **Email**: Marco LP <your.email@example.com>

---

**Pronto? Inizia a correggere!** 🎉

```bash
correttore-web
# Apri http://localhost:5000
```
