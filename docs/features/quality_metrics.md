# 📊 Metriche di Qualità - Document Analyzer

Guida completa alle metriche utilizzate dal Document Quality Analyzer per valutare la qualità dei documenti.

## 🎯 Quality Rating

Il **Quality Rating** è una valutazione complessiva della qualità del documento basata su due fattori principali:
1. **Error Rate** (percentuale errori sul totale parole)
2. **Readability Score** (indice Gulpease)

### Scale di Valutazione

| Rating | Badge | Criteri | Descrizione |
|--------|-------|---------|-------------|
| **Excellent** | 🟢 | <2% errori + Gulpease >60 | Qualità eccellente, pubblicabile |
| **Good** | 🟡 | 2-5% errori + Gulpease 40-60 | Buona qualità, necessarie piccole correzioni |
| **Fair** | 🟠 | 5-10% errori + Gulpease 20-40 | Qualità sufficiente, revisione consigliata |
| **Poor** | 🔴 | >10% errori o Gulpease <20 | Qualità insufficiente, revisione necessaria |

### Calcolo Quality Rating

```python
def calculate_quality_rating(error_rate: float, gulpease: float) -> str:
    """
    error_rate: percentuale errori (es. 3.5 per 3.5%)
    gulpease: punteggio 0-100
    """
    if error_rate < 2 and gulpease > 60:
        return "Excellent"
    elif error_rate < 5 and gulpease > 40:
        return "Good"
    elif error_rate < 10 and gulpease > 20:
        return "Fair"
    else:
        return "Poor"
```

### Esempio Pratico

```python
from correttore.core.document_analyzer import DocumentAnalyzer

analyzer = DocumentAnalyzer()
result = analyzer.analyze_document("document.docx")

print(f"Quality Rating: {result.quality_rating}")
# Output: "Good"

# Dettagli
error_rate = (result.total_errors / result.total_words) * 100
print(f"Error Rate: {error_rate:.2f}%")  # 3.2%
print(f"Gulpease: {result.readability_score:.1f}")  # 52.5
```

## 📖 Readability Score (Gulpease)

L'**Indice Gulpease** è la metrica standard per misurare la leggibilità dei testi italiani.

### Formula

```
Gulpease = 89 + (300 × frasi - 10 × lettere) / parole
```

Dove:
- `frasi` = numero totale di frasi
- `lettere` = numero totale di caratteri (esclusi spazi)
- `parole` = numero totale di parole

### Scale di Leggibilità

| Score | Livello | Target Audience | Esempi |
|-------|---------|-----------------|--------|
| **80-100** | Elementare | Bambini 6-11 anni | Favole, libri per bambini |
| **60-80** | Facile | Adulti con educazione base | Giornali, blog, email |
| **40-60** | Medio | Educazione media superiore | Articoli, saggi, manuali |
| **20-40** | Difficile | Educazione universitaria | Testi accademici, saggi tecnici |
| **0-20** | Molto Difficile | Specialisti | Paper scientifici, testi giuridici |

### Interpretazione Risultati

#### Gulpease 80-100: Elementare
✅ **Caratteristiche:**
- Frasi molto brevi (5-10 parole)
- Parole semplici e comuni
- Struttura lineare

❌ **Evitare:**
- Tecnicismi
- Subordinate complesse
- Parole lunghe

**Esempio:**
```
"Il gatto dorme. È sul divano. Dorme tutto il giorno."
Gulpease: ~95
```

#### Gulpease 60-80: Facile
✅ **Caratteristiche:**
- Frasi brevi/medie (10-15 parole)
- Linguaggio quotidiano
- Struttura chiara

📊 **Ideale per:**
- Blog e articoli web
- Email aziendali
- Guide pratiche

**Esempio:**
```
"La nostra azienda offre servizi di qualità. I clienti apprezzano 
l'attenzione ai dettagli e la professionalità del team."
Gulpease: ~68
```

#### Gulpease 40-60: Medio
✅ **Caratteristiche:**
- Frasi medie (15-20 parole)
- Terminologia specifica moderata
- Alcune subordinate

📊 **Ideale per:**
- Articoli professionali
- Manuali tecnici
- Report aziendali

**Esempio:**
```
"L'implementazione del sistema richiede un'attenta pianificazione 
delle risorse disponibili, considerando sia gli aspetti tecnologici 
che quelli organizzativi."
Gulpease: ~45
```

#### Gulpease 20-40: Difficile
✅ **Caratteristiche:**
- Frasi lunghe (20-30 parole)
- Terminologia tecnica
- Strutture complesse

📊 **Ideale per:**
- Paper accademici
- Testi scientifici
- Documenti legali

**Esempio:**
```
"La metodologia adottata nel presente studio si basa sull'analisi 
comparativa dei dati raccolti attraverso un protocollo sperimentale 
che tiene in considerazione molteplici variabili indipendenti."
Gulpease: ~28
```

#### Gulpease 0-20: Molto Difficile
✅ **Caratteristiche:**
- Frasi molto lunghe (>30 parole)
- Terminologia altamente specializzata
- Sintassi complessa

⚠️ **Attenzione:**
- Comprensibile solo a specialisti
- Richiede background specifico

### Migliorare la Leggibilità

#### Tecniche per Aumentare Gulpease

1. **Accorciare le frasi**
   ```
   ❌ Prima (Gulpease: 35):
   "Il sistema, che è stato sviluppato utilizzando le più moderne 
   tecnologie disponibili sul mercato, offre prestazioni eccellenti 
   in termini di velocità e affidabilità."
   
   ✅ Dopo (Gulpease: 55):
   "Il sistema è stato sviluppato con tecnologie moderne. Offre 
   prestazioni eccellenti. È veloce e affidabile."
   ```

2. **Usare parole più corte**
   ```
   ❌ "implementazione" → ✅ "uso"
   ❌ "ottimizzazione" → ✅ "migliora"
   ❌ "metodologia" → ✅ "metodo"
   ```

3. **Ridurre subordinate**
   ```
   ❌ Prima:
   "Il documento, che è stato preparato dal team, contiene le 
   informazioni che sono necessarie per completare il progetto."
   
   ✅ Dopo:
   "Il team ha preparato il documento. Contiene le informazioni 
   necessarie per il progetto."
   ```

### Calcolo Programmatico

```python
from correttore.core.document_analyzer import DocumentAnalyzer

# Analizza testo
analyzer = DocumentAnalyzer()
result = analyzer.analyze_document("document.docx")

# Ottieni metriche
print(f"Gulpease Score: {result.readability_score:.1f}")
print(f"Livello: {result.readability_level}")
print(f"Parole totali: {result.total_words}")

# Interpreta risultato
if result.readability_score >= 60:
    print("✅ Facile da leggere per il pubblico generale")
elif result.readability_score >= 40:
    print("📖 Richiede educazione media superiore")
else:
    print("⚠️  Difficile, considerare semplificazione")
```

## ❌ Error Metrics

### Tipologie di Errori

#### 1. Errori Grammaticali
- Concordanza soggetto-verbo
- Concordanza genere/numero
- Uso tempi verbali
- Punteggiatura

**Peso:** Alto (critico per qualità)

#### 2. Errori Ortografici
- Typo semplici
- Accenti mancanti/errati
- Apostrofi

**Peso:** Medio (visibili ma facilmente correggibili)

#### 3. Warning
- Suggerimenti stilistici
- Ridondanze
- Frasi lunghe
- Parole ripetute

**Peso:** Basso (opzionali)

### Error Rate

```python
error_rate = (total_errors / total_words) * 100
```

| Error Rate | Valutazione | Azione |
|------------|-------------|--------|
| <1% | Eccellente | Nessuna azione necessaria |
| 1-2% | Molto buono | Correzione opzionale |
| 2-5% | Accettabile | Correzione consigliata |
| 5-10% | Problematico | Correzione necessaria |
| >10% | Critico | Revisione completa richiesta |

### Esempio

```python
result = analyzer.analyze_document("document.docx")

# Calcola error rate
error_rate = (result.total_errors / result.total_words) * 100
warning_rate = (result.total_warnings / result.total_words) * 100

print(f"📊 Error Rate: {error_rate:.2f}%")
print(f"⚠️  Warning Rate: {warning_rate:.2f}%")

# Valuta qualità
if error_rate < 2:
    print("✅ Qualità eccellente!")
elif error_rate < 5:
    print("📝 Alcune correzioni consigliate")
else:
    print("⚠️  Revisione necessaria")
```

## 🌐 Categorie Speciali

### Foreign Words (Parole Straniere)

Identifica parole in lingue diverse dall'italiano.

**Esempi:**
- Email, software, feedback (inglese)
- Croissant, restaurant (francese)
- Curriculum, agenda (latino)

**Utilizzo:**
```python
result = analyzer.analyze_document("document.docx")

if result.special_categories_count > 0:
    print(f"🌐 Parole straniere trovate: {len(result.foreign_words)}")
    for word in result.foreign_words:
        print(f"  - {word}")
```

### Sensitive Words (Parole Sensibili)

Identifica termini che richiedono attenzione speciale:
- Linguaggio offensivo
- Termini discriminatori
- Parole politically incorrect
- Gergo inappropriato

**Utilizzo:**
```python
if len(result.sensitive_words) > 0:
    print("⚠️  Attenzione: parole sensibili rilevate")
    for word in result.sensitive_words:
        print(f"  ⚠️  {word}")
```

## 📈 Metriche Aggregate

### Document Health Score

Combina tutte le metriche in un singolo score 0-100:

```python
def calculate_health_score(result):
    """Calcola score complessivo 0-100"""
    # Pesi
    weights = {
        'quality': 0.40,      # 40% quality rating
        'readability': 0.30,  # 30% leggibilità
        'errors': 0.20,       # 20% error rate
        'special': 0.10       # 10% categorie speciali
    }
    
    # Normalizza metriche (0-100)
    quality_score = {
        'Excellent': 100, 'Good': 75, 
        'Fair': 50, 'Poor': 25
    }[result.quality_rating]
    
    readability_score = result.readability_score
    
    error_rate = (result.total_errors / result.total_words) * 100
    error_score = max(0, 100 - error_rate * 10)
    
    special_score = max(0, 100 - result.special_categories_count * 5)
    
    # Calcola weighted average
    health = (
        quality_score * weights['quality'] +
        readability_score * weights['readability'] +
        error_score * weights['errors'] +
        special_score * weights['special']
    )
    
    return round(health, 1)
```

### Dashboard Metriche

```python
def print_metrics_dashboard(result):
    """Stampa dashboard completo metriche"""
    print("=" * 50)
    print("📊 DOCUMENT QUALITY DASHBOARD")
    print("=" * 50)
    
    print(f"\n🎯 OVERALL QUALITY: {result.quality_rating}")
    
    print(f"\n📖 READABILITY")
    print(f"   Score: {result.readability_score:.1f}/100")
    print(f"   Level: {result.readability_level}")
    
    print(f"\n❌ ERRORS")
    print(f"   Total: {result.total_errors}")
    error_rate = (result.total_errors / result.total_words) * 100
    print(f"   Rate: {error_rate:.2f}%")
    
    print(f"\n⚠️  WARNINGS")
    print(f"   Total: {result.total_warnings}")
    
    print(f"\n🌐 SPECIAL CATEGORIES")
    print(f"   Foreign Words: {len(result.foreign_words)}")
    print(f"   Sensitive Words: {len(result.sensitive_words)}")
    
    print(f"\n📄 DOCUMENT STATS")
    print(f"   Words: {result.total_words:,}")
    print(f"   Processing Time: {result.processing_time:.2f}s")
    
    print("=" * 50)

# Uso
result = analyzer.analyze_document("document.docx")
print_metrics_dashboard(result)
```

## 🎓 Best Practices

### Quando Usare Quale Metrica

| Scenario | Metrica Principale | Soglia Raccomandata |
|----------|-------------------|---------------------|
| **Blog/Web** | Readability Score | >60 (Facile) |
| **Email Aziendale** | Readability Score | 50-70 |
| **Report Tecnico** | Error Rate | <3% |
| **Documento Legale** | Error Rate | <1% |
| **Contenuto Marketing** | Quality Rating | Good+ |
| **Paper Accademico** | Error Rate + Citations | <0.5% |

### Workflow Consigliato

1. **Draft iniziale**: Non preoccuparti delle metriche
2. **Prima revisione**: Controlla Error Rate
3. **Seconda revisione**: Ottimizza Readability
4. **Revisione finale**: Verifica Quality Rating

### Automazione

```python
def quality_gate(document_path: Path, min_quality: str = "Good"):
    """Quality gate per CI/CD"""
    analyzer = DocumentAnalyzer()
    result = analyzer.analyze_document(document_path)
    
    quality_order = ['Poor', 'Fair', 'Good', 'Excellent']
    min_index = quality_order.index(min_quality)
    actual_index = quality_order.index(result.quality_rating)
    
    if actual_index >= min_index:
        print(f"✅ Quality gate PASSED: {result.quality_rating}")
        return True
    else:
        print(f"❌ Quality gate FAILED: {result.quality_rating} < {min_quality}")
        return False

# Uso in CI/CD
if not quality_gate(Path("document.docx"), min_quality="Good"):
    exit(1)  # Fail build
```

## 📚 Riferimenti

- [Indice Gulpease - Wikipedia](https://it.wikipedia.org/wiki/Indice_Gulpease)
- [LanguageTool Documentation](https://languagetool.org/)
- [Document Analyzer API](document_analyzer.md)

---

**Ultima modifica**: Novembre 2025  
**Versione**: 2.0.0
