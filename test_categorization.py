#!/usr/bin/env python3
"""Test categorizzazione errori punteggiatura"""

import sys
sys.path.insert(0, 'src')

from correttore.utils.corrige_categorizer import CorrigeCategorizer, CorrectionContext, CorrigeCategory

categorizer = CorrigeCategorizer()

# Test vari tipi di correzioni
test_cases = [
    {
        "name": "Spazio dopo virgola",
        "original": "Aurelia,due",
        "corrected": "Aurelia, due",
        "context": "Aurelia,due cuori che si amano",
        "expected": CorrigeCategory.PUNTEGGIATURA
    },
    {
        "name": "Errore ortografico",
        "original": "vlta",
        "corrected": "volta",
        "context": "una vlta al giorno",
        "expected": CorrigeCategory.ERRORI
    },
    {
        "name": "Spazio mancante",
        "original": "equilibrio,unendo",
        "corrected": "equilibrio, unendo",
        "context": "trovano il loro equilibrio,unendo il calore",
        "expected": CorrigeCategory.PUNTEGGIATURA
    },
]

print("=" * 70)
print("TEST CATEGORIZZAZIONE ERRORI")
print("=" * 70)

for test in test_cases:
    print(f"\n📝 Test: {test['name']}")
    print(f"   Original: '{test['original']}'")
    print(f"   Corrected: '{test['corrected']}'")
    
    context = CorrectionContext(
        original_text=test['original'],
        corrected_text=test['corrected'],
        paragraph_context=test['context'],
        position=0,
        correction_type='test',
        rule_id='TEST_RULE'
    )
    
    result = categorizer.categorize_correction(context)
    
    expected_cat = test['expected']
    actual_cat = result.category
    
    status = "✅ PASS" if actual_cat == expected_cat else "❌ FAIL"
    
    print(f"   Expected: {expected_cat.value}")
    print(f"   Actual:   {actual_cat.value}")
    print(f"   {status}")

print("\n" + "=" * 70)
print("TEST COMPLETATI")
print("=" * 70)
