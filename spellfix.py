# spellfix.py
import re, enchant
from typing import Set

# ---------- Inizializza Hunspell/Enchant ---------
_DICT_IT = enchant.Dict("it_IT")      # carica il dizionario italiano
_WORD_RE = re.compile(r"\w+|\W+")     # tokenizza "parola / non-parola"

# ---------- Glossario personale ------------------
try:
    import json, pathlib
    _GLOSS_PATH = pathlib.Path(__file__).with_name("glossario_extra.json")
    _GLOSS_FIX  = json.loads(_GLOSS_PATH.read_text(encoding="utf-8"))
except FileNotFoundError:
    _GLOSS_FIX = {}

# ---------- Helpers ------------------------------
def _match_case(tgt: str, src: str) -> str:
    if src.isupper():      return tgt.upper()
    if src.islower():      return tgt.lower()
    if src[0].isupper():   return tgt.capitalize()
    return tgt

def _fix_token(tok: str, skip: Set[str]) -> str:
    raw = tok.strip("«»“”()[]{}.,;:!?")  # puntegg. out
    key = raw.lower()

    if not raw:
        return tok
    
    key = raw.lower()

    if key in skip:            # nomi propri ecc.
        return tok

    # 1-a) regola personalizzata
    if key in _GLOSS_FIX:
        return tok.replace(raw, _match_case(_GLOSS_FIX[key], raw))

    # 1-b) Hunspell con suggerimento UNIVOCO
    if not _DICT_IT.check(raw):
        sugg = _DICT_IT.suggest(raw)
        if len(sugg) == 1:
            return tok.replace(raw, _match_case(sugg[0], raw))

    return tok

# ---------- Funzione pubblica --------------------
def spellfix_paragraph(text: str, glossary: Set[str]) -> str:
    tokens = _WORD_RE.findall(text)          # suddividi parola / non-parola
    skip   = {w.lower() for w in glossary}   # nomi propri da non toccare
    fixed  = [_fix_token(tok, skip) for tok in tokens]
    return "".join(fixed)
