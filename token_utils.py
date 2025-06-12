 # token_utils.py
import re
import tiktoken
 
DEFAULT_MODEL = "gpt-4o-mini"
try:
    ENC = tiktoken.encoding_for_model(DEFAULT_MODEL)
except KeyError:
    ENC = tiktoken.get_encoding("cl100k_base")
    
WORD_RE = re.compile(r"\w+|\W+")

# ───────────────────────── Rilevazione Nomi Propri ──────────────────────────
# • PascalCase  (≥ 3 lettere, prima maiuscola, poi minuscole)
# • Acronimi ALL-CAPS corti (2-4 lettere: USA, ONU…)
#   Parole di servizio (CAPITOLO, INDICE, ecc.) sono filtrate altrove.
NAME_RE = re.compile(
    r"\b("                       # inizio gruppo
    r"[A-Z][a-z]{2,}\w*"         # PascalCase
    r"|"
    r"[A-Z]{2,4}"                # ALL-CAPS di 2-4 lettere
    r")\b"
)
# ─────────────────────────────────────────────────────────────────────────────
 
def tokenize(text: str):
    return WORD_RE.findall(text)

def count_tokens(text: str) -> int:
    """Conta i token reali secondo l’encoding del modello."""
    return len(ENC.encode(text or ""))
    
def token_starts(tokens):
    pos, starts = 0, []
    for tok in tokens:
        starts.append(pos)
        pos += len(tok)
    return starts

# (facoltativo) Helpers leggeri da importare altrove -------------------------
def find_names(text: str):
    """Restituisce l’insieme dei nomi propri trovati nel testo."""
    return set(NAME_RE.findall(text))

def is_name(word: str):
    """True se 'word' rispetta NAME_RE (versione singola)."""
    return bool(NAME_RE.fullmatch(word))
# ----------------------------------------------------------------------------
