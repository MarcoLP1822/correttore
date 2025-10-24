#!/usr/bin/env python3
"""Test rapido per vedere se OpenAI corregge gli errori visibili"""

import asyncio
from correttore.services.openai_service import OpenAIService

# Errori ESATTI dalle immagini
test_cases = [
    ("C'era una vlta", "Dovrebbe correggere: vlta → volta"),
    ("in un piccolo borggo", "Dovrebbe correggere: borggo → borgo"),
    ("mani callose carezzzzavano", "Dovrebbe correggere: carezzzzavano → carezzavano"),
    ("Per duee giorni", "Dovrebbe correggere: duee → due"),
    ("il legno milliore", "Dovrebbe correggere: milliore → migliore"),
    ("la cassa fu prontal", "Dovrebbe correggere: prontal → pronta"),
    ("e incise sul coperchio c erano", "Dovrebbe correggere: c erano → c'erano"),
    ("Qvesta essere una", "Dovrebbe correggere: Qvesta → Questa"),
    ("una cassella di testo", "Dovrebbe correggere: cassella → casella"),
    ("Acondroplasiaaa", "Dovrebbe correggere: Acondroplasiaaa → Acondroplasia"),
    ("tuttavvqja alcune note", "Dovrebbe correggere: tuttavvqja → tuttavia"),
    ("non sono smplca", "Dovrebbe correggere: smplca → semplice"),
    ("commissionardiglù", "Dovrebbe correggere il dialetto/errore"),
]

print("🧪 TEST RAPIDO CORREZIONI OPENAI\n")
print("="*70)

async def test_all():
    service = OpenAIService()
    
    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"\n{i}. ORIGINALE: '{text}'")
        print(f"   {expected}")
        
        corrected = await service.correct_text_async(text)
        
        if corrected:
            if corrected == text:
                print(f"   ❌ NON MODIFICATO: '{corrected}'")
            else:
                print(f"   ✅ CORRETTO IN:   '{corrected}'")
        else:
            print(f"   ❌ ERRORE - Nessuna risposta")
        
        # Piccola pausa per non sovraccaricare
        await asyncio.sleep(0.5)

print("\n🚀 Inizio test con OpenAI...\n")
asyncio.run(test_all())
print("\n" + "="*70)
print("\n✅ Test completati!")
