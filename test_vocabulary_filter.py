#!/usr/bin/env python3
"""
Test per verificare il filtro del vocabolario personalizzato
"""

# Test 1: Verifica caricamento vocabolario
print("=" * 60)
print("TEST 1: Caricamento vocabolario")
print("=" * 60)

from src.correttore.core.grammarcheck import _load_custom_vocabulary

vocab = _load_custom_vocabulary()
print(f"✓ Vocabolario caricato: {len(vocab)} parole")

# Test parole critiche
test_words = ['universo', 'attraversare', 'antiviolenza', 'videochiamata']
print("\nVerifica parole nel vocabolario:")
for word in test_words:
    present = word in vocab
    status = "✅" if present else "❌"
    print(f"  {status} {word}: {'presente' if present else 'MANCANTE'}")

# Test 2: Verifica grammarcheck
print("\n" + "=" * 60)
print("TEST 2: Test grammarcheck con parole del vocabolario")
print("=" * 60)

from src.correttore.core.grammarcheck import grammarcheck

testi_test = [
    "L'universo è vasto e misterioso.",
    "Dobbiamo attraversare il ponte.",
    "Il centro antiviolenza è aperto.",
    "Ho ricevuto una videochiamata importante."
]

for testo in testi_test:
    risultato = grammarcheck(testo)
    cambiato = "🔄 MODIFICATO" if risultato != testo else "✅ INVARIATO"
    print(f"\n{cambiato}")
    print(f"  Original: {testo}")
    if risultato != testo:
        print(f"  Corrected: {risultato}")

# Test 3: Test con LanguageTool Service
print("\n" + "=" * 60)
print("TEST 3: Test LanguageTool Service")
print("=" * 60)

try:
    from src.correttore.services.languagetool_service import LanguageToolService
    
    service = LanguageToolService()
    
    test_text = "L'universo è infinito. Dobbiamo attraversare il fiume. Il centro antiviolenza aiuta le vittime."
    
    errors = service.check_text(test_text, use_cache=False)
    
    print(f"Errori trovati dopo filtro: {len(errors)}")
    if errors:
        print("\nErrori rimanenti:")
        for err in errors[:5]:  # Mostra max 5
            print(f"  - {err.rule_id}: {err.message}")
    else:
        print("✅ Nessun errore trovato (come previsto)")
        
except Exception as e:
    print(f"⚠️ Test LanguageTool Service fallito (potrebbe essere normale se server non attivo): {e}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETATI")
print("=" * 60)
