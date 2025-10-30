# 🚀 Guida Rapida - Come Avviare il Correttore

## 📋 Modalità di Avvio

Dopo la migrazione a Clean Architecture (v2.0), il **Correttore** può essere avviato in diverse modalità:

### 1. 🖥️ **Interfaccia a Linea di Comando (CLI)**

```bash
# Correzione documento singolo
python -m correttore documento.docx
# oppure
correttore documento.docx

# Con opzioni avanzate  
correttore documento.docx --mode balanced --quality-threshold 0.9 --backup

# Preview senza modifiche
correttore documento.docx --preview --dry-run

# Modalità batch per più documenti
correttore *.docx --batch

# Aiuto completo
correttore --help
```

### 2. 🌐 **Interfaccia Web (Raccomandato per uso interattivo)**

```bash
# Avvia server web
python -m correttore
# oppure
python -m correttore --web

# Accesso: http://localhost:5000
```

**Features Web Interface:**
- ✅ Upload documenti drag & drop
- ✅ Processamento real-time con progress bar
- ✅ Dashboard monitoring integrato
- ✅ Download automatico risultati
- ✅ Job tracking completo

### 3. 📊 **Dashboard di Monitoring**

Una volta avviata l'interfaccia web, accedi a:
- **Main Interface**: http://localhost:5000
- **Dashboard Analytics**: http://localhost:5000/dashboard

## 🔧 Modalità di Correzione

| Modalità | Descrizione | Quando Usare |
|----------|-------------|--------------|
| `conservative` | Correzioni sicure e minimali | Documenti formali, testi legali |
| `balanced` | Equilibrio tra sicurezza e miglioramenti | **Default - uso generale** |
| `aggressive` | Correzioni più estese | Bozze, testi informali |
| `historical` | Ottimizzato per libri storici | Testi storici, narrativa |

## 📁 Struttura Post-Migrazione (v2.0)

```
Correttore/
├── src/correttore/            # 🚀 Package principale
│   ├── core/                  # Logica business
│   ├── services/              # Servizi esterni
│   ├── utils/                 # Utilità
│   ├── interfaces/            # UI (CLI + Web)
│   ├── models/                # Data models
│   └── config/                # Configurazione
├── tests/                     # Suite test completa
├── data/                      # Glossari
├── scripts/                   # Script setup
├── docs/                      # Documentazione
├── examples/                  # Esempi di utilizzo
└── bin/                       # Launcher scripts
```

## ⚡ Esempi Pratici

### Correzione Rapida
```bash
correttore libro.docx
```

### Correzione con Quality Control
```bash
correttore romanzo.docx --mode aggressive --quality-threshold 0.95 --backup
```

### Analisi Leggibilità
```bash
correttore-analyze documento.docx
# oppure
python bin/analyze.py documento.docx
```

### Interfaccia Web Completa
```bash
python -m correttore
# Apri http://localhost:5000 nel browser
```

## 🛠️ Risoluzione Problemi

### Import Errors
Se vedi errori di import, reinstalla il package:
```bash
cd C:\Users\Youcanprint1\Desktop\AI\Correttore
pip install -e .
correttore --help
```

### LanguageTool Non Disponibile
Installa LanguageTool con lo script dedicato:
```bash
python scripts/install_languagetool.py
```

### Web Interface Non Si Avvia
Controlla che Flask sia installato:
```bash
pip install flask
python -m correttore
```

## 📞 Supporto

- **Help CLI**: `correttore --help`
- **Versione**: `correttore --version` o `python -m correttore --version`
- **Documentazione**: Vedi [docs/README.md](README.md)

---

## 🎯 TL;DR - Comandi Essenziali

```bash
# Correzione normale
correttore documento.docx

# Interfaccia web (raccomandato)
python -m correttore

# Analisi leggibilità
correttore-analyze documento.docx

# Aiuto completo
correttore --help
```

**🌐 Per la migliore esperienza utente, usa: `python -m correttore`**
