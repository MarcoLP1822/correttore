# services/openai_service.py
"""
Servizio per l'integrazione con OpenAI GPT-4o-mini.
Encapsula tutte le chiamate AI con retry, rate limiting e gestione errori.
"""

import logging
import asyncio
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

import openai
from openai import AsyncOpenAI

from correttore.config.settings import get_openai_config
from correttore.utils.token_utils import count_tokens
from correttore.services.intelligent_cache import get_cache
from correttore.models import (
    CorrectionRecord,
    CorrectionCategory,
    CorrectionSource,
)

logger = logging.getLogger(__name__)

@dataclass
class CorrectionRequest:
    """Richiesta di correzione per OpenAI"""
    text: str
    context: Optional[str] = None
    preserve_formatting: bool = True
    language: str = "italiano"

@dataclass
class CorrectionResponse:
    """Risposta di correzione da OpenAI"""
    original_text: str
    corrected_text: str
    success: bool
    error_message: Optional[str] = None
    tokens_used: int = 0
    response_time: float = 0.0

class OpenAIService:
    """
    Servizio centralizzato per interazioni con OpenAI.
    Gestisce autenticazione, retry, rate limiting e caching.
    """
    
    def __init__(self):
        self.config = get_openai_config()
        self.cache_service = get_cache()
        
        # Setup client OpenAI
        openai.api_key = self.config.api_key
        self.client = AsyncOpenAI(api_key=self.config.api_key)
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset_time = 0
        
        logger.info("🤖 OpenAI Service initialized")
    
    def correct_text(self, text: str, context: Optional[str] = None) -> Optional[str]:
        """
        Corregge un testo usando OpenAI in modo sincrono.
        
        Args:
            text: Testo da correggere
            context: Contesto opzionale per migliorare la correzione
            
        Returns:
            Optional[str]: Testo corretto o None se fallita
        """
        try:
            # Esegui correzione asincrona in modo sincrono
            return asyncio.run(self.correct_text_async(text, context))
        except Exception as e:
            logger.error(f"❌ Sync text correction failed: {e}")
            return None
    
    async def correct_text_async(self, text: str, context: Optional[str] = None) -> Optional[str]:
        """
        Corregge un testo usando OpenAI in modo asincrono.
        
        Args:
            text: Testo da correggere
            context: Contesto opzionale
            
        Returns:
            Optional[str]: Testo corretto o None se fallita
        """
        request = CorrectionRequest(
            text=text,
            context=context,
            preserve_formatting=True,
            language="italiano"
        )
        
        response = await self.process_correction_request(request)
        
        if response.success:
            return response.corrected_text
        else:
            logger.warning(f"⚠️  Correction request failed: {response.error_message}")
            return None
    
    async def process_correction_request(self, request: CorrectionRequest) -> CorrectionResponse:
        """
        Elabora una richiesta di correzione completa con tutte le safety measures.
        
        Args:
            request: Richiesta di correzione
            
        Returns:
            CorrectionResponse: Risposta completa
        """
        start_time = time.time()
        
        # 1. Validazione input
        if not request.text.strip():
            return CorrectionResponse(
                original_text=request.text,
                corrected_text=request.text,
                success=False,
                error_message="Empty text provided"
            )
        
        # 2. Check cache
        cache_key = self._generate_cache_key(request)
        cached_entry = self.cache_service.get_with_similarity(request.text)
        if cached_entry:
            logger.debug("💾 Cache hit for OpenAI request")
            return CorrectionResponse(
                original_text=request.text,
                corrected_text=cached_entry.corrected_text,
                success=True,
                response_time=time.time() - start_time
            )
        
        # 3. Rate limiting
        await self._handle_rate_limiting()
        
        # 4. Esegui richiesta con retry
        try:
            corrected_text = await self._make_correction_request(request)
            
            if corrected_text:
                # Cache il risultato con metadata
                self.cache_service.cache_with_metadata(
                    text=request.text,
                    correction=corrected_text,
                    quality=0.9,  # Qualità alta per OpenAI
                    correction_type='openai_gpt'
                )
                
                response = CorrectionResponse(
                    original_text=request.text,
                    corrected_text=corrected_text,
                    success=True,
                    tokens_used=count_tokens(request.text + corrected_text),
                    response_time=time.time() - start_time
                )
                
                logger.debug(f"✅ OpenAI correction completed in {response.response_time:.2f}s")
                return response
            else:
                return CorrectionResponse(
                    original_text=request.text,
                    corrected_text=request.text,
                    success=False,
                    error_message="OpenAI returned empty response",
                    response_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"❌ OpenAI correction request failed: {e}")
            return CorrectionResponse(
                original_text=request.text,
                corrected_text=request.text,
                success=False,
                error_message=str(e),
                response_time=time.time() - start_time
            )
    
    async def correct_text_batch(self, texts: List[str], max_concurrent: Optional[int] = None) -> List[Optional[str]]:
        """
        Corregge una lista di testi in parallelo con controllo concorrenza.
        
        Args:
            texts: Lista di testi da correggere
            max_concurrent: Numero massimo di richieste concorrenti
            
        Returns:
            List[Optional[str]]: Testi corretti (None se falliti)
        """
        if max_concurrent is None:
            max_concurrent = self.config.max_concurrent_requests
            
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def correct_with_semaphore(text: str) -> Optional[str]:
            async with semaphore:
                return await self.correct_text_async(text)
        
        tasks = [correct_with_semaphore(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converti eccezioni in None
        corrected_texts = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Batch correction error: {result}")
                corrected_texts.append(None)
            else:
                corrected_texts.append(result)
        
        success_count = sum(1 for r in corrected_texts if r is not None)
        logger.info(f"📊 Batch correction: {success_count}/{len(texts)} successful")
        
        return corrected_texts
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Ritorna statistiche di utilizzo del servizio"""
        return {
            'total_requests': self.request_count,
            'rate_limit_reset_time': self.rate_limit_reset_time,
            'last_request_time': self.last_request_time,
            'cache_stats': {
                'hits': getattr(self.cache_service, '_hits', 0),
                'misses': getattr(self.cache_service, '_misses', 0),
                'lookups': getattr(self.cache_service, '_lookups', 0)
            }
        }
    
    # Metodi privati
    
    async def _make_correction_request(self, request: CorrectionRequest) -> Optional[str]:
        """Esegue la richiesta OpenAI con retry automatico"""
        
        # Prepara il prompt
        prompt = self._build_correction_prompt(request)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    timeout=self.config.timeout
                )
                
                self.request_count += 1
                self.last_request_time = time.time()
                
                # Estrai il testo corretto
                content = response.choices[0].message.content
                if content is None:
                    logger.warning("⚠️  Empty response from OpenAI")
                    return None
                    
                corrected_text = content.strip()
                
                # Validazione base della risposta
                if self._validate_correction_response(request.text, corrected_text):
                    return corrected_text
                else:
                    logger.warning(f"⚠️  Invalid correction response from OpenAI")
                    return None
                
            except openai.RateLimitError as e:
                logger.warning(f"⚠️  Rate limit hit, attempt {attempt + 1}")
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    raise e
                    
            except openai.APITimeoutError as e:
                logger.warning(f"⚠️  Timeout, attempt {attempt + 1}")
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    raise e
                    
            except Exception as e:
                logger.error(f"❌ OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    raise e
        
        return None
    
    def _build_correction_prompt(self, request: CorrectionRequest) -> str:
        """Costruisce il prompt per la correzione"""
        
        base_prompt = f"""Correggi il seguente testo in italiano, correggendo TUTTI gli errori:

TESTO DA CORREGGERE:
{request.text}

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

TESTO CORRETTO:"""

        if request.context:
            base_prompt = f"""CONTESTO: {request.context}

{base_prompt}"""
        
        return base_prompt
    
    def _get_system_prompt(self) -> str:
        """Ritorna il prompt di sistema per OpenAI"""
        return """Sei un correttore di bozze esperto in lingua italiana. 
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
    
    def _validate_correction_response(self, original: str, corrected: str) -> bool:
        """Valida che la risposta di correzione sia ragionevole"""
        
        if not corrected:
            return False
        
        # La correzione non deve essere troppo diversa in lunghezza
        length_ratio = len(corrected) / len(original) if len(original) > 0 else 0
        if length_ratio < 0.5 or length_ratio > 2.0:
            logger.warning(f"⚠️  Suspicious length change: {length_ratio:.2f}")
            return False
        
        # Non dovrebbe contenere placeholder o errori tipici dell'AI
        suspicious_patterns = [
            "[CORRETTO]", "[ERRORE]", "```", "**", "Non posso", "Mi dispiace"
        ]
        
        for pattern in suspicious_patterns:
            if pattern.lower() in corrected.lower():
                logger.warning(f"⚠️  Suspicious content in response: {pattern}")
                return False
        
        return True
    
    def _generate_cache_key(self, request: CorrectionRequest) -> str:
        """Genera una chiave cache per la richiesta"""
        import hashlib
        
        # Combina testo e parametri rilevanti
        cache_input = f"{request.text}|{request.context or ''}|{request.language}"
        
        return hashlib.md5(cache_input.encode('utf-8')).hexdigest()
    
    async def _handle_rate_limiting(self):
        """Gestisce il rate limiting per rispettare i limiti OpenAI"""
        current_time = time.time()
        
        # Rate limiting semplice: attesa minima tra richieste
        time_since_last = current_time - self.last_request_time
        min_interval = 60.0 / self.config.requests_per_minute
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            logger.debug(f"⏱️  Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
    
    def create_correction_record_from_response(
        self,
        original_text: str,
        corrected_text: str,
        context: Optional[str] = None,
        position: int = 0
    ) -> Optional[CorrectionRecord]:
        """
        Crea un CorrectionRecord dalle correzioni GPT.
        
        Per GPT, confrontiamo il testo originale con quello corretto
        e creiamo un record generale per le differenze trovate.
        
        Args:
            original_text: Testo originale
            corrected_text: Testo corretto da GPT
            context: Contesto opzionale
            position: Posizione nel documento
            
        Returns:
            CorrectionRecord se ci sono differenze, None altrimenti
        """
        # Se identici, nessuna correzione
        if original_text.strip() == corrected_text.strip():
            return None
        
        # Determina la categoria basandosi sul tipo di correzione
        # Per GPT, usiamo ERRORI_RICONOSCIUTI come default
        category = CorrectionCategory.ERRORI_RICONOSCIUTI
        
        # Se il testo è molto simile, probabilmente è un miglioramento di stile
        similarity = self._calculate_similarity(original_text, corrected_text)
        if similarity > 0.9:
            category = CorrectionCategory.MIGLIORABILI
        
        # Usa il contesto fornito o il testo completo
        record_context = context or original_text
        
        # Calcola indici paragrafo (approssimativo)
        paragraph_index = original_text.count('\n\n')
        sentence_index = original_text.count('. ')
        
        # Crea il record
        record = CorrectionRecord(
            category=category,
            source=CorrectionSource.OPENAI_GPT,
            original_text=original_text,
            corrected_text=corrected_text,
            context=record_context,
            position=position,
            length=len(original_text),
            paragraph_index=paragraph_index,
            sentence_index=sentence_index,
            rule_id="GPT_CORRECTION",
            rule_description="Correzione AI avanzata",
            message="Testo migliorato da OpenAI GPT",
            suggestions=[corrected_text],
            confidence_score=0.85,  # Alta confidenza per GPT
            severity="warning",
            additional_info={
                'model': self.config.model,
                'similarity': similarity,
            }
        )
        
        return record
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcola similarità tra due testi (Jaccard similarity semplificata).
        
        Args:
            text1: Primo testo
            text2: Secondo testo
            
        Returns:
            Punteggio di similarità (0.0-1.0)
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


# Factory function per uso diretto
def create_openai_service() -> OpenAIService:
    """Crea un'istanza del servizio OpenAI con configurazione predefinita"""
    return OpenAIService()
