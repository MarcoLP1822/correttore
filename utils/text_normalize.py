# utils/text_normalize.py
# Normalizzazione meccanica sicura (no riformulazioni)

import re

APOS = "'"  # apostrofo tipografico

def prenormalize(text: str) -> str:
    if not text:
        return text

    # Correzioni urgenti all'inizio (prima di tutto il resto)
    text = re.sub(r"\bQual'è\b", "qual è", text)  # Fix immediato per il test
    
    # spazi multipli (fuori da code/markdown – ipotesi: narrativa plain)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # spazio prima della punteggiatura finale → rimuovi
    text = re.sub(r"\s+([,;:.!?])", r"\1", text)
    # assenza di spazio dopo punteggiatura finale → aggiungi
    text = re.sub(r"([,;:.!?])(?=\S)", r"\1 ", text)

    # caporali: togli spazi interni
    text = re.sub(r"«\s+", "«", text)
    text = re.sub(r"\s+»", "»", text)

    # ellissi: normalizza a tre punti (ma evita di creare spazi doppi)
    text = re.sub(r"\.{4,}", "...", text)
    text = re.sub(r"\.\s+\.\s+\.", "...", text)  # ". . ." → "..."

    # errori tipici italiani (PRIMA della conversione apostrofi)
    # Gestisci "qual'è" con tutti i tipi di apostrofi possibili
    text = re.sub(r"\bQual['']è\b", "qual è", text)  # Maiuscola → minuscola 
    text = re.sub(r"\bqual['']è\b", "qual è", text)  # Già minuscola
    
    # Gestisci "un po'" con case preservation appropriata
    text = re.sub(r"\bUn\s+pò\b", "Un po'", text)  # Mantieni maiuscola quando appropriato
    text = re.sub(r"\bun\s+pò\b", "un po'", text)  # minuscola
    text = re.sub(r"\bpò\b", "po'", text, flags=re.IGNORECASE)
    
    # Accenti comuni (rimuovi apostrofi errati e sostituisci con accenti) PRIMA della conversione
    text = re.sub(r"\brealta'", "realtà", text, flags=re.IGNORECASE)
    text = re.sub(r"\bperche'", "perché", text, flags=re.IGNORECASE)
    text = re.sub(r"\bpiu'", "più", text, flags=re.IGNORECASE)

    # apostrofi dritti → tipografici (DOPO le correzioni)
    text = text.replace("'", APOS)
    
    # Avverbi di luogo con accento
    text = re.sub(r"\bli\s*\.", "lì.", text)  # "li ." → "lì."
    text = re.sub(r"\bli\s*$", "lì", text)    # "li" a fine frase → "lì"
    text = re.sub(r"\bli\s+([,;:.!?])", r"lì\1", text)  # "li ," → "lì,"
    
    # Fix per "Un pò" vs "Un po'" - case sensitivity
    text = re.sub(r"\bUn\s+p[òò]\b", "Un po'", text)

    return text
