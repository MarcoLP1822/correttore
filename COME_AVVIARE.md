# 🚀 Guida Rapida - Come Avviare il Correttore

## 📋 Modalità di Avvio

Dopo la ristrutturazione, il **Correttore** può essere avviato in diverse modalità:

### 1. 🖥️ **Interfaccia a Linea di Comando (CLI)**

```bash
# Correzione documento singolo
python main.py documento.docx

# Con opzioni avanzate  
python main.py documento.docx --mode balanced --quality-threshold 0.9 --backup

# Preview senza modifiche
python main.py documento.docx --preview --dry-run

# Modalità batch per più documenti
python main.py *.docx --batch

# Aiuto completo
python main.py --help
```

### 2. 🌐 **Interfaccia Web (Raccomandato per uso interattivo)**

```bash
# Avvia server web
python main.py --web
# oppure
python main.py web
# oppure
python main.py server

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

## 📁 Struttura Post-Ristrutturazione

```
Correttore/
├── main.py                    # 🚀 Entry point principale
├── src/
│   ├── core/                  # Logica business
│   ├── services/              # Servizi esterni
│   ├── utils/                 # Utilità
│   └── interfaces/            # UI (CLI + Web)
├── tests/                     # Suite test completa
├── config/                    # Configurazione
├── data/                      # Glossari
├── scripts/                   # Script setup
└── tools/                     # Tool sviluppo
```

## ⚡ Esempi Pratici

### Correzione Rapida
```bash
python main.py libro.docx
```

### Correzione con Quality Control
```bash
python main.py romanzo.docx --mode aggressive --quality-threshold 0.95 --backup
```

### Modalità Demo (senza dipendenze)
```bash
python main.py documento.docx --demo-mode --preview
```

### Interfaccia Web Completa
```bash
python main.py --web
# Apri http://localhost:5000 nel browser
```

## 🛠️ Risoluzione Problemi

### Import Errors
Se vedi errori di import, assicurati di essere nella directory root:
```bash
cd C:\Users\Youcanprint1\Desktop\AI\Correttore
python main.py --help
```

### LanguageTool Non Disponibile
Il sistema funziona anche senza LanguageTool in modalità demo:
```bash
python main.py documento.docx --demo-mode
```

### Web Interface Non Si Avvia
Controlla che Flask sia installato:
```bash
pip install flask
python main.py --web
```

## 📞 Supporto

- **Help CLI**: `python main.py --help`
- **Versione**: `python main.py --version`
- **Test Sistema**: `python main.py --demo-mode test.docx --preview`

---

## 🎯 TL;DR - Comandi Essenziali

```bash
# Correzione normale
python main.py documento.docx

# Interfaccia web (raccomandato)
python main.py --web

# Preview senza modifiche
python main.py documento.docx --preview

# Aiuto completo
python main.py --help
```

**🌐 Per la migliore esperienza utente, usa: `python main.py --web`**
