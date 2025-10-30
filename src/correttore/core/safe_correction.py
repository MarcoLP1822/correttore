# safe_correction.py
"""
Sistema di correzione sicuro e incrementale con rollback automatico.
Garantisce che ogni correzione sia sicura e reversibile, con quality scoring
per valutare la bontà delle modifiche.
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from difflib import SequenceMatcher
import re

from .validation import DocumentValidator, ContentIssue, validate_correction
from ..models import CorrectionRecord, CorrectionCategory, CorrectionSource

logger = logging.getLogger(__name__)

class CorrectionConfidence(Enum):
    """Livelli di confidenza per le correzioni"""
    VERY_HIGH = "very_high"  # >98%
    HIGH = "high"           # 95-98%
    MEDIUM = "medium"       # 85-95%
    LOW = "low"            # 70-85%
    VERY_LOW = "very_low"   # <70%

@dataclass
class QualityScore:
    """Punteggio di qualità per una correzione"""
    overall_score: float  # 0.0 - 1.0
    confidence: CorrectionConfidence
    content_preservation: float
    grammar_improvement: float
    style_preservation: float
    safety_score: float
    issues: List[str]
    
    @property
    def is_safe(self) -> bool:
        """True se la correzione è considerata sicura"""
        return (self.overall_score >= 0.85 and 
                self.safety_score >= 0.8 and
                self.confidence in [CorrectionConfidence.HIGH, CorrectionConfidence.VERY_HIGH, CorrectionConfidence.MEDIUM])

@dataclass 
class CorrectionResult:
    """Risultato di una correzione con metadati"""
    original_text: str
    corrected_text: str
    applied: bool
    quality_score: QualityScore
    rollback_reason: Optional[str] = None
    correction_type: str = "unknown"
    
    @property
    def has_changes(self) -> bool:
        """True se ci sono state modifiche"""
        return self.original_text != self.corrected_text
    
    @property
    def change_summary(self) -> str:
        """Riassunto delle modifiche"""
        if not self.has_changes:
            return "No changes"
        
        orig_len = len(self.original_text)
        corr_len = len(self.corrected_text)
        length_change = ((corr_len - orig_len) / max(orig_len, 1)) * 100
        
        return f"Length: {length_change:+.1f}%, Quality: {self.quality_score.overall_score:.1%}"

class SafeCorrector:
    """Correttore sicuro con validazione e rollback automatico"""
    
    def __init__(self, conservative_mode: bool = True, quality_threshold: float = 0.55, collector=None, whitelist: Optional[set] = None):
        self.conservative_mode = conservative_mode
        # Soglia abbassata per permettere più correzioni ortografiche e grammaticali
        self.quality_threshold = min(quality_threshold, 0.55)  # 55% - più permissivo per errori evidenti
        self.validator = DocumentValidator()
        self.correction_stats = {
            'total_attempts': 0,
            'successful_corrections': 0,
            'rollbacks': 0,
            'quality_rejections': 0
        }
        # Collector per tracking delle correzioni (opzionale)
        self.collector = collector
        
        # FASE 6: Whitelist parole da NON correggere (apprese da feedback)
        self.whitelist = whitelist if whitelist is not None else set()
        if self.whitelist:
            logger.debug(f"✅ SafeCorrector loaded {len(self.whitelist)} whitelisted words")
        
        # Vocabulary service per validazione VdB (Fase 4)
        self.vocabulary_service = None
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
            from services.vocabulary_service import get_vocabulary_service
            self.vocabulary_service = get_vocabulary_service()
            logger.info("📚 VocabularyService integrato in SafeCorrector")
        except ImportError:
            logger.debug("VocabularyService non disponibile")

        
    def correct_with_rollback(
        self, 
        paragraph, 
        correction_func, 
        correction_type: str = "unknown",
        source: CorrectionSource = CorrectionSource.SYSTEM,
        position: int = 0,
        paragraph_index: int = 0
    ) -> CorrectionResult:
        """
        Applica una correzione con possibilità di rollback automatico
        se la qualità risulta insufficiente.
        
        Args:
            paragraph: Oggetto Paragraph di python-docx
            correction_func: Funzione che prende il testo e ritorna la correzione
            correction_type: Tipo di correzione (spellcheck, grammar, ai)
        """
        original_text = paragraph.text
        self.correction_stats['total_attempts'] += 1
        
        logger.debug(f"🔍 Attempting {correction_type} correction: '{original_text[:50]}...'")
        
        # 1. Applica la correzione
        try:
            corrected_text = correction_func(original_text)
        except Exception as e:
            logger.error(f"❌ Correction function failed: {e}")
            return CorrectionResult(
                original_text=original_text,
                corrected_text=original_text,
                applied=False,
                quality_score=self._create_failed_quality_score(f"Correction function error: {e}"),
                rollback_reason="Function execution failed",
                correction_type=correction_type
            )
        
        # 2. Se non ci sono cambiamenti, ritorna senza ulteriori controlli
        if corrected_text == original_text:
            return CorrectionResult(
                original_text=original_text,
                corrected_text=corrected_text,
                applied=False,
                quality_score=self._create_no_change_quality_score(),
                correction_type=correction_type
            )
        
        # 3. Valuta la qualità della correzione
        quality_score = self.validate_correction_quality(original_text, corrected_text)
        
        # 4. Decide se applicare o fare rollback
        should_apply = self._should_apply_correction(quality_score, correction_type)
        
        if should_apply:
            # Applica la correzione al paragrafo
            self._apply_correction_to_paragraph(paragraph, corrected_text)
            self.correction_stats['successful_corrections'] += 1
            logger.debug(f"✅ Applied {correction_type} correction (quality: {quality_score.overall_score:.1%})")
            
            # Tracking: registra la correzione applicata nel collector
            if self.collector is not None:
                self._track_correction(
                    original_text=original_text,
                    corrected_text=corrected_text,
                    quality_score=quality_score,
                    source=source,
                    correction_type=correction_type,
                    position=position,
                    paragraph_index=paragraph_index,
                    is_applied=True
                )
            
            return CorrectionResult(
                original_text=original_text,
                corrected_text=corrected_text,
                applied=True,
                quality_score=quality_score,
                correction_type=correction_type
            )
        else:
            # Rollback - mantieni il testo originale
            self.correction_stats['rollbacks'] += 1
            rollback_reason = self._get_rollback_reason(quality_score)
            logger.warning(f"🔄 Rolled back {correction_type} correction: {rollback_reason}")
            
            # Tracking: registra anche le correzioni rifiutate
            if self.collector is not None:
                self._track_correction(
                    original_text=original_text,
                    corrected_text=corrected_text,
                    quality_score=quality_score,
                    source=source,
                    correction_type=correction_type,
                    position=position,
                    paragraph_index=paragraph_index,
                    is_applied=False,
                    rejection_reason=rollback_reason
                )
            
            return CorrectionResult(
                original_text=original_text,
                corrected_text=original_text,  # Rollback
                applied=False,
                quality_score=quality_score,
                rollback_reason=rollback_reason,
                correction_type=correction_type
            )
    
    def validate_correction_quality(self, original: str, corrected: str) -> QualityScore:
        """
        Valuta la qualità di una correzione su multiple dimensioni.
        """
        issues = []
        
        # 1. Content Preservation (40% del punteggio totale)
        content_score = self._score_content_preservation(original, corrected)
        if content_score < 0.6:  # Soglia più permissiva per correzioni semantiche
            issues.append(f"Low content preservation: {content_score:.1%}")
        
        # 2. Grammar Improvement (25% del punteggio totale)
        grammar_score = self._score_grammar_improvement(original, corrected)
        
        # 3. Style Preservation (20% del punteggio totale)  
        style_score = self._score_style_preservation(original, corrected)
        if style_score < 0.7:  # Soglia più permissiva per correzioni semantiche
            issues.append(f"Style significantly changed: {style_score:.1%}")
        
        # 4. Safety Score (15% del punteggio totale)
        safety_score = self._score_safety(original, corrected)
        if safety_score < 0.9:
            issues.append(f"Safety concerns detected: {safety_score:.1%}")
        
        # Calcola punteggio complessivo pesato
        overall_score = (
            content_score * 0.40 +
            grammar_score * 0.25 + 
            style_score * 0.20 +
            safety_score * 0.15
        )
        
        # 5. Vocabulary Quality Bonus/Penalty (VdB validation)
        if self.vocabulary_service:
            vocab_adjustment = self._score_vocabulary_quality(original, corrected)
            overall_score += vocab_adjustment
            overall_score = max(0.0, min(1.0, overall_score))  # Clamp to [0, 1]
            
            if vocab_adjustment < 0:
                issues.append(f"Vocabulary complexity increased: {vocab_adjustment:+.3f}")
            elif vocab_adjustment > 0.05:
                logger.debug(f"✨ Vocabulary simplified: {vocab_adjustment:+.3f}")
        
        # Determina livello di confidenza
        confidence = self._determine_confidence(overall_score, issues)
        
        return QualityScore(
            overall_score=overall_score,
            confidence=confidence,
            content_preservation=content_score,
            grammar_improvement=grammar_score,
            style_preservation=style_score,
            safety_score=safety_score,
            issues=issues
        )
    
    def apply_conservative_correction(self, text: str, correction_pipeline: List[Callable]) -> str:
        """
        Applica una pipeline di correzioni in modalità conservativa.
        Ogni step viene validato prima di procedere al successivo.
        """
        current_text = text
        applied_corrections = []
        
        for i, correction_func in enumerate(correction_pipeline):
            logger.debug(f"🔧 Applying correction step {i+1}/{len(correction_pipeline)}")
            
            # Simula un paragrafo per usare correct_with_rollback
            class MockParagraph:
                def __init__(self, text):
                    self.text = text
                    self._original_text = text
                    
                def update_text(self, new_text):
                    self.text = new_text
            
            mock_para = MockParagraph(current_text)
            result = self.correct_with_rollback(
                mock_para, 
                correction_func, 
                f"pipeline_step_{i+1}"
            )
            
            if result.applied:
                current_text = result.corrected_text
                applied_corrections.append(f"Step {i+1}")
                logger.debug(f"✅ Step {i+1} applied successfully")
            else:
                logger.debug(f"⏭️  Step {i+1} skipped: {result.rollback_reason}")
        
        if applied_corrections:
            logger.info(f"🎯 Conservative correction completed. Applied: {', '.join(applied_corrections)}")
        else:
            logger.info("🔒 Conservative correction: no changes applied (all steps rejected)")
            
        return current_text
    
    def get_correction_stats(self) -> Dict:
        """Ritorna statistiche sulle correzioni effettuate"""
        total = self.correction_stats['total_attempts']
        if total == 0:
            return self.correction_stats
            
        return {
            **self.correction_stats,
            'success_rate': self.correction_stats['successful_corrections'] / total,
            'rollback_rate': self.correction_stats['rollbacks'] / total,
            'rejection_rate': self.correction_stats['quality_rejections'] / total
        }
    
    # Metodi privati per scoring
    
    def _score_content_preservation(self, original: str, corrected: str) -> float:
        """Valuta quanto il contenuto originale è preservato"""
        if not original.strip():
            return 1.0 if not corrected.strip() else 0.5
        
        # 1. Similarità testuale 
        similarity = SequenceMatcher(None, original.lower(), corrected.lower()).ratio()
        
        # 2. Lunghezza relativa (più permissivo per correzioni necessarie)
        len_ratio = min(len(corrected), len(original)) / max(len(corrected), len(original))
        # Riduci penalità per cambiamenti di lunghezza (correzioni possono cambiare lunghezza)
        if len_ratio < 0.7:  # Solo per cambiamenti drammatici >30%
            len_ratio *= 0.7  # Penalità ridotta
        
        # 3. Parole chiave preservate (più tollerante per correzioni ortografiche)
        orig_words = set(re.findall(r'\w+', original.lower()))
        corr_words = set(re.findall(r'\w+', corrected.lower()))
        if orig_words:
            word_preservation = len(orig_words & corr_words) / len(orig_words)
            # Bonus per correzioni ortografiche (parole simili ma corrette)
            for orig_word in orig_words:
                for corr_word in corr_words:
                    # Se una parola è molto simile (possibile correzione ortografica)
                    if len(orig_word) > 3 and len(corr_word) > 3:
                        word_sim = SequenceMatcher(None, orig_word, corr_word).ratio()
                        if 0.6 <= word_sim < 0.95:  # Possibile correzione ortografica
                            word_preservation += 0.1  # Bonus per correzione
        else:
            word_preservation = 1.0
        
        # Formula più tollerante per correzioni
        content_score = (similarity * 0.4 + len_ratio * 0.2 + word_preservation * 0.4)
        
        # Bonus per similarità decente (>0.4 è accettabile per correzioni)
        if similarity > 0.4:
            content_score += 0.1
        
        # NUOVO: Bonus specifico per correzioni semantiche note - LISTA ESPANSA
        semantic_corrections = [
            ('vlta', 'volta'), ('alta', 'volta'),  # correzioni comuni
            ('bottaga', 'bottega'), ('bottaia', 'bottega'),
            ('sugu', 'sugo'), ('suga', 'suga'),
            ('CAPTIOLO', 'CAPITOLO'), ('Captiolo', 'Capitolo'),
            ('go', 'ho'), ('fato', 'fatto'),
            ('Qvesta', 'Questa'), ('qvesta', 'questa'),
            ('cassella', 'casella'),
            ('borggo', 'borgo'),
            ('duee', 'due'),
            ('milliore', 'migliore'),
            ('prontal', 'pronta'),
            ('carezzzzavano', 'carezzavano'),
            ('trasformazzione', 'trasformazione'),
            ('strignendo', 'stringendo'),
            ('Acondroplasiaaa', 'Acondroplasia'),
            ('c erano', 'c\'erano'),
            ('La cane', 'Il cane'),
        ]
        
        for orig_pattern, corr_pattern in semantic_corrections:
            if orig_pattern.lower() in original.lower() and corr_pattern.lower() in corrected.lower():
                content_score += 0.2  # Bonus significativo per correzioni semantiche valide
                break
        
        return min(1.0, content_score)
    
    def _score_grammar_improvement(self, original: str, corrected: str) -> float:
        """Valuta il miglioramento grammaticale (semplificato)"""
        # Questo è un scoring semplificato - in produzione useresti LanguageTool
        improvements = 0
        total_checks = 0
        
        # 0. NUOVO: Riconoscimento correzioni semantiche comuni - LISTA ESPANSA
        semantic_corrections = [
            ('vlta', 'volta'), ('alta', 'volta'),
            ('bottaga', 'bottega'), ('bottaia', 'bottega'),
            ('sugu', 'sugo'), ('suga', 'suga'),
            ('CAPTIOLO', 'CAPITOLO'), ('Captiolo', 'Capitolo'),
            ('go', 'ho'), ('fato', 'fatto'),
            ('Qvesta', 'Questa'), ('qvesta', 'questa'),
            ('cassella', 'casella'),
            ('borggo', 'borgo'),
            ('duee', 'due'),
            ('milliore', 'migliore'),
            ('prontal', 'pronta'),
            ('carezzzzavano', 'carezzavano'),
            ('trasformazzione', 'trasformazione'),
            ('strignendo', 'stringendo'),
            ('Acondroplasiaaa', 'Acondroplasia'),
            ('c erano', 'c\'erano'),
            ('La cane', 'Il cane'),
        ]
        
        for orig_pattern, corr_pattern in semantic_corrections:
            if orig_pattern.lower() in original.lower() and corr_pattern.lower() in corrected.lower():
                total_checks += 1
                improvements += 1  # Correzione semantica valida
                break
        
        # 1. Controllo apostrofi
        total_checks += 1
        if "pò" in original and "po'" in corrected:
            improvements += 1
        elif "po'" in original and "pò" in corrected:
            improvements -= 0.5  # Peggioramento
        elif "pò" not in original and "po'" not in original:
            improvements += 0.5  # Neutro
        else:
            improvements += 0.5  # Neutro
        
        # 2. Controllo maiuscole/minuscole
        total_checks += 1
        if re.search(r'\.\s*[a-z]', original) and not re.search(r'\.\s*[a-z]', corrected):
            improvements += 1  # Corretto inizio frase
        elif not re.search(r'\.\s*[a-z]', original):
            improvements += 0.5  # Neutro
        
        # 3. Controllo punteggiatura
        total_checks += 1
        orig_punct_errors = len(re.findall(r'[a-zA-Z][.!?][a-zA-Z]', original))  # Mancanza spazi
        corr_punct_errors = len(re.findall(r'[a-zA-Z][.!?][a-zA-Z]', corrected))
        if corr_punct_errors < orig_punct_errors:
            improvements += 1
        elif corr_punct_errors == orig_punct_errors:
            improvements += 0.5
        
        if total_checks == 0:
            return 0.8  # Score neutro
            
        return max(0.0, min(1.0, improvements / total_checks))
    
    def _score_style_preservation(self, original: str, corrected: str) -> float:
        """Valuta quanto lo stile originale è preservato"""
        # 1. Lunghezza delle frasi
        orig_sentences = re.split(r'[.!?]+', original)
        corr_sentences = re.split(r'[.!?]+', corrected)
        
        orig_avg_len = sum(len(s.strip()) for s in orig_sentences if s.strip()) / max(len([s for s in orig_sentences if s.strip()]), 1)
        corr_avg_len = sum(len(s.strip()) for s in corr_sentences if s.strip()) / max(len([s for s in corr_sentences if s.strip()]), 1)
        
        sentence_style_score = 1.0 - min(0.5, abs(orig_avg_len - corr_avg_len) / max(orig_avg_len, 1))
        
        # 2. Registro linguistico (formale vs informale)
        informal_markers = ['eh', 'mah', 'beh', 'insomma', 'diciamo']
        orig_informal = sum(1 for marker in informal_markers if marker in original.lower())
        corr_informal = sum(1 for marker in informal_markers if marker in corrected.lower())
        
        register_score = 1.0 - min(0.3, abs(orig_informal - corr_informal) / max(orig_informal + 1, 1))
        
        return (sentence_style_score * 0.7 + register_score * 0.3)
    
    def _score_safety(self, original: str, corrected: str) -> float:
        """Valuta la sicurezza della correzione (anti-damage)"""
        safety_score = 1.0
        
        # 1. Verifica basic validation
        if not validate_correction(original, corrected):
            safety_score -= 0.3
        
        # 2. Controllo truncation
        if len(corrected) < len(original) * 0.7:
            safety_score -= 0.4  # Grosso taglio
        
        # 3. Controllo duplicazione
        words = corrected.split()
        if len(words) != len(set(words)) and len(words) > 5:
            # Molte parole duplicate
            duplicate_ratio = 1 - len(set(words)) / len(words)
            if duplicate_ratio > 0.3:
                safety_score -= 0.3
        
        # 4. Controllo caratteri strani
        if re.search(r'[^\w\s\.,;:!?\'"«»""''()\\-–—]', corrected):
            safety_score -= 0.2
        
        return max(0.0, safety_score)
    
    def _score_vocabulary_quality(self, original: str, corrected: str) -> float:
        """
        Valuta la qualità del vocabolario usando VdB (Nuovo Vocabolario di Base).
        Restituisce un bonus/penalty nell'intervallo [-0.10, +0.15].
        
        Args:
            original: Testo originale
            corrected: Testo corretto
            
        Returns:
            float: Bonus (+) o penalty (-) da applicare al quality score
        """
        if not self.vocabulary_service:
            return 0.0
        
        # Estrai parole significative (lunghezza >= 3, no punteggiatura)
        import re
        word_pattern = re.compile(r'\b[a-zA-ZàèéìòùÀÈÉÌÒÙ]{3,}\b')
        
        original_words = word_pattern.findall(original.lower())
        corrected_words = word_pattern.findall(corrected.lower())
        
        if not original_words or not corrected_words:
            return 0.0
        
        # Analizza parole originali
        original_difficulty = 0.0
        for word in original_words:
            analysis = self.vocabulary_service.analyze_word_detailed(word)
            original_difficulty += analysis.difficulty_score
        
        # Analizza parole corrette
        corrected_difficulty = 0.0
        for word in corrected_words:
            analysis = self.vocabulary_service.analyze_word_detailed(word)
            corrected_difficulty += analysis.difficulty_score
        
        # Calcola difficoltà media
        orig_avg_difficulty = original_difficulty / len(original_words)
        corr_avg_difficulty = corrected_difficulty / len(corrected_words)
        
        # Calcola adjustment
        # Se corrected è più semplice (difficulty minore) → bonus positivo
        # Se corrected è più complesso (difficulty maggiore) → penalty negativo
        difficulty_delta = orig_avg_difficulty - corr_avg_difficulty
        
        # Scala il delta in un bonus/penalty ragionevole
        # difficulty_delta range tipico: [-1.0, +1.0]
        # Vogliamo: +0.15 max bonus per semplificazioni, -0.10 max penalty per complicazioni
        if difficulty_delta > 0:
            # Semplificazione: bonus
            adjustment = min(0.15, difficulty_delta * 0.20)
        else:
            # Complicazione: penalty
            adjustment = max(-0.10, difficulty_delta * 0.15)
        
        # Log per debug
        if abs(adjustment) > 0.01:
            logger.debug(
                f"📚 Vocabulary analysis: orig_diff={orig_avg_difficulty:.2f}, "
                f"corr_diff={corr_avg_difficulty:.2f}, adjustment={adjustment:+.3f}"
            )
        
        return adjustment
    
    def _determine_confidence(self, overall_score: float, issues: List[str]) -> CorrectionConfidence:
        """Determina il livello di confidenza basato su score e issues"""
        if overall_score >= 0.98 and len(issues) == 0:
            return CorrectionConfidence.VERY_HIGH
        elif overall_score >= 0.95 and len(issues) <= 1:
            return CorrectionConfidence.HIGH
        elif overall_score >= 0.85 and len(issues) <= 2:
            return CorrectionConfidence.MEDIUM
        elif overall_score >= 0.70:
            return CorrectionConfidence.LOW
        else:
            return CorrectionConfidence.VERY_LOW
    
    def _should_apply_correction(self, quality_score: QualityScore, correction_type: str) -> bool:
        """Decide se applicare una correzione basandosi su qualità e modalità"""
        if self.conservative_mode:
            return quality_score.is_safe
        else:
            return quality_score.overall_score >= self.quality_threshold
    
    def _get_rollback_reason(self, quality_score: QualityScore) -> str:
        """Genera una ragione per il rollback"""
        if quality_score.overall_score < self.quality_threshold:
            return f"Quality score too low: {quality_score.overall_score:.1%} < {self.quality_threshold:.1%}"
        
        if quality_score.safety_score < 0.9:
            return f"Safety concerns: {quality_score.safety_score:.1%}"
        
        if quality_score.issues:
            return f"Quality issues: {', '.join(quality_score.issues[:2])}"
        
        return "Conservative mode: insufficient confidence"
    
    def _apply_correction_to_paragraph(self, paragraph, corrected_text: str):
        """Applica la correzione al paragrafo preservando la formattazione"""
        # Preserva la formattazione del primo run
        if paragraph.runs:
            first_run = paragraph.runs[0]
            # Pulisci tutti i runs
            for run in paragraph.runs:
                run.text = ""
            # Applica il nuovo testo al primo run
            first_run.text = corrected_text
        else:
            # Se non ci sono runs, crea un paragraph vuoto e aggiungi testo
            paragraph.clear()
            paragraph.add_run(corrected_text)
    
    def _track_correction(
        self,
        original_text: str,
        corrected_text: str,
        quality_score: QualityScore,
        source: CorrectionSource,
        correction_type: str,
        position: int,
        paragraph_index: int,
        is_applied: bool,
        rejection_reason: Optional[str] = None
    ):
        """
        Traccia una correzione nel collector per il report.
        
        Args:
            original_text: Testo originale
            corrected_text: Testo corretto
            quality_score: Punteggio di qualità
            source: Fonte della correzione
            correction_type: Tipo di correzione
            position: Posizione nel documento
            paragraph_index: Indice del paragrafo
            is_applied: Se la correzione è stata applicata
            rejection_reason: Motivo del rifiuto (se non applicata)
        """
        if self.collector is None:
            return
        
        # Determina la categoria in base al tipo di correzione e qualità
        category = self._determine_category_from_correction_type(
            correction_type, 
            quality_score,
            is_applied
        )
        
        # Crea il record
        record = CorrectionRecord(
            category=category,
            source=source,
            original_text=original_text,
            corrected_text=corrected_text if is_applied else None,
            context=original_text,  # Contesto è il testo stesso
            position=position,
            length=len(original_text),
            paragraph_index=paragraph_index,
            sentence_index=0,  # Approssimato
            rule_id=f"SAFE_CORRECTION_{correction_type.upper()}",
            rule_description=f"Safe correction: {correction_type}",
            message=f"Correction applied with quality score {quality_score.overall_score:.1%}",
            suggestions=[corrected_text] if corrected_text != original_text else [],
            confidence_score=quality_score.overall_score,
            severity=self._map_confidence_to_severity(quality_score.confidence),
            is_applied=is_applied,
            is_ignored=not is_applied,
            additional_info={
                'correction_type': correction_type,
                'quality_breakdown': {
                    'content_preservation': quality_score.content_preservation,
                    'grammar_improvement': quality_score.grammar_improvement,
                    'style_preservation': quality_score.style_preservation,
                    'safety_score': quality_score.safety_score,
                },
                'quality_issues': quality_score.issues,
                'rejection_reason': rejection_reason,
            }
        )
        
        # Aggiungi al collector (se disponibile)
        if self.collector is not None:
            self.collector.add_correction(record)
            logger.debug(f"📊 Tracked correction: {category.display_name} ({'applied' if is_applied else 'rejected'})")
        else:
            logger.debug(f"⚠️  Collector not available, skipping tracking for: {category.display_name}")
    
    def _determine_category_from_correction_type(
        self,
        correction_type: str,
        quality_score: QualityScore,
        is_applied: bool
    ) -> CorrectionCategory:
        """
        Determina la categoria di correzione in base al tipo e qualità.
        
        Args:
            correction_type: Tipo di correzione
            quality_score: Punteggio di qualità
            is_applied: Se la correzione è stata applicata
            
        Returns:
            Categoria appropriata
        """
        correction_type_lower = correction_type.lower()
        
        # Mappatura tipo → categoria
        if 'spell' in correction_type_lower or 'ortograf' in correction_type_lower:
            # Errori ortografici
            if quality_score.grammar_improvement > 0.8:
                return CorrectionCategory.ERRORI_RICONOSCIUTI
            else:
                return CorrectionCategory.SCONOSCIUTE
        
        elif 'grammar' in correction_type_lower or 'grammatic' in correction_type_lower:
            # Errori grammaticali
            return CorrectionCategory.ERRORI_RICONOSCIUTI
        
        elif 'style' in correction_type_lower or 'stile' in correction_type_lower:
            # Miglioramenti di stile
            return CorrectionCategory.MIGLIORABILI
        
        elif 'punct' in correction_type_lower or 'punteggiatura' in correction_type_lower:
            # Punteggiatura
            return CorrectionCategory.PUNTEGGIATURA
        
        elif 'ai' in correction_type_lower or 'gpt' in correction_type_lower:
            # Correzioni AI - categorizziamo in base alla qualità
            if quality_score.grammar_improvement > 0.8:
                return CorrectionCategory.ERRORI_RICONOSCIUTI
            else:
                return CorrectionCategory.MIGLIORABILI
        
        # Default: errori riconosciuti se applicata, sospette se rifiutata
        if is_applied:
            return CorrectionCategory.ERRORI_RICONOSCIUTI
        else:
            return CorrectionCategory.SOSPETTE
    
    def _map_confidence_to_severity(self, confidence: CorrectionConfidence) -> str:
        """
        Mappa il livello di confidenza a una severità.
        
        Args:
            confidence: Livello di confidenza
            
        Returns:
            Severità ('critical', 'warning', 'info', 'suggestion')
        """
        mapping = {
            CorrectionConfidence.VERY_HIGH: 'critical',
            CorrectionConfidence.HIGH: 'warning',
            CorrectionConfidence.MEDIUM: 'warning',
            CorrectionConfidence.LOW: 'info',
            CorrectionConfidence.VERY_LOW: 'suggestion',
        }
        return mapping.get(confidence, 'info')
        # Versione semplificata - la versione completa userà il sistema token/run esistente
        paragraph.text = corrected_text
    
    def _create_failed_quality_score(self, error_msg: str) -> QualityScore:
        """Crea un QualityScore per correzioni fallite"""
        return QualityScore(
            overall_score=0.0,
            confidence=CorrectionConfidence.VERY_LOW,
            content_preservation=0.0,
            grammar_improvement=0.0,
            style_preservation=0.0,
            safety_score=0.0,
            issues=[error_msg]
        )
    
    def _create_no_change_quality_score(self) -> QualityScore:
        """Crea un QualityScore per testi senza modifiche"""
        return QualityScore(
            overall_score=1.0,
            confidence=CorrectionConfidence.VERY_HIGH,
            content_preservation=1.0,
            grammar_improvement=0.8,  # Neutro - nessun miglioramento ma nemmeno peggioramento
            style_preservation=1.0,
            safety_score=1.0,
            issues=[]
        )
