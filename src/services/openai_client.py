# openai_client.py
"""
Ritorna sempre la stessa istanza di AsyncOpenAI
(lazy-loaded la prima volta che serve).
"""
import os
from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None

def get_async_client() -> AsyncOpenAI:
    """Istanza condivisa di AsyncOpenAI."""
    global _client
    if _client is None:                         # crea solo la prima volta
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client
