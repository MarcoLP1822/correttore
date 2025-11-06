#!/usr/bin/env python3
"""
Test rapido per verificare che il vocabolario riconosca correttamente le parole
"""

import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from correttore.services.vocabulary_service import VocabularyService

def test_vocabulary():
    """Test del vocabolario"""
    print("🧪 Test riconoscimento parole nel vocabolario\n")
    
    # Inizializza servizio
    vocab_service = VocabularyService()
    
    print(f"✓ Vocabolario caricato: {vocab_service.vocabulary_size} parole\n")
    
    # Test parole specifiche
    test_words = [
        "forza",      # Ha livello null
        "abbandonare", # Ha livello fondamentale
        "casa",       # Dovrebbe essere nel vocabolario
        "xyzabc"      # Sicuramente NON nel vocabolario
    ]
    
    print("📝 Test singole parole:\n")
    for word in test_words:
        is_in = vocab_service.is_in_vocabulary(word)
        level = vocab_service.get_word_level(word)
        print(f"  • {word:15} -> Nel VdB: {is_in:5} | Livello: {level or 'null'}")
    
    # Test breakdown su un testo
    print("\n📊 Test breakdown su testo di esempio:\n")
    test_text = "La forza della casa è grande e il mare è blu."
    
    breakdown = vocab_service.get_vocabulary_breakdown(test_text)
    
    print(f"  Totale parole: {breakdown['total_words']}")
    print(f"  • Fondamentali: {breakdown['fondamentale']['count']} ({breakdown['fondamentale']['percentage']}%)")
    print(f"  • Alto uso: {breakdown['alto_uso']['count']} ({breakdown['alto_uso']['percentage']}%)")
    print(f"  • Alta disponibilità: {breakdown['alta_disponibilita']['count']} ({breakdown['alta_disponibilita']['percentage']}%)")
    print(f"  • Non classificate: {breakdown['non_classificato']['count']} ({breakdown['non_classificato']['percentage']}%)")
    print(f"  • Fuori VdB: {breakdown['fuori_vdb']['count']} ({breakdown['fuori_vdb']['percentage']}%)")
    
    if breakdown['fuori_vdb']['words']:
        print(f"\n  Parole fuori VdB: {', '.join(breakdown['fuori_vdb']['words'])}")
    
    print("\n✅ Test completato!")

if __name__ == "__main__":
    test_vocabulary()
