"""
Sistema di Cache Intelligente per Correzioni - FASE 4
======================================================

Implementa cache avanzata con:
- Similarity matching per testi simili
- TTL configurabile e gestione persistente
- Metadata qualità correzioni
- Statistiche usage e hit rate
- Cleanup automatico scaduti
- Processamento parallelo ottimizzato
"""

import hashlib
import json
import pickle
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import sqlite3
from difflib import SequenceMatcher
from collections import OrderedDict

from correttore.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entry cache con metadata avanzati"""
    text_hash: str
    original_text: str
    corrected_text: str
    quality_score: float
    correction_type: str
    timestamp: float
    access_count: int = 0
    last_accessed: float = 0.0
    processing_time: float = 0.0
    token_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        return cls(**data)


@dataclass 
class CacheStats:
    """Statistiche cache dettagliate"""
    total_entries: int
    hit_rate: float
    miss_rate: float
    size_mb: float
    oldest_entry: Optional[str]
    newest_entry: Optional[str]
    top_accessed: List[Tuple[str, int]]
    expired_count: int
    avg_quality: float
    performance_gain: float


class IntelligentCache:
    """
    Sistema di cache intelligente per correzioni con similarity matching
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 24):
        """
        Inizializza cache intelligente
        
        Args:
            cache_dir: Directory cache (default: .cache/)
            ttl_hours: Time-to-live in ore
        """
        self.settings = get_settings()
        self.cache_dir = cache_dir or Path(".cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        self.ttl_hours = ttl_hours
        self.ttl_seconds = ttl_hours * 3600
        
        # Database SQLite per cache persistente
        self.db_path = self.cache_dir / "corrections_cache.db"
        self._init_database()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._lookups = 0
        self._lock = threading.RLock()
        
    def _init_database(self):
        """Inizializza database SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    text_hash TEXT PRIMARY KEY,
                    original_text TEXT NOT NULL,
                    corrected_text TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    correction_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL DEFAULT 0.0,
                    processing_time REAL DEFAULT 0.0,
                    token_count INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_quality_score ON cache_entries(quality_score)
            ''')
            conn.commit()
    
    def _compute_hash(self, text: str) -> str:
        """Computa hash univoco per testo"""
        # Normalizza testo per hash consistente
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Computa similarity score tra due testi"""
        return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()
    
    def get_exact_match(self, text: str) -> Optional[CacheEntry]:
        """Cerca match esatto in cache"""
        with self._lock:
            text_hash = self._compute_hash(text)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM cache_entries WHERE text_hash = ?
                ''', (text_hash,))
                
                row = cursor.fetchone()
                if row:
                    entry = CacheEntry(**dict(row))
                    
                    # Verifica TTL
                    if time.time() - entry.timestamp > self.ttl_seconds:
                        self._remove_entry(text_hash)
                        return None
                    
                    # Aggiorna accesso
                    self._update_access(text_hash)
                    return entry
                    
            return None
    
    def get_with_similarity(self, text: str, threshold: float = 0.95) -> Optional[CacheEntry]:
        """
        Cerca in cache con similarity matching
        
        Args:
            text: Testo da cercare
            threshold: Soglia similarity (0.0-1.0)
            
        Returns:
            CacheEntry se trovato match simile, None altrimenti
        """
        with self._lock:
            self._lookups += 1
            
            # Prima prova match esatto
            exact_match = self.get_exact_match(text)
            if exact_match:
                self._hits += 1
                logger.debug(f"Cache HIT (exact): {text[:50]}...")
                return exact_match
                
            # Cerca match per similitudine
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM cache_entries 
                    WHERE timestamp > ?
                    ORDER BY last_accessed DESC
                    LIMIT 100
                ''', (time.time() - self.ttl_seconds,))
                
                best_match = None
                best_similarity = 0.0
                
                for row in cursor:
                    entry = CacheEntry(**dict(row))
                    similarity = self._compute_similarity(text, entry.original_text)
                    
                    if similarity >= threshold and similarity > best_similarity:
                        best_similarity = similarity
                        best_match = entry
                
                if best_match:
                    self._hits += 1
                    self._update_access(best_match.text_hash)
                    logger.debug(f"Cache HIT (similarity {best_similarity:.3f}): {text[:50]}...")
                    return best_match
            
            self._misses += 1
            logger.debug(f"Cache MISS: {text[:50]}...")
            return None
    
    def cache_with_metadata(self, text: str, correction: str, quality: float, 
                          correction_type: str = "ai", processing_time: float = 0.0,
                          token_count: int = 0) -> None:
        """
        Caches correzione con metadata
        
        Args:
            text: Testo originale
            correction: Testo corretto
            quality: Score qualità (0.0-1.0)
            correction_type: Tipo correzione (spell/grammar/ai)
            processing_time: Tempo elaborazione in secondi
            token_count: Numero token processati
        """
        with self._lock:
            text_hash = self._compute_hash(text)
            timestamp = time.time()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO cache_entries 
                    (text_hash, original_text, corrected_text, quality_score, 
                     correction_type, timestamp, access_count, last_accessed,
                     processing_time, token_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    text_hash, text, correction, quality, correction_type, 
                    timestamp, 0, timestamp, processing_time, token_count
                ))
                conn.commit()
                
            logger.debug(f"Cached correction: {text[:50]}... (quality: {quality:.3f})")
    
    def _update_access(self, text_hash: str) -> None:
        """Aggiorna statistiche accesso"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE cache_entries 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE text_hash = ?
            ''', (time.time(), text_hash))
            conn.commit()
    
    def _remove_entry(self, text_hash: str) -> None:
        """Rimuove entry da cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM cache_entries WHERE text_hash = ?', (text_hash,))
            conn.commit()
    
    def cleanup_expired(self) -> int:
        """
        Pulisce entries scadute
        
        Returns:
            Numero entries rimosse
        """
        cutoff_time = time.time() - self.ttl_seconds
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM cache_entries WHERE timestamp < ?
            ''', (cutoff_time,))
            expired_count = cursor.fetchone()[0]
            
            conn.execute('DELETE FROM cache_entries WHERE timestamp < ?', (cutoff_time,))
            conn.commit()
            
        logger.info(f"Cleaned up {expired_count} expired cache entries")
        return expired_count
    
    def get_cache_stats(self) -> CacheStats:
        """Restituisce statistiche cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Count totale entries
            cursor = conn.execute('SELECT COUNT(*) as count FROM cache_entries')
            total_entries = cursor.fetchone()['count']
            
            # Oldest e newest entries  
            cursor = conn.execute('''
                SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest 
                FROM cache_entries
            ''')
            times = cursor.fetchone()
            oldest_entry = datetime.fromtimestamp(times['oldest']).isoformat() if times['oldest'] else None
            newest_entry = datetime.fromtimestamp(times['newest']).isoformat() if times['newest'] else None
            
            # Top accessed
            cursor = conn.execute('''
                SELECT text_hash, access_count 
                FROM cache_entries 
                ORDER BY access_count DESC 
                LIMIT 5
            ''')
            top_accessed = [(row['text_hash'][:8], row['access_count']) for row in cursor]
            
            # Expired count
            cutoff_time = time.time() - self.ttl_seconds
            cursor = conn.execute('SELECT COUNT(*) as count FROM cache_entries WHERE timestamp < ?', (cutoff_time,))
            expired_count = cursor.fetchone()['count']
            
            # Average quality
            cursor = conn.execute('SELECT AVG(quality_score) as avg_quality FROM cache_entries')
            avg_quality = cursor.fetchone()['avg_quality'] or 0.0
            
            # Performance gain estimation
            cursor = conn.execute('SELECT SUM(processing_time) as total_time FROM cache_entries WHERE access_count > 0')
            saved_time = cursor.fetchone()['total_time'] or 0.0
            
            # Size calculation (approximate)
            size_mb = (self.db_path.stat().st_size / 1024 / 1024) if self.db_path.exists() else 0.0
            
            # Rates
            hit_rate = (self._hits / self._lookups) if self._lookups > 0 else 0.0
            miss_rate = (self._misses / self._lookups) if self._lookups > 0 else 0.0
            
        return CacheStats(
            total_entries=total_entries,
            hit_rate=hit_rate,
            miss_rate=miss_rate,
            size_mb=size_mb,
            oldest_entry=oldest_entry,
            newest_entry=newest_entry,
            top_accessed=top_accessed,
            expired_count=expired_count,
            avg_quality=avg_quality,
            performance_gain=saved_time
        )
    
    def clear_cache(self) -> None:
        """Pulisce completamente la cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM cache_entries')
            conn.commit()
            
        self._hits = 0
        self._misses = 0
        self._lookups = 0
        logger.info("Cache cleared completely")
    
    def optimize_cache(self) -> Dict[str, int]:
        """
        Ottimizza cache rimuovendo entries poco utilizzate
        
        Returns:
            Statistiche ottimizzazione
        """
        removed_expired = self.cleanup_expired()
        
        # Rimuovi entries con basso usage e vecchie
        cutoff_time = time.time() - (self.ttl_seconds / 2)  # Metà TTL
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM cache_entries 
                WHERE access_count <= 1 AND timestamp < ?
            ''', (cutoff_time,))
            low_usage_count = cursor.fetchone()[0]
            
            conn.execute('''
                DELETE FROM cache_entries 
                WHERE access_count <= 1 AND timestamp < ?
            ''', (cutoff_time,))
            conn.commit()
        
        optimization_stats = {
            'removed_expired': removed_expired,
            'removed_low_usage': low_usage_count,
            'total_removed': removed_expired + low_usage_count
        }
        
        logger.info(f"Cache optimization: {optimization_stats}")
        return optimization_stats


# Cache globale singleton
_cache_instance: Optional[IntelligentCache] = None

def get_cache() -> IntelligentCache:
    """Restituisce istanza cache globale"""
    global _cache_instance
    if _cache_instance is None:
        settings = get_settings()
        _cache_instance = IntelligentCache(
            ttl_hours=getattr(settings, 'cache_ttl_hours', 24)
        )
    return _cache_instance


def clear_global_cache():
    """Pulisce cache globale"""
    global _cache_instance
    if _cache_instance:
        _cache_instance.clear_cache()
        _cache_instance = None
