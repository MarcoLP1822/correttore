# Nuovo Vocabolario di Base (NVdB) - Guida d'Uso

## 📚 Cosa abbiamo estratto

Dal PDF `correttore files/nuovovocabolariodibase.pdf` sono state estratte **6.388 parole** del Nuovo Vocabolario di Base della lingua italiana (2016) di Tullio De Mauro.

## 📁 File creati

### `data/vocabolario/nvdb_parole.json`
**Uso: rapido caricamento nel correttore**
- Lista semplice di tutte le parole
- Formato: `["parola1", "parola2", ...]`
- Veloce da caricare e usare per controlli

### `data/vocabolario/nvdb_completo.json`
**Uso: gestione completa con metadata**
- Struttura completa con metadata
- Include campo `livello` per ogni parola (attualmente `null`)
- Include campo `note` per annotazioni
- Statistiche di classificazione

Struttura:
```json
{
  "metadata": {
    "nome": "Nuovo Vocabolario di Base della lingua italiana",
    "autore": "Tullio De Mauro",
    "anno": 2016,
    "totale_parole": 6388,
    "livelli": {
      "fondamentale": {"count": 0, ...},
      "alto_uso": {"count": 0, ...},
      "alta_disponibilita": {"count": 0, ...},
      "non_classificato": {"count": 6388, ...}
    }
  },
  "vocabolario": {
    "parola": {
      "livello": null,
      "note": ""
    }
  }
}
```

### `data/vocabolario/nvdb_parole.txt`
**Uso: editing manuale facile**
- Una parola per riga
- Facile da editare manualmente
- Utile per comparazioni

### `data/vocabolario/nvdb_da_classificare.txt`
**Uso: template per classificazione manuale**
- Formato: `parola|livello`
- Prime 50 parole come esempio
- Da usare per importazione massiva

## 🔧 Tool disponibili

### 1. Estrazione (già eseguito)
```bash
python tools/extract_nvdb.py
```
Estrae tutte le parole dal PDF e crea i file iniziali.

### 2. Classificazione

#### Mostra statistiche
```bash
python tools/classify_nvdb.py stats
```

#### Classificazione interattiva
```bash
python tools/classify_nvdb.py interactive
```
Modalità guidata per classificare parole una per una.

#### Classifica singola parola
```bash
python tools/classify_nvdb.py classify <parola> <livello>
```
Esempio:
```bash
python tools/classify_nvdb.py classify casa fondamentale
python tools/classify_nvdb.py classify abbastanza alto_uso
python tools/classify_nvdb.py classify forbice alta_disponibilita
```

#### Importa classificazioni da file
```bash
python tools/classify_nvdb.py import <file>
```
Il file deve avere formato:
```
# Commenti iniziano con #
casa|fondamentale
essere|fondamentale
avere|fondamentale
abbastanza|alto_uso
forbice|alta_disponibilita
```

#### Esporta per livello
```bash
python tools/classify_nvdb.py export
```
Crea file separati in `data/vocabolario/levels/`:
- `fondamentale.txt`
- `alto_uso.txt`
- `alta_disponibilita.txt`
- `non_classificato.txt`

## 📊 I tre livelli del NVdB

Dal PDF originale:

### 1. **Fondamentale** (≈2.000 parole)
- Parole più frequenti in assoluto della lingua italiana
- Es: essere, avere, fare, dire, casa, giorno, ecc.

### 2. **Alto uso** (≈2.750 parole)
- Parole ancora molto frequenti
- Es: abbastanza, accettare, accompagnare, ecc.

### 3. **Alta disponibilità** (≈2.337 parole)
- Parole comuni nel parlato ma rare nello scritto
- Es: forbice, abbronzare, zanzara, ecc.

## 💡 Come usare nel correttore

### Caricamento veloce (solo controllo presenza)
```python
import json

# Carica lista semplice
with open('data/vocabolario/nvdb_parole.json', 'r', encoding='utf-8') as f:
    nvdb_words = set(json.load(f))

# Verifica se una parola è nel vocabolario
if word.lower() in nvdb_words:
    print("Parola nel NVdB ✓")
```

### Caricamento completo (con livelli)
```python
import json

# Carica struttura completa
with open('data/vocabolario/nvdb_completo.json', 'r', encoding='utf-8') as f:
    nvdb = json.load(f)

# Verifica parola e ottieni livello
word = "casa"
if word in nvdb['vocabolario']:
    level = nvdb['vocabolario'][word]['livello']
    if level == 'fondamentale':
        print("Parola molto comune ✓")
    elif level == 'alto_uso':
        print("Parola frequente ✓")
    elif level == 'alta_disponibilita':
        print("Parola comune nel parlato ✓")
    else:
        print("Parola nel vocabolario (livello non classificato)")
```

## 🎯 Possibili utilizzi nel progetto

### 1. **Miglioramento correzione ortografica**
- Parola nel NVdB → probabilmente corretta
- Parola NON nel NVdB → potrebbe essere errore o termine tecnico
- Riduce falsi positivi

### 2. **Analisi leggibilità avanzata**
Oltre a GULPEASE, calcolare:
```python
def calcola_metriche_nvdb(testo, nvdb_words):
    parole = estrai_parole(testo)
    in_nvdb = sum(1 for p in parole if p.lower() in nvdb_words)
    percentuale = (in_nvdb / len(parole)) * 100
    
    return {
        'percentuale_nvdb': percentuale,
        'parole_difficili': len(parole) - in_nvdb
    }
```

### 3. **Suggerimenti intelligenti**
- Se parola fuori NVdB, suggerisci sinonimi più comuni
- Avvisa utente di parole "difficili"

### 4. **Modalità "testo semplice"**
- Evidenzia tutte le parole fuori NVdB
- Come fa la rivista "due parole" (citata nel PDF)

## 🔄 Classificazione manuale futura

Quando avrai tempo per classificare le parole:

### Opzione A: File di importazione
1. Crea un file `classificazioni.txt`:
```
casa|fondamentale
essere|fondamentale
avere|fondamentale
...
```

2. Importa:
```bash
python tools/classify_nvdb.py import classificazioni.txt
```

### Opzione B: Interattiva
```bash
python tools/classify_nvdb.py interactive
```
Ti guida parola per parola.

### Opzione C: Diretta su JSON
Modifica `data/vocabolario/nvdb_completo.json` cambiando:
```json
"casa": {
  "livello": null  ← cambia in "fondamentale"
}
```

## 📈 Vantaggio competitivo

**Corrige.it usa il VdB del 1997 (datato)**  
**Tu hai il NVdB del 2016 (più moderno)** ✨

Il tuo vocabolario include parole entrate nell'uso dopo il 1997:
- Termini tecnologici (smartphone, internet, ecc.)
- Neologismi recenti
- Aggiornamenti linguistici

## 🚀 Prossimi passi

1. ✅ **Estrazione completata** (6.388 parole)
2. ⏳ **Integrazione nel correttore** (prossimo step)
3. ⏳ **Classificazione manuale** (quando hai tempo)
4. ⏳ **Feature avanzate** (suggerimenti, analisi, ecc.)

## 📞 Tool di supporto

Tutti gli script sono in `tools/`:
- `extract_nvdb.py` - Estrazione dal PDF
- `classify_nvdb.py` - Gestione classificazione

Per aiuto dettagliato:
```bash
python tools/classify_nvdb.py
```
