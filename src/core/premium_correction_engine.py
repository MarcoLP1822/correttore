# premium_correction_engine.py
"""
Motore di correzione premium per italiano di alta qualità.
Integra tutti i sistemi per garantire correzioni accurate e affidabili.
"""

import logging
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass
import asyncio
from pathlib import Path

from openai import AsyncOpenAI
from docx.text.paragraph import Paragraph

from .enhanced_correction_system import EnhancedCorrectionSystem, CorrectionLevel
from .enhanced_languagetool import EnhancedLanguageTool, ItalianSpecificCorrector
from .safe_correction import SafeCorrector, QualityScore

logger = logging.getLogger(__name__)

@dataclass
class PremiumCorrectionResult:
    """Risultato della correzione premium"""
    original_text: str
    corrected_text: str
    total_corrections: int
    confidence_score: float
    correction_levels: List[CorrectionLevel]
    languagetool_corrections: List[Tuple[str, str]]
    specific_corrections: List[Tuple[str, str]]
    quality_score: QualityScore
    applied: bool
    details: Dict

class PremiumCorrectionEngine:
    """Motore di correzione premium per italiano"""
    
    def __init__(self, openai_client: AsyncOpenAI, languagetool_url: str = "http://localhost:8081"):
        self.openai_client = openai_client
        self.enhanced_system = EnhancedCorrectionSystem()
        self.languagetool = EnhancedLanguageTool(languagetool_url)
        self.italian_corrector = ItalianSpecificCorrector()
        self.safe_corrector = SafeCorrector(conservative_mode=False, quality_threshold=0.75)
        
    async def correct_paragraph_premium(self, paragraph: Any, par_id: int) -> PremiumCorrectionResult:
        """Correzione premium di un paragrafo"""
        original_text = paragraph.text
        
        if not original_text.strip():
            return self._create_empty_result(original_text)
        
        logger.info(f"🎯 Avvio correzione premium per paragrafo {par_id}")
        
        try:
            # FASE 1: Correzioni specifiche italiane (pre-processing)
            phase1_text, specific_corrections = self.italian_corrector.fix_specific_errors(original_text)
            logger.info(f"📌 Fase 1 - Specifiche italiane: {len(specific_corrections)} correzioni")
            
            # FASE 2: LanguageTool (errori standard)
            lt_errors = self.languagetool.check_text(phase1_text)
            phase2_text, lt_corrections = self.languagetool.apply_corrections(phase1_text, lt_errors, confidence_threshold=0.8)
            logger.info(f"🔧 Fase 2 - LanguageTool: {len(lt_corrections)} correzioni")
            
            # FASE 3: Sistema multi-livello (errori complessi)
            phase3_text, correction_levels = await self.enhanced_system.correct_text_multilevel(phase2_text, self.openai_client)
            logger.info(f"🚀 Fase 3 - Multi-livello: {len(correction_levels)} livelli applicati")
            
            # FASE 4: Validazione qualità
            quality_score = self.safe_corrector.validate_correction_quality(original_text, phase3_text)
            
            # FASE 5: Decisione finale
            should_apply = self._should_apply_premium_correction(quality_score, original_text, phase3_text)
            
            if should_apply:
                # Applica al paragrafo
                paragraph.text = phase3_text
                applied = True
                final_text = phase3_text
                logger.info(f"✅ Correzione premium applicata (qualità: {quality_score.overall_score:.1%})")
            else:
                applied = False
                final_text = original_text
                logger.info(f"⏭️  Correzione premium respinta (qualità: {quality_score.overall_score:.1%})")
            
            # Calcola statistiche
            total_corrections = len(specific_corrections) + len(lt_corrections) + sum(len(level.corrections) for level in correction_levels)
            confidence_score = self._calculate_confidence(correction_levels, lt_corrections, specific_corrections)
            
            return PremiumCorrectionResult(
                original_text=original_text,
                corrected_text=final_text,
                total_corrections=total_corrections,
                confidence_score=confidence_score,
                correction_levels=correction_levels,
                languagetool_corrections=lt_corrections,
                specific_corrections=specific_corrections,
                quality_score=quality_score,
                applied=applied,
                details=self._create_details(specific_corrections, lt_corrections, correction_levels, quality_score)
            )
            
        except Exception as e:
            logger.error(f"❌ Errore nella correzione premium: {e}")
            return self._create_error_result(original_text, str(e))
    
    def _should_apply_premium_correction(self, quality_score: QualityScore, original: str, corrected: str) -> bool:
        """Decide se applicare la correzione premium"""
        # Criteri più severi per il sistema premium
        
        # 1. Qualità minima richiesta
        if quality_score.overall_score < 0.75:
            return False
        
        # 2. Sicurezza minima richiesta  
        if quality_score.safety_score < 0.85:
            return False
        
        # 3. Preservazione contenuto minima
        if quality_score.content_preservation < 0.80:
            return False
        
        # 4. Non applicare se il testo è sostanzialmente uguale
        if original.strip() == corrected.strip():
            return False
        
        # 5. Non applicare cambiamenti troppo drastici
        length_ratio = len(corrected) / max(len(original), 1)
        if length_ratio < 0.7 or length_ratio > 1.3:
            return False
        
        return True
    
    def _calculate_confidence(self, correction_levels: List[CorrectionLevel], 
                            lt_corrections: List[Tuple[str, str]], 
                            specific_corrections: List[Tuple[str, str]]) -> float:
        """Calcola confidenza complessiva"""
        confidences = []
        
        # Correzioni specifiche: alta confidenza
        if specific_corrections:
            confidences.extend([0.95] * len(specific_corrections))
        
        # LanguageTool: confidenza media-alta
        if lt_corrections:
            confidences.extend([0.85] * len(lt_corrections))
        
        # Livelli di correzione: usa le loro confidenze
        for level in correction_levels:
            if level.corrections:
                confidences.extend([level.confidence] * len(level.corrections))
        
        # Se non ci sono correzioni, confidenza neutrale
        if not confidences:
            return 0.8
        
        # Media pesata
        return sum(confidences) / len(confidences)
    
    def _create_details(self, specific_corrections: List[Tuple[str, str]], 
                       lt_corrections: List[Tuple[str, str]], 
                       correction_levels: List[CorrectionLevel],
                       quality_score: QualityScore) -> Dict:
        """Crea dettagli della correzione"""
        return {
            "specific_corrections": len(specific_corrections),
            "languagetool_corrections": len(lt_corrections),
            "multilevel_corrections": sum(len(level.corrections) for level in correction_levels),
            "quality_breakdown": {
                "overall": quality_score.overall_score,
                "content_preservation": quality_score.content_preservation,
                "grammar_improvement": quality_score.grammar_improvement,
                "style_preservation": quality_score.style_preservation,
                "safety": quality_score.safety_score
            },
            "confidence": quality_score.confidence.value,
            "issues": quality_score.issues,
            "multilevel_summary": self.enhanced_system.get_correction_summary(correction_levels)
        }
    
    def _create_empty_result(self, text: str) -> PremiumCorrectionResult:
        """Crea risultato vuoto per testo vuoto"""
        empty_quality = QualityScore(
            overall_score=1.0,
            confidence=self.safe_corrector._determine_confidence(1.0, []),
            content_preservation=1.0,
            grammar_improvement=1.0,
            style_preservation=1.0,
            safety_score=1.0,
            issues=[]
        )
        
        return PremiumCorrectionResult(
            original_text=text,
            corrected_text=text,
            total_corrections=0,
            confidence_score=1.0,
            correction_levels=[],
            languagetool_corrections=[],
            specific_corrections=[],
            quality_score=empty_quality,
            applied=False,
            details={}
        )
    
    def _create_error_result(self, text: str, error_msg: str) -> PremiumCorrectionResult:
        """Crea risultato di errore"""
        error_quality = QualityScore(
            overall_score=0.0,
            confidence=self.safe_corrector._determine_confidence(0.0, [error_msg]),
            content_preservation=0.0,
            grammar_improvement=0.0,
            style_preservation=0.0,
            safety_score=0.0,
            issues=[error_msg]
        )
        
        return PremiumCorrectionResult(
            original_text=text,
            corrected_text=text,
            total_corrections=0,
            confidence_score=0.0,
            correction_levels=[],
            languagetool_corrections=[],
            specific_corrections=[],
            quality_score=error_quality,
            applied=False,
            details={"error": error_msg}
        )

async def test_premium_correction():
    """Test del sistema premium"""
    from openai import AsyncOpenAI
    import os
    
    # Configura client OpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Inizializza motore
    engine = PremiumCorrectionEngine(client)
    
    # Test cases dai tuoi esempi
    test_cases = [
        "bottaga",  # dovrebbe diventare "bottega"
        "ansiano",  # dovrebbe diventare "anziano"
        "U giorno",  # dovrebbe diventare "Un giorno"
        "Lui, però, non abbandonò mai la sua piccola bottaga",
        "C'era una vlta, in un piccolo borggo arroccato tra le montagne, un ansiano falegname",
        "Qvesta essere una cassella di testo"
    ]
    
    print("🧪 Test del sistema di correzione premium")
    print("=" * 50)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{i}. TESTO ORIGINALE: '{test_text}'")
        
        # Simula un paragrafo
        class MockParagraph:
            def __init__(self, text):
                self.text = text
        
        mock_para = MockParagraph(test_text)
        result = await engine.correct_paragraph_premium(mock_para, i)
        
        print(f"   CORRETTO:        '{result.corrected_text}'")
        print(f"   APPLICATO:       {result.applied}")
        print(f"   CORREZIONI:      {result.total_corrections}")
        print(f"   CONFIDENZA:      {result.confidence_score:.1%}")
        print(f"   QUALITÀ:         {result.quality_score.overall_score:.1%}")
        
        if result.specific_corrections:
            print(f"   SPECIFICHE:      {result.specific_corrections}")
        if result.languagetool_corrections:
            print(f"   LANGUAGETOOL:    {result.languagetool_corrections}")
        if result.correction_levels:
            print(f"   LIVELLI:         {[level.name for level in result.correction_levels]}")

if __name__ == "__main__":
    asyncio.run(test_premium_correction())
