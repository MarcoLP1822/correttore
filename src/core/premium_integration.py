# premium_integration.py
"""
Integrazione del sistema premium nel flusso di correzione esistente.
"""

import logging
from typing import List, Optional
from pathlib import Path

from openai import AsyncOpenAI
from docx.text.paragraph import Paragraph

from .premium_correction_engine import PremiumCorrectionEngine, PremiumCorrectionResult
from .safe_correction import SafeCorrector

logger = logging.getLogger(__name__)

class PremiumCorrector:
    """Wrapper per integrare il sistema premium nel flusso esistente"""
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.premium_engine = PremiumCorrectionEngine(openai_client)
        self.stats = {
            'total_paragraphs': 0,
            'corrected_paragraphs': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'rejected': 0
        }
    
    async def correct_paragraph_premium_safe(self, paragraph: Paragraph, par_id: int, 
                                           mods: List, glossary: set) -> bool:
        """
        Correzione premium di un paragrafo con integrazione nel sistema esistente.
        Ritorna True se la correzione è stata applicata.
        """
        self.stats['total_paragraphs'] += 1
        
        try:
            # Esegui correzione premium
            result = await self.premium_engine.correct_paragraph_premium(paragraph, par_id)
            
            # Aggiorna statistiche
            if result.applied:
                self.stats['corrected_paragraphs'] += 1
                
                # Classifica per confidenza
                if result.confidence_score >= 0.9:
                    self.stats['high_confidence'] += 1
                elif result.confidence_score >= 0.8:
                    self.stats['medium_confidence'] += 1
                else:
                    self.stats['low_confidence'] += 1
                
                # Registra la modifica nel sistema esistente
                if result.original_text != result.corrected_text:
                    # Importa la classe Modification dal sistema esistente
                    from .correttore import Modification
                    mods.append(Modification(par_id, result.original_text, result.corrected_text))
                    
                    # Aggiorna glossario con nomi trovati
                    from .correttore import NAME_RE, GLOSSARY_STOP
                    for name in NAME_RE.findall(result.corrected_text):
                        if name.upper() not in GLOSSARY_STOP:
                            glossary.add(name)
                
                logger.info(f"✅ Premium correction applied to paragraph {par_id} "
                          f"(confidence: {result.confidence_score:.1%}, "
                          f"corrections: {result.total_corrections})")
                
                # Log dettagli se ci sono molte correzioni
                if result.total_corrections > 3:
                    logger.info(f"   📊 Details: {result.details}")
                    
                return True
            else:
                self.stats['rejected'] += 1
                logger.debug(f"⏭️  Premium correction rejected for paragraph {par_id} "
                           f"(quality: {result.quality_score.overall_score:.1%})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Premium correction failed for paragraph {par_id}: {e}")
            self.stats['rejected'] += 1
            return False
    
    def get_correction_stats(self) -> dict:
        """Ottieni statistiche delle correzioni premium"""
        total = self.stats['total_paragraphs']
        if total == 0:
            return self.stats
            
        success_rate = self.stats['corrected_paragraphs'] / total
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'rejection_rate': self.stats['rejected'] / total,
            'high_confidence_rate': self.stats['high_confidence'] / max(self.stats['corrected_paragraphs'], 1),
            'avg_corrections_per_paragraph': self.stats['corrected_paragraphs'] / max(total, 1)
        }

# Funzione per sostituire correct_paragraph_group nel sistema esistente
async def correct_paragraph_group_premium(
    paragraphs: List[Paragraph],
    all_paras: List[Paragraph],
    start_par_id: int,
    client: AsyncOpenAI,
    glossary: set[str],
    mods: List,
    context_size: int = 3,
    safe_corrector: Optional[SafeCorrector] = None,
    use_premium: bool = True
):
    """
    Versione premium di correct_paragraph_group che sostituisce quella esistente.
    Combina il sistema premium con fallback al sistema originale se necessario.
    """
    
    if not use_premium:
        # Fallback al sistema originale
        from .correttore import correct_paragraph_group
        return await correct_paragraph_group(
            paragraphs, all_paras, start_par_id, client, 
            glossary, mods, context_size, safe_corrector
        )
    
    # Inizializza correttore premium
    premium_corrector = PremiumCorrector(client)
    
    # Statistiche del chunk
    chunk_stats = {
        'premium_applied': 0,
        'premium_rejected': 0,
        'fallback_used': 0,
        'no_changes': 0
    }
    
    logger.info(f"🚀 Starting premium correction for chunk {start_par_id} "
              f"({len(paragraphs)} paragraphs)")
    
    # Processa ogni paragrafo
    for idx, paragraph in enumerate(paragraphs):
        par_id = start_par_id + idx
        original_text = paragraph.text
        
        # Salta paragrafi vuoti
        if not original_text.strip():
            chunk_stats['no_changes'] += 1
            continue
        
        try:
            # Prova correzione premium
            premium_success = await premium_corrector.correct_paragraph_premium_safe(
                paragraph, par_id, mods, glossary
            )
            
            if premium_success:
                chunk_stats['premium_applied'] += 1
            else:
                chunk_stats['premium_rejected'] += 1
                
                # Se premium fallisce, prova il sistema originale come fallback
                logger.debug(f"🔄 Trying fallback correction for paragraph {par_id}")
                
                try:
                    # Usa il safe_corrector se disponibile
                    if safe_corrector:
                        from .correttore import spellfix_paragraph
                        
                        def spellcheck_func(text):
                            return spellfix_paragraph(text, glossary)
                        
                        result = safe_corrector.correct_with_rollback(
                            paragraph, spellcheck_func, "fallback_spellcheck"
                        )
                        
                        if result.applied:
                            from .correttore import Modification
                            mods.append(Modification(par_id, original_text, result.corrected_text))
                            chunk_stats['fallback_used'] += 1
                            logger.debug(f"✅ Fallback correction applied to paragraph {par_id}")
                        else:
                            chunk_stats['no_changes'] += 1
                    else:
                        chunk_stats['no_changes'] += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️  Fallback correction also failed for paragraph {par_id}: {e}")
                    chunk_stats['no_changes'] += 1
                    
        except Exception as e:
            logger.error(f"❌ All correction methods failed for paragraph {par_id}: {e}")
            chunk_stats['no_changes'] += 1
    
    # Log finale del chunk
    logger.info(f"🎯 Premium chunk {start_par_id} completed: "
              f"premium={chunk_stats['premium_applied']} "
              f"rejected={chunk_stats['premium_rejected']} "
              f"fallback={chunk_stats['fallback_used']} "
              f"unchanged={chunk_stats['no_changes']}")
    
    # Log statistiche del correttore premium
    premium_stats = premium_corrector.get_correction_stats()
    if premium_stats['total_paragraphs'] > 0:
        logger.info(f"📊 Premium stats: success_rate={premium_stats['success_rate']:.1%} "
                  f"high_conf={premium_stats['high_confidence_rate']:.1%}")

# Funzione helper per abilitare il sistema premium in tutto il documento
def enable_premium_correction():
    """
    Abilita il sistema di correzione premium sostituendo la funzione originale.
    Chiamare questa funzione all'inizio del processo di correzione.
    """
    import sys
    from . import correttore
    
    # Sostituisci la funzione originale con quella premium
    original_func = correttore.correct_paragraph_group
    
    async def premium_wrapper(*args, **kwargs):
        # Aggiungi il parametro use_premium=True per default
        kwargs.setdefault('use_premium', True)
        return await correct_paragraph_group_premium(*args, **kwargs)
    
    # Sostituisci nel modulo
    correttore.correct_paragraph_group = premium_wrapper
    
    logger.info("🚀 Premium correction system enabled!")
    
    return original_func  # Ritorna la funzione originale per eventuale ripristino
