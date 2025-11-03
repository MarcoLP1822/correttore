import os, json, re, logging
from openai import AsyncOpenAI
from correttore.config.settings import OPENAI_MODEL, load_yaml_config
from correttore.services.intelligent_cache import get_cached, set_cached
from typing import List, Dict

# Carica configurazione temperatura
_config = load_yaml_config()
_temperature = _config.get('openai', {}).get('temperature', 0.2)

_SYSTEM_MSG = """
Sei un correttore di bozze ESPERTO madrelingua italiano con focus su PRECISIONE ASSOLUTA.

CORREZIONI SPECIFICHE OBBLIGATORIE:
• bottaga → bottega (bottega = negozio di artigiano, NON "bottaia" che è recipiente!)
• vlta → volta (in "C'era una volta", NON "alta"!)
• sugu → sugo (sugo = condimento, NON "suga" che non esiste!)
• fato → fatto (participio passato di "fare")
• go → ho (verbo avere con H!)
• ansiano → anziano
• fallegname → falegname
• borggo → borgo
• milliore → migliore
• carezzzzavano → carezzavano
• cassella → casella
• strignendo → stringendo
• trasformazzione → trasformazione
• CAPTIOLO → CAPITOLO

ALTRI ERRORI COMUNI:
• SPAZI: "U giorno"→"Un giorno", spazi doppi→spazio singolo  
• GRAMMATICA H: "o fatto"→"ho fatto", "a detto"→"ha detto"
• ACCORDI: "la cane"→"il cane", "un'uomo"→"un uomo"
• APOSTROFI: pò→po', qual'è→qual è
• PUNTEGGIATURA: spazi dopo punti/virgole quando mancanti

REGOLE FERREE:
1. bottega = negozio artigiano (MAI bottaia!)
2. volta = "una volta" (MAI alta in questo contesto!)
3. sugo = condimento (MAI suga!)
4. Se vedi "bottaga" → SEMPRE "bottega"
5. Se vedi "vlta" in "C'era una vlta" → SEMPRE "volta"
6. Se vedi "sugu" → SEMPRE "sugo"

METODO:
• Correggi SOLO errori evidenti e certi al 100%
• USA il dizionario italiano standard
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

CORREZIONI SPECIFICHE OBBLIGATORIE:
• bottaga → bottega (bottega = negozio di artigiano, NON "bottaia" che è recipiente!)
• vlta → volta (in "C'era una volta", NON "alta"!)
• sugu → sugo (sugo = condimento, NON "suga" che non esiste!)
• fato → fatto (participio passato di "fare")
• go → ho (verbo avere con H!)
• ansiano → anziano
• fallegname → falegname
• borggo → borgo
• milliore → migliore
• carezzzzavano → carezzavano
• cassella → casella
• strignendo → stringendo
• trasformazzione → trasformazione
• CAPTIOLO → CAPITOLO

ALTRI ERRORI COMUNI:
• SPAZI: "U giorno"→"Un giorno", spazi doppi→spazio singolo
• GRAMMATICA H: "o fatto"→"ho fatto", "a detto"→"ha detto"
• ACCORDI: "la cane"→"il cane", "un'uomo"→"un uomo"  
• APOSTROFI: pò→po', qual'è→qual è
• PUNTEGGIATURA: spazi dopo punti/virgole quando mancanti

REGOLE FERREE:
1. bottega = negozio artigiano (MAI bottaia!)
2. volta = "una volta" (MAI alta in questo contesto!)
3. sugo = condimento (MAI suga!)
4. Se vedi "bottaga" → SEMPRE "bottega"
5. Se vedi "vlta" in "C'era una vlta" → SEMPRE "volta"
6. Se vedi "sugu" → SEMPRE "sugo"

METODO:
• Correggi SOLO errori evidenti e certi al 100%
• USA il dizionario italiano standard
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
        logger.debug(f"Trovate {len(correzioni)} correzioni nel batch di {len(uncached)} paragrafi")
        
        # Crea un mapping per le correzioni ricevute
        correzioni_map = {}
        for corr in correzioni:
            idx = corr.get("id")
            txt_corretto = corr.get("txt", "")
            if idx is not None:
                correzioni_map[idx] = txt_corretto
        
        # Applica correzioni a tutti i paragrafi uncached
        for i, (original_idx, original_txt) in enumerate(uncached):
            if i in correzioni_map:
                # Correzione disponibile
                txt_corretto = correzioni_map[i]
                out[original_idx] = txt_corretto
                # Cache il risultato
                set_cached(original_txt, txt_corretto)
                logger.debug(f"Correzione applicata id={i}: '{original_txt[:30]}...' -> '{txt_corretto[:30]}...'")
            else:
                # Nessuna correzione disponibile, mantieni originale
                out[original_idx] = original_txt
                logger.debug(f"Nessuna correzione per id={i}, mantenuto testo originale")
                # Cache anche i "non cambiamenti" per evitare retry
                set_cached(original_txt, original_txt)
    
    except Exception as e:
        logger.error("Errore parsing batch GPT: %s", e)
        # Fallback: restituisci testi originali
        for i, txt in uncached:
            out[i] = txt

    return [out[i] for i in range(len(texts))]