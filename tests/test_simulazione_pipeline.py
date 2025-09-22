#!/usr/bin/env python3
"""
Test simulato della pipeline invertita senza OpenAI API.
Simula il comportamento dell'AI e di LanguageTool per testare la logica anti-regressione.
"""

import sys
import asyncio
from pathlib import Path

# Aggiungi il path per gli import
sys.path.append('src/core')

def simulate_ai_correction(text: str) -> str:
    """Simula le correzioni che l'AI dovrebbe fare correttamente"""
    corrections = {
        'vlta': 'volta',
        'bottaga': 'bottega',
        'sugu': 'sugo',
        'U giorno': 'Un giorno',
        'alfredo': 'Alfredo',
        'ansiano': 'anziano',
    }
    
    result = text
    for error, correction in corrections.items():
        result = result.replace(error, correction)
    
    return result

def simulate_languagetool_old_pipeline(text: str) -> str:
    """Simula le correzioni problematiche che LanguageTool faceva prima"""
    # Queste sono le correzioni SBAGLIATE che LanguageTool faceva
    problematic_corrections = {
        'vlta': 'alta',          # Errore semantico
        'bottaga': 'bottaia',    # Errore semantico
        'sugu': 'suga',          # Errore semantico
    }
    
    result = text
    for error, bad_correction in problematic_corrections.items():
        result = result.replace(error, bad_correction)
    
    return result

def simulate_languagetool_quality_check(text: str) -> str:
    """Simula LanguageTool in modalità quality check (nuovo pipeline)"""
    # Solo correzioni evidenti che non causano problemi semantici
    safe_corrections = {
        'CAPTIOLO': 'CAPITOLO',
        'carezzzzavano': 'carezzavano', 
        ' go ': ' ho ',
        'fato': 'fatto',
    }
    
    result = text
    for error, correction in safe_corrections.items():
        result = result.replace(error, correction)
    
    return result

async def test_pipeline_logic():
    """Testa la logica della pipeline senza API esterne"""
    
    print("🧪 Test Logica Pipeline - Simulazione")
    print("="*50)
    
    # Import della funzione anti-regressione
    try:
        from correttore import _introduces_regression  # type: ignore[reportMissingImports]
        print("✅ Funzione _introduces_regression importata correttamente")
    except ImportError as e:
        print(f"❌ Errore import: {e}")
        return
    
    test_cases = [
        "C'era una vlta un principe",
        "Visitò la bottaga del falegname", 
        "Preparò un ottimo sugu",
        "U giorno andò al mercato",
        "Il falegname alfredo lavorava",
        "ansiano nonno raccontava storie",
        "CAPTIOLO primo del libro",
        "carezzzzavano il gatto",
    ]
    
    print("\n📊 Test Comparativo Pipeline:")
    print("="*50)
    
    for i, original in enumerate(test_cases, 1):
        print(f"\n{i}. Test case: '{original}'")
        print("-" * 40)
        
        # VECCHIA PIPELINE: LanguageTool → AI
        lt_first = simulate_languagetool_old_pipeline(original)
        ai_after_lt = simulate_ai_correction(lt_first)
        
        # NUOVA PIPELINE: AI → LanguageTool (Quality Check)
        ai_first = simulate_ai_correction(original)
        
        # Test anti-regressione
        lt_after_ai = simulate_languagetool_old_pipeline(ai_first)  # Simula tentativo regressione
        
        # Verifica se la funzione anti-regressione blocca il problema
        regression_detected = _introduces_regression(original, ai_first, lt_after_ai)
        
        if regression_detected:
            final_new_pipeline = ai_first  # Mantiene correzione AI
            quality_check_applied = "❌ Bloccato (regressione rilevata)"
        else:
            # Se non c'è regressione, applica quality check sicuro
            final_new_pipeline = simulate_languagetool_quality_check(ai_first)
            quality_check_applied = "✅ Applicato (sicuro)"
        
        print(f"   Vecchia pipeline: '{original}' → '{ai_after_lt}'")
        print(f"   Nuova pipeline:   '{original}' → '{final_new_pipeline}'")
        print(f"   Quality check:    {quality_check_applied}")
        
        # Valutazione
        if ai_after_lt != final_new_pipeline:
            print(f"   📈 MIGLIORAMENTO: nuova pipeline produce risultato diverso")
        else:
            print(f"   ✅ MANTENUTO: stesso risultato di qualità")
    
    print(f"\n🎯 Risultati attesi:")
    print("   • vlta → volta (non più → alta)")
    print("   • bottaga → bottega (non più → bottaia)")
    print("   • sugu → sugo (non più → suga)")
    print("   • Altre correzioni preservate")

async def main():
    await test_pipeline_logic()

if __name__ == "__main__":
    asyncio.run(main())
