# utils_openai.py
import asyncio, json, re, time, logging
from typing import List, Dict, Set
from openai import AsyncOpenAI, OpenAI, RateLimitError, APIConnectionError, BadRequestError
from settings import OPENAI_MODEL, RETRY_BACKOFF, MAX_RETRY

logger = logging.getLogger(__name__)

_FENCE_RE      = re.compile(r"^```[\w]*\n?|```$", re.S)

def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()

def _parse_corr(raw: str) -> List[Dict]:
    data = json.loads(raw)
    if "corr" not in data:
        raise ValueError("JSON senza chiave 'corr'")
    return data["corr"]

# ------------------------------------------------------------------ #
#  Prompt per il correttore
SYSTEM_MSG_BASE = """
Sei un correttore di bozze madrelingua italiano con decenni di esperienza.

• Correggi **solo** refusi, errori ortografici / grammaticali e punteggiatura.  
• Non eliminare, spostare o accorciare parole, frasi o capoversi.  
• Non riformulare lo stile; se una parte è già corretta, lasciala invariata.

NOMI / TERMINI FANTASY ↓  
Se trovi varianti ortografiche dei nomi presenti nell’elenco seguente,
uniforma la grafia a quella esatta dell’elenco.

OUTPUT: restituisci **SOLO JSON** con la chiave `'corr'`
( lista di {id:int, txt:str} ) — niente testo extra.
"""

def build_messages(context: str,
                   payload_json: str,
                   glossary: Set[str]) -> List[Dict]:
    system_msg = SYSTEM_MSG_BASE + "\\nLista: " + ", ".join(sorted(glossary))
    return [
        {"role": "system",    "content": system_msg},
        {"role": "assistant", "content": "Contesto (NON modificare):\\n" + context},
        {"role": "user",      "content": payload_json},
    ]
# ------------------------------------------------------------------ #
from random import uniform
from asyncio import sleep

async def _retry_async(call_coroutine, *, max_attempts, backoff_seq):
    """
    Esegue una coroutine con retry esponenziale e jitter.
    Restituisce il risultato o rilancia dopo max_attempts falliti.
    """
    for attempt, delay in enumerate((*backoff_seq, 0), start=1):
        try:
            return await call_coroutine()
        except (RateLimitError, APIConnectionError) as exc:
            if attempt >= max_attempts:
                logger.error("OpenAI: troppi errori (%s). Rinuncio.", exc)
                raise
            jitter = uniform(0, 0.3 * delay)
            wait = delay + jitter
            logger.warning("OpenAI errore (%s). Retry %s/%s fra %.1fs",
                           exc.__class__.__name__, attempt, max_attempts, wait)
            await sleep(wait)
        except BadRequestError as exc:
            # Context length exceeded o JSON malformato → non ritentare
            logger.error("Request non valida: %s", exc)
            raise

async def _chat_async(messages, client):
    async def _one_call():
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=messages,
        )
        return _parse_corr(_strip_fences(resp.choices[0].message.content))

    return await _retry_async(
        _one_call,
        max_attempts=MAX_RETRY,
        backoff_seq=RETRY_BACKOFF,
    )

# ========== FUNZIONI PUBBLICHE (quelle che userai da main.py) ====== #
async def get_corrections_async(payload_json: str,
                                client: AsyncOpenAI,
                                glossary: Set[str],
                                context: str = "") -> List[Dict]:
    msgs = build_messages(context, payload_json, glossary)
    return await _chat_async(msgs, client)

def get_corrections_sync(payload_json: str,
                         client: OpenAI,
                         glossary: Set[str],
                         context: str = "") -> List[Dict]:
    msgs = build_messages(context, payload_json, glossary)
    return _chat_async(msgs, client)
