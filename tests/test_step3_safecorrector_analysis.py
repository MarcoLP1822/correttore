#!/usr/bin/env python3
"""
Test STEP 3: Analisi dettagliata del SafeCorrector per capire i rollback
"""

import logging
import sys
sys.path.append('.')

from src.core.safe_correction import SafeCorrector
from src.core.spellfix import spellfix_paragraph

# Setup logging più dettagliato
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_safecorrector_rollbacks():
    """Analizza in dettaglio perché SafeCorrector fa rollback"""
    
    test_cases = [
        ("vlta", "volta"),
        ("borggo", "borgo"), 
        ("ansiano", "anziano"),
        ("carezzzzavano", "carezzavano"),
        ("Qvesta", "Questa"),
    ]
    
    print("🔬 ANALISI DETTAGLIATA SAFECORRECTOR - STEP 3\n")
    print("=" * 80)
    
    # Test con diverse configurazioni
    configs = [
        ("Conservative TRUE, Threshold 0.75", True, 0.75),
        ("Conservative FALSE, Threshold 0.75", False, 0.75),
        ("Conservative FALSE, Threshold 0.50", False, 0.50),
        ("Conservative FALSE, Threshold 0.30", False, 0.30),
    ]
    
    for config_name, conservative, threshold in configs:
        print(f"\n🔧 CONFIGURAZIONE: {config_name}")
        print("-" * 60)
        
        safe_corrector = SafeCorrector(conservative_mode=conservative, quality_threshold=threshold)
        
        for original, expected in test_cases:
            print(f"\n📝 Test: '{original}' → '{expected}'")
            
            # Test qualità della correzione diretta
            quality_score = safe_corrector.validate_correction_quality(original, expected)
            
            print(f"   Quality Score: {quality_score.overall_score:.3f}")
            print(f"   Content Preservation: {quality_score.content_preservation:.3f}")
            print(f"   Grammar Improvement: {quality_score.grammar_improvement:.3f}")
            print(f"   Style Preservation: {quality_score.style_preservation:.3f}")
            print(f"   Safety Score: {quality_score.safety_score:.3f}")
            print(f"   Confidence: {quality_score.confidence}")
            print(f"   Issues: {quality_score.issues}")
            
            # Test se verrebbe applicata
            should_apply = safe_corrector._should_apply_correction(quality_score, "spellcheck")
            print(f"   Would Apply: {'✅ YES' if should_apply else '❌ NO'}")
            
            if not should_apply:
                rollback_reason = safe_corrector._get_rollback_reason(quality_score)
                print(f"   Rollback Reason: {rollback_reason}")
    
    # Test spellfix diretto
    print(f"\n🔧 TEST SPELLFIX DIRETTO")
    print("-" * 60)
    
    for original, expected in test_cases:
        spellfix_result = spellfix_paragraph(original, set())
        print(f"'{original}' → spellfix → '{spellfix_result}' (expected: '{expected}')")
        print(f"   Spellfix Match: {'✅' if spellfix_result == expected else '❌'}")

def test_specific_quality_scores():
    """Test specifici per capire i punteggi di qualità"""
    
    print(f"\n🔬 ANALISI PUNTEGGI SPECIFICI")
    print("=" * 80)
    
    # Test le correzioni semantiche note dal SafeCorrector stesso
    safe_corrector = SafeCorrector(conservative_mode=False, quality_threshold=0.30)
    
    semantic_corrections = [
        ('vlta', 'volta'), ('bottaga', 'bottega'), ('sugu', 'sugo'),
        ('CAPTIOLO', 'CAPITOLO'), ('go', 'ho'), ('fato', 'fatto'),
        ('La cane', 'Il cane'), ('Qvesta', 'Questa'), ('cassella', 'casella')
    ]
    
    print("Correzioni semantiche implementate nel SafeCorrector:")
    for orig, corr in semantic_corrections:
        quality = safe_corrector.validate_correction_quality(orig, corr)
        should_apply = safe_corrector._should_apply_correction(quality, "semantic")
        
        print(f"  '{orig}' → '{corr}': Quality={quality.overall_score:.3f}, Apply={'✅' if should_apply else '❌'}")
        
        if not should_apply:
            reason = safe_corrector._get_rollback_reason(quality)
            print(f"    Rollback: {reason}")

if __name__ == "__main__":
    analyze_safecorrector_rollbacks()
    test_specific_quality_scores()
