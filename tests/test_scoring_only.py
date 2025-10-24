#!/usr/bin/env python3
"""Test del sistema di scoring per vedere se accetta le correzioni"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from correttore.core.safe_correction import SafeCorrector

# Errori ESATTI dalle immagini con le correzioni attese
test_corrections = [
    ("vlta", "volta", "Correzione ortografica"),
    ("borggo", "borgo", "Doppia consonante errata"),
    ("carezzzzavano", "carezzavano", "Troppe z"),
    ("duee", "due", "Doppia e errata"),
    ("milliore", "migliore", "ll → gl"),
    ("prontal", "pronta", "l finale errato"),
    ("c erano", "c'erano", "Apostrofo mancante"),
    ("Qvesta", "Questa", "Q → Qu"),
    ("cassella", "casella", "Doppia s errata"),
    ("Acondroplasiaaa", "Acondroplasia", "Troppe a"),
    ("tuttavvqja", "tuttavia", "vvqj → vi"),
    ("smplca", "semplice", "Lettere mancanti"),
    ("commissionardiglù", "commissionargli", "Dialetto/errore"),
    ("bottaga", "bottega", "a → e"),
    ("bottaia", "bottega", "ai → eg"),
]

print("🧪 TEST SISTEMA DI SCORING\n")
print("="*80)

safe_corrector = SafeCorrector(quality_threshold=0.55)

passed = 0
failed = 0

for original, corrected, description in test_corrections:
    quality = safe_corrector.validate_correction_quality(original, corrected)
    
    # Una correzione passa se supera la soglia
    is_accepted = quality.overall_score >= 0.55
    
    if is_accepted:
        status = "✅ PASS"
        passed += 1
    else:
        status = "❌ FAIL"
        failed += 1
    
    print(f"\n{status} '{original}' → '{corrected}'")
    print(f"    {description}")
    print(f"    Score: {quality.overall_score:.2%} | Confidence: {quality.confidence.value}")
    print(f"    Content: {quality.content_preservation:.2%} | Grammar: {quality.grammar_improvement:.2%}")
    print(f"    Style: {quality.style_preservation:.2%} | Safety: {quality.safety_score:.2%}")
    
    if not is_accepted:
        print(f"    ⚠️  SOTTO SOGLIA 55% - Correzione rifiutata!")
        if quality.issues:
            print(f"    Issues: {', '.join(quality.issues)}")

print("\n" + "="*80)
print(f"\n📊 RISULTATI:")
print(f"   ✅ Passati: {passed}/{len(test_corrections)} ({passed/len(test_corrections)*100:.1f}%)")
print(f"   ❌ Falliti: {failed}/{len(test_corrections)} ({failed/len(test_corrections)*100:.1f}%)")

if failed > 0:
    print(f"\n⚠️  {failed} correzioni verrebbero rifiutate dal sistema!")
    print("   La soglia potrebbe essere ancora troppo alta.")
else:
    print("\n✅ Tutte le correzioni sarebbero accettate!")
