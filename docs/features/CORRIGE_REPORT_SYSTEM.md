# Sistema di Report in Stile Corrige.it

## Panoramica

Il sistema di correzione ora supporta la generazione di report secondo lo standard **Corrige.it**, il servizio professionale di correzione ortografica e grammaticale.

## Novità

### 1. **Categorizzazione Automatica**

Le correzioni vengono automaticamente classificate in 10 categorie standard:

- ✅ **Errori di ortografia o grammatica riconosciuti**: Errori certi identificati dal sistema
- ❓ **Sconosciute**: Parole non riconosciute (potrebbero essere errori o termini specialistici)
- ⚠️ **Sospette**: Parole corrette ma che potrebbero essere errori nel contesto
- 📝 **Migliorabili**: Suggerimenti per migliorare lo stile e le convenzioni redazionali
- ⚡ **Punteggiatura**: Problemi nell'uso della punteggiatura
- 😳 **Imbarazzanti**: Parole potenzialmente imbarazzanti o volgari
- 🔄 **Varianti**: Varianti ortografiche per verificare la coerenza
- 👤 **Nomi propri, sigle ecc.**: Nomi propri e acronimi identificati
- 🌍 **Parole di altre lingue**: Parole straniere presenti nel testo
- ℹ️ **Con info**: Parole con informazioni terminologiche o enciclopediche

### 2. **Template HTML Professionale**

Il nuovo template HTML replica lo stile visivo di Corrige.it:
- Design moderno e professionale
- Navigazione per categorie con contatori
- Colori e layout ottimizzati per la leggibilità
- Responsive e ottimizzato per stampa

### 3. **Report Markdown Strutturato**

Il report Markdown include:
- Quadro di sintesi con statistiche
- Descrizioni dettagliate per ogni categoria
- Contesti di utilizzo per ogni correzione
- Suggerimenti interattivi (simulati)

## Come Utilizzare

### Generare Report Corrige-Style

```python
from correttore.utils.report_generator import ReportGenerator, CorrectionStats
from correttore.utils.diff_engine import DocumentDiff

# Crea report generator
generator = ReportGenerator()

# Genera report in stile Corrige
output_path = Path('output/resoconto.html')
generator.generate_correction_report(
    document_diff=doc_diff,
    correction_stats=stats,
    quality_reports=quality_reports,
    output_path=output_path,
    template='corrige',      # ← Usa template Corrige
    format_type='html'       # o 'markdown', 'json'
)
```

### Template Disponibili

1. **`corrige`**: Report in stile Corrige.it con categorizzazione completa
2. **`standard`**: Report standard con statistiche e modifiche
3. **`detailed`**: Report dettagliato con tutte le informazioni
4. **`summary`**: Riassunto rapido dei risultati

### Formati di Output

- **HTML**: Report visivo professionale (consigliato per presentazioni)
- **Markdown**: Report testuale strutturato (consigliato per revisioni)
- **JSON**: Dati strutturati per elaborazione programmatica

## Struttura del Report Corrige

### 1. Header e Quadro di Sintesi

Il report inizia con:
- Nome documento e data/ora controllo
- Statistiche generali (paragrafi, parole, segnalazioni)
- Distribuzione percentuale per categoria

### 2. Sezioni per Categoria

Ogni categoria include:
- **Descrizione**: Spiega il tipo di segnalazione
- **Conteggio**: Numero di occorrenze trovate
- **Lista dettagliata**: Ogni parola con:
  - Parola originale evidenziata
  - Correzione o suggerimento (se disponibile)
  - Spiegazione del problema
  - Contesto (~10 parole intorno)
  - Varianti disponibili (per categoria Varianti)
  - Bottoni interattivi (Corretta/Errore) per categorie Sconosciute e Sospette

### 3. Navigazione

Il report HTML include:
- Indice cliccabile delle categorie
- Contatori per ogni categoria
- Design responsive per desktop e mobile

## Esempio di Output

Vedi il file `examples/output/test_corrige_report.html` per un esempio completo.

### Esempio Categoria "Sospette"

```markdown
## Sospette

*Questa sezione segnala parole in sé corrette ma che potrebbero essere 
un errore rispetto al contesto e che vale la pena controllare.*

**2 errori nell'uso di 2 parole**

### ditali

**Suggerimento:** di tali

*Possibile confusione: ditali → di tali*

**Contesto:**
- ...Non sono sicuro ditali argomenti da trattare...

[ Corretta ] [ Errore ]
```

## Personalizzazione

### Aggiungere Parole Imbarazzanti

Nel file `corrige_categorizer.py`:

```python
self.imbarazzanti = {
    'cacca', 'culo', 'merda', 'cazzo', 'puttana', 'figa', 
    'minchia', 'coglione', 'stronzo', 'bastardo', 'porca',
    # Aggiungi le tue parole qui
}
```

### Aggiungere Varianti Ortografiche

```python
self.varianti_comuni = {
    'obiettivo': ['obbiettivo'],
    'email': ['e-mail', 'e mail'],
    # Aggiungi le tue varianti qui
}
```

### Aggiungere Pattern Migliorabili

```python
self.migliorabili_patterns = [
    (re.compile(r'\d+a\b'), 'Usare ordinale con ª: 1ª, 2ª'),
    (re.compile(r"tutt'altro"), "Preferire 'tuttaltro'"),
    # Aggiungi i tuoi pattern qui
]
```

## Test

Esegui il test di esempio:

```bash
python examples/test_corrige_report.py
```

Il test genera:
- `test_corrige_report.html` - Report visivo completo
- `test_corrige_report.md` - Report Markdown
- `test_corrige_report.json` - Dati strutturati

## Integrazione nel Workflow

Il template Corrige può essere utilizzato ovunque si generi un report:

```python
# In main.py o nel tuo script
if args.report_style == 'corrige':
    template = 'corrige'
else:
    template = 'standard'

generator.generate_correction_report(
    # ... parametri ...
    template=template,
    format_type=args.format  # html, markdown, json
)
```

## Differenze con Report Standard

| Caratteristica | Report Standard | Report Corrige |
|----------------|----------------|----------------|
| Categorizzazione | Per tipo di modifica | Per categoria semantica |
| Focus | Statistiche e performance | Qualità linguistica |
| Target | Sviluppatori, QA | Redattori, correttori |
| Interattività | Limitata | Bottoni feedback |
| Design | Tecnico | Professionale/Editoriale |
| Dettaglio contesto | Variabile | Sempre ~10 parole |

## Vantaggi

✅ **Professionalità**: Report comparabili a servizi professionali  
✅ **Chiarezza**: Categorie intuitive e ben documentate  
✅ **Completezza**: Copre tutti i tipi di segnalazione linguistica  
✅ **Flessibilità**: 3 formati di output (HTML, MD, JSON)  
✅ **Personalizzazione**: Facilmente estendibile  

## Note Tecniche

- La categorizzazione usa pattern euristici e può essere migliorata con ML
- Le lingue straniere supportate: inglese, francese, tedesco, spagnolo, latino
- I pattern di punteggiatura coprono i casi più comuni
- Il sistema di varianti è espandibile con dizionari esterni

## Prossimi Sviluppi

- [ ] Integrazione con API LanguageTool per categorizzazione più precisa
- [ ] Database dizionario varianti esterno
- [ ] Supporto per feedback utente (bottoni Corretta/Errore funzionanti)
- [ ] Export PDF con stile Corrige
- [ ] Statistiche comparative tra revisioni
