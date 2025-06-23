import os, json, re, logging
from openai import AsyncOpenAI
from settings import OPENAI_MODEL
from cache_llm import get_cached, set_cached
from typing import List, Dict

_SYSTEM_MSG = """
Sei un correttore di bozze madrelingua italiano con anni di esperienza editoriale.

Correggi solo:
• refusi
• accordi grammaticali (verbi, articoli, preposizioni)
• punteggiatura ambigua o mancante, senza alterare lo stile originale

Non fare le seguenti cose:
• Non spezzare o riformulare frasi.
• Non inserire punto e virgola.
• Non modificare lo stile dell'autore, anche se informale.
• Non rimuovere o cambiare interiezioni ("no?!?", "eh", "mah").

Se tutto è già corretto, restituisci il testo invariato.

Restituisci solo JSON nel formato:
{"corretto": "testo corretto"}
"""

def _strip_fences(text: str) -> str:
    return re.sub(r"^```[\w]*\n?|```$", "", text.strip())

async def llm_correct(text: str, client: AsyncOpenAI) -> str:
    if not text.strip():
        return text

    print("[LLM] 👉 Invio a GPT:", text[:80].replace("\n", " "), "...")
    messages = [
        {"role": "system",    "content": _SYSTEM_MSG},
        {"role": "user",      "content": text.strip()},
    ]

    try:
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            messages=messages,
            response_format={"type": "json_object"},
        )
        print("[LLM] ✅ Risposta ricevuta.")
        raw = _strip_fences(resp.choices[0].message.content)
        data = json.loads(raw)
        return data.get("corretto", text)
    except Exception as e:
        print(f"[LLM] ❌ Errore GPT: {e}")
        return text
    
async def llm_correct_batch(texts: List[str], client: AsyncOpenAI) -> List[str]:
    """
    Corregge una lista di stringhe. 1 Logga ogni fase e usa la cache.
    """
    logger = logging.getLogger("LLM-BATCH")

    # 2 Cache check
    out: Dict[int, str] = {}
    uncached = []
    for i, t in enumerate(texts):
        hit = get_cached(t)
        if hit is not None:
            logger.debug("Cache HIT  id=%s  '%s…'", i, t[:50])
            out[i] = hit
        else:
            logger.debug("Cache MISS id=%s  '%s…'", i, t[:50])
            uncached.append((i, t))

    if not uncached:
        logger.debug("Batch interamente risolto da cache.")
        return [out[i] for i in range(len(texts))]

    # 3 Costruisci JSON richieste
    richieste = [{"id": i, "txt": txt} for i, txt in uncached]
    user_json = json.dumps({"richieste": richieste}, ensure_ascii=False)

    # 4 Invia a GPT
    logger.info("Invio batch GPT  paragrafi=%d", len(uncached))
    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": _SYSTEM_MSG},
            {"role": "user",   "content": user_json},
        ],
        response_format={"type": "json_object"},
    )
    logger.info("✓ Batch GPT completato.")

    # Parsa la risposta JSON
    raw = _strip_fences(resp.choices[0].message.content)
    data = json.loads(raw)

    # 5. Mappa correzioni ricevute
    for item in data.get("correzioni", []):
        idx = item["id"]
        corr = item["txt"]
        out[idx] = corr
        set_cached(texts[idx], corr)

    # ➡️ PATCH: riempi eventuali id mancanti con il testo originale
    for idx, txt in enumerate(texts):
        if idx not in out:
            out[idx] = txt            # nessuna modifica da GPT

    # 6. Restituisci lista nell'ordine originale
    return [out[i] for i in range(len(texts))]
