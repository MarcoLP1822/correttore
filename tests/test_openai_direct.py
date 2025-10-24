#!/usr/bin/env python3
"""Test diretto per vedere cosa corregge OpenAI"""

import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv('.env.local')

# Frasi ESATTE dal documento con errori NON corretti
test_cases = [
    "Per duee giorni interi lavorò",
    "Quando la cassa fu prontal, la consegnò a Emma",
    "incise sul coperchio c erano una farfalla",
    "Qvesta essere una cassella di testo",
    "bottaga",
]

async def test_openai():
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    system_prompt = """Sei un correttore di bozze esperto in lingua italiana. 
Il tuo compito è correggere TUTTI gli errori di ortografia, grammatica e punteggiatura mantenendo:
- Il significato originale del testo
- Lo stile e il tono dell'autore
- La formattazione esistente
- I nomi propri e le citazioni

CORREZIONI PRIORITARIE:
- Errori ortografici evidenti (vlta→volta, borggo→borgo, duee→due, Qvesta→Questa, ecc.)
- Errori di battitura (carezzzzavano→carezzavano, Acondroplasiaaa→Acondroplasia)
- Articoli sbagliati (La cane→Il cane)
- Apostrofi mancanti (c erano→c'erano)
- Forme verbali errate (go→ho, fato→fatto)

Rispondi SOLO con il testo corretto, senza spiegazioni o commenti aggiuntivi."""

    print("🧪 TEST OPENAI DIRETTO\n")
    print("="*70)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. INPUT:  '{text}'")
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""Correggi il seguente testo in italiano, correggendo TUTTI gli errori:

TESTO DA CORREGGERE:
{text}

ISTRUZIONI:
1. Correggi TUTTI gli errori di ortografia, grammatica e punteggiatura
2. Presta particolare attenzione a:
   - Errori di battitura (lettere ripetute, lettere sbagliate)
   - Articoli errati (il/la, un/una)
   - Apostrofi mancanti
   - Parole incomplete o errate
3. Mantieni la formattazione esistente (maiuscole, corsivi, etc.)
4. Non modificare nomi propri, luoghi o citazioni già corretti
5. Preserva lo stile e il tono originale

TESTO CORRETTO:"""}
                ],
                temperature=0.0,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            if content is None:
                print(f"   ❌ ERRORE: Risposta vuota da OpenAI")
                continue
                
            corrected = content.strip()
            
            if corrected == text:
                print(f"   ❌ NON MODIFICATO")
            else:
                print(f"   OUTPUT: '{corrected}'")
                print(f"   ✅ CORRETTO")
                
        except Exception as e:
            print(f"   ❌ ERRORE: {e}")
        
        await asyncio.sleep(0.5)
    
    print("\n" + "="*70)
    print("\n✅ Test completati!")

if __name__ == "__main__":
    asyncio.run(test_openai())
