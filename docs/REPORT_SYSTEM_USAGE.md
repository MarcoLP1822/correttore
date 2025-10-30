# 📋 Guida Utilizzo Report HTML - Sistema di Correzione

**Data**: 24 Ottobre 2025  
**Versione**: 1.0.0

---

## 🎯 Panoramica

Il sistema di report HTML fornisce un'analisi dettagliata e interattiva delle correzioni ortografiche e grammaticali, simile a Corrige.it. Il report è completamente standalone e può essere visualizzato in qualsiasi browser moderno.

---

## 📊 Struttura Report

### 1. **Pagina Sintesi**

La pagina iniziale mostra:

- **Tabella Segnalazioni di Correzione**: Errori che richiedono intervento
  - ❌ Errori Riconosciuti
  - ❓ Sconosciute
  - ⚠️ Sospette
  - ✨ Migliorabili
  - 🔣 Punteggiatura

- **Tabella Segnalazioni di Informazione**: Informazioni senza errori
  - 😳 Imbarazzanti
  - ↔️ Varianti
  - 👤 Nomi/Sigle
  - 🌐 Lingue
  - ℹ️ Con Info

- **Metadati Elaborazione**:
  - Tempo di elaborazione
  - Parole totali
  - Contesti verificati
  - Data e sistema

### 2. **Tabs Categoria**

Ogni categoria ha una pagina dedicata con:

- **Intestazione**: Descrizione e informazioni sulla categoria
- **Statistiche**: Parole uniche e occorrenze totali
- **Lista Errori Raggruppati**: Errori organizzati per tipo
- **Occorrenze**: Ogni occorrenza con contesto completo

---

## 💻 Generazione Report - Da Codice

### Importazione Base

```python
from correttore.core.correction_collector import CorrectionCollector
from correttore.utils.html_report_generator import generate_orthography_report
```

### Creazione Report

```python
# Crea collector e aggiungi correzioni
collector = CorrectionCollector()
collector.start_tracking()

# ... aggiungi correzioni usando add_correction() ...

collector.stop_tracking()

# Genera report HTML
report_path = generate_orthography_report(
    collector=collector,
    output_path="outputs/report_ortografia.html",
    document_name="Il Mio Documento",
    standalone=True,  # Include CSS e JS inline
    show_feedback_buttons=False  # Pulsanti feedback (futuro)
)

print(f"Report generato: {report_path}")
```

### Esempio Completo con Correzioni

```python
from correttore.models import CorrectionRecord, CorrectionCategory, CorrectionSource
from datetime import datetime

# Aggiungi una correzione
collector.add_correction(CorrectionRecord(
    id="err_001",
    category=CorrectionCategory.ERRORI_RICONOSCIUTI,
    original_text="perchè",
    corrected_text="perché",
    context="Non so perchè i gatti dormono così tanto.",
    position=8,
    paragraph_index=0,
    sentence_index=0,
    source=CorrectionSource.LANGUAGETOOL,
    confidence_score=0.98,
    rule_id="ACCENT_ERROR",
    message="Accento errato: 'perchè' dovrebbe essere 'perché' con accento acuto.",
    suggestions=["perché"],
    timestamp=datetime.now()
))
```

---

## 🔧 Integrazione nel Workflow Esistente

### Modifica CorrectionEngine

Aggiungi la generazione del report alla fine del processo di correzione:

```python
# In src/correttore/core/correction_engine.py

from ..utils.html_report_generator import generate_orthography_report

class CorrectionEngine:
    def correct_document(self, input_file: str, output_file: str = None, 
                        generate_report: bool = True):
        # ... codice esistente ...
        
        # Alla fine, dopo tutte le correzioni
        if generate_report and hasattr(self, 'collector'):
            report_path = output_file.replace('.docx', '_report.html')
            generate_orthography_report(
                self.collector,
                report_path,
                Path(input_file).stem,
                standalone=True
            )
            print(f"Report generato: {report_path}")
        
        return result
```

### Dalla Web Interface

```python
# In src/correttore/interfaces/web_interface.py

@app.route('/correggi', methods=['POST'])
def correggi_documento():
    # ... codice esistente ...
    
    # Genera report
    report_path = os.path.join(app.config['OUTPUT_FOLDER'], 
                              f"{doc_name}_report.html")
    
    generate_orthography_report(
        engine.collector,
        report_path,
        doc_name
    )
    
    # Restituisci entrambi i file
    return jsonify({
        'documento_corretto': output_path,
        'report_html': report_path
    })
```

---

## 🎨 Personalizzazione

### Modificare Stili CSS

Modifica `templates/report/assets/report.css`:

```css
:root {
    /* Cambia colori principali */
    --color-primary: #2c3e50;
    --color-accent: #3498db;
    
    /* Cambia colori categorie */
    --color-error: #e74c3c;
    --color-warning: #f39c12;
    --color-success: #27ae60;
}
```

### Aggiungere Grafici

Nel template `sintesi.html`, abilita la sezione grafici:

```html
{% if show_charts %}
<div class="charts-section">
    <h3>📈 Visualizzazioni</h3>
    <div class="charts-grid">
        <canvas id="distribution-chart"></canvas>
    </div>
</div>
{% endif %}
```

Poi passa `show_charts=True` nei dati del template.

---

## 🌐 Visualizzazione Report

### Aprire in Browser

```bash
# Windows
start test_output/report_test.html

# macOS
open test_output/report_test.html

# Linux
xdg-open test_output/report_test.html
```

### Da Python

```python
import webbrowser
webbrowser.open(report_path)
```

---

## 🧪 Test e Debug

### Script di Test

Usa `test_report_generator.py`:

```bash
python test_report_generator.py
```

Genera un report con dati di esempio per tutte le categorie.

### Verificare Template

```python
from pathlib import Path
from correttore.utils.html_report_generator import HTMLReportGenerator

generator = HTMLReportGenerator()
print(f"Templates dir: {generator.templates_dir}")
print(f"CSS: {generator.templates_dir / 'assets' / 'report.css'}")
print(f"JS: {generator.templates_dir / 'assets' / 'report.js'}")
```

---

## 📱 Responsive Design

Il report è ottimizzato per:

- 🖥️ **Desktop**: Layout a due colonne per sintesi
- 💻 **Tablet**: Layout adattivo con tabs scrollabili
- 📱 **Mobile**: Layout singola colonna, tabs verticali

---

## 🔮 Funzionalità Future

### Pulsanti Feedback (FASE 6)

Quando implementata, permetterà:
- Segnalare correzioni corrette/errate
- Apprendimento automatico
- Miglioramento dizionario custom

### Grafici Interattivi

Con Chart.js o Plotly:
- Distribuzione errori per categoria
- Timeline elaborazione
- Heatmap documento

### Export PDF

Con weasyprint:

```python
from weasyprint import HTML

HTML(report_path).write_pdf(report_path.replace('.html', '.pdf'))
```

---

## 🐛 Troubleshooting

### Errore: Template Not Found

**Causa**: Directory templates non trovata  
**Soluzione**:

```python
from pathlib import Path

# Specifica directory manualmente
templates_dir = Path(__file__).parent / "templates" / "report"
generator = HTMLReportGenerator(templates_dir=str(templates_dir))
```

### CSS Non Applicato

**Causa**: CSS non inline in modalità standalone  
**Soluzione**: Verifica che `standalone=True` e file CSS esista

```python
generate_orthography_report(..., standalone=True)
```

### Contesti Troppo Lunghi

**Causa**: Contesti superiori a 200 caratteri rallentano rendering  
**Soluzione**: Tronca contesti in `CorrectionRecord`:

```python
if len(context) > 200:
    context = context[:100] + "..." + context[-100:]
```

---

## 📚 Riferimenti API

### `generate_orthography_report()`

```python
def generate_orthography_report(
    collector: CorrectionCollector,
    output_path: str,
    document_name: str = "Documento",
    standalone: bool = True,
    show_feedback_buttons: bool = False
) -> str
```

**Parametri**:
- `collector`: CorrectionCollector con correzioni
- `output_path`: Path output HTML
- `document_name`: Nome documento per intestazione
- `standalone`: Include CSS/JS inline
- `show_feedback_buttons`: Mostra pulsanti (futuro)

**Returns**: Path file generato

---

## 🚀 Best Practices

### 1. Performance

- Genera report solo per documenti < 50k parole
- Usa `standalone=True` per distribuzione
- Cache report generati se documento non cambia

### 2. Organizzazione File

```
outputs/
├── documenti_corretti/
│   ├── documento.docx
│   └── documento_report.html
└── report_archiviati/
    └── 2025-10/
        └── documento_report.html
```

### 3. Naming Convention

```python
import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_name = f"{doc_name}_{timestamp}_report.html"
```

---

## ✅ Checklist Implementazione

- [x] Template HTML base creati
- [x] CSS responsive implementato
- [x] JavaScript navigazione funzionante
- [x] HTMLReportGenerator implementato
- [x] Test con dati di esempio passato
- [x] Export standalone funzionante
- [ ] Integrazione in CorrectionEngine (TODO)
- [ ] Integrazione Web Interface (TODO)
- [ ] Sistema feedback (FASE 6)
- [ ] Grafici interattivi (Futuro)

---

**Nota**: Questo sistema è parte della FASE 2 del piano di implementazione. Le FASI successive aggiungeranno analisi leggibilità, lemmatizzazione, e feedback interattivo.

---

*Ultima modifica: 24 Ottobre 2025*
