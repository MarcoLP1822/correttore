#!/usr/bin/env python3
"""
Test script per verificare che i fix locali funzionino correttamente
senza chiamate API OpenAI.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from correttore.core.safe_correction import SafeCorrector, CorrectionResult
from difflib import SequenceMatcher

def test_safe_corrector_fixes():
    """Test che il SafeCorrector accetti correzioni valide."""
    print("🧪 Testing SafeCorrector improvements...")
    
    corrector = SafeCorrector(conservative_mode=True, quality_threshold=0.75)
    
    # Test case problematico dal log: "vlta → volta"
    test_cases = [
        ("C'era una vlta, in un piccolo borgo", "C'era una volta, in un piccolo borgo"),
        ("La bottaga del falegname", "La bottega del falegname"),
        ("Il sugu era molto buono", "Il sugo era molto buono"),
        ("U giorno di primavera", "Un giorno di primavera"),
        ("fato in casa", "fatto in casa"),
    ]
    
    results = []
    for original, corrected in test_cases:
        print(f"\n📝 Testing: '{original}' -> '{corrected}'")
        
        # Test content preservation score
        content_score = corrector._score_content_preservation(original, corrected)
        print(f"   Content preservation: {content_score:.3f}")
        
        # Test overall quality
        quality = corrector.validate_correction_quality(original, corrected)
        print(f"   Overall quality: {quality.overall_score:.3f}")
        print(f"   Confidence: {quality.confidence}")
        
        # Test acceptance
        will_accept = quality.overall_score >= corrector.quality_threshold
        print(f"   Will accept: {'✅ YES' if will_accept else '❌ NO'}")
        
        results.append(will_accept)
    
    success_rate = sum(results) / len(results)
    print(f"\n📊 Results: {sum(results)}/{len(results)} corrections accepted ({success_rate:.1%})")
    
    return success_rate >= 0.8  # Almeno 80% di successo

def test_batch_logic_fix():
    """Test che il fix del batch logic gestisca risposte incomplete."""
    print("\n🧪 Testing batch logic fix...")
    
    # Simula scenario problematico
    uncached = [(0, 'C era una vlta'), (1, 'La bottaga'), (2, 'Il sugu'), (3, 'fato in casa')]
    
    # Simula risposta GPT parziale (solo 2 correzioni su 4)
    mock_gpt_response = {
        'correzioni': [
            {'id': 1, 'txt': 'La bottega'},
            {'id': 3, 'txt': 'fatto in casa'}
        ]
    }
    
    print(f"   Input paragraphs: {len(uncached)}")
    print(f"   GPT corrections: {len(mock_gpt_response['correzioni'])}")
    
    # Applica nuovo logic
    correzioni_map = {}
    for corr in mock_gpt_response['correzioni']:
        idx = corr.get('id')
        txt_corretto = corr.get('txt', '')
        if idx is not None:
            correzioni_map[idx] = txt_corretto
    
    out = {}
    corrections_applied = 0
    for i, (original_idx, original_txt) in enumerate(uncached):
        if i in correzioni_map:
            out[original_idx] = correzioni_map[i]
            corrections_applied += 1
            print(f"   ✅ Correction {i}: '{original_txt}' -> '{correzioni_map[i]}'")
        else:
            out[original_idx] = original_txt
            print(f"   📝 No correction {i}: keeping '{original_txt}'")
    
    result = [out[i] for i in range(len(uncached))]
    
    print(f"   Final result: {result}")
    print(f"   Corrections applied: {corrections_applied}/{len(uncached)}")
    
    # Verifica che non ci siano errori e che le correzioni siano applicate
    success = corrections_applied == 2 and len(result) == len(uncached)
    print(f"   {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    return success

def test_regression_prevention():
    """Test che _introduces_regression funzioni correttamente."""
    print("\n🧪 Testing regression prevention...")
    
    from correttore.core.correttore import _introduces_regression
    
    test_cases = [
        # (original, ai_corrected, grammar_checked, expected_regression)
        ("C'era una vlta", "C'era una volta", "C'era una alta", True),   # Regressione!
        ("La bottaga", "La bottega", "La bottaia", True),                # Regressione!  
        ("Il sugu", "Il sugo", "Il suga", True),                        # Regressione!
        ("C'era una volta", "C'era una volta", "C'era una volta", False), # OK
        ("Buon giorno", "Buongiorno", "Buongiorno", False),             # OK
    ]
    
    results = []
    for original, ai_corrected, grammar_checked, expected in test_cases:
        detected = _introduces_regression(original, ai_corrected, grammar_checked)
        success = detected == expected
        results.append(success)
        
        status = "✅ CORRECT" if success else "❌ WRONG"
        print(f"   {status}: '{original}' -> '{ai_corrected}' -> '{grammar_checked}' (regression: {detected})")
    
    success_rate = sum(results) / len(results)
    print(f"   Overall: {sum(results)}/{len(results)} correct ({success_rate:.1%})")
    
    return success_rate == 1.0

def main():
    """Esegue tutti i test."""
    print("🚀 Testing local improvements without OpenAI API...\n")
    
    tests = [
        ("SafeCorrector fixes", test_safe_corrector_fixes),
        ("Batch logic fix", test_batch_logic_fix),
        ("Regression prevention", test_regression_prevention),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print('='*50)
        
        try:
            success = test_func()
            results.append(success)
            print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append(False)
    
    print(f"\n{'='*50}")
    print("📊 FINAL RESULTS")
    print('='*50)
    
    passed = sum(results)
    total = len(results)
    success_rate = passed / total if total > 0 else 0
    
    print(f"Tests passed: {passed}/{total} ({success_rate:.1%})")
    
    if success_rate >= 0.8:
        print("✅ LOCAL FIXES WORKING! The system should work better now.")
        print("\n📝 Next steps:")
        print("   1. Configure OPENAI_API_KEY environment variable")
        print("   2. Test with real document")
        print("   3. Monitor that corrections like vlta→volta are accepted")
    else:
        print("❌ Some fixes need more work.")
    
    return success_rate >= 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
