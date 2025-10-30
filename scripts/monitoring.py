"""
Sistema di monitoring e metriche per il Correttore.

Traccia performance, qualità e statistiche operative in tempo reale.
"""
import time
import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from correttore.config.settings import Settings


@dataclass
class CorrectionMetric:
    """Metrica singola di correzione."""
    timestamp: datetime
    text_length: int
    processing_time: float
    quality_score: float
    correction_type: str  # 'spell', 'grammar', 'ai'
    success: bool
    error_type: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Converte in dizionario per serializzazione."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CorrectionMetric':
        """Crea da dizionario."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ApiMetrics:
    """Metriche API."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    rate_limit_hits: int = 0
    timeout_errors: int = 0
    
    def success_rate(self) -> float:
        """Calcola success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def average_cost_per_request(self) -> float:
        """Calcola costo medio per richiesta."""
        if self.successful_requests == 0:
            return 0.0
        return self.total_cost / self.successful_requests


@dataclass
class QualityMetrics:
    """Metriche di qualità."""
    corrections_attempted: int = 0
    corrections_applied: int = 0
    corrections_rejected: int = 0
    average_quality_score: float = 0.0
    content_preservation_rate: float = 0.0
    grammar_improvement_rate: float = 0.0
    style_preservation_rate: float = 0.0
    safety_score: float = 0.0
    
    def application_rate(self) -> float:
        """Calcola tasso di applicazione correzioni."""
        if self.corrections_attempted == 0:
            return 0.0
        return self.corrections_applied / self.corrections_attempted


@dataclass
class PerformanceMetrics:
    """Metriche di performance."""
    total_documents: int = 0
    total_processing_time: float = 0.0
    total_characters_processed: int = 0
    average_processing_speed: float = 0.0  # chars/second
    peak_processing_speed: float = 0.0
    slowest_processing_speed: float = float('inf')
    memory_usage_mb: float = 0.0
    
    def average_time_per_document(self) -> float:
        """Calcola tempo medio per documento."""
        if self.total_documents == 0:
            return 0.0
        return self.total_processing_time / self.total_documents


class QualityMonitor:
    """Monitor della qualità delle correzioni."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.metrics_history: List[CorrectionMetric] = []
        self.quality_trends = deque(maxlen=100)  # Ultimi 100 score
        
    def record_correction(self, 
                         text_length: int,
                         processing_time: float,
                         quality_score: float,
                         correction_type: str,
                         success: bool,
                         error_type: Optional[str] = None):
        """Registra una correzione."""
        metric = CorrectionMetric(
            timestamp=datetime.now(),
            text_length=text_length,
            processing_time=processing_time,
            quality_score=quality_score,
            correction_type=correction_type,
            success=success,
            error_type=error_type
        )
        
        self.metrics_history.append(metric)
        
        if success:
            self.quality_trends.append(quality_score)
            
    def get_correction_accuracy(self, time_window: Optional[timedelta] = None) -> float:
        """Calcola accuracy rate delle correzioni."""
        metrics = self._filter_metrics_by_time(time_window)
        
        if not metrics:
            return 0.0
            
        successful = sum(1 for m in metrics if m.success)
        return successful / len(metrics)
        
    def get_content_preservation_rate(self, time_window: Optional[timedelta] = None) -> float:
        """Calcola tasso di preservazione contenuto."""
        metrics = self._filter_metrics_by_time(time_window)
        
        if not metrics:
            return 0.0
            
        # Simula calcolo preservazione contenuto
        # In implementazione reale, questo richiederebbe accesso ai quality reports
        preservation_scores = [m.quality_score * 0.9 for m in metrics if m.success]
        
        if not preservation_scores:
            return 0.0
            
        return statistics.mean(preservation_scores)
        
    def get_quality_trend(self, lookback_count: int = 50) -> List[float]:
        """Restituisce trend qualità recente."""
        return list(self.quality_trends)[-lookback_count:]
        
    def detect_quality_degradation(self, threshold: float = 0.1) -> bool:
        """Rileva degradazione qualità."""
        if len(self.quality_trends) < 10:
            return False
            
        recent_scores = list(self.quality_trends)[-10:]
        older_scores = list(self.quality_trends)[-20:-10] if len(self.quality_trends) >= 20 else []
        
        if not older_scores:
            return False
            
        recent_avg = statistics.mean(recent_scores)
        older_avg = statistics.mean(older_scores)
        
        return (older_avg - recent_avg) > threshold
        
    def _filter_metrics_by_time(self, time_window: Optional[timedelta]) -> List[CorrectionMetric]:
        """Filtra metriche per finestra temporale."""
        if time_window is None:
            return self.metrics_history
            
        cutoff_time = datetime.now() - time_window
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]


class ApiPerformanceMonitor:
    """Monitor delle performance API."""
    
    def __init__(self):
        self.metrics = ApiMetrics()
        self.response_times: List[float] = []
        self.request_history = deque(maxlen=1000)
        
    def record_api_call(self, 
                       response_time: float,
                       success: bool,
                       tokens_used: int = 0,
                       cost: float = 0.0,
                       error_type: Optional[str] = None):
        """Registra chiamata API."""
        self.metrics.total_requests += 1
        self.response_times.append(response_time)
        
        call_record = {
            'timestamp': datetime.now(),
            'response_time': response_time,
            'success': success,
            'tokens': tokens_used,
            'cost': cost,
            'error_type': error_type
        }
        self.request_history.append(call_record)
        
        if success:
            self.metrics.successful_requests += 1
            self.metrics.total_tokens += tokens_used
            self.metrics.total_cost += cost
        else:
            self.metrics.failed_requests += 1
            
            if error_type == 'rate_limit':
                self.metrics.rate_limit_hits += 1
            elif error_type == 'timeout':
                self.metrics.timeout_errors += 1
                
        # Aggiorna tempo medio di risposta
        if self.response_times:
            self.metrics.average_response_time = statistics.mean(self.response_times[-100:])
            
    def get_requests_per_minute(self, window_minutes: int = 5) -> float:
        """Calcola richieste per minuto."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_requests = [
            r for r in self.request_history 
            if r['timestamp'] >= cutoff_time
        ]
        
        return len(recent_requests) / window_minutes
        
    def get_error_rate(self, window_minutes: int = 60) -> float:
        """Calcola error rate."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_requests = [
            r for r in self.request_history 
            if r['timestamp'] >= cutoff_time
        ]
        
        if not recent_requests:
            return 0.0
            
        errors = sum(1 for r in recent_requests if not r['success'])
        return errors / len(recent_requests)
        
    def is_rate_limited(self) -> bool:
        """Verifica se siamo in rate limiting."""
        # Controlla se ci sono stati rate limit hits negli ultimi 5 minuti
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_rate_limits = [
            r for r in self.request_history 
            if r['timestamp'] >= cutoff_time and r['error_type'] == 'rate_limit'
        ]
        
        return len(recent_rate_limits) > 0


class SystemMonitor:
    """Monitor generale del sistema."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.quality_monitor = QualityMonitor(settings)
        self.api_monitor = ApiPerformanceMonitor()
        self.performance_metrics = PerformanceMetrics()
        self.start_time = datetime.now()
        
    def record_document_processing(self,
                                 document_path: Path,
                                 processing_time: float,
                                 characters_processed: int,
                                 corrections_made: int,
                                 quality_score: float):
        """Registra processamento documento."""
        self.performance_metrics.total_documents += 1
        self.performance_metrics.total_processing_time += processing_time
        self.performance_metrics.total_characters_processed += characters_processed
        
        # Calcola velocità
        speed = characters_processed / processing_time if processing_time > 0 else 0
        self.performance_metrics.average_processing_speed = (
            self.performance_metrics.total_characters_processed / 
            self.performance_metrics.total_processing_time
        )
        
        if speed > self.performance_metrics.peak_processing_speed:
            self.performance_metrics.peak_processing_speed = speed
            
        if speed < self.performance_metrics.slowest_processing_speed:
            self.performance_metrics.slowest_processing_speed = speed
            
    def get_system_health(self) -> Dict[str, Any]:
        """Restituisce stato di salute del sistema."""
        return {
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'correction_accuracy': self.quality_monitor.get_correction_accuracy(),
            'api_success_rate': self.api_monitor.metrics.success_rate(),
            'average_quality_score': (
                statistics.mean(self.quality_monitor.quality_trends) 
                if self.quality_monitor.quality_trends else 0.0
            ),
            'processing_speed': self.performance_metrics.average_processing_speed,
            'documents_processed': self.performance_metrics.total_documents,
            'api_requests': self.api_monitor.metrics.total_requests,
            'total_cost': self.api_monitor.metrics.total_cost,
            'memory_usage_mb': self._get_memory_usage(),
            'quality_degradation': self.quality_monitor.detect_quality_degradation(),
            'rate_limited': self.api_monitor.is_rate_limited()
        }
        
    def generate_performance_report(self) -> Dict[str, Any]:
        """Genera report completo delle performance."""
        health = self.get_system_health()
        
        # Metriche dettagliate
        report = {
            'system_health': health,
            'quality_metrics': {
                'correction_accuracy_24h': self.quality_monitor.get_correction_accuracy(
                    timedelta(hours=24)
                ),
                'content_preservation_rate': self.quality_monitor.get_content_preservation_rate(),
                'quality_trend': self.quality_monitor.get_quality_trend(),
                'quality_degradation_detected': self.quality_monitor.detect_quality_degradation()
            },
            'api_metrics': {
                'success_rate': self.api_monitor.metrics.success_rate(),
                'average_response_time': self.api_monitor.metrics.average_response_time,
                'requests_per_minute': self.api_monitor.get_requests_per_minute(),
                'error_rate_1h': self.api_monitor.get_error_rate(60),
                'total_cost': self.api_monitor.metrics.total_cost,
                'average_cost_per_request': self.api_monitor.metrics.average_cost_per_request(),
                'tokens_used': self.api_monitor.metrics.total_tokens,
                'rate_limit_hits': self.api_monitor.metrics.rate_limit_hits,
                'timeout_errors': self.api_monitor.metrics.timeout_errors
            },
            'performance_metrics': {
                'documents_processed': self.performance_metrics.total_documents,
                'average_time_per_document': self.performance_metrics.average_time_per_document(),
                'processing_speed': self.performance_metrics.average_processing_speed,
                'peak_speed': self.performance_metrics.peak_processing_speed,
                'slowest_speed': (
                    self.performance_metrics.slowest_processing_speed 
                    if self.performance_metrics.slowest_processing_speed != float('inf') 
                    else 0
                ),
                'total_characters': self.performance_metrics.total_characters_processed,
                'uptime_hours': health['uptime_hours']
            },
            'alerts': self._generate_alerts()
        }
        
        return report
        
    def save_metrics(self, filepath: Path):
        """Salva metriche su file."""
        report = self.generate_performance_report()
        
        # Aggiungi timestamp
        report['generated_at'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
    def load_metrics(self, filepath: Path):
        """Carica metriche da file."""
        if not filepath.exists():
            return
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Ricostruisci oggetti da dati serializzati
        # Implementazione semplificata - in produzione servirebbero deserializzatori completi
        if 'api_metrics' in data:
            api_data = data['api_metrics']
            self.api_monitor.metrics.total_requests = api_data.get('total_requests', 0)
            self.api_monitor.metrics.successful_requests = api_data.get('successful_requests', 0)
            # ... altri campi
            
    def _get_memory_usage(self) -> float:
        """Ottieni uso memoria corrente."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            # Fallback se psutil non disponibile
            return 0.0
            
    def _generate_alerts(self) -> List[Dict[str, Any]]:
        """Genera alert basati sulle metriche."""
        alerts = []
        
        # Alert qualità
        if self.quality_monitor.detect_quality_degradation():
            alerts.append({
                'type': 'quality_degradation',
                'level': 'warning',
                'message': 'Quality degradation detected in recent corrections',
                'timestamp': datetime.now().isoformat()
            })
            
        # Alert API
        if self.api_monitor.get_error_rate(60) > 0.1:  # 10% error rate
            alerts.append({
                'type': 'high_api_error_rate',
                'level': 'error',
                'message': f'High API error rate: {self.api_monitor.get_error_rate(60):.1%}',
                'timestamp': datetime.now().isoformat()
            })
            
        if self.api_monitor.is_rate_limited():
            alerts.append({
                'type': 'rate_limited',
                'level': 'warning',
                'message': 'API rate limiting detected',
                'timestamp': datetime.now().isoformat()
            })
            
        # Alert performance
        if (self.performance_metrics.average_processing_speed > 0 and 
            self.performance_metrics.average_processing_speed < 100):  # chars/second
            alerts.append({
                'type': 'slow_processing',
                'level': 'warning',
                'message': f'Slow processing speed: {self.performance_metrics.average_processing_speed:.0f} chars/sec',
                'timestamp': datetime.now().isoformat()
            })
            
        return alerts


# Singleton monitor globale
_global_monitor: Optional[SystemMonitor] = None


def get_monitor(settings: Optional[Settings] = None) -> SystemMonitor:
    """Ottieni monitor globale."""
    global _global_monitor
    
    if _global_monitor is None:
        if settings is None:
            settings = Settings()
        _global_monitor = SystemMonitor(settings)
        
    return _global_monitor


def reset_monitor():
    """Reset monitor globale (per test)."""
    global _global_monitor
    _global_monitor = None


if __name__ == "__main__":
    # Test del sistema di monitoring
    print("=== SISTEMA DI MONITORING TEST ===\n")
    
    settings = Settings()
    monitor = SystemMonitor(settings)
    
    # Simula alcune correzioni
    print("Simulando correzioni...")
    for i in range(10):
        monitor.quality_monitor.record_correction(
            text_length=100 + i * 50,
            processing_time=0.5 + i * 0.1,
            quality_score=0.8 + (i % 3) * 0.1,
            correction_type=['spell', 'grammar', 'ai'][i % 3],
            success=i % 10 != 9  # 90% success rate
        )
        
    # Simula chiamate API
    print("Simulando chiamate API...")
    for i in range(20):
        monitor.api_monitor.record_api_call(
            response_time=1.0 + i * 0.1,
            success=i % 8 != 7,  # 87.5% success rate
            tokens_used=50 + i * 10,
            cost=0.001 + i * 0.0001
        )
        
    # Simula processamento documenti
    print("Simulando processamento documenti...")
    for i in range(5):
        monitor.record_document_processing(
            document_path=Path(f"doc_{i}.docx"),
            processing_time=10.0 + i * 2,
            characters_processed=5000 + i * 1000,
            corrections_made=20 + i * 5,
            quality_score=0.85 + i * 0.02
        )
        
    # Genera report
    print("\nGenerando report...")
    report = monitor.generate_performance_report()
    
    print(f"Accuracy: {report['quality_metrics']['correction_accuracy_24h']:.1%}")
    print(f"API Success Rate: {report['api_metrics']['success_rate']:.1%}")
    print(f"Processing Speed: {report['performance_metrics']['processing_speed']:.0f} chars/sec")
    print(f"Total Cost: ${report['api_metrics']['total_cost']:.4f}")
    print(f"Documents Processed: {report['performance_metrics']['documents_processed']}")
    
    if report['alerts']:
        print(f"\nAlerts: {len(report['alerts'])}")
        for alert in report['alerts']:
            print(f"  {alert['level'].upper()}: {alert['message']}")
    else:
        print("\nNessun alert rilevato.")
        
    # Salva report
    report_file = Path("monitoring_report.json")
    monitor.save_metrics(report_file)
    print(f"\nReport salvato in: {report_file}")
