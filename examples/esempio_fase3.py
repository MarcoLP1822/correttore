#!/usr/bin/env python3
"""
Esempio di utilizzo della Fase 3: Analisi Leggibilità Frase per Frase

Questo script mostra come utilizzare le nuove funzionalità implementate:
- Analisi frase per frase con GULPEASE
- Generazione di report HTML interattivi
- Identificazione frasi difficili
"""

import sys
from pathlib import Path

# Aggiungi il percorso src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from correttore.utils.readability import ReadabilityAnalyzer
from correttore.utils.readability_report_generator import generate_readability_report


def esempio_base():
    """Esempio base: analisi frase per frase"""
    print("=" * 60)
    print("ESEMPIO 1: Analisi Frase per Frase")
    print("=" * 60)
    print()
    
    testo = """
    La leggibilità è un aspetto fondamentale della scrittura.
    Un testo chiaro è più facile da comprendere.
    Frasi brevi migliorano la leggibilità.
    L'utilizzo di terminologia eccessivamente complessa può ostacolare la comprensione.
    """
    
    analyzer = ReadabilityAnalyzer()
    
    # Analizza frase per frase
    frasi = analyzer.analyze_by_sentence(testo)
    
    print(f"Analizzate {len(frasi)} frasi:\n")
    
    for frase in frasi:
        emoji = frase.get_difficulty_emoji()
        print(f"{emoji} Frase {frase.sentence_index}: {frase.text}")
        print(f"   GULPEASE: {frase.gulpease_score:.1f} - {frase.difficulty_level}")
        print(f"   Parole: {frase.word_count}")
        print()


def esempio_statistiche():
    """Esempio: statistiche aggregate"""
    print("=" * 60)
    print("ESEMPIO 2: Statistiche Aggregate")
    print("=" * 60)
    print()
    
    testo = """
    L'intelligenza artificiale sta trasformando il mondo.
    I computer imparano dai dati.
    Gli algoritmi sono sempre più sofisticati.
    Le applicazioni pratiche sono innumerevoli.
    La tecnologia evolve rapidamente.
    """
    
    analyzer = ReadabilityAnalyzer()
    frasi = analyzer.analyze_by_sentence(testo)
    stats = analyzer.get_sentence_statistics(frasi)
    
    print("📊 Statistiche del documento:\n")
    print(f"Totale frasi: {stats['total_sentences']}")
    print(f"GULPEASE medio: {stats['avg_gulpease']:.2f}")
    print(f"Parole/frase (media): {stats['avg_words_per_sentence']:.2f}")
    print()
    print("Distribuzione difficoltà:")
    print(f"  📗 Molto facili (80-100): {stats['distribution']['very_easy']}")
    print(f"  📘 Facili (60-79):        {stats['distribution']['easy']}")
    print(f"  📙 Difficili (40-59):     {stats['distribution']['difficult']}")
    print(f"  📕 Molto difficili (0-39): {stats['distribution']['very_difficult']}")
    print()


def esempio_frasi_difficili():
    """Esempio: individuazione frasi difficili"""
    print("=" * 60)
    print("ESEMPIO 3: Individuazione Frasi Difficili")
    print("=" * 60)
    print()
    
    testo = """
    Il gatto dorme. Il cane gioca.
    La metodologia implementata utilizza paradigmi computazionali avanzati.
    L'integrazione sistemica richiede un'analisi approfondita delle interdipendenze.
    Il sole splende. La luna brilla.
    """
    
    analyzer = ReadabilityAnalyzer()
    frasi = analyzer.analyze_by_sentence(testo)
    
    # Trova frasi con GULPEASE < 60
    difficili = analyzer.get_difficult_sentences(frasi, threshold=60)
    
    print(f"🔍 Trovate {len(difficili)} frasi difficili (GULPEASE < 60):\n")
    
    for frase in difficili:
        print(f"📕 GULPEASE {frase.gulpease_score:.1f}")
        print(f"   {frase.text}")
        print()


def esempio_report_html():
    """Esempio: generazione report HTML completo"""
    print("=" * 60)
    print("ESEMPIO 4: Generazione Report HTML")
    print("=" * 60)
    print()
    
    testo = """
    L'analisi della leggibilità è uno strumento prezioso per scrittori ed editori.
    
    Un testo leggibile raggiunge meglio il suo pubblico.
    Le frasi brevi sono generalmente più facili da comprendere.
    Tuttavia, anche la varietà sintattica ha la sua importanza.
    
    L'indice GULPEASE è specifico per la lingua italiana.
    Considera la lunghezza delle parole e delle frasi.
    I valori vanno da 0 a 100, dove valori più alti indicano maggiore facilità.
    
    Per un pubblico con licenza media, un valore sopra 60 è consigliato.
    Testi tecnici possono avere valori inferiori ma rimanere appropriati.
    L'importante è conoscere il proprio pubblico di riferimento.
    """
    
    output_path = "test_output/esempio_report_leggibilita.html"
    
    print("Generazione report HTML...")
    
    try:
        report_path = generate_readability_report(
            text=testo,
            output_path=output_path,
            document_title="Esempio Analisi Leggibilità"
        )
        
        print(f"✅ Report generato con successo!")
        print(f"📄 Percorso: {report_path}")
        print()
        print("Il report include:")
        print("  • Sintesi con GULPEASE globale e statistiche")
        print("  • Tabella interattiva di tutte le frasi analizzate")
        print("  • Analisi del vocabolario")
        print("  • Grafici e visualizzazioni")
        print()
        print("🌐 Apri il file HTML in un browser per visualizzarlo!")
        
    except Exception as e:
        print(f"❌ Errore: {e}")


def esempio_da_file():
    """Esempio: analisi di un file di testo"""
    print("=" * 60)
    print("ESEMPIO 5: Analisi da File")
    print("=" * 60)
    print()
    
    # Crea un file di test se non esiste
    test_file = Path("test_output/esempio_testo.txt")
    test_file.parent.mkdir(exist_ok=True, parents=True)
    
    if not test_file.exists():
        test_file.write_text("""
        La scrittura chiara è un'arte che si può imparare.
        Richiede pratica e attenzione al lettore.
        
        Le frasi brevi sono più facili da comprendere.
        Parole semplici rendono il testo accessibile.
        La punteggiatura aiuta a organizzare le idee.
        
        Un buon testo bilancia chiarezza e profondità.
        Non sempre la semplicità significa superficialità.
        L'obiettivo è comunicare efficacemente.
        """, encoding='utf-8')
    
    print(f"Lettura file: {test_file}")
    testo = test_file.read_text(encoding='utf-8')
    
    # Analisi
    analyzer = ReadabilityAnalyzer()
    frasi = analyzer.analyze_by_sentence(testo)
    stats = analyzer.get_sentence_statistics(frasi)
    
    print(f"\n📊 Analisi completata:")
    print(f"   Frasi totali: {stats['total_sentences']}")
    print(f"   GULPEASE medio: {stats['avg_gulpease']:.2f}")
    
    # Genera report
    output_html = "test_output/esempio_da_file_report.html"
    report_path = generate_readability_report(
        text=testo,
        output_path=output_html,
        document_title="Analisi da File"
    )
    
    print(f"   Report HTML: {report_path}")
    print()


def main():
    """Esegue tutti gli esempi"""
    print()
    print("🚀 ESEMPI DI UTILIZZO - FASE 3: ANALISI LEGGIBILITÀ")
    print()
    
    try:
        esempio_base()
        print("\n" + "="*60 + "\n")
        
        esempio_statistiche()
        print("\n" + "="*60 + "\n")
        
        esempio_frasi_difficili()
        print("\n" + "="*60 + "\n")
        
        esempio_report_html()
        print("\n" + "="*60 + "\n")
        
        esempio_da_file()
        
        print("\n" + "="*60)
        print("✅ Tutti gli esempi completati!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Errore durante l'esecuzione: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
