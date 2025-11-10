"""
Script di test per verificare l'integrazione del Vocabolario di Base.
"""

from correttore.utils.readability import ReadabilityAnalyzer
from correttore.services.vocabulary_service import get_vocabulary_service

# Test testo semplice
testo_semplice = """
La casa è bella. Il sole brilla nel cielo. 
I bambini giocano nel parco con la palla.
"""

# Test testo complesso
testo_complesso = """
L'implementazione dell'algoritmo richiede un'analisi approfondita 
della complessità computazionale e delle ottimizzazioni necessarie 
per garantire prestazioni accettabili in scenari di produzione.
"""

def test_vocabulary_service():
    """Test del servizio vocabolario"""
    print("\n" + "=" * 70)
    print("TEST VOCABULARY SERVICE")
    print("=" * 70)
    
    vocab = get_vocabulary_service()
    
    print(f"\n✓ Vocabolario caricato: {vocab.vocabulary_size} parole")
    
    # Test parole comuni
    test_words = ['casa', 'essere', 'avere', 'implementazione', 'algoritmo', 'xyz123']
    print("\nTest presenza parole:")
    for word in test_words:
        in_vocab = vocab.is_in_vocabulary(word)
        status = "✓" if in_vocab else "✗"
        print(f"  {status} {word}: {'nel vocabolario' if in_vocab else 'NON nel vocabolario'}")
    
    # Test info dettagliate
    print("\nInfo dettagliate parole:")
    for word in ['casa', 'implementazione']:
        info = vocab.get_word_info(word)
        print(f"\n  {word}:")
        print(f"    - Nel vocabolario: {info.in_vocabulary}")
        print(f"    - Livello: {info.level or 'non classificato'}")
        if info.note:
            print(f"    - Note: {info.note}")

def test_readability_analyzer():
    """Test analizzatore leggibilità con vocabolario"""
    print("\n" + "=" * 70)
    print("TEST READABILITY ANALYZER")
    print("=" * 70)
    
    analyzer = ReadabilityAnalyzer()
    
    # Test testo semplice
    print("\n📝 TESTO SEMPLICE:")
    print(f'"{testo_semplice.strip()}"')
    print("\nAnalisi:")
    
    result = analyzer.analyze(testo_semplice)
    print(f"  Gulpease: {result['gulpease']}")
    print(f"  Parole: {result['words']}")
    
    if result['vocabulary']:
        vocab = result['vocabulary']
        print(f"  Copertura NVdB: {vocab['coverage_percentage']:.1f}%")
        print(f"  Qualità lessicale: {vocab['lexical_quality']}")
        print(f"  Parole difficili: {vocab['difficult_words_count']}")
    
    # Test testo complesso
    print("\n📝 TESTO COMPLESSO:")
    print(f'"{testo_complesso.strip()}"')
    print("\nAnalisi:")
    
    result = analyzer.analyze(testo_complesso)
    print(f"  Gulpease: {result['gulpease']}")
    print(f"  Parole: {result['words']}")
    
    if result['vocabulary']:
        vocab = result['vocabulary']
        print(f"  Copertura NVdB: {vocab['coverage_percentage']:.1f}%")
        print(f"  Qualità lessicale: {vocab['lexical_quality']}")
        print(f"  Parole difficili: {vocab['difficult_words_count']}")
        if vocab['difficult_words_sample']:
            print(f"  Esempi: {', '.join(vocab['difficult_words_sample'][:5])}")

def main():
    print("\n🧪 TEST INTEGRAZIONE VOCABOLARIO DI BASE")
    
    test_vocabulary_service()
    test_readability_analyzer()
    
    print("\n" + "=" * 70)
    print("✓ Test completati con successo!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
