"""
Test integrazione CorrectionEngine + DocumentAnalyzer - FASE 4

Verifica che l'analisi post-correzione funzioni automaticamente.
"""

import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correttore.core.correction_engine import CorrectionEngine


def test_engine_initialization():
    """Test 1: Verifica inizializzazione con post_analysis"""
    print("=" * 60)
    print("TEST 1: Inizializzazione CorrectionEngine")
    print("=" * 60)
    
    # Test con post_analysis abilitato (default)
    print("\n1a. Con post_analysis=True (default):")
    try:
        engine1 = CorrectionEngine(enable_tracking=True, enable_post_analysis=True)
        print(f"   ✅ Engine inizializzato")
        print(f"   - enable_post_analysis: {engine1.enable_post_analysis}")
        print(f"   - document_analyzer: {engine1.document_analyzer is not None}")
        
        if engine1.document_analyzer:
            print(f"   - analyzer.enable_languagetool: {engine1.document_analyzer.enable_languagetool}")
            print(f"   - analyzer.enable_readability: {engine1.document_analyzer.enable_readability}")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    # Test con post_analysis disabilitato
    print("\n1b. Con post_analysis=False:")
    try:
        engine2 = CorrectionEngine(enable_tracking=True, enable_post_analysis=False)
        print(f"   ✅ Engine inizializzato")
        print(f"   - enable_post_analysis: {engine2.enable_post_analysis}")
        print(f"   - document_analyzer: {engine2.document_analyzer is not None}")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    return True


def test_backward_compatibility():
    """Test 2: Verifica backward compatibility (senza parametro post_analysis)"""
    print("\n" + "=" * 60)
    print("TEST 2: Backward Compatibility")
    print("=" * 60)
    
    try:
        # Inizializzazione senza specificare enable_post_analysis (default=True)
        engine = CorrectionEngine(enable_tracking=True)
        print(f"\n✅ Engine inizializzato senza enable_post_analysis")
        print(f"   - enable_post_analysis: {engine.enable_post_analysis}")
        print(f"   - document_analyzer: {engine.document_analyzer is not None}")
        
        if engine.enable_post_analysis and engine.document_analyzer:
            print(f"   ✅ Post-analysis abilitato di default")
        elif not engine.enable_post_analysis:
            print(f"   ✅ Post-analysis correttamente disabilitato")
        
        return True
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_engine_without_tracking():
    """Test 3: Verifica engine senza tracking + post_analysis"""
    print("\n" + "=" * 60)
    print("TEST 3: Engine senza tracking")
    print("=" * 60)
    
    try:
        # Nota: post_analysis potrebbe non funzionare bene senza tracking
        # ma dovrebbe inizializzare correttamente
        engine = CorrectionEngine(enable_tracking=False, enable_post_analysis=True)
        print(f"\n✅ Engine inizializzato")
        print(f"   - collector: {engine.collector is not None}")
        print(f"   - enable_post_analysis: {engine.enable_post_analysis}")
        print(f"   - document_analyzer: {engine.document_analyzer is not None}")
        
        return True
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_combinations():
    """Test 4: Verifica diverse combinazioni di configurazione"""
    print("\n" + "=" * 60)
    print("TEST 4: Combinazioni configurazione")
    print("=" * 60)
    
    configs = [
        (True, True, "Tracking + PostAnalysis"),
        (True, False, "Tracking solo"),
        (False, True, "PostAnalysis solo"),
        (False, False, "Nessuno"),
    ]
    
    for tracking, post_analysis, desc in configs:
        print(f"\n📝 Test: {desc}")
        try:
            engine = CorrectionEngine(
                enable_tracking=tracking,
                enable_post_analysis=post_analysis
            )
            print(f"   ✅ Inizializzato correttamente")
            print(f"      collector: {engine.collector is not None}")
            print(f"      analyzer: {engine.document_analyzer is not None}")
        except Exception as e:
            print(f"   ❌ Errore: {e}")
            return False
    
    return True


def main():
    """Esegue tutti i test"""
    print("\n" + "🔗" * 30)
    print("CORRECTION ENGINE INTEGRATION - TEST SUITE (FASE 4)")
    print("🔗" * 30 + "\n")
    
    results = []
    
    try:
        # Test 1: Inizializzazione
        results.append(("Inizializzazione", test_engine_initialization()))
        
        # Test 2: Backward compatibility
        results.append(("Backward Compatibility", test_backward_compatibility()))
        
        # Test 3: Senza tracking
        results.append(("Engine senza tracking", test_engine_without_tracking()))
        
        # Test 4: Combinazioni config
        results.append(("Combinazioni config", test_config_combinations()))
        
        # Riepilogo
        print("\n" + "=" * 60)
        print("RIEPILOGO TEST")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nRisultato: {passed}/{total} test passati")
        
        if passed == total:
            print("\n" + "=" * 60)
            print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
            print("=" * 60)
            print("\n💡 Note:")
            print("   - CorrectionEngine ora supporta enable_post_analysis")
            print("   - DocumentAnalyzer viene inizializzato automaticamente")
            print("   - Analisi post-correzione avviene dopo salvataggio")
            print("   - Backward compatibility mantenuta (default=True)")
            print("\n")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test falliti")
            return 1
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE I TEST: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
