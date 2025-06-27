import re, json
from pathlib import Path
from typing import Set
from difflib import get_close_matches
from token_utils import WORD_RE         # già definito altrove
from rapidfuzz import process, fuzz

# ─── 1. Percorsi assoluti ───────────────────────────────────────────
_THIS_DIR   = Path(__file__).resolve().parent
GLOSS_PATH  = _THIS_DIR / "glossario.txt"
GLOSS_JSON  = _THIS_DIR / "glossario_extra.json"

# ─── 2. Caricamento glossari ────────────────────────────────────────
try:
    with GLOSS_PATH.open(encoding="utf-8") as fh:
        CANONICAL = [l.strip() for l in fh if l.strip()]
except FileNotFoundError:
    CANONICAL = []

try:
    _GLOSS_FIX: dict[str, str] = json.loads(GLOSS_JSON.read_text(encoding="utf-8"))
except FileNotFoundError:
    _GLOSS_FIX = {}

# ─── 3. Helpers interni ──────────────────────────────────────────────
def _match_case(tgt: str, src: str) -> str:
    if src.isupper():  return tgt.upper()
    if src.islower():  return tgt.lower()
    if src.istitle():  return tgt.capitalize()
    return tgt

def _fix_token(tok: str, skip: Set[str]) -> str:
    raw = tok.strip("«»“”()[]{}.,;:!?")
    key = raw.lower()
    if not raw or key in skip:
      return tok
    # 3a. correzione da glossario_extra.json
    if key in _GLOSS_FIX:
        return tok.replace(raw, _match_case(_GLOSS_FIX[key], raw))
    # 3b. fallback fuzzy sul glossario.txt
    best = process.extractOne(raw, CANONICAL, scorer=fuzz.WRatio)
    if best:
        cand, score, _ = best
        if " " not in cand and score >= 93:
            return tok.replace(raw, _match_case(cand, raw))
    return tok

# ─── 4. Funzione pubblica ───────────────────────────────────────────
def spellfix_paragraph(text: str, skip_glossary: Set[str] | None = None) -> str:
    """
    Corregge refusi basandosi su glossario_extra.json (priorità) e,
    in seconda battuta, su glossario.txt con un match fuzzy (score ≥ 93).

    `skip_glossary` serve per evitare di toccare nomi già confermati nel
    glossario dinamico (passato dal resto del programma).
    """
    skip_glossary = skip_glossary or set()
    tokens = WORD_RE.findall(text)
    fixed  = [_fix_token(tok, skip_glossary) for tok in tokens]
    return "".join(fixed)
