import re, json, pathlib
from typing import Set
from difflib import get_close_matches
from token_utils import WORD_RE

_WORD_RE = re.compile(r"\w+|\W+")

# Carica glossario extra
try:
    _GLOSS_PATH = pathlib.Path(__file__).with_name("glossario_extra.json")
    _GLOSS_FIX = json.loads(_GLOSS_PATH.read_text(encoding="utf-8"))
except FileNotFoundError:
    _GLOSS_FIX = {}

def _match_case(tgt: str, src: str) -> str:
    if src.isupper(): return tgt.upper()
    if src.islower(): return tgt.lower()
    if src.istitle(): return tgt.capitalize()
    return tgt

def _fix_token(tok: str, skip: Set[str]) -> str:
    raw = tok.strip("«»“”()[]{}.,;:!?")
    key = raw.lower()
    if not raw or key in skip:
        return tok

    # 1. Correzione da glossario
    if key in _GLOSS_FIX:
        return tok.replace(raw, _match_case(_GLOSS_FIX[key], raw))

    # 2. Correzione con match vicino (fallback)
    close = get_close_matches(key, _GLOSS_FIX.keys(), n=1, cutoff=0.88)
    if close:
        return tok.replace(raw, _match_case(_GLOSS_FIX[close[0]], raw))

    return tok  # Nessuna correzione

from rapidfuzz import process, fuzz
CANONICAL = [l.strip() for l in open("glossario.txt", encoding="utf-8")]
THRESHOLD = 85  # 0-100

def spellfix_paragraph(text: str, _glossary=None) -> str:
    tokens = WORD_RE.findall(text)
    fixed = []
    for tok in tokens:
        raw = tok.strip("«»“”()[]{}.,;:!?")
        if not raw:
            fixed.append(tok); continue
        best = process.extractOne(raw, CANONICAL, scorer=fuzz.WRatio)
        if best:
            cand, score, _ = best

            # 1) scarta se il candidato contiene spazi
            # 2) scarta se la similarità è sotto 93
            if " " in cand or score < 93:
                fixed.append(tok)
                continue

            # Se supera i controlli, applica la correzione
            tok = tok.replace(raw, _match_case(cand, raw))
        fixed.append(tok)
    return "".join(fixed)
