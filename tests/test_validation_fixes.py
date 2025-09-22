#!/usr/bin/env python3
# test_validation_fixes.py

"""Test rapido per verificare che le soglie di validazione siano più permissive"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from core.validation import validate_correction, DocumentValidator
from core.safe_correction import SafeCorrector

def test_semantic_corrections():
    """Test correzioni semantiche che prima fallivano"""
    
    validator = DocumentValidator()
    safe_corrector = SafeCorrector()
    
    # Casi test specifici dal nostro racconto
    test_cases = [
        ("vlta", "volta"),  # Correzione semantica critica
        ("bottaga", "bottega"),  # Correzione semantica critica
        ("sugu", "sugo"),  # Correzione semantica critica
        ("CAPTIOLO", "CAPITOLO"),  # Già funzionava
        ("go fatto", "ho fatto"),  # Già funzionava
        ("La cane", "Il cane"),  # Già funzionava
    ]
    
    print("=== Test Validation Fixes ===\n")
    
    for original, corrected in test_cases:
        print(f"Test: '{original}' → '{corrected}'")
        
        # Test validazione base
        basic_valid = validate_correction(original, corrected)
        print(f"  ✓ Validazione base: {'PASS' if basic_valid else 'FAIL'}")
        
        # Test integrità paragrafo
        paragraph_valid = validator.validate_paragraph_integrity(original, corrected)
        print(f"  ✓ Integrità paragrafo: {'PASS' if paragraph_valid else 'FAIL'}")
        
        # Test SafeCorrector
        quality_score = safe_corrector.validate_correction_quality(original, corrected)
        safe_valid = quality_score.overall_score >= 0.75  # Nostra soglia
        print(f"  ✓ SafeCorrector (score: {quality_score.overall_score:.3f}): {'PASS' if safe_valid else 'FAIL'}")
        
        if quality_score.issues:
            print(f"    Issues: {', '.join(quality_score.issues)}")
        
        print()

if __name__ == "__main__":
    test_semantic_corrections()
