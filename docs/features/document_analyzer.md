# 🔍 Document Quality Analyzer

Sistema di analisi qualità documenti **senza applicare correzioni** - utile per ottenere metriche e report diagnostici prima della correzione.

## 📋 Panoramica

Il `DocumentAnalyzer` permette di:
- ✅ Analizzare qualità documento senza modificarlo
- 📊 Ottenere metriche di leggibilità (Gulpease)
- 🔍 Rilevare errori grammaticali e ortografici
- 🌐 Identificare categorie speciali (lingue straniere, parole sensibili)
- 📄 Generare report HTML diagnostici
- ⚡ Eseguire analisi post-correzione automatica

## 🚀 Quick Start

### CLI

```bash
# Analisi base
correttore analyze documento.docx

# Con output directory personalizzata
correttore analyze documento.docx --output-dir ./reports/

# Disabilita LanguageTool per velocizzare
correttore analyze documento.docx --no-languagetool

# Disabilita categorie speciali
correttore analyze documento.docx --no-special-categories
```

### Web Interface

1. Carica documento nella dashboard
2. Click su "🔍 Analizza Qualità"
3. Visualizza report interattivo

### API Python

```python
from pathlib import Path
from correttore.core.document_analyzer import DocumentAnalyzer

# Inizializza analyzer
analyzer = DocumentAnalyzer(
    enable_languagetool=True,      # Check grammaticale
    enable_readability=True,       # Analisi leggibilità
    enable_special_categories=True # Categorie speciali
)

# Analizza documento
result = analyzer.analyze_document(
    document_path=Path("input.docx"),
    output_report=True,
    output_dir=Path("reports/")
)

# Accedi ai risultati
print(f"✅ Success: {result.success}")
print(f"📊 Quality Rating: {result.quality_rating}")
print(f"📖 Readability Score: {result.readability_score:.1f}")
print(f"📝 Readability Level: {result.readability_level}")
print(f"❌ Total Errors: {result.total_errors}")
print(f"⚠️  Total Warnings: {result.total_warnings}")
print(f"📄 Report Path: {result.report_path}")
```

## 📊 Configurazione

### Parametri di Inizializzazione

```python
DocumentAnalyzer(
    enable_languagetool: bool = True,       # LanguageTool checking
    enable_readability: bool = True,        # Analisi leggibilità Gulpease
    enable_special_categories: bool = True, # Categorie speciali
    config: Optional[AnalyzerConfig] = None # Config personalizzata
)
```

### Parametri analyze_document()

```python
analyzer.analyze_document(
    document_path: Path,           # Percorso documento
    output_report: bool = True,    # Genera report HTML
    output_dir: Optional[Path] = None  # Directory output (default: outputs/)
) -> DocumentAnalysisResult
```

## 📈 Risultati

### DocumentAnalysisResult

```python
@dataclass
class DocumentAnalysisResult:
    success: bool                    # Analisi completata con successo
    
    # Metriche principali
    total_words: int                 # Parole totali
    total_errors: int                # Errori totali
    total_warnings: int              # Warning totali
    
    # Leggibilità
    readability_score: float         # Gulpease score (0-100)
    readability_level: str           # "Facile", "Medio", "Difficile"
    
    # Qualità
    quality_rating: str              # "Excellent", "Good", "Fair", "Poor"
    
    # Categorie speciali
    special_categories_count: int    # Elementi categorie speciali
    foreign_words: List[str]         # Parole straniere rilevate
    sensitive_words: List[str]       # Parole sensibili rilevate
    
    # Report
    report_path: Optional[Path]      # Percorso report HTML
    
    # Metadati
    processing_time: float           # Tempo elaborazione (secondi)
    timestamp: datetime              # Timestamp analisi
    error_message: Optional[str]     # Messaggio errore (se success=False)
```

### Metodi Utility

```python
# Verifica problemi critici
if result.has_critical_issues():
    print("⚠️ Documento richiede correzione!")

# Ottieni riepilogo
summary = result.get_summary()
print(summary)

# Esporta in dict
data = result.to_dict()
```

## 🎯 Metriche di Qualità

### Quality Rating

| Rating | Criteri |
|--------|---------|
| **Excellent** | <2% errori, Gulpease >60 |
| **Good** | 2-5% errori, Gulpease 40-60 |
| **Fair** | 5-10% errori, Gulpease 20-40 |
| **Poor** | >10% errori, Gulpease <20 |

### Readability Score (Gulpease)

| Score | Livello | Descrizione |
|-------|---------|-------------|
| **80-100** | Elementare | Comprensibile da bambini |
| **60-80** | Facile | Facile per adulti |
| **40-60** | Medio | Richiede educazione media |
| **20-40** | Difficile | Richiede educazione superiore |
| **0-20** | Molto Difficile | Richiede specializzazione |

## 🔧 Integrazione con CorrectionEngine

### Analisi Post-Correzione Automatica

```python
from correttore.core.correction_engine import CorrectionEngine

# Abilita analisi post-correzione
engine = CorrectionEngine(
    enable_tracking=True,
    enable_post_analysis=True  # ✅ Analisi automatica dopo correzione
)

# Correggi documento
result = engine.correct_document(
    "input.docx",
    output_path="output_corretto.docx"
)

# L'analisi viene eseguita automaticamente e loggata
# Report salvato in outputs/
```

### Workflow Completo

```python
# 1. Analisi PRE-correzione
analyzer = DocumentAnalyzer()
pre_analysis = analyzer.analyze_document(
    "input.docx",
    output_dir="reports/pre/"
)

print(f"📊 Pre-correzione: {pre_analysis.total_errors} errori")

# 2. Correzione
engine = CorrectionEngine(enable_post_analysis=False)
correction_result = engine.correct_document(
    "input.docx",
    output_path="output_corretto.docx"
)

# 3. Analisi POST-correzione
post_analysis = analyzer.analyze_document(
    "output_corretto.docx",
    output_dir="reports/post/"
)

print(f"📊 Post-correzione: {post_analysis.total_errors} errori")
print(f"✅ Miglioramento: {pre_analysis.total_errors - post_analysis.total_errors} errori risolti")
```

## 📄 Report HTML

Il report generato include:

### Sezioni Principali

1. **📊 Statistics Overview**
   - Total words, errors, warnings
   - Quality rating badge
   - Processing time

2. **📖 Readability Analysis**
   - Gulpease score con gauge visuale
   - Readability level
   - Interpretazione risultato

3. **❌ Error Details**
   - Lista errori per categoria
   - Context snippets
   - Suggested corrections

4. **🌐 Special Categories**
   - Foreign words detected
   - Sensitive words flagged
   - Context information

### Personalizzazione Template

```python
# Report template: templates/analysis_report.html
# Personalizza modificando il template Jinja2
```

## 🔍 Esempi Avanzati

### Analisi Batch

```python
from pathlib import Path

analyzer = DocumentAnalyzer(enable_languagetool=False)  # Faster
documents = Path("documents/").glob("*.docx")

results = []
for doc in documents:
    result = analyzer.analyze_document(doc, output_report=False)
    results.append({
        "file": doc.name,
        "quality": result.quality_rating,
        "errors": result.total_errors,
        "readability": result.readability_score
    })

# Ordina per qualità
results.sort(key=lambda x: x["errors"])
print(f"📈 Documento migliore: {results[0]['file']}")
```

### Monitoraggio Continuo

```python
import time

def monitor_quality(document_path: Path, interval: int = 60):
    """Monitora qualità documento ogni N secondi"""
    analyzer = DocumentAnalyzer()
    
    while True:
        result = analyzer.analyze_document(document_path, output_report=False)
        print(f"[{result.timestamp}] Errors: {result.total_errors}, Quality: {result.quality_rating}")
        
        time.sleep(interval)

# Usa in background mentre editi
monitor_quality(Path("draft.docx"), interval=30)
```

### Export Metriche

```python
import json

result = analyzer.analyze_document("document.docx")

# Export JSON
with open("metrics.json", "w") as f:
    json.dump(result.to_dict(), f, indent=2, default=str)

# Export CSV
import csv
with open("metrics.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=result.to_dict().keys())
    writer.writeheader()
    writer.writerow(result.to_dict())
```

## ⚡ Performance

### Ottimizzazioni

```python
# Analisi veloce (senza LanguageTool)
analyzer = DocumentAnalyzer(enable_languagetool=False)  # 5x più veloce

# Solo leggibilità
analyzer = DocumentAnalyzer(
    enable_languagetool=False,
    enable_special_categories=False
)  # 10x più veloce

# Senza report HTML
result = analyzer.analyze_document(doc, output_report=False)  # 20% più veloce
```

### Benchmark Tipici

| Documento | LanguageTool | Tempo |
|-----------|--------------|-------|
| 1.000 parole | ✅ | ~3s |
| 1.000 parole | ❌ | ~0.5s |
| 10.000 parole | ✅ | ~15s |
| 10.000 parole | ❌ | ~2s |

## 🐛 Troubleshooting

### LanguageTool non risponde

```python
# Verifica server attivo
from correttore.services.languagetool_service import LanguageToolService

service = LanguageToolService()
if not service.is_server_running():
    print("❌ LanguageTool server non attivo")
    # Avvia server: python start_languagetool.py
```

### Memoria insufficiente

```python
# Disabilita funzioni pesanti
analyzer = DocumentAnalyzer(
    enable_languagetool=False,  # Riduce uso memoria
    enable_special_categories=False
)
```

### Report non generato

```python
# Verifica permessi directory
output_dir = Path("reports/")
output_dir.mkdir(parents=True, exist_ok=True)

result = analyzer.analyze_document(doc, output_dir=output_dir)
if result.report_path:
    print(f"✅ Report: {result.report_path}")
else:
    print("❌ Report non generato:", result.error_message)
```

## 📚 Vedi Anche

- [Report System](report_system.md) - Sistema report HTML
- [NVDB Vocabulary](nvdb.md) - Vocabolario di base
- [QUICKSTART](../QUICKSTART.md) - Guida rapida
- [API Reference](../api/README.md) - API completa

## 🤝 Contributi

Per miglioramenti o bug report: [GitHub Issues](https://github.com/MarcoLP1822/correttore/issues)

---

**Ultima modifica**: Novembre 2025  
**Versione**: 2.0.0
