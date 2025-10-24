# cache_llm.py
"""
Cache very-lightweight per evitare richieste duplicate a GPT.
Usa un dizionario serializzato su disco (.llm_cache.pkl).
"""

import hashlib
import os
import pickle
from pathlib import Path
from threading import Lock

_LOCK = Lock()
_CACHE_PATH = Path(".llm_cache.pkl")          # puoi spostarlo dove vuoi

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _load_cache() -> dict:
    if _CACHE_PATH.exists():
        with _CACHE_PATH.open("rb") as f:
            return pickle.load(f)
    return {}

_cache: dict[str, str] = _load_cache()        # chiave = sha256(text) → valore = testo corretto

def _save_cache() -> None:
    with _CACHE_PATH.open("wb") as f:
        pickle.dump(_cache, f)

# API pubblica usata in llm_correct.py ---------------------------------
def get_cached(text: str) -> str | None:
    return _cache.get(_hash(text))

def set_cached(text: str, corrected: str) -> None:
    with _LOCK:                              # sicurezza thread-safe
        _cache[_hash(text)] = corrected
        _save_cache()
