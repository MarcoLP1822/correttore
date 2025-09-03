# settings.py
"""
Configurazione centralizzata dell'applicazione
(modello OpenAI, limiti token, retry, …)
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

OPENAI_MODEL = "gpt-4o-mini-2024-07-18"     # modello da usare ovunque
MAX_TOKENS   = 10_000            # contesto massimo per i prompt
MAX_RETRY = 5                    # numero massimo di retry
RETRY_BACKOFF = (1, 2, 4)        # secondi di attesa ai retry


@dataclass
class OpenAIConfig:
    """Configurazione OpenAI con tutti i campi necessari"""
    api_key: str
    model: str = "gpt-4o-mini"
    max_tokens: int = 3500
    temperature: float = 0.3
    timeout: int = 45
    max_retries: int = 3
    retry_delay: float = 2.0
    requests_per_minute: int = 40
    max_concurrent_requests: int = 3

@dataclass
class LanguageToolConfig:
    """Configurazione LanguageTool con tutti i campi necessari"""
    enabled: bool = True
    host: str = 'localhost'
    port: int = 8081
    timeout: int = 30
    max_retries: int = 3
    language: str = 'it'
    jar_path: str = 'languagetool/languagetool-commandline.jar'
    whitelist_file: str = 'config/languagetool_whitelist.txt'
    custom_rules_file: str = 'config/languagetool_custom_rules.xml'

@dataclass
class CorrectionConfig:
    """Configurazione per il motore di correzione"""
    max_concurrent_workers: int = 5
    target_processing_time_minutes: int = 5
    quality_threshold: float = 0.85
    cache_enabled: bool = True
    backup_enabled: bool = True
    max_retries: int = 5
    min_quality_threshold: float = 0.85
    max_workers: int = 5
    batch_size: int = 10
    min_success_rate: float = 0.80
    min_paragraph_length: int = 20


def load_yaml_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """Carica la configurazione dal file YAML"""
    if config_file is None:
        config_file = "config.yaml"
    
    config_path = Path(config_file)
    if not config_path.exists():
        # Fallback ai valori di default
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if isinstance(config, dict) else {}
    except Exception as e:
        print(f"Errore nel caricamento del config YAML: {e}")
        return {}


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


def load_settings(config_file: Optional[str] = None) -> Settings:
    """Carica le impostazioni dal file di configurazione YAML"""
    # Per ora restituisce le impostazioni di default, ma può essere esteso
    # per caricare configurazioni specifiche dal YAML
    return get_settings()

def get_validation_config():
    """Restituisce la configurazione per la validazione."""
    return {
        'quality_threshold': Settings.DEFAULT_QUALITY_THRESHOLD,
        'quality_weights': Settings.QUALITY_WEIGHTS,
        'backup_enabled': True,
        'validate_before_processing': True,
        'validate_after_processing': True,
        'backup_retention_days': Settings.METRICS_RETENTION_DAYS,
    }

def get_openai_config() -> OpenAIConfig:
    """Restituisce la configurazione per OpenAI."""
    # Carica configurazione YAML
    yaml_config = load_yaml_config()
    openai_config = yaml_config.get('openai', {})
    
    # Ottieni API key dall'ambiente
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Crea configurazione con valori dal YAML o defaults
    return OpenAIConfig(
        api_key=api_key,
        model=openai_config.get('model', 'gpt-4o-mini'),
        max_tokens=openai_config.get('max_tokens', 3500),
        temperature=openai_config.get('temperature', 0.3),
        timeout=openai_config.get('timeout', 45),
        max_retries=openai_config.get('max_retries', 3),
        retry_delay=openai_config.get('retry_delay', 2.0),
        requests_per_minute=openai_config.get('requests_per_minute', 40),
        max_concurrent_requests=openai_config.get('max_concurrent_requests', 3)
    )

def get_languagetool_config():
    """Restituisce la configurazione per LanguageTool."""
    config_data = load_yaml_config()
    languagetool_config = config_data.get('languagetool', {})
    
    return LanguageToolConfig(
        enabled=languagetool_config.get('enabled', True),
        host=languagetool_config.get('host', 'localhost'),
        port=languagetool_config.get('port', 8081),
        timeout=languagetool_config.get('timeout', 30),
        max_retries=languagetool_config.get('max_retries', 3),
        language=languagetool_config.get('language', 'it'),
        jar_path=languagetool_config.get('jar_path', 'languagetool/languagetool-commandline.jar'),
        whitelist_file=languagetool_config.get('whitelist_file', 'config/languagetool_whitelist.txt'),
        custom_rules_file=languagetool_config.get('custom_rules_file', 'config/languagetool_custom_rules.xml')
    )

def get_correction_config():
    """Restituisce la configurazione per il motore di correzione."""
    config_data = load_yaml_config()
    correction_config = config_data.get('correction', {})
    
    return CorrectionConfig(
        max_concurrent_workers=correction_config.get('max_concurrent_workers', Settings.MAX_CONCURRENT_WORKERS),
        target_processing_time_minutes=correction_config.get('target_processing_time_minutes', Settings.TARGET_PROCESSING_TIME_MINUTES),
        quality_threshold=correction_config.get('quality_threshold', Settings.DEFAULT_QUALITY_THRESHOLD),
        cache_enabled=correction_config.get('cache_enabled', True),
        backup_enabled=correction_config.get('backup_enabled', True),
        max_retries=correction_config.get('max_retries', Settings.MAX_RETRY),
        min_quality_threshold=correction_config.get('min_quality_threshold', Settings.DEFAULT_QUALITY_THRESHOLD),
        max_workers=correction_config.get('max_workers', Settings.MAX_CONCURRENT_WORKERS),
        batch_size=correction_config.get('batch_size', 10),
        min_success_rate=correction_config.get('min_success_rate', 0.80),
        min_paragraph_length=correction_config.get('min_paragraph_length', 20)
    )
