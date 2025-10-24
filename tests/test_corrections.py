#!/usr/bin/env python3
"""
Script di test per verificare le correzioni
"""

from correttore.services.openai_service import OpenAIService
from correttore.core.safe_correction import SafeCorrector, QualityScore

# Test texts con errori
test_cases = [
    "C'era una vlta, in un piccolo borggo",
    "duee giorni interi lavorò",
    "le sue mani callose carezzzzavano",
    "Quando la cassa fu prontal",
    "Qvesta essere una cassella di testo",
    "Acondroplasiaaa",
    "lu sugu te lu calzone",
    "Come che te go fato",
    "La cane",
    "c erano una farfalla"
]

print("🧪 Test Correzioni\n")
print("="*60)

# Test OpenAI Service
print("\n1️⃣  Test OpenAI Service:")
print("-"*60)

openai_service = OpenAIService()

for i, text in enumerate(test_cases[:3], 1):  # Solo primi 3 per non consumare troppi token
    print(f"\n{i}. Input:  '{text}'")
    corrected = openai_service.correct_text(text)
    if corrected:
        print(f"   Output: '{corrected}'")
        if corrected != text:
            print(f"   ✅ CORRETTO")
        else:
            print(f"   ⚠️  NON MODIFICATO")
    else:
        print(f"   ❌ ERRORE")

# Test SafeCorrector
print("\n\n2️⃣  Test SafeCorrector Quality Scores:")
print("-"*60)

safe_corrector = SafeCorrector(quality_threshold=0.55)

# Simula correzioni
test_corrections = [
    ("vlta", "volta"),
    ("borggo", "borgo"),
    ("duee", "due"),
    ("Qvesta", "Questa"),
    ("carezzzzavano", "carezzavano"),
    ("Acondroplasiaaa", "Acondroplasia"),
]

for original, corrected in test_corrections:
    quality = safe_corrector.validate_correction_quality(original, corrected)
    status = "✅ PASS" if quality.overall_score >= 0.55 else "❌ FAIL"
    print(f"\n'{original}' → '{corrected}'")
    print(f"  Score: {quality.overall_score:.2%} - Confidence: {quality.confidence.value} {status}")
    if quality.issues:
        print(f"  Issues: {', '.join(quality.issues)}")

print("\n" + "="*60)
print("\n✅ Test completati!")
