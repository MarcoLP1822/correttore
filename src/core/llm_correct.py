import os, json, re, logging
from openai import AsyncOpenAI
from config.settings import OPENAI_MODEL, load_yaml_config
from src.services.cache_llm import get_cached, set_cached
from typing import List, Dict

# Carica configurazione temperatura
_config = load_yaml_config()
_temperature = _config.get('openai', {}).get('temperature', 0.2)

_SYSTEM_MSG = """
Sei un correttore di bozze ESPERTO madrelingua italiano con focus su PRECISIONE ASSOLUTA.

CORREZIONI PRIORITARIE (errori evidenti):
• ORTOGRAFIA: bottaga→bottega (NON bottaia!), ansiano→anziano, vlta→volta, fallegname→falegname
• SPAZI: "U giorno"→"Un giorno", "U uomo"→"Un uomo", spazi doppi→spazio singolo  
• GRAMMATICA H: "o fatto"→"ho fatto", "a detto"→"ha detto"
• ACCORDI: "la cane"→"il cane", "un'uomo"→"un uomo"
• APOSTROFI: pò→po', qual'è→qual è
• PUNTEGGIATURA: spazi dopo punti/virgole quando mancanti

METODO:
• Correggi SOLO errori evidenti e certi al 100%
• USA il dizionario italiano standard (bottega NON bottaia)
• Mantieni significato e stile originale
• NON riformulare o cambiare struttura frasi
• Se dubiti anche minimamente, NON correggere

Se tutto è già corretto, restituisci il testo invariato.

OUTPUT:
Restituisci **solo** JSON nel formato

{"corretto":"TESTO_CORRETTO_QUI"}

(non aggiungere testo fuori dal JSON)
"""

_BATCH_SYSTEM_MSG = """
Sei un correttore di bozze ESPERTO madrelingua italiano con focus su PRECISIONE ASSOLUTA.

CORREZIONI PRIORITARIE (errori evidenti):
• ORTOGRAFIA: bottaga→bottega (NON bottaia!), ansiano→anziano, vlta→volta, fallegname→falegname  
• SPAZI: "U giorno"→"Un giorno", "U uomo"→"Un uomo", spazi doppi→spazio singolo
• GRAMMATICA H: "o fatto"→"ho fatto", "a detto"→"ha detto"
• ACCORDI: "la cane"→"il cane", "un'uomo"→"un uomo"  
• APOSTROFI: pò→po', qual'è→qual è
• PUNTEGGIATURA: spazi dopo punti/virgole quando mancanti

METODO:
• Correggi SOLO errori evidenti e certi al 100%
• USA il dizionario italiano standard (bottega NON bottaia)
• Mantieni significato e stile originale
• NON riformulare o cambiare struttura frasi
• Se dubiti anche minimamente, NON correggere

Se tutto è già corretto, restituisci il testo invariato.

Riceverai un JSON con array "richieste" contenente oggetti con "id" e "txt".
Restituisci **solo** JSON nel formato:

{"correzioni":[{"id":0,"txt":"TESTO_CORRETTO_QUI"},{"id":1,"txt":"ALTRO_TESTO_CORRETTO"}]}

(non aggiungere testo fuori dal JSON)
"""

def _strip_fences(text: str) -> str:
    return re.sub(r"^```[\w]*\n?|```$", "", text.strip())

async def llm_correct(text: str, client: AsyncOpenAI) -> str:
    if not text.strip():
        return text

    print("[LLM] 👉 Invio a GPT:", text[:80].replace("\n", " "), "...")
    
    messages = [
        {"role": "system", "content": _SYSTEM_MSG},
        {"role": "user", "content": text.strip()},
    ]

    try:
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=_temperature,
            messages=messages,  # type: ignore  # OpenAI types are complex
            response_format={"type": "json_object"},
        )
        print("[LLM] ✅ Risposta ricevuta.")
        
        # Handle potential None content
        content = resp.choices[0].message.content
        if content is None:
            print("[LLM] ⚠️ Risposta vuota da GPT")
            return text
            
        raw = _strip_fences(content)
        data = json.loads(raw)
        return data.get("corretto", text)
    except Exception as e:
        print(f"[LLM] ❌ Errore GPT: {e}")
        return text
    
async def llm_correct_batch(texts: List[str], client: AsyncOpenAI) -> List[str]:
    """
    Corregge una lista di stringhe con cache support
    """
    logger = logging.getLogger("LLM-BATCH")

    # Cache check
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

    # Costruisci JSON richieste
    richieste = [{"id": i, "txt": txt} for i, txt in uncached]
    user_json = json.dumps({"richieste": richieste}, ensure_ascii=False)

    # Invia a GPT
    logger.info("Invio batch GPT  paragrafi=%d", len(uncached))
    
    try:
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=_temperature,
            messages=[
                {"role": "system", "content": _BATCH_SYSTEM_MSG},
                {"role": "user", "content": user_json},
            ],  # type: ignore  # OpenAI types are complex
            response_format={"type": "json_object"},
        )
        logger.info("✓ Batch GPT completato.")

        # Parse risposta
        content = resp.choices[0].message.content
        if content is None:
            logger.warning("Risposta GPT vuota per batch")
            return texts
            
        logger.debug(f"Risposta GPT batch: {content[:200]}...")
        raw = _strip_fences(content)
        
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"Errore JSON parsing batch GPT: {e}, raw: {raw[:500]}")
            # Fallback: restituisci testi originali
            for i, txt in uncached:
                out[i] = txt
            return [out[i] for i in range(len(texts))]
            
        correzioni = data.get("correzioni", [])
        logger.debug(f"Trovate {len(correzioni)} correzioni nel batch")
        
        # Applica correzioni
        for corr in correzioni:
            idx = corr.get("id")
            txt_corretto = corr.get("txt", "")
            if idx is not None and idx < len(uncached):
                original_idx, original_txt = uncached[idx]
                out[original_idx] = txt_corretto
                # Cache il risultato
                set_cached(original_txt, txt_corretto)
                logger.debug(f"Correzione applicata id={idx}: '{original_txt[:30]}...' -> '{txt_corretto[:30]}...'")
            else:
                logger.warning(f"ID correzione invalido: {idx}, max={len(uncached)}")
    
    except Exception as e:
        logger.error("Errore parsing batch GPT: %s", e)
        # Fallback: restituisci testi originali
        for i, txt in uncached:
            out[i] = txt

    return [out[i] for i in range(len(texts))]