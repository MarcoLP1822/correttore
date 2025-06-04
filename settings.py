# settings.py
"""
Configurazione centralizzata dell’applicazione
(modello OpenAI, limiti token, retry, …)
"""

OPENAI_MODEL = "gpt-4o-mini"     # modello da usare ovunque
MAX_TOKENS   = 10_000            # contesto massimo per i prompt
RETRY_BACKOFF = (1, 2, 4)        # secondi di attesa ai retry
