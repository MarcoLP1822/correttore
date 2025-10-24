"""
Sistema di Processamento Parallelo Ottimizzato - FASE 4
========================================================

Implementa:
- Correzione concorrente con semafori
- Load balancing automatico
- Rate limiting intelligente  
- Gestione errori paralleli
- Monitoring performance
- Circuit breaker per API
"""

import asyncio
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Any, Tuple, Union
from queue import Queue, Empty
import math

from correttore.config.settings import get_settings
from correttore.services.intelligent_cache import get_cache
from correttore.core.error_handling import ErrorHandler, CorrectionError

logger = logging.getLogger(__name__)


@dataclass
class ProcessingTask:
    """Task di processamento per il sistema parallelo"""
    task_id: str
    content: str
    chunk_index: int
    priority: int = 1
    attempts: int = 0
    max_attempts: int = 3
    estimated_tokens: int = 0
    processing_type: str = "correction"  # correction, validation, formatting
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """Risultato di processamento"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    processing_time: float = 0.0
    tokens_used: int = 0
    cached: bool = False
    attempts: int = 1


@dataclass
class ParallelStats:
    """Statistiche processamento parallelo"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    cached_results: int
    total_processing_time: float
    avg_processing_time: float
    throughput_per_minute: float
    parallelism_efficiency: float
    cache_hit_rate: float


class WorkerPool:
    """Pool di worker con load balancing"""
    
    def __init__(self, max_workers: int = 5, rate_limit_per_minute: int = 60):
        """
        Inizializza pool worker
        
        Args:
            max_workers: Numero massimo worker concorrenti
            rate_limit_per_minute: Limite richieste per minuto
        """
        self.max_workers = max_workers
        self.rate_limit = rate_limit_per_minute
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Rate limiting
        self.request_times: List[float] = []
        self.rate_lock = threading.Lock()
        
        # Monitoring
        self.active_workers = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = time.time()
        
        # Circuit breaker
        self.error_handler = ErrorHandler()
        
        logger.info(f"Worker pool initialized: {max_workers} workers, {rate_limit_per_minute} req/min")
    
    def can_submit_request(self) -> bool:
        """Verifica se può inviare nuova richiesta (rate limiting)"""
        with self.rate_lock:
            current_time = time.time()
            
            # Rimuovi richieste più vecchie di 1 minuto
            self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            return len(self.request_times) < self.rate_limit
    
    def record_request(self):
        """Registra nuova richiesta per rate limiting"""
        with self.rate_lock:
            self.request_times.append(time.time())
    
    def submit_task(self, func: Callable, task: ProcessingTask) -> Future:
        """
        Sottomette task al pool
        
        Args:
            func: Funzione da eseguire
            task: Task di processamento
            
        Returns:
            Future per il risultato
        """
        if not self.can_submit_request():
            # Attendi prima di sottomettere
            wait_time = 60 / self.rate_limit
            time.sleep(wait_time)
        
        self.record_request()
        self.active_workers += 1
        
        future = self.executor.submit(self._execute_with_monitoring, func, task)
        future.add_done_callback(lambda f: setattr(self, 'active_workers', self.active_workers - 1))
        
        return future
    
    def _execute_with_monitoring(self, func: Callable, task: ProcessingTask) -> ProcessingResult:
        """Esegue task con monitoring"""
        start_time = time.time()
        
        try:
            # Controllo circuit breaker
            if self.error_handler.circuit_breaker_openai():
                raise CorrectionError("Circuit breaker open - API temporaneamente non disponibile")
            
            result = func(task)
            
            processing_time = time.time() - start_time
            self.completed_tasks += 1
            
            return ProcessingResult(
                task_id=task.task_id,
                success=True,
                result=result,
                processing_time=processing_time,
                attempts=task.attempts + 1
            )
            
        except Exception as e:
            self.failed_tasks += 1
            processing_time = time.time() - start_time
            
            logger.error(f"Task {task.task_id} failed: {e}")
            
            return ProcessingResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                processing_time=processing_time,
                attempts=task.attempts + 1
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche pool"""
        runtime = time.time() - self.start_time
        total_tasks = self.completed_tasks + self.failed_tasks
        
        return {
            'active_workers': self.active_workers,
            'max_workers': self.max_workers,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'success_rate': self.completed_tasks / total_tasks if total_tasks > 0 else 0.0,
            'throughput_per_minute': (total_tasks / runtime) * 60 if runtime > 0 else 0.0,
            'runtime_seconds': runtime
        }
    
    def shutdown(self, wait: bool = True):
        """Chiude pool worker"""
        self.executor.shutdown(wait=wait)


class ParallelCorrector:
    """
    Sistema di correzione parallela con cache intelligente
    """
    
    def __init__(self, max_concurrent: int = 5, rate_limit: int = 60):
        """
        Inizializza correttore parallelo
        
        Args:
            max_concurrent: Numero massimo richieste concorrenti
            rate_limit: Limite richieste per minuto
        """
        self.settings = get_settings()
        self.cache = get_cache()
        self.worker_pool = WorkerPool(max_concurrent, rate_limit)
        
        # Statistics
        self.total_tasks = 0
        self.cached_results = 0
        self.processing_start_time = 0.0
        
        logger.info(f"Parallel corrector initialized: {max_concurrent} workers")
    
    def process_chunks_parallel(self, chunks: List[str], 
                              correction_func: Callable,
                              use_cache: bool = True) -> List[ProcessingResult]:
        """
        Processa chunks in parallelo con cache intelligente
        
        Args:
            chunks: Lista chunk di testo da processare
            correction_func: Funzione correzione da applicare
            use_cache: Se usare cache intelligente
            
        Returns:
            Lista risultati processamento
        """
        self.processing_start_time = time.time()
        self.total_tasks = len(chunks)
        
        # Crea tasks
        tasks = []
        for i, chunk in enumerate(chunks):
            task = ProcessingTask(
                task_id=f"chunk_{i}",
                content=chunk,
                chunk_index=i,
                estimated_tokens=int(len(chunk.split()) * 1.3)  # Stima approssimativa
            )
            tasks.append(task)
        
        # Bilancia carico
        balanced_tasks = self._balance_load(tasks)
        
        # Processa con cache check
        results = []
        futures = []
        
        for task in balanced_tasks:
            # Controlla cache prima
            if use_cache:
                cached_result = self._check_cache(task)
                if cached_result:
                    self.cached_results += 1
                    results.append(cached_result)
                    continue
            
            # Sottomette a worker pool
            future = self.worker_pool.submit_task(
                lambda t: self._process_single_task(t, correction_func), 
                task
            )
            futures.append((future, task))
        
        # Raccoglie risultati
        for future, task in futures:
            try:
                result = future.result(timeout=120)  # 2 min timeout
                
                # Cache risultato se successo e qualità alta
                if use_cache and result.success and hasattr(result.result, 'quality_score'):
                    if result.result.quality_score > 0.8:
                        self._cache_result(task, result)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error getting result for task {task.task_id}: {e}")
                results.append(ProcessingResult(
                    task_id=task.task_id,
                    success=False,
                    error=str(e)
                ))
        
        # Ordina risultati per chunk_index
        results.sort(key=lambda r: int(r.task_id.split('_')[1]))
        
        logger.info(f"Parallel processing completed: {len(results)} results, "
                   f"{self.cached_results} from cache")
        
        return results
    
    def _check_cache(self, task: ProcessingTask) -> Optional[ProcessingResult]:
        """Controlla se risultato è in cache"""
        cached_entry = self.cache.get_with_similarity(task.content, threshold=0.95)
        
        if cached_entry:
            return ProcessingResult(
                task_id=task.task_id,
                success=True,
                result=cached_entry.corrected_text,
                processing_time=0.0,
                cached=True
            )
        
        return None
    
    def _cache_result(self, task: ProcessingTask, result: ProcessingResult):
        """Cache risultato se di qualità"""
        if hasattr(result.result, 'corrected_text'):
            self.cache.cache_with_metadata(
                text=task.content,
                correction=result.result.corrected_text,
                quality=getattr(result.result, 'quality_score', 0.8),
                correction_type=task.processing_type,
                processing_time=result.processing_time,
                token_count=result.tokens_used
            )
    
    def _process_single_task(self, task: ProcessingTask, correction_func: Callable) -> Any:
        """Processa singolo task"""
        return correction_func(task.content)
    
    def _balance_load(self, tasks: List[ProcessingTask]) -> List[ProcessingTask]:
        """
        Bilancia carico tra worker basato su dimensione task
        
        Args:
            tasks: Lista task da bilanciare
            
        Returns:
            Task riordinati per load balancing
        """
        # Ordina per priorità e dimensione stimata
        def sort_key(task):
            return (-task.priority, -task.estimated_tokens)
        
        return sorted(tasks, key=sort_key)
    
    def estimate_optimal_workers(self, total_tokens: int, 
                                target_time_minutes: int = 5) -> int:
        """
        Stima numero ottimale di worker
        
        Args:
            total_tokens: Numero totale token da processare
            target_time_minutes: Tempo target in minuti
            
        Returns:
            Numero ottimale worker
        """
        # Stima basata su throughput API (tokens/min per worker)
        estimated_throughput_per_worker = 1000  # tokens/min per worker
        
        required_throughput = total_tokens / target_time_minutes
        optimal_workers = math.ceil(required_throughput / estimated_throughput_per_worker)
        
        # Limita ai vincoli di rate limiting
        max_by_rate_limit = self.worker_pool.rate_limit // 20  # ~3 req/min per worker
        
        return min(optimal_workers, max_by_rate_limit, 10)  # Max 10 worker
    
    def get_parallel_stats(self) -> ParallelStats:
        """Restituisce statistiche processamento parallelo"""
        runtime = time.time() - self.processing_start_time if self.processing_start_time else 1
        pool_stats = self.worker_pool.get_stats()
        cache_stats = self.cache.get_cache_stats()
        
        completed = pool_stats['completed_tasks']
        failed = pool_stats['failed_tasks']
        total = completed + failed
        
        return ParallelStats(
            total_tasks=self.total_tasks,
            completed_tasks=completed,
            failed_tasks=failed,
            cached_results=self.cached_results,
            total_processing_time=runtime,
            avg_processing_time=runtime / total if total > 0 else 0,
            throughput_per_minute=pool_stats['throughput_per_minute'],
            parallelism_efficiency=completed / self.total_tasks if self.total_tasks > 0 else 0,
            cache_hit_rate=cache_stats.hit_rate
        )
    
    def shutdown(self):
        """Chiude sistema parallelo"""
        self.worker_pool.shutdown()
        logger.info("Parallel corrector shutdown completed")


# Singleton globale
_parallel_corrector: Optional[ParallelCorrector] = None

def get_parallel_corrector(max_concurrent: int = 5) -> ParallelCorrector:
    """Restituisce istanza corrector parallelo globale"""
    global _parallel_corrector
    if _parallel_corrector is None:
        _parallel_corrector = ParallelCorrector(max_concurrent=max_concurrent)
    return _parallel_corrector


def shutdown_parallel_corrector():
    """Chiude corrector parallelo globale"""
    global _parallel_corrector
    if _parallel_corrector:
        _parallel_corrector.shutdown()
        _parallel_corrector = None
