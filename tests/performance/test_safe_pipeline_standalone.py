# test_safe_pipeline_standalone.py
"""
Test della nuova pipeline di correzione sicura (standalone, senza LanguageTool).
Verifica che il sistema integrato funzioni correttamente.
"""

import asyncio
import logging
from pathlib import Path
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Importa i moduli del sistema
from correttore.core.safe_correction import SafeCorrector, CorrectionResult, QualityScore
from correttore.core.validation import DocumentValidator
from dataclasses import dataclass

# Definizione locale di Modification per il test
@dataclass
class Modification:
    par_id: int
    original: str
    corrected: str

# Mock delle costanti da correttore.py
NAME_RE = re.compile(r"\b([A-Z][a-z]{2,}\w*|[A-Z]{2,4})\b")
GLOSSARY_STOP = {"CAPITOLO", "CAPITOLI", "PROLOGO", "EPILOGO", "INDICE"}

class MockParagraph:
    """Mock di un paragrafo Word per test"""
    def __init__(self, text):
        self.text = text
        self._original_text = text
        # Add runs attribute to make it compatible with _apply_text_preserving_format
        self.runs = []
    
    def clear(self):
        """Mock clear method for paragraph"""
        self.text = ""
        self.runs = []

def create_test_paragraphs():
    """Crea paragrafi di test con vari tipi di errori"""
    test_texts = [
        "Questo è un paragrafo senza errori che non dovrebbe essere modificato.",
        "Questo paragrafo ha alcuni errori di ortographia che dovrebbero essere corretti.",
        "Un'altra frase con refuso e qualche problema grammaticale da sistemare.",
        "Questo testo ha pò errori invece di po' e altri problemi.",
        "",  # Paragrafo vuoto
        "CAPPITOLO 1",  # Errore in maiuscolo
        "La seguente frase ha molti errori ortographici e grammaticali che devono essere sistemati correttamente.",
        "Marco e Giulia sono andati al cinema ieri sera.",  # Nomi propri per glossario
        "Nel romanzo di Tolkien, Frodo è il protagonista principale."  # Altri nomi
    ]
    
    return [MockParagraph(text) for text in test_texts]

async def test_safe_pipeline():
    """Test della pipeline di correzione sicura completa"""
    print("\n=== TEST PIPELINE CORREZIONE SICURA ===")
    
    # Setup
    safe_corrector = SafeCorrector(conservative_mode=True, quality_threshold=0.85)
    paragraphs = create_test_paragraphs()
    
    # Simula il glossario e altre strutture
    glossary = set()
    mods = []
    
    print(f"📄 Created test document with {len(paragraphs)} paragraphs")
    
    # Test del spellcheck sicuro
    print("\n--- Test Spellcheck Sicuro ---")
    spellcheck_applied = 0
    
    for i, para in enumerate(paragraphs):
        if not para.text.strip():
            continue
            
        original = para.text
        
        # Mock spellcheck function
        def mock_spellcheck(text):
            corrections = {
                "ortographia": "ortografia",
                "refuso": "errore", 
                "pò": "po'",
                "CAPPITOLO": "CAPITOLO",
                "ortographici": "ortografici"
            }
            corrected = text
            for wrong, right in corrections.items():
                corrected = corrected.replace(wrong, right)
            return corrected
        
        # Test con safe corrector
        result = safe_corrector.correct_with_rollback(para, mock_spellcheck, "spellcheck")
        
        if result.applied:
            spellcheck_applied += 1
            print(f"✅ Paragraph {i+1}: Spellcheck applied (quality: {result.quality_score.overall_score:.1%})")
            print(f"   '{original[:50]}...' → '{result.corrected_text[:50]}...'")
        else:
            reason = result.rollback_reason or "No changes needed"
            print(f"⏭️  Paragraph {i+1}: {reason}")
            
    print(f"📊 Spellcheck: {spellcheck_applied}/{len([p for p in paragraphs if p.text.strip()])} applied")
    
    # Test del grammar check (simulato)
    print("\n--- Test Grammar Check Sicuro ---")
    grammar_applied = 0
    
    for i, para in enumerate(paragraphs):
        if not para.text.strip():
            continue
            
        original = para.text
        
        # Mock grammar check
        def mock_grammar(text):
            # Simula correzioni grammaticali semplici
            corrections = {
                "un'altra frase": "un altro esempio",
                " qui.": ".",
                "sistemati correttamente": "corretti"
            }
            corrected = text
            for wrong, right in corrections.items():
                corrected = corrected.replace(wrong, right)
            return corrected
        
        corrected = mock_grammar(para.text)
        
        # Validazione manuale (come nel sistema reale)
        if corrected != original:
            from correttore.core.validation import validate_correction
            if validate_correction(original, corrected):
                para.text = corrected
                grammar_applied += 1
                print(f"✅ Paragraph {i+1}: Grammar applied")
                print(f"   '{original[:50]}...' → '{corrected[:50]}...'")
                
                # Simula aggiornamento glossario
                for name in NAME_RE.findall(corrected):
                    if name.upper() not in GLOSSARY_STOP:
                        glossary.add(name)
            else:
                print(f"🔄 Paragraph {i+1}: Grammar rolled back (validation failed)")
        else:
            print(f"⏭️  Paragraph {i+1}: No grammar changes needed")
            
    print(f"📊 Grammar: {grammar_applied}/{len([p for p in paragraphs if p.text.strip()])} applied")
    
    # Test AI correction (simulato)
    print("\n--- Test AI Correction ---")
    
    # Simula batch AI processing
    ai_texts = []
    para_mapping = []
    for i, para in enumerate(paragraphs):
        if para.text.strip():
            ai_texts.append(para.text)
            para_mapping.append(i)
    
    # Mock AI correction
    def mock_ai_batch(texts):
        corrected = []
        for text in texts:
            # Simula miglioramenti AI minimali
            improvements = {
                "problema grammaticale": "errore grammaticale",
                "devono essere sistemati": "vanno corretti",
                "sono andati": "andarono"
            }
            result = text
            for old, new in improvements.items():
                result = result.replace(old, new)
            corrected.append(result)
        return corrected
    
    ai_corrected_list = mock_ai_batch(ai_texts)
    ai_applied = 0
    
    for j, ai_corrected in enumerate(ai_corrected_list):
        i = para_mapping[j]
        para = paragraphs[i]
        original = para.text
        
        if ai_corrected != original:
            from correttore.core.validation import validate_correction
            if validate_correction(original, ai_corrected):
                para.text = ai_corrected
                ai_applied += 1
                
                # Simula registrazione modifica
                mods.append(Modification(i+1, original, ai_corrected))
                
                # Aggiorna glossario
                for name in NAME_RE.findall(ai_corrected):
                    if name.upper() not in GLOSSARY_STOP:
                        glossary.add(name)
                
                print(f"✅ Paragraph {i+1}: AI correction applied")
                print(f"   '{original[:50]}...' → '{ai_corrected[:50]}...'")
            else:
                print(f"🔄 Paragraph {i+1}: AI correction rolled back")
        else:
            print(f"⏭️  Paragraph {i+1}: No AI changes")
    
    print(f"📊 AI Correction: {ai_applied}/{len(ai_texts)} applied")
    
    # Statistiche finali
    total_corrections = spellcheck_applied + grammar_applied + ai_applied
    total_paragraphs = len([p for p in paragraphs if p.text.strip()])
    
    print(f"\n📊 STATISTICHE FINALI:")
    print(f"   • Paragrafi processati: {total_paragraphs}")
    print(f"   • Correzioni applicate: {total_corrections}")
    print(f"   • Modifiche registrate: {len(mods)}")
    print(f"   • Glossario aggiornato: {len(glossary)} termini")
    if total_paragraphs > 0:
        print(f"   • Success rate: {total_corrections/total_paragraphs:.1%}")
    
    # Mostra il glossario
    if glossary:
        print(f"   • Glossario: {', '.join(sorted(glossary))}")
    
    # Statistiche del safe corrector
    stats = safe_corrector.get_correction_stats()
    print(f"   • Safe corrector stats:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"     - {key}: {value:.1%}")
        else:
            print(f"     - {key}: {value}")
    
    print("✅ Pipeline test completed successfully!")
    
    return paragraphs, mods, glossary

async def test_error_handling():
    """Test della gestione errori"""
    print("\n=== TEST GESTIONE ERRORI ===")
    
    safe_corrector = SafeCorrector(conservative_mode=True, quality_threshold=0.85)
    
    # Test con funzione che genera errore
    def failing_correction(text):
        raise Exception("Simulated correction failure")
    
    para = MockParagraph("Test text")
    result = safe_corrector.correct_with_rollback(para, failing_correction, "error_test")
    
    print(f"❌ Error handling: applied={result.applied}, reason='{result.rollback_reason}'")
    assert not result.applied
    assert result.rollback_reason and "Function execution failed" in result.rollback_reason
    
    # Test con correzione che ritorna contenuto pericoloso
    def dangerous_correction(text):
        return "Completely different text that destroys content"
    
    result2 = safe_corrector.correct_with_rollback(para, dangerous_correction, "dangerous_test")
    print(f"🛡️  Dangerous correction blocked: applied={result2.applied}, quality={result2.quality_score.overall_score:.1%}")
    assert not result2.applied
    
    # Test con correzione che taglia molto testo
    def truncating_correction(text):
        return text[:10]  # Taglia drasticamente
    
    long_para = MockParagraph("Questo è un testo molto lungo che dovrebbe essere preservato nella sua interezza per mantenere il significato.")
    result3 = safe_corrector.correct_with_rollback(long_para, truncating_correction, "truncation_test")
    print(f"✂️  Truncating correction blocked: applied={result3.applied}, quality={result3.quality_score.overall_score:.1%}")
    assert not result3.applied
    
    print("✅ Error handling test completed!")

def test_quality_scoring():
    """Test dettagliato del sistema di quality scoring"""
    print("\n=== TEST QUALITY SCORING ===")
    
    corrector = SafeCorrector()
    
    test_cases = [
        ("Buona correzione", "Questo ha un errore ortographico.", "Questo ha un errore ortografico."),
        ("Correzione neutra", "Questo testo è già corretto.", "Questo testo è già corretto."),
        ("Correzione pericolosa", "Testo originale completo.", "Testo diverso."),
        ("Correzione vuota", "Testo originale.", ""),
        ("Correzione duplicata", "Parola unica.", "Parola parola parola parola.")
    ]
    
    for name, original, corrected in test_cases:
        quality = corrector.validate_correction_quality(original, corrected)
        print(f"{name}:")
        print(f"  Overall: {quality.overall_score:.1%} | Content: {quality.content_preservation:.1%} | Safety: {quality.safety_score:.1%}")
        print(f"  Confidence: {quality.confidence.value} | Safe: {quality.is_safe}")
        if quality.issues:
            print(f"  Issues: {', '.join(quality.issues)}")
        print()
    
    print("✅ Quality scoring test completed!")

if __name__ == "__main__":
    print("🧪 TESTING SAFE CORRECTION PIPELINE (STANDALONE)")
    print("=" * 60)
    
    async def run_all_tests():
        try:
            await test_safe_pipeline()
            await test_error_handling()
            test_quality_scoring()
            
            print("\n" + "=" * 60)
            print("🎉 TUTTI I TEST DELLA PIPELINE COMPLETATI CON SUCCESSO!")
            print("✅ Sistema di correzione sicura integrato e funzionante")
            print("🔒 Validazione e rollback automatico operativi")
            print("📊 Quality scoring multidimensionale attivo")
            
        except Exception as e:
            print(f"\n❌ TEST FALLITO: {e}")
            raise
    
    asyncio.run(run_all_tests())
