# 📊 Sistema di Report in Stile Corrige.it

## ✨ Completato con Successo!

Il sistema di correzione ora genera report professionali secondo lo standard **Corrige.it**, organizzando le correzioni nelle seguenti categorie:

### 📋 Categorie Implementate

1. **Errori di ortografia o grammatica riconosciuti** - Errori certi identificati
2. **Sconosciute** - Parole non riconosciute
3. **Sospette** - Possibili errori da verificare
4. **Migliorabili** - Suggerimenti stilistici e redazionali
5. **Punteggiatura** - Problemi di punteggiatura
6. **Imbarazzanti** - Parole potenzialmente imbarazzanti
7. **Varianti** - Varianti ortografiche per coerenza
8. **Nomi propri, sigle ecc.** - Identificazione nomi e acronimi
9. **Parole di altre lingue** - Parole straniere
10. **Con info** - Informazioni terminologiche

### 🎨 Caratteristiche

- **Report HTML**: Design moderno e professionale con navigazione per categorie
- **Report Markdown**: Strutturato e facilmente consultabile
- **Report JSON**: Dati strutturati per elaborazione programmatica
- **Categorizzazione Automatica**: Sistema intelligente di classificazione errori
- **Contesti**: Ogni correzione mostrata con ~10 parole di contesto
- **Statistiche Complete**: Quadro di sintesi con distribuzione per categoria

### 🚀 Come Testare

```bash
# Esegui il test di esempio
python examples/test_corrige_report.py
```

I report vengono generati in `examples/output/`:
- `test_corrige_report.html` - Visualizza in un browser
- `test_corrige_report.md` - Visualizza in un editor
- `test_corrige_report.json` - Dati strutturati

### 📝 Utilizzo nel Codice

```python
from correttore.utils.report_generator import ReportGenerator

generator = ReportGenerator()
generator.generate_correction_report(
    document_diff=doc_diff,
    correction_stats=stats,
    quality_reports=quality_reports,
    output_path=output_path,
    template='corrige',      # ← Template Corrige.it
    format_type='html'       # html, markdown o json
)
```

### 📖 Documentazione Completa

Vedi `docs/features/CORRIGE_REPORT_SYSTEM.md` per:
- Guida dettagliata all'utilizzo
- Personalizzazione delle categorie
- Esempi di output
- Integrazione nel workflow

### 🎯 Esempio di Output

Il report HTML include:

**Header con statistiche**
```
Documento controllato il 03/11/2025 alle 17:16
Paragrafi controllati: 7
Segnalazioni totali: 5
```

**Distribuzione per categoria**
| Categoria | Segnalazioni | % |
|-----------|--------------|---|
| Sospette | 2 | 40% |
| Migliorabili | 1 | 20% |
| Punteggiatura | 1 | 20% |
| Varianti | 1 | 20% |

**Dettaglio per ogni parola**
```
### ditali
Suggerimento: di tali
Possibile confusione: ditali → di tali
Contesto: ...Non sono sicuro ditali argomenti...
[ Corretta ] [ Errore ]
```

### ✅ Tutto Funzionante!

Il sistema è stato testato con successo e genera report in tutti e tre i formati (HTML, Markdown, JSON) con categorizzazione completa secondo lo standard Corrige.it.
