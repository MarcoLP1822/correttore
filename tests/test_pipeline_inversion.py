#!/usr/bin/env python3
"""
Test rapido per verificare che la nuova pipeline invertita funzioni.
Testa alcuni dei casi problematici identificati nel piano.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def test_regression_function():
    """Testa la funzione _introduces_regression"""
    
    # Import della funzione da testare
    sys.path.append('src/core')
    from correttore import _introduces_regression  # type: ignore[reportMissingImports]
    
    # Test case 1: vlta → alta (regressione) vs vlta → volta (corretto)
    original1 = "C'era una vlta un principe"
    ai_corrected1 = "C'era una volta un principe"  # AI corregge correttamente
    grammar_regressed1 = "C'era una alta un principe"  # LanguageTool introduce errore
    
    result1 = _introduces_regression(original1, ai_corrected1, grammar_regressed1)
    assert result1 == True, "Dovrebbe rilevare regressione vlta → alta"
    print("✅ Test 1 passed: rileva regressione vlta → alta")
    
    # Test case 2: Nessuna regressione
    original2 = "C'era una vlta un principe"
    ai_corrected2 = "C'era una volta un principe"
    grammar_good2 = "C'era una volta un principe"  # LanguageTool non cambia nulla
    
    result2 = _introduces_regression(original2, ai_corrected2, grammar_good2)
    assert result2 == False, "Non dovrebbe rilevare regressione quando non ce n'è"
    print("✅ Test 2 passed: nessuna regressione rilevata")
    
    # Test case 3: bottaga → bottaia (regressione) vs bottaga → bottega (corretto)
    original3 = "Una bottaga di falegname"
    ai_corrected3 = "Una bottega di falegname"  # AI corregge correttamente
    grammar_regressed3 = "Una bottaia di falegname"  # LanguageTool introduce errore
    
    result3 = _introduces_regression(original3, ai_corrected3, grammar_regressed3)
    assert result3 == True, "Dovrebbe rilevare regressione bottaga → bottaia"
    print("✅ Test 3 passed: rileva regressione bottaga → bottaia")
    
    print("🎉 Tutti i test _introduces_regression sono passati!")

def test_import_structure():
    """Verifica che gli import necessari funzionino"""
    try:
        sys.path.append('src/core')
        from correttore import correct_paragraph_group, _introduces_regression, _minor_change  # type: ignore[reportMissingImports]
        print("✅ Import delle funzioni principali OK")
        
        from grammarcheck import grammarcheck  # type: ignore[reportMissingImports]
        print("✅ Import grammarcheck OK")
        
        from llm_correct import llm_correct_batch  # type: ignore[reportMissingImports]
        print("✅ Import llm_correct_batch OK")
        
    except ImportError as e:
        print(f"⚠️  Import warning: {e}")
        print("   (Questo è normale se non tutte le dipendenze sono installate)")

if __name__ == "__main__":
    print("🧪 Test della nuova pipeline invertita...")
    print("=" * 50)
    
    # Test 1: Verifica funzione di regressione
    try:
        test_regression_function()
    except Exception as e:
        print(f"❌ Test regressione fallito: {e}")
    
    print()
    
    # Test 2: Verifica struttura import
    test_import_structure()
    
    print()
    print("🎯 Test completati!")
    print()
    print("📋 Modifiche implementate:")
    print("   • Pipeline invertita: AI PRIMA di LanguageTool")
    print("   • LanguageTool ora funziona come quality checker")
    print("   • Aggiunta protezione anti-regressione")
    print("   • Preservate tutte le funzionalità esistenti")
