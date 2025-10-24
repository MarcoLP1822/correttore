#!/usr/bin/env python3
"""
Demo dell'analisi di leggibilità con confronto tra diversi tipi di testo.
Mostra come l'indice Gulpease varia in base alla complessità del testo.
"""

from correttore.utils.readability import ReadabilityAnalyzer


def demo_readability():
    """Dimostra l'analisi di leggibilità su diversi tipi di testo."""
    
    analyzer = ReadabilityAnalyzer()
    
    # Definisci testi di esempio con diversi livelli di complessità
    examples = [
        {
            "nome": "Testo per Bambini",
            "testo": """
            Il gatto è sul tetto. Il sole brilla. 
            Il cane dorme. Gli uccelli cantano.
            Oggi fa caldo. Il cielo è blu.
            """
        },
        {
            "nome": "Testo Semplice",
            "testo": """
            Oggi è una bella giornata. Il sole splende nel cielo azzurro.
            Gli uccelli cantano sugli alberi. La gente passeggia nel parco.
            I bambini giocano felici. È primavera e la natura si risveglia.
            """
        },
        {
            "nome": "Testo Standard",
            "testo": """
            L'analisi della leggibilità è importante per valutare la comprensibilità
            di un testo. L'indice Gulpease è una formula sviluppata specificamente
            per la lingua italiana. Considera la lunghezza media delle parole e
            delle frasi per determinare quanto sia facile leggere un documento.
            """
        },
        {
            "nome": "Testo Tecnico",
            "testo": """
            L'implementazione dell'algoritmo di analisi lessicografica necessita
            di considerazioni metodologiche particolarmente sofisticate. La 
            parametrizzazione del sistema richiede l'ottimizzazione dei coefficienti
            attraverso procedure di validazione empirica su corpus rappresentativi.
            """
        },
        {
            "nome": "Testo Accademico",
            "testo": """
            La concettualizzazione epistemologica della problematica ermeneutica
            contemporanea evidenzia l'indispensabilità di un approccio multidisciplinare
            che tenga in considerazione simultaneamente le implicazioni metodologiche,
            le contingenze contestuali e le ramificazioni teoretiche dell'investigazione
            scientifica nel contesto della ricerca accademica postmoderna.
            """
        }
    ]
    
    print("=" * 80)
    print("DEMO ANALISI DI LEGGIBILITÀ - INDICE GULPEASE")
    print("=" * 80)
    print()
    
    # Analizza ogni esempio
    results = []
    for i, example in enumerate(examples, 1):
        stats = analyzer.analyze(example["testo"])
        results.append({
            "nome": example["nome"],
            "stats": stats
        })
        
        print(f"\n{i}. {example['nome'].upper()}")
        print("-" * 80)
        print(f"Testo: {example['testo'].strip()[:100]}...")
        print()
        print(f"   📊 Indice Gulpease:     {stats['gulpease']:.2f}/100")
        print(f"   📝 Parole:              {stats['words']}")
        print(f"   🔤 Frasi:               {stats['sentences']}")
        print(f"   📏 Lung. media parola:  {stats['avg_word_length']:.2f} lettere")
        print(f"   📐 Lung. media frase:   {stats['avg_sentence_length']:.2f} parole")
        print()
        print("   👥 Difficoltà:")
        print(f"      Elementare: {stats['difficulty']['licenza_elementare']}")
        print(f"      Media:      {stats['difficulty']['licenza_media']}")
        print(f"      Superiore:  {stats['difficulty']['diploma_superiore']}")
    
    # Riepilogo comparativo
    print("\n" + "=" * 80)
    print("RIEPILOGO COMPARATIVO")
    print("=" * 80)
    print()
    print(f"{'Tipo di Testo':<25} {'Gulpease':>10} {'Parole':>8} {'Frasi':>6} {'Difficoltà (Media)':>20}")
    print("-" * 80)
    
    for result in results:
        nome = result['nome']
        stats = result['stats']
        gulpease = stats['gulpease']
        words = stats['words']
        sentences = stats['sentences']
        difficulty = stats['difficulty']['licenza_media']
        
        print(f"{nome:<25} {gulpease:>10.2f} {words:>8} {sentences:>6}  {difficulty:>20}")
    
    print("\n" + "=" * 80)
    print("CONCLUSIONI")
    print("=" * 80)
    print("""
I risultati mostrano chiaramente come l'indice Gulpease vari in base alla
complessità del testo:

1. Testi con frasi corte e parole semplici hanno punteggi alti (80-100)
2. Testi standard hanno punteggi medi (50-70)
3. Testi tecnici/accademici hanno punteggi bassi (20-40)

L'indice Gulpease è utile per:
✓ Valutare la leggibilità dei documenti
✓ Adattare lo stile al pubblico target
✓ Migliorare la comprensibilità dei testi
✓ Confrontare diverse versioni di un documento
    """)
    print("=" * 80)


if __name__ == "__main__":
    demo_readability()
