#!/usr/bin/env python3
"""
Test STEP 3: Analisi del motivo per cui alcuni errori vengono corretti e altri no
"""

import logging
import sys
import os
sys.path.append('.')

# Import delle funzioni principali
from correttore.core.precheck import has_errors
from correttore.core.spellfix import spellfix_paragraph
from correttore.core.safe_correction import SafeCorrector

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_full_pipeline_simulation():
    """Simula ESATTAMENTE quello che succede nella pipeline reale"""
    
    # Errori test dal documento
    test_paragraphs = {
        "CAPTIOLO 1": "CAPITOLO 1",
        "C'era una vlta, in un piccolo borggo arroccato tra le montagne, un ansiano falegname": 
            "C'era una volta, in un piccolo borgo arroccato tra le montagne, un anziano falegname",
        "Le sue mani callose carezzzzavano il legno": 
            "Le sue mani callose carezzavano il legno",
        "La cane": "Il cane",
        "Qvesta storia": "Questa storia",
    }
    
    print("🔍 SIMULAZIONE PIPELINE COMPLETA - STEP 3\n")
    print("=" * 80)
    
    correction_stats = {
        'filtrati_fuori': 0,
        'passati_filtro': 0,
        'spellcheck_successo': 0,
        'spellcheck_fallito': 0,
        'ai_necessaria': 0,
        'totali': len(test_paragraphs)
    }
    
    for i, (original, expected) in enumerate(test_paragraphs.items(), 1):
        print(f"\n📝 PARAGRAFO {i}: '{original[:50]}...'")
        print("-" * 50)
        
        # STEP 1: FILTRO has_errors()
        has_err = has_errors(original)
        print(f"1️⃣ FILTRO has_errors(): {has_err}")
        
        if not has_err:
            print("❌ PARAGRAFO SALTATO COMPLETAMENTE!")
            correction_stats['filtrati_fuori'] += 1
            continue
        
        correction_stats['passati_filtro'] += 1
        
        # STEP 2: SPELLCHECK
        current_text = original
        glossary = set()  # Glossario vuoto per test
        
        try:
            spellcheck_corrected = spellfix_paragraph(current_text, glossary)
            
            safe_corrector = SafeCorrector(conservative_mode=True, quality_threshold=0.75)
            
            # Simula la funzione spellcheck dentro SafeCorrector
            def spellcheck_func(text):
                return spellfix_paragraph(text, glossary)
            
            # Crea un mock paragraph object
            class MockParagraph:
                def __init__(self, text):
                    self._text = text
                
                @property
                def text(self):
                    return self._text
                
                @text.setter
                def text(self, value):
                    self._text = value
            
            mock_para = MockParagraph(current_text)
            spellcheck_result = safe_corrector.correct_with_rollback(
                mock_para, spellcheck_func, "spellcheck"
            )
            
            print(f"2️⃣ SPELLCHECK:")
            print(f"   Original: '{current_text}'")
            print(f"   Corrected: '{spellcheck_corrected}'")
            print(f"   Applied: {spellcheck_result.applied}")
            print(f"   Quality Score: {spellcheck_result.quality_score.overall_score:.3f}")
            
            if spellcheck_result.applied:
                current_text = spellcheck_result.corrected_text
                correction_stats['spellcheck_successo'] += 1
                print("   ✅ SPELLCHECK APPLICATO")
            else:
                correction_stats['spellcheck_fallito'] += 1
                print(f"   ❌ SPELLCHECK RIFIUTATO: {spellcheck_result.rollback_reason}")
                
        except Exception as e:
            print(f"   ⚠️ SPELLCHECK ERRORE: {e}")
            correction_stats['spellcheck_fallito'] += 1
        
        # STEP 3: Verifica se serve AI
        if current_text == original or abs(len(current_text) - len(original)) < 3:
            print("3️⃣ AI CORRECTION: Richiesta (testo invariato o poche modifiche)")
            correction_stats['ai_necessaria'] += 1
        else:
            print("3️⃣ AI CORRECTION: Non necessaria (già corretto sufficientemente)")
        
        # RISULTATO FINALE
        final_corrected = current_text != original
        print(f"\n🎯 RISULTATO FINALE:")
        print(f"   Input: '{original}'")
        print(f"   Output: '{current_text}'")
        print(f"   Corretto: {'✅ SÌ' if final_corrected else '❌ NO'}")
        print(f"   Aspettato: '{expected}'")
        print(f"   Match Aspettativa: {'✅ SÌ' if current_text == expected else '❌ NO'}")
    
    # STATISTICHE FINALI
    print("\n" + "=" * 80)
    print("📊 STATISTICHE PIPELINE COMPLETA")
    print("=" * 80)
    print(f"Paragrafi totali: {correction_stats['totali']}")
    print(f"Filtrati fuori da has_errors(): {correction_stats['filtrati_fuori']} ({correction_stats['filtrati_fuori']/correction_stats['totali']*100:.1f}%)")
    print(f"Passati il filtro: {correction_stats['passati_filtro']} ({correction_stats['passati_filtro']/correction_stats['totali']*100:.1f}%)")
    print(f"Spellcheck applicato: {correction_stats['spellcheck_successo']}")
    print(f"Spellcheck rifiutato: {correction_stats['spellcheck_fallito']}")
    print(f"AI necessaria: {correction_stats['ai_necessaria']}")
    
    # ANALISI PROBLEMI
    print("\n🔍 ANALISI PROBLEMI IDENTIFICATI:")
    if correction_stats['filtrati_fuori'] > 0:
        print(f"❌ PROBLEMA CRITICO: {correction_stats['filtrati_fuori']} paragrafi non vengono mai processati!")
    
    if correction_stats['spellcheck_fallito'] > 0:
        print(f"⚠️ PROBLEMA: {correction_stats['spellcheck_fallito']} spellcheck falliti (SafeCorrector troppo conservativo)")
    
    coverage_rate = (correction_stats['passati_filtro'] / correction_stats['totali']) * 100
    print(f"\n📈 COPERTURA PIPELINE: {coverage_rate:.1f}%")
    
    if coverage_rate < 100:
        print("❌ SISTEMA NON COPRE TUTTI GLI ERRORI!")
    else:
        print("✅ Tutti i paragrafi vengono processati")

if __name__ == "__main__":
    test_full_pipeline_simulation()
