# settings.py
"""
Configurazione centralizzata dell'applicazione
(modello OpenAI, limiti token, retry, …)
"""

OPENAI_MODEL = "gpt-4o-mini-2024-07-18"     # modello da usare ovunque
MAX_TOKENS   = 10_000            # contesto massimo per i prompt
MAX_RETRY = 5                    # numero massimo di retry
RETRY_BACKOFF = (1, 2, 4)        # secondi di attesa ai retry


# Configurazione avanzata per classi di configurazione
class Settings:
    """Configurazione avanzata per il sistema di monitoring."""
    
    # OpenAI Configuration
    OPENAI_MODEL = OPENAI_MODEL
    MAX_TOKENS = MAX_TOKENS
    MAX_RETRY = MAX_RETRY
    RETRY_BACKOFF = RETRY_BACKOFF
    
    # Monitoring Configuration
    METRICS_RETENTION_DAYS = 30
    REALTIME_WINDOW_SIZE = 100
    EXPORT_INTERVAL_MINUTES = 60
    
    # Quality Configuration
    DEFAULT_QUALITY_THRESHOLD = 0.85
    QUALITY_WEIGHTS = {
        'content_preservation': 0.40,
        'grammar_improvement': 0.25,
        'style_preservation': 0.20,
        'safety_score': 0.15
    }
    
    # Cache Configuration
    CACHE_SIMILARITY_THRESHOLD = 0.85
    CACHE_MAX_ENTRIES = 1000
    CACHE_EXPIRY_DAYS = 7
    
    # Parallel Processing Configuration
    MAX_CONCURRENT_WORKERS = 5
    TARGET_PROCESSING_TIME_MINUTES = 5
    RATE_LIMIT_PER_MINUTE = 60


# Istanza globale settings
_settings_instance = None

def get_settings() -> Settings:
    """Restituisce l'istanza globale delle impostazioni."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance

def get_validation_config():
    """Restituisce la configurazione per la validazione."""
    return {
        'quality_threshold': Settings.DEFAULT_QUALITY_THRESHOLD,
        'quality_weights': Settings.QUALITY_WEIGHTS,
        'backup_enabled': True,
        'validate_before_processing': True,
        'validate_after_processing': True,
    }
