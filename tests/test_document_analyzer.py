"""
Test script per DocumentAnalyzer - FASE 2

Test delle funzionalità principali del DocumentAnalyzer.
"""

import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correttore.core import DocumentAnalyzer
from correttore.models import AnalysisConfig

def test_text_analysis():
    """Test analisi testo semplice"""
    print("=" * 60)
    print("TEST 1: Analisi testo semplice")
    print("=" * 60)
    
    # Crea analyzer senza LanguageTool (per velocità)
    config = AnalysisConfig(
        enable_languagetool=False,
        enable_readability=True,
        enable_special_categories=False
    )
    
    analyzer = DocumentAnalyzer(config=config)
    
    # Testo di test
    test_text = """
    Questo è un testo di prova per testare l'analisi di leggibilità.
    Il sistema deve calcolare l'indice Gulpease e determinare il livello di difficoltà.
    Alcune frasi sono più complesse di altre.
    """
    
    print(f"\n📝 Testo da analizzare:")
    print(test_text)
    
    # Analizza
    result = analyzer.analyze_text(test_text)
    
    print(f"\n✅ Risultati analisi:")
    print(f"   - Punteggio leggibilità: {result.get('readability_score', 'N/A')}")
    print(f"   - Livello difficoltà: {result.get('readability_level', 'N/A')}")
    print(f"   - Totale parole: {result.get('total_words', 'N/A')}")
    
    return result

def test_analyzer_initialization():
    """Test inizializzazione con diverse configurazioni"""
    print("\n" + "=" * 60)
    print("TEST 2: Inizializzazione con diverse config")
    print("=" * 60)
    
    # Config 1: Solo readability
    config1 = AnalysisConfig(
        enable_languagetool=False,
        enable_readability=True,
        enable_special_categories=False
    )
    analyzer1 = DocumentAnalyzer(config=config1)
    print(f"\n✅ Config 1 (solo readability):")
    print(f"   - LT: {analyzer1.enable_languagetool}")
    print(f"   - Read: {analyzer1.enable_readability}")
    print(f"   - Special: {analyzer1.enable_special_categories}")
    
    # Config 2: Tutti disabilitati
    config2 = AnalysisConfig(
        enable_languagetool=False,
        enable_readability=False,
        enable_special_categories=False
    )
    analyzer2 = DocumentAnalyzer(config=config2)
    print(f"\n✅ Config 2 (tutti disabilitati):")
    print(f"   - LT: {analyzer2.enable_languagetool}")
    print(f"   - Read: {analyzer2.enable_readability}")
    print(f"   - Special: {analyzer2.enable_special_categories}")
    
    # Config 3: Parametri diretti (no config object)
    analyzer3 = DocumentAnalyzer(
        enable_languagetool=False,
        enable_readability=True,
        enable_special_categories=True
    )
    print(f"\n✅ Config 3 (parametri diretti):")
    print(f"   - LT: {analyzer3.enable_languagetool}")
    print(f"   - Read: {analyzer3.enable_readability}")
    print(f"   - Special: {analyzer3.enable_special_categories}")

def main():
    """Esegue tutti i test"""
    print("\n" + "🔍" * 30)
    print("DOCUMENT ANALYZER - TEST SUITE")
    print("🔍" * 30 + "\n")
    
    try:
        # Test 1: Analisi testo
        test_text_analysis()
        
        # Test 2: Inizializzazione
        test_analyzer_initialization()
        
        print("\n" + "=" * 60)
        print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE I TEST: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
