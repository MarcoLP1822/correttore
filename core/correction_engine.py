# core/correction_engine.py
"""
Motore di correzione principale con integrazione AI, validazione qualità e rollback.
Orchestrazione del processo di correzione con safety guarantees.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import as_completed, ThreadPoolExecutor

from docx import Document as DocxDocument  # Renamed to avoid type confusion
from docx.text.paragraph import Paragraph

from core.document_handler import DocumentHandler, DocumentInfo
from services.openai_service import OpenAIService
from services.languagetool_service import LanguageToolService
from services.cache_service import get_cache
from src.core.safe_correction import SafeCorrector, QualityScore, CorrectionConfidence
from config.settings import get_correction_config

logger = logging.getLogger(__name__)

@dataclass
class CorrectionContext:
    """Contesto per una sessione di correzione"""
    source_document: DocxDocument  # type: ignore
    document_info: DocumentInfo
    target_paragraphs: List[Paragraph]
    corrections_applied: int = 0
    corrections_rejected: int = 0
    total_processed: int = 0
    corrections_log: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class CorrectionResult:
    """Risultato di una correzione completa"""
    success: bool
    document: Optional[DocxDocument]  # type: ignore
    context: CorrectionContext
    error_message: Optional[str] = None
    quality_scores: List[QualityScore] = field(default_factory=list)

class CorrectionEngine:
    """
    Motore principale di correzione con orchestrazione completa del processo.
    Integra AI, grammatica, caching e safety systems.
    """
    
    def __init__(self):
        self.document_handler = DocumentHandler()
        self.openai_service = OpenAIService()
        self.languagetool_service = LanguageToolService()
        self.cache_service = get_cache()
        self.safe_corrector = SafeCorrector()
        
        self.config = get_correction_config()
        # self.app_config = get_app_config()  # Commentato fino a quando non sarà implementato
        
        logger.info("🔧 CorrectionEngine initialized")
    
    def correct_document(self, input_path, output_path=None) -> CorrectionResult:
        """
        Corregge un documento completo con tutte le safety guarantees.
        
        Args:
            input_path: Percorso del documento da correggere
            output_path: Percorso di output (opzionale)
            
        Returns:
            CorrectionResult: Risultato completo della correzione
        """
        from pathlib import Path
        input_path = Path(input_path)
        
        if not output_path:
            output_path = input_path.parent / f"{input_path.stem}_corretto{input_path.suffix}"
        else:
            output_path = Path(output_path)
        
        logger.info(f"🎯 Starting document correction: {input_path.name}")
        
        try:
            # 1. Caricamento documento con validazione
            document, doc_info = self.document_handler.load_document(input_path, create_backup_copy=True)
            
            # 2. Identifica paragrafi da correggere
            all_paragraphs = self.document_handler.extract_all_paragraphs(document)
            target_paragraphs = [p for p in all_paragraphs 
                               if self._should_correct_paragraph(p)]
            
            context = CorrectionContext(
                source_document=document,
                document_info=doc_info,
                target_paragraphs=target_paragraphs
            )
            
            logger.info(f"📊 Found {len(target_paragraphs)} paragraphs to correct")
            
            # 3. Processo di correzione con batching
            success = self._process_corrections(context)
            
            if not success:
                return CorrectionResult(
                    success=False,
                    document=None,
                    context=context,
                    error_message="Correction process failed"
                )
            
            # 4. Salvataggio con validazione
            save_success = self.document_handler.save_document(
                document, output_path, validate_after_save=True
            )
            
            if not save_success:
                return CorrectionResult(
                    success=False,
                    document=document,
                    context=context,
                    error_message="Failed to save corrected document"
                )
            
            # 5. Report finale
            self._log_correction_summary(context, output_path)
            
            return CorrectionResult(
                success=True,
                document=document,
                context=context
            )
            
        except Exception as e:
            logger.error(f"❌ Document correction failed: {e}")
            
            # Tentativo di ripristino da backup se disponibile
            if hasattr(doc_info, 'backup_path') and doc_info.backup_path:
                logger.info("🔄 Attempting restore from backup...")
                if self.document_handler.restore_from_backup(doc_info.backup_path, input_path):
                    logger.info("✅ Document restored from backup")
                else:
                    logger.error("❌ Failed to restore from backup")
            
            return CorrectionResult(
                success=False,
                document=None,
                context=CorrectionContext(
                    source_document=DocxDocument(),  # type: ignore
                    document_info=DocumentInfo(
                        path=Path(""),
                        total_paragraphs=0,
                        total_characters=0,
                        needs_correction_count=0,
                        validation_result=ValidationResult(is_valid=False, errors=[], warnings=[])  # type: ignore
                    ),
                    target_paragraphs=[]
                ),
                error_message=str(e)
            )
    
    def correct_text_fragment(self, text: str, use_cache: bool = True) -> Tuple[str, QualityScore]:
        """
        Corregge un singolo frammento di testo.
        
        Args:
            text: Testo da correggere
            use_cache: Se utilizzare la cache
            
        Returns:
            Tuple[str, QualityScore]: Testo corretto e punteggio qualità
        """
        logger.debug(f"🔤 Correcting text fragment: {text[:50]}...")
        
        # 1. Check cache se abilitata
        if use_cache and self.config.cache_enabled:
            cached_entry = self.cache_service.get_with_similarity(text)
            if cached_entry:
                logger.debug("💾 Cache hit for text fragment")
                return cached_entry.corrected_text, QualityScore(  
                    overall_score=0.9,
                    confidence=CorrectionConfidence.HIGH,  # type: ignore
                    content_preservation=1.0,
                    grammar_improvement=0.8,
                    style_preservation=1.0,
                    safety_score=0.95,
                    issues=[]
                )
        
        # 2. Pre-validazione con LanguageTool
        lt_errors = self.languagetool_service.check_text(text)
        
        # 3. Correzione AI se necessaria
        if lt_errors or self._needs_ai_correction(text):
            corrected_text = self.openai_service.correct_text(text)
            if not corrected_text:
                logger.warning("⚠️  AI correction failed, using original text")
                corrected_text = text
        else:
            corrected_text = text
        
        # 4. Validazione qualità
        quality_score = self.safe_corrector.validate_correction_quality(text, corrected_text)
        
        # 5. Decisione applicazione correzione
        if quality_score.overall_score >= self.config.min_quality_threshold:
            # Cache il risultato se migliorato
            if use_cache and self.config.cache_enabled and corrected_text != text:
                self.cache_service.cache_with_metadata(
                    text=text,
                    correction=corrected_text,
                    quality=quality_score.overall_score if hasattr(quality_score, 'overall_score') else 0.8,
                    correction_type='correction_engine'
                )
            
            logger.debug(f"✅ Text corrected (score: {quality_score.overall_score:.2f})")
            return corrected_text, quality_score
        else:
            logger.debug(f"⚠️  Correction rejected (score: {quality_score.overall_score:.2f})")
            return text, quality_score
    
    def correct_paragraph_batch(self, paragraphs: List[Paragraph], max_workers: Optional[int] = None) -> List[Tuple[bool, QualityScore]]:
        """
        Corregge un batch di paragrafi in parallelo.
        
        Args:
            paragraphs: Lista di paragrafi da correggere
            max_workers: Numero massimo di thread (default: dalla config)
            
        Returns:
            List[Tuple[bool, QualityScore]]: Risultati per ogni paragrafo
        """
        if max_workers is None:
            max_workers = self.config.max_workers
        
        logger.info(f"🔄 Processing {len(paragraphs)} paragraphs with {max_workers} workers")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Invia tutti i task
            future_to_paragraph = {
                executor.submit(self._correct_single_paragraph, para): para 
                for para in paragraphs
            }
            
            # Raccogli i risultati mantenendo l'ordine
            for future in as_completed(future_to_paragraph):
                paragraph = future_to_paragraph[future]
                try:
                    success, quality_score = future.result()
                    results.append((success, quality_score))
                    
                    if success:
                        logger.debug(f"✅ Paragraph corrected (score: {quality_score.overall_score:.2f})")
                    else:
                        logger.debug(f"⚠️  Paragraph correction rejected")
                        
                except Exception as e:
                    logger.error(f"❌ Error correcting paragraph: {e}")
                    results.append((False, QualityScore(
                        overall_score=0.0,
                        confidence=CorrectionConfidence.VERY_LOW,
                        content_preservation=0.0,
                        grammar_improvement=0.0,
                        style_preservation=0.0,
                        safety_score=0.0,
                        issues=[f"Error: {str(e)}"]
                    )))
        
        success_count = sum(1 for success, _ in results if success)
        logger.info(f"📊 Batch complete: {success_count}/{len(paragraphs)} corrections applied")
        
        return results
    
    # Metodi privati
    
    def _process_corrections(self, context: CorrectionContext) -> bool:
        """Elabora tutte le correzioni per il contesto dato"""
        
        if not context.target_paragraphs:
            logger.info("ℹ️  No paragraphs require correction")
            return True
        
        # Processo in batch per efficienza
        batch_size = self.config.batch_size
        total_paragraphs = len(context.target_paragraphs)
        
        for i in range(0, total_paragraphs, batch_size):
            batch = context.target_paragraphs[i:i + batch_size]
            
            logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(total_paragraphs-1)//batch_size + 1}")
            
            # Correggi il batch
            batch_results = self.correct_paragraph_batch(batch)
            
            # Aggiorna statistiche
            for (success, quality_score) in batch_results:
                context.total_processed += 1
                if success:
                    context.corrections_applied += 1
                else:
                    context.corrections_rejected += 1
                
                # Log dettagliato per debugging
                context.corrections_log.append({
                    'paragraph_index': context.total_processed - 1,
                    'success': success,
                    'quality_score': quality_score.overall_score,
                    'timestamp': self._get_timestamp()
                })
        
        # Verifica soglia di successo
        success_rate = context.corrections_applied / context.total_processed if context.total_processed > 0 else 0
        
        if success_rate < self.config.min_success_rate:
            logger.error(f"❌ Success rate too low: {success_rate:.2%} < {self.config.min_success_rate:.2%}")
            return False
        
        logger.info(f"✅ Correction process completed with {success_rate:.2%} success rate")
        return True
    
    def _correct_single_paragraph(self, paragraph: Paragraph) -> Tuple[bool, QualityScore]:
        """Corregge un singolo paragrafo"""
        original_text = paragraph.text
        
        if not original_text.strip():
            return False, QualityScore(
                overall_score=0.0,
                confidence=CorrectionConfidence.VERY_LOW,
                content_preservation=1.0,  # Empty text preserved
                grammar_improvement=0.0,
                style_preservation=1.0,
                safety_score=1.0,  # Safe to skip empty
                issues=["Empty text skipped"]
            )
        
        try:
            corrected_text, quality_score = self.correct_text_fragment(original_text)
            
            # Applica la correzione se migliorata
            if corrected_text != original_text and quality_score.overall_score >= self.config.min_quality_threshold:
                # Preserva la formattazione applicando solo il testo
                self._apply_text_preserving_format(paragraph, corrected_text)
                return True, quality_score
            else:
                return False, quality_score
                
        except Exception as e:
            logger.error(f"❌ Error correcting paragraph: {e}")
            return False, QualityScore(
                overall_score=0.0,
                confidence=CorrectionConfidence.VERY_LOW,
                content_preservation=0.0,
                grammar_improvement=0.0,
                style_preservation=0.0,
                safety_score=0.0,
                issues=[f"Exception: {str(e)}"]
            )
    
    def _apply_text_preserving_format(self, paragraph: Paragraph, new_text: str):
        """Applica il nuovo testo preservando la formattazione esistente"""
        # Questa è una versione semplificata
        # Una versione più sofisticata dovrebbe preservare run specifici
        if paragraph.runs:
            paragraph.runs[0].text = new_text
            # Rimuovi run extra
            for run in paragraph.runs[1:]:
                run.text = ""
        else:
            paragraph.text = new_text
    
    def _should_correct_paragraph(self, paragraph: Paragraph) -> bool:
        """Determina se un paragrafo deve essere corretto"""
        text = paragraph.text.strip()
        
        if not text:
            return False
        
        # Evita paragrafi con equazioni matematiche
        if self._has_math_content(paragraph):
            return False
        
        # Evita paragrafi troppo corti (probabilmente titoli/labels)
        if len(text) < self.config.min_paragraph_length:
            return False
        
        # Evita paragrafi con pattern speciali (codici, date, numeri)
        if self._is_special_content(text):
            return False
        
        return True
    
    def _has_math_content(self, paragraph: Paragraph) -> bool:
        """Controlla se il paragrafo contiene contenuto matematico"""
        return bool(paragraph._p.xpath(".//*[local-name()='oMath' or local-name()='oMathPara']"))
    
    def _is_special_content(self, text: str) -> bool:
        """Controlla se il testo è contenuto speciale da non correggere"""
        import re
        
        special_patterns = [
            r'^\d+[\.\)]\s*$',              # numerazione "1." "1)"
            r'^\s*CAPITOLO\s+\d+\s*$',      # titoli capitolo
            r'^\s*[A-Z\s]{3,}\s*$',         # titoli tutto maiuscolo
            r'^[A-Z][a-z]+\s+\d{4}$',      # date "Gennaio 2024"
            r'^\s*\*{3,}\s*$',              # separatori asterischi
        ]
        
        for pattern in special_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _needs_ai_correction(self, text: str) -> bool:
        """Euristica per determinare se il testo potrebbe beneficiare di correzione AI"""
        # Pattern che suggeriscono possibili errori
        import re
        
        error_indicators = [
            r'( {2,})',                     # spazi multipli
            r'([,;:.!?]\S)',               # punteggiatura senza spazio
            r'(\S[,;:.!?])',               # nessuno spazio prima punteggiatura
            r'\b(pò)\b',                   # "pò" sbagliato
            r'\b(qual è)\b',               # possibile "qual'è"
            r'(«\s)|(\s»)',                # virgolette con spazi errati
        ]
        
        for pattern in error_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _log_correction_summary(self, context: CorrectionContext, output_path):
        """Registra un riassunto della sessione di correzione"""
        success_rate = context.corrections_applied / context.total_processed if context.total_processed > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 CORRECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📄 Source document: {context.document_info.path.name}")
        logger.info(f"💾 Output document: {output_path.name}")
        logger.info(f"📝 Total paragraphs: {context.document_info.total_paragraphs}")
        logger.info(f"🎯 Paragraphs processed: {context.total_processed}")
        logger.info(f"✅ Corrections applied: {context.corrections_applied}")
        logger.info(f"⚠️  Corrections rejected: {context.corrections_rejected}")
        logger.info(f"📈 Success rate: {success_rate:.2%}")
        logger.info("=" * 60)
    
    def _get_timestamp(self) -> str:
        """Genera timestamp per logging"""
        from datetime import datetime
        return datetime.now().isoformat()


# Factory function per uso diretto
def create_correction_engine() -> CorrectionEngine:
    """Crea un'istanza del motore di correzione con configurazione predefinita"""
    return CorrectionEngine()
