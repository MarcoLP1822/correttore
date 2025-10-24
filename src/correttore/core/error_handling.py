# core/error_handling.py
"""
Sistema di gestione errori robusto per il correttore.
Gestisce errori API, corruzione dati, timeouts e recovery automatico.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Livelli di gravità degli errori"""
    LOW = "low"           # Warning, procedere
    MEDIUM = "medium"     # Errore recuperabile
    HIGH = "high"         # Errore critico, stop necessario
    CRITICAL = "critical" # Errore irreversibile, rollback

# ════════════════════════ ERRORI SPECIFICI ════════════════════════

class CorrectionError(Exception):
    """Errore base per il sistema di correzione"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.severity = severity
        self.context = context or {}


class APITimeoutError(CorrectionError):
    """Errore di timeout API"""
    def __init__(self, message: str = "API timeout", timeout_duration: float = 30.0):
        super().__init__(message, ErrorSeverity.MEDIUM)
        self.timeout_duration = timeout_duration


class RateLimitError(CorrectionError):
    """Errore di rate limiting API"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: float = 60.0):
        super().__init__(message, ErrorSeverity.MEDIUM)
        self.retry_after = retry_after
        self.timestamp = time.time()

class ContentLossError(CorrectionError):
    """Errore per perdita di contenuto durante la correzione"""
    def __init__(self, original_length: int, corrected_length: int, threshold: float = 0.1):
        loss_percent = abs(corrected_length - original_length) / original_length
        message = f"Content loss detected: {loss_percent:.1%} change (original: {original_length}, corrected: {corrected_length})"
        context = {
            "original_length": original_length,
            "corrected_length": corrected_length,
            "loss_percent": loss_percent,
            "threshold": threshold
        }
        super().__init__(message, ErrorSeverity.HIGH, context)

class FormattingLossError(CorrectionError):
    """Errore per perdita di formattazione"""
    def __init__(self, formatting_type: str, location: str):
        message = f"Formatting loss detected: {formatting_type} at {location}"
        context = {"formatting_type": formatting_type, "location": location}
        super().__init__(message, ErrorSeverity.MEDIUM, context)

class APIRateLimitError(CorrectionError):
    """Errore per rate limiting delle API"""
    def __init__(self, service: str, retry_after: Optional[float] = None):
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f", retry after {retry_after}s"
        context = {"service": service, "retry_after": retry_after}
        super().__init__(message, ErrorSeverity.LOW, context)

class DocumentCorruptionError(CorrectionError):
    """Errore per corruzione del documento"""
    def __init__(self, document_path: Path, corruption_type: str):
        message = f"Document corruption detected in {document_path.name}: {corruption_type}"
        context = {"document_path": str(document_path), "corruption_type": corruption_type}
        super().__init__(message, ErrorSeverity.CRITICAL, context)

# ════════════════════════ AZIONI DI RECOVERY ════════════════════════

@dataclass
class RecoveryAction:
    """Azione di recovery per gestire un errore"""
    action_type: str
    description: str
    execute: Callable[[], bool]
    estimated_time: float = 0.0
    success_rate: float = 1.0

@dataclass 
class RepairAction:
    """Azione di riparazione per documenti corrotti"""
    repair_type: str
    description: str
    execute: Callable[[Path], bool]
    backup_required: bool = True

# ════════════════════════ CIRCUIT BREAKER ════════════════════════

@dataclass
class CircuitBreakerStats:
    """Statistiche del circuit breaker"""
    total_requests: int = 0
    failed_requests: int = 0
    success_requests: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    state_changes: int = 0

class CircuitBreakerState(Enum):
    """Stati del circuit breaker"""
    CLOSED = "closed"      # Normale operazione
    OPEN = "open"          # Servizio guasto, blocco richieste
    HALF_OPEN = "half_open"  # Test recovery

class CircuitBreaker:
    """
    Circuit breaker per proteggere da servizi instabili.
    Protegge l'applicazione da chiamate ripetute a servizi guasti.
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 success_threshold: int = 2):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  
        self.success_threshold = success_threshold
        
        self.stats = CircuitBreakerStats()
        self.state = CircuitBreakerState.CLOSED
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        
    def call(self, func: Callable, *args, **kwargs):
        """Esegue una chiamata protetta dal circuit breaker"""
        current_time = time.time()
        
        # Check se possiamo provare a chiamare
        if not self._can_call(current_time):
            raise CorrectionError(
                f"Circuit breaker is OPEN for {func.__name__}",
                ErrorSeverity.MEDIUM,
                {"circuit_breaker_state": self.state.value}
            )
        
        self.stats.total_requests += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success(current_time)
            return result
            
        except Exception as e:
            self._on_failure(current_time, e)
            raise
    
    def _can_call(self, current_time: float) -> bool:
        """Determina se possiamo fare una chiamata"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
            
        elif self.state == CircuitBreakerState.OPEN:
            # Check se è tempo di provare recovery
            if current_time - self.stats.last_failure_time >= self.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False
            
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
            
        return False
    
    def _on_success(self, current_time: float):
        """Gestisce successo della chiamata"""
        self.stats.success_requests += 1
        self.stats.last_success_time = current_time
        self.consecutive_failures = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.consecutive_successes += 1
            if self.consecutive_successes >= self.success_threshold:
                self._transition_to_closed()
    
    def _on_failure(self, current_time: float, error: Exception):
        """Gestisce fallimento della chiamata"""
        self.stats.failed_requests += 1
        self.stats.last_failure_time = current_time
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.consecutive_failures >= self.failure_threshold:
                self._transition_to_open()
                
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transizione a stato OPEN"""
        logger.warning("🚨 Circuit breaker transitioning to OPEN state")
        self.state = CircuitBreakerState.OPEN
        self.stats.state_changes += 1
        
    def _transition_to_half_open(self):
        """Transizione a stato HALF_OPEN"""
        logger.info("🔄 Circuit breaker transitioning to HALF_OPEN state")
        self.state = CircuitBreakerState.HALF_OPEN
        self.stats.state_changes += 1
        self.consecutive_successes = 0
        
    def _transition_to_closed(self):
        """Transizione a stato CLOSED"""
        logger.info("✅ Circuit breaker transitioning to CLOSED state")
        self.state = CircuitBreakerState.CLOSED
        self.stats.state_changes += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche del circuit breaker"""
        failure_rate = 0.0
        if self.stats.total_requests > 0:
            failure_rate = self.stats.failed_requests / self.stats.total_requests
            
        return {
            "state": self.state.value,
            "total_requests": self.stats.total_requests,
            "success_requests": self.stats.success_requests,
            "failed_requests": self.stats.failed_requests,
            "failure_rate": failure_rate,
            "consecutive_failures": self.consecutive_failures,
            "state_changes": self.stats.state_changes,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time
        }

# ════════════════════════ ERROR HANDLER PRINCIPALE ════════════════════════

class ErrorHandler:
    """
    Gestore centrale degli errori con recovery automatico e logging.
    Coordina circuit breakers, recovery actions e logging dettagliato.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_counts: Dict[Type[Exception], int] = {}
        self.recovery_actions: Dict[Type[Exception], RecoveryAction] = {}
        
        # Inizializza circuit breakers per servizi
        self.circuit_breakers["openai"] = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=120.0,
            success_threshold=2
        )
        self.circuit_breakers["languagetool"] = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            success_threshold=2
        )
        
        self._setup_recovery_actions()
    
    def _setup_recovery_actions(self):
        """Configura azioni di recovery standard"""
        
        # Recovery per timeout API
        self.recovery_actions[APITimeoutError] = RecoveryAction(
            action_type="retry_with_backoff",
            description="Retry with exponential backoff",
            execute=lambda: self._wait_with_backoff(5.0),
            estimated_time=5.0,
            success_rate=0.8
        )
        
        # Recovery per rate limiting
        self.recovery_actions[APIRateLimitError] = RecoveryAction(
            action_type="wait_rate_limit", 
            description="Wait for rate limit reset",
            execute=lambda: self._wait_rate_limit(),
            estimated_time=60.0,
            success_rate=0.95
        )
    
    def handle_api_timeout(self, context: Dict[str, Any]) -> RecoveryAction:
        """Gestisce timeout delle API"""
        service = context.get("service", "unknown")
        timeout = context.get("timeout_seconds", 30)
        
        logger.warning(f"⏱️  API timeout for {service} ({timeout}s)")
        
        # Incrementa failure counter per circuit breaker
        if service in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[service]
            # Il circuit breaker gestirà le statistiche quando chiamato
        
        return RecoveryAction(
            action_type="retry_with_longer_timeout",
            description=f"Retry {service} with longer timeout",
            execute=lambda: True,  # Implementazione specifica nel caller
            estimated_time=timeout * 1.5
        )
    
    def handle_content_corruption(self, doc_path: Path) -> RepairAction:
        """Gestisce corruzione del documento"""
        logger.error(f"📄 Document corruption detected: {doc_path.name}")
        
        return RepairAction(
            repair_type="restore_from_backup",
            description="Restore document from backup",
            execute=lambda path: self._restore_from_backup(path),
            backup_required=False  # Usa backup esistente
        )
    
    def circuit_breaker_openai(self) -> bool:
        """Verifica se il circuit breaker OpenAI permette chiamate"""
        cb = self.circuit_breakers.get("openai")
        if cb:
            return cb.state == CircuitBreakerState.CLOSED
        return True
    
    def get_circuit_breaker(self, service: str) -> Optional[CircuitBreaker]:
        """Ottieni circuit breaker per un servizio"""
        return self.circuit_breakers.get(service)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log centralizzato degli errori con context"""
        error_type = type(error)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        context_str = ""
        if context:
            context_items = [f"{k}={v}" for k, v in context.items()]
            context_str = f" [{', '.join(context_items)}]"
        
        if isinstance(error, CorrectionError):
            level = {
                ErrorSeverity.LOW: logger.info,
                ErrorSeverity.MEDIUM: logger.warning,
                ErrorSeverity.HIGH: logger.error,
                ErrorSeverity.CRITICAL: logger.critical
            }.get(error.severity, logger.error)
            
            level(f"❌ {error.severity.value.upper()}: {error}{context_str}")
        else:
            logger.error(f"❌ UNEXPECTED: {error.__class__.__name__}: {error}{context_str}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche degli errori"""
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_errors": total_errors,
            "error_counts": {cls.__name__: count for cls, count in self.error_counts.items()},
            "circuit_breaker_stats": {
                service: cb.get_stats() 
                for service, cb in self.circuit_breakers.items()
            }
        }
    
    def _wait_with_backoff(self, base_delay: float) -> bool:
        """Attende con backoff esponenziale"""
        time.sleep(base_delay)
        return True
    
    def _wait_rate_limit(self) -> bool:
        """Attende reset del rate limit"""
        time.sleep(60)  # Wait standard per rate limit
        return True
        
    def _restore_from_backup(self, doc_path: Path) -> bool:
        """Ripristina documento da backup"""
        try:
            # Logica di ripristino implementata in DocumentValidator
            from correttore.core.validation import DocumentValidator
            validator = DocumentValidator()
            return validator.restore_from_backup(doc_path.parent / f"{doc_path.stem}_backup.docx", doc_path)
        except Exception as e:
            logger.error(f"❌ Failed to restore from backup: {e}")
            return False

# ════════════════════════ FACTORY FUNCTIONS ════════════════════════

def create_error_handler() -> ErrorHandler:
    """Crea un gestore errori configurato"""
    return ErrorHandler()

def handle_correction_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Optional[RecoveryAction]:
    """Gestisce un errore di correzione e restituisce azione di recovery"""
    handler = create_error_handler()
    handler.log_error(error, context)
    
    if isinstance(error, APITimeoutError):
        return handler.handle_api_timeout(context or {})
    elif isinstance(error, DocumentCorruptionError):
        # RepairAction, non RecoveryAction
        return None
    
    return None
