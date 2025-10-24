# 🚀 Quick Start Guide - Correttore v2.0

Guida rapida per iniziare con la nuova struttura Clean Architecture.

## ⚡ Setup Veloce (5 minuti)

### 1. Preparazione Ambiente

```bash
# Verifica Python (richiesto >= 3.8)
python --version

# Naviga nella directory del progetto
cd correttore

# Attiva virtual environment (se esiste)
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Oppure creane uno nuovo
python -m venv .venv
.venv\Scripts\activate  # Windows
```

### 2. Installazione

```bash
# Installa il package in modalità editable
pip install -e .

# Verifica installazione
python -m correttore --version
```

### 3. Configurazione

```bash
# Copia il file .env di esempio
copy .env.example .env  # Windows
# oppure
cp .env.example .env    # Linux/Mac

# Modifica .env con il tuo API key OpenAI
notepad .env  # Windows
nano .env     # Linux/Mac
```

Aggiungi la tua chiave OpenAI:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### 4. Setup LanguageTool

```bash
# Installa LanguageTool localmente
python scripts/install_languagetool.py

# Verifica installazione
python scripts/languagetool_manager.py --check
```

## 🎯 Primi Passi

### Interfaccia Web (Consigliata)

```bash
# Avvia l'interfaccia web
python -m correttore

# Apri browser a: http://localhost:5000
```

L'interfaccia web offre:
- 📤 Drag & drop file
- 📊 Dashboard real-time
- 📈 Analisi leggibilità
- 💾 Download risultati

### Correzione da CLI

```bash
# Correggi un documento
python -m correttore examples/racconto.docx

# Con opzioni
python -m correttore examples/racconto.docx \
  --mode balanced \
  --output-dir ./corrected \
  --backup

# Modalità preview (senza modifiche)
python -m correttore examples/racconto.docx --preview
```

### Analisi Leggibilità

```bash
# Analizza un documento
python bin/analyze.py examples/racconto.docx

# Esporta report
python bin/analyze.py examples/racconto.docx --export report.txt
```

## 📝 Esempi di Uso

### 1. Correzione Base

```bash
python -m correttore mio_documento.docx
```

Output:
- `mio_documento_corretto.docx` - Documento corretto
- `outputs/mio_documento_corretto_diff.md` - Report differenze
- `outputs/mio_documento_corretto_glossario.md` - Glossario nomi

### 2. Modalità Conservativa (Sicura)

```bash
python -m correttore documento.docx --mode conservative
```

Applica solo correzioni con alta confidenza.

### 3. Modalità Aggressiva (Massima Correzione)

```bash
python -m correttore documento.docx --mode aggressive
```

Applica tutte le correzioni suggerite.

### 4. Testi Storici

```bash
python -m correttore libro_storia.docx --mode historical
```

Preserva termini storici e arcaici.

### 5. Batch Processing

```bash
python -m correttore *.docx --batch
```

Processa tutti i file .docx nella directory.

## 🔧 Uso Programmatico

### Script Python

```python
from correttore import CorrectionEngine
from correttore.core.document_handler import DocumentHandler

# Setup
engine = CorrectionEngine()
handler = DocumentHandler()

# Carica documento
doc_path = "examples/racconto.docx"
doc = handler.load_document(doc_path)

# Correggi
result = engine.correct_document(doc)

# Salva
output_path = "output/corrected.docx"
handler.save_document(result, output_path)

print(f"✓ Documento corretto salvato in: {output_path}")
```

### Analisi Leggibilità Programmatica

```python
from correttore.utils.readability import ReadabilityAnalyzer

analyzer = ReadabilityAnalyzer()

text = """
Il tuo testo da analizzare.
Può essere su più righe.
"""

# Analizza
stats = analyzer.analyze(text)

# Stampa risultati
print(f"Gulpease: {stats['gulpease']}")
print(f"Difficoltà: {stats['difficulty']}")
print(f"Frasi: {stats['sentence_count']}")
print(f"Parole: {stats['word_count']}")
```

## 🎨 Modalità Correzione

### Conservative (Sicura)
- ✅ Alta confidenza richiesta
- ✅ Preserva stile originale
- ✅ Ideale per documenti sensibili
```bash
python -m correttore doc.docx --mode conservative
```

### Balanced (Equilibrata) - **Default**
- ⚖️ Bilanciamento qualità/sicurezza
- ⚖️ Correzioni moderate
- ⚖️ Uso generale
```bash
python -m correttore doc.docx --mode balanced
```

### Aggressive (Massima)
- 🚀 Tutte le correzioni suggerite
- 🚀 Riscrittura più invasiva
- 🚀 Per bozze e draft
```bash
python -m correttore doc.docx --mode aggressive
```

### Historical (Testi Storici)
- 🏛️ Preserva termini antichi
- 🏛️ Rispetta forme arcaiche
- 🏛️ Per libri di storia
```bash
python -m correttore doc.docx --mode historical
```

## 📊 Output e Report

Ogni correzione genera:

1. **Documento Corretto** (`*_corretto.docx`)
   - Testo corretto con formattazione preservata

2. **Report Diff** (`outputs/*_diff.md`)
   - Differenze tra originale e corretto
   - Evidenziazione modifiche

3. **Report Glossario** (`outputs/*_glossario.md`)
   - Nomi propri identificati
   - Frequenza d'uso

4. **Backup** (`backups/*_backup.json`)
   - Copia sicurezza originale
   - Per rollback se necessario

## 🐛 Troubleshooting

### LanguageTool non si avvia

```bash
# Reinstalla
python scripts/install_languagetool.py --force

# Verifica Java
java -version  # Richiesto Java 8+
```

### Errore API OpenAI

```bash
# Verifica chiave API
echo $OPENAI_API_KEY  # Linux/Mac
echo %OPENAI_API_KEY%  # Windows

# Testa connessione
python -c "from openai import OpenAI; print(OpenAI().models.list())"
```

### Import errors

```bash
# Reinstalla package
pip install -e . --force-reinstall

# Verifica installazione
pip show correttore
```

## 📚 Documentazione Completa

- [README.md](../README.md) - Overview completa
- [docs/COME_AVVIARE.md](../docs/COME_AVVIARE.md) - Guida dettagliata
- [docs/GUIDA_WEB_LEGGIBILITA.md](../docs/GUIDA_WEB_LEGGIBILITA.md) - Web interface
- [docs/GULPEASE.md](../docs/GULPEASE.md) - Indice Gulpease
- [CHANGELOG.md](../CHANGELOG.md) - Modifiche versione

## 💡 Tips & Tricks

### 1. Velocizza con Cache

La cache intelligente memorizza correzioni precedenti:
```bash
# Prima esecuzione: ~2 minuti
python -m correttore doc.docx

# Esecuzioni successive: ~10 secondi
python -m correttore doc.docx
```

### 2. Preview Veloce

```bash
# Vedi cosa verrebbe corretto senza modificare
python -m correttore doc.docx --preview --verbose
```

### 3. Qualità Custom

```bash
# Aumenta soglia qualità (più conservativo)
python -m correttore doc.docx --quality-threshold 0.95

# Diminuisci soglia (più aggressivo)
python -m correttore doc.docx --quality-threshold 0.70
```

### 4. Usa Configurazione File

Crea `config.yaml`:
```yaml
mode: balanced
quality_threshold: 0.85
backup: true
verbose: true
```

Poi:
```bash
python -m correttore doc.docx --config config.yaml
```

## 🚀 Prossimi Passi

1. ✅ Completa setup (sopra)
2. 📖 Leggi [documentazione completa](../docs/)
3. 🧪 Testa con file di esempio
4. 🎯 Configura per tue esigenze
5. 🔧 Personalizza glossari in `data/`
6. 📊 Monitora performance con dashboard

## 🤝 Supporto

- 📝 [Issues](https://github.com/MarcoLP1822/correttore/issues)
- 💬 [Discussions](https://github.com/MarcoLP1822/correttore/discussions)
- 📧 Email: your.email@example.com

---

**Buona correzione! 🎉**
