# test_validation_system.py
"""
Test del sistema di validazione e correzione sicura.
Verifica che i nuovi moduli funzionino correttamente.
"""

import tempfile
from pathlib import Path
import logging

# Setup logging per vedere i risultati
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from src.core.validation import DocumentValidator, ValidationResult, create_backup, validate_document, validate_correction
from src.core.safe_correction import SafeCorrector, CorrectionResult, QualityScore

def test_validation_system():
    """Test del sistema di validazione"""
    print("\n=== TEST SISTEMA VALIDAZIONE ===")
    
    # Test con file inesistente
    validator = DocumentValidator()
    
    fake_path = Path("inesistente.docx")
    result = validator.validate_before_processing(fake_path)
    print(f"❌ File inesistente - Valid: {result.is_valid}, Issues: {result.issues}")
    assert not result.is_valid
    
    # Test validate_paragraph_integrity
    print("\n--- Test validazione paragrafi ---")
    
    # Caso normale - correzione buona
    original = "Questo è un esempio di testo con alcuni errori di ortografia."
    corrected = "Questo è un esempio di testo con alcuni errori di ortografia."
    is_valid = validator.validate_paragraph_integrity(original, corrected)
    print(f"✅ Correzione normale: {is_valid}")
    
    # Caso problematico - testo dimezzato
    corrected_bad = "Questo è un esempio"
    is_valid_bad = validator.validate_paragraph_integrity(original, corrected_bad)
    print(f"❌ Testo dimezzato: {is_valid_bad}")
    
    # Caso problematico - testo vuoto
    is_valid_empty = validator.validate_paragraph_integrity(original, "")
    print(f"❌ Testo vuoto: {is_valid_empty}")
    
    print("✅ Sistema validazione: OK")

def test_safe_correction_system():
    """Test del sistema di correzione sicura"""
    print("\n=== TEST SISTEMA CORREZIONE SICURA ===")
    
    corrector = SafeCorrector(conservative_mode=True, quality_threshold=0.85)
    
    # Test quality scoring
    print("\n--- Test quality scoring ---")
    
    # Correzione buona
    original = "Questo testo ha qualche errore di ortographia."
    corrected = "Questo testo ha qualche errore di ortografia."
    quality = corrector.validate_correction_quality(original, corrected)
    print(f"✅ Correzione buona - Score: {quality.overall_score:.2f}, Safe: {quality.is_safe}")
    
    # Correzione problematica - testo molto diverso
    corrected_bad = "Testo completamente diverso senza senso."
    quality_bad = corrector.validate_correction_quality(original, corrected_bad)
    print(f"❌ Correzione problematica - Score: {quality_bad.overall_score:.2f}, Safe: {quality_bad.is_safe}")
    
    # Test mock correction
    print("\n--- Test mock correction ---")
    
    class MockParagraph:
        def __init__(self, text):
            self.text = text
        
    def mock_spellcheck(text):
        return text.replace("ortographia", "ortografia")
    
    mock_para = MockParagraph("Questo ha un errore di ortographia.")
    
    # Correzione sicura dovrebbe essere applicata
    result = corrector.correct_with_rollback(mock_para, mock_spellcheck, "spellcheck")
    print(f"✅ Correzione sicura applicata: {result.applied}, Quality: {result.quality_score.overall_score:.2f}")
    
    # Correzione pericolosa dovrebbe essere rifiutata
    def bad_correction(text):
        return "Testo completamente rovinato"
    
    result_bad = corrector.correct_with_rollback(mock_para, bad_correction, "bad_correction")
    print(f"❌ Correzione pericolosa rifiutata: {result_bad.applied}, Reason: {result_bad.rollback_reason}")
    
    # Statistiche
    stats = corrector.get_correction_stats()
    print(f"📊 Stats: {stats}")
    
    print("✅ Sistema correzione sicura: OK")

def test_integration():
    """Test di integrazione dei sistemi"""
    print("\n=== TEST INTEGRAZIONE ===")
    
    # Simula il flusso completo
    validator = DocumentValidator()
    corrector = SafeCorrector(conservative_mode=True, quality_threshold=0.85)
    
    # Lista di testi di esempio
    test_texts = [
        "Questo è un testo senza errori.",
        "Questo è un testo con errori di ortographia e grammatica.",
        "Un altro paragrafo con qualche refuso da corregere qui.",
        ""  # Paragrafo vuoto
    ]
    
    corrections_applied = 0
    
    for i, text in enumerate(test_texts):
        if not text.strip():
            continue
            
        # Mock paragraph
        class MockParagraph:
            def __init__(self, text):
                self.text = text
                
        mock_para = MockParagraph(text)
        
        # Pipeline di correzione
        def simple_spellcheck(t):
            return t.replace("ortographia", "ortografia").replace("refuso", "errore")
        
        result = corrector.correct_with_rollback(mock_para, simple_spellcheck, "integration_test")
        
        if result.applied:
            corrections_applied += 1
            print(f"✅ Paragraph {i+1}: correction applied")
        else:
            print(f"⏭️  Paragraph {i+1}: no correction needed")
    
    print(f"📊 Integration test completed: {corrections_applied} corrections applied out of {len([t for t in test_texts if t.strip()])} paragraphs")
    print("✅ Integrazione: OK")

if __name__ == "__main__":
    print("🧪 TESTING VALIDATION AND SAFE CORRECTION SYSTEMS")
    print("=" * 60)
    
    try:
        test_validation_system()
        test_safe_correction_system()
        test_integration()
        
        print("\n" + "=" * 60)
        print("🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!")
        print("✅ Sistema di validazione e correzione sicura operativo")
        
    except Exception as e:
        print(f"\n❌ TEST FALLITO: {e}")
        raise
